# SNEAK-013 independent red-team review

Successor of SNEAK-012. Reviewer: Claude (Opus 5.5) on magicSTUDIObox.local, branch `redteam/claude-20261020` from `origin/main` @ `ee7432bf551451fc620df270a86a986a23000d46`. Python 3.15.0, Node v26.0.0, git 2.54.0. `main` not modified. No score is computed or claimed.

Machine-readable findings: `redteam/findings_SNEAK-013.jsonl`. Raw audit output: `redteam/out/audit_result.json`, `redteam/out/aok_identity.jsonl`, `redteam/out/audit_stdout.txt`. Reproduce with `python3 redteam/audit_redteam.py` (writes only under `redteam/out/`).

## 1. Remote state preserved

`git fetch --all --prune` (exit 0). Local `main` left at `bbd99be`, one behind `origin/main` (`ee7432b`, SNEAK-012 BAND bootstrap). Preserved without rewriting: `origin/custody/markdown-exact-20261020` (`d93dc18`), `predecessor/main` (`bbcffb7`), `predecessor-local/main` (`fc7a6e8`), the R4/R5 snapshots, `receipts/NOTEBOOK_R4_INCOMPLETE.json`, `TEST_RED.txt` and the author negative checks. No stashes.

## 2. Custody verifiers and tests

| Check | Exit | State |
|---|---|---|
| `custody_snapshot.py verify SNAPSHOT.json` | 0 | SUPPORTED (root `dcabcb5d…`, 167 leaves, commit `2662f8e`) |
| `custody_snapshot.py verify SNAPSHOT_MERGED.json` | 0 | SUPPORTED (root `6fcec1a8…`, 179 leaves, commit `48e72e9`) |
| `verify_custody_snapshot.mjs` both receipts | 0 | SUPPORTED, same roots |
| `python3 -m unittest discover -s tests -v` | 0 | 8 tests OK |
| Independent recomputation (own code, `git archive` path, no project imports) | 0 | SUPPORTED: both roots and all leaf records identical |

Tamper suite against the project's own Python **and** Node verifiers, in a disposable clone:

| Case | Expected | Observed |
|---|---|---|
| control | ACCEPT | ACCEPT |
| copied file byte, leaf hash, record sha, root, ordering swap, proof direction, missing manifest member, snapshot commit swap | REJECT | REJECT (all 8) |
| receipt claims `signed: true` | REJECT | **ACCEPT** |
| receipt claims `mmr: COMMITTED` | REJECT | **ACCEPT** |
| receipt rewrites `meaning` | REJECT | **ACCEPT** |

**RT-03 FAILED (medium).** `check()` compares only six keys. A receipt can assert SIGNED or MMR_COMMITTED and still pass both verifiers, contrary to the AGENTS.md rule. Fix: compare the full regenerated receipt.

## 3. Source PDF and AoK identities

**PDF hash discrepancy: UNKNOWN.** I did not reproduce a discrepancy at this commit. Three tracked copies, the zip member, `INTEGRITY.sha256` and all 99 textual references equal `f9c730d4c6464cdfeedb540e0d4b6080b7bfcde9fab496a1eac0dbc15b0aa1cc` (117,881 bytes). A human needs to say where the discrepancy was seen.

What is a real identity gap (RT-05): R5 occurrences index an **assistant transcription** of a pasted excerpt (`478045e4…`), not PDF bytes. `pdf_sha256` sits beside the offsets but does not ground them, and 0/46 FCG edges target the PDF. Quote presence on the declared PDF page is SUPPORTED 46/46, but only after NFKC and whitespace normalisation of the independent extraction.

Recomputed identities (RT-06, SUPPORTED): content 46/46, context 46/46, FCO 46/46, offsets 46/46, FCG node identity 46/46, FCG edge context 46/46.

Observed weaknesses:
- RT-07 (medium): `fco_candidate_sha256` hashes `verified`, `pass_gate`, `observed_outcome` and `evidence`, so recording any verdict changes the FCO identity.
- RT-08 (low): M28 and M29 share one span and an identical `context_sha256`. M19 "tokens" occurs twice; `str.index` happens to pick the right one. `pdf_page` is assigned from the ID prefix rather than derived.
- RT-09 (low): the committed FCG has 47 nodes (one extra SourceFCO) but the committed ingest script emits 46, so the artefact is not the script's output as-is.
- RT-10: the Markdown "exact bytes" branch forks from `d421d17`, not main. It adds a trailing newline to match reported sizes only; no source hash exists. State IMPLEMENTED; exactness UNKNOWN.

## 4. LOMO

All 80 matrix rows remain NOT_EXECUTED. I ran one-component **graph** ablations on the 46-atom AoK set. Removing source-atom, occurrence-context or policy-binding changed the graph root, so those ablations are EXECUTED. Rights-binding, scan-receipt, memory-reference, authorization-receipt and parent-breakpoint are not represented in the graph at all, so removing them is a no-op (NOT_TESTED). **Runtime behaviour: NOT_TESTED for every row.** No application, agent action or authorization gate exists to observe, and a graph change is not runtime evidence.

## 5. Requirements against real receipts

| Atoms | Evidence | State |
|---|---|---|
| M01 Band **Desktop** | Agents run via band-sdk, not Desktop; `desktop_acceptance` NOT_TESTED | NOT_TESTED |
| M02–M04 room, two agents | SNEAK-012: both agents connected (OBSERVED by this reviewer: 7/7 file hashes, PIDs 61365/61385 live, credential files 0600). Tom reply is receipt-only in a deleted test room; Jerry reply NOT_TESTED; no shared persistent room | OBSERVED (connection) / NOT_TESTED (shared room) |
| M05–M12 plan, board, claims, handoffs | No room, board or handoff record | NOT_TESTED |
| **M13–M15 human decision via BAND** | No human event record exists | **NOT_TESTED. Not satisfiable until a real human answers inside BAND.** |
| M16–M20 Desktop views, tokens, cost | none | NOT_TESTED |
| M21–M27 Cognee | see below | NOT_TESTED |
| M28–M30 essentiality, judge | none | NOT_TESTED |
| E01–E02 | none | NOT_TESTED |
| S01–S09 Snyk, F01–F05 Flexprice | no receipts | NOT_TESTED; scores NOT_COMPUTED |

<a id="cognee"></a>**Cognee (RT-14).** The supplied endpoint is a **Cognee Cloud** tenant (`*.aws.cognee.ai`). The rule text requires Cognee **Open Source**, so whether a Cloud tenant satisfies M21 needs a human decision. Observed: `/openapi.json` 200, `/health` 200, `GET /api/v1/datasets/` 200 with `X-Api-Key`. Skills (`GET/POST /api/v1/skills/`) and agents endpoints exist in the tenant spec but were not exercised; they are paused pending the owner's confirmation of key use. No write, recall or behaviour-change receipt exists.

## 6. Security findings

- RT-17 (high): the BAND user key and Cognee key were pasted in chat and appear in remote command text. Rotate both.
- RT-16 (medium): the live Tom and Jerry agents use band-sdk 6.0.1 `ClaudeSDKAdapter` defaults: `permission_mode=acceptEdits`, `approvals=None`, running on the owner's claude.ai login. Any room participant who @mentions them can induce edits and spend. Exploit NOT_TESTED. Configuring chat-based approvals would also provide the M13–M15 path.
- RT-03 (medium): unbound receipt metadata (above).
- RT-20 (low): the R6 inventory walks the working tree, including untracked files, and rewrites its receipt in place.

## 7–8. Branch, PR and takeover

This report is on `redteam/claude-20261020`; the PR targets `main` and must not be merged without human approval. No takeover was performed (RT-19). The architect's last commit was at 11:57 local; no persistent BAND room or board exists, so there is no BAND task ownership to inspect, and no lease mechanism is implemented. I withheld my own pending Tom and Jerry provisioning because SNEAK-012 had already created those agents, and running it would have duplicated them. Divergence from owner intent (RT-18): the owner asked for Ollama local models on magicstudio, but SNEAK-012 used `claude_sdk` on magicPRObox.

## Human decisions requested

1. Where was the PDF hash discrepancy observed?
2. Is Cognee Cloud acceptable for M21, or must this run on Cognee OSS?
3. Should Tom and Jerry stay on `claude_sdk`/magicpro, or move to Ollama/magicstudio?
4. Make one real approval decision inside a BAND room. Only that can move M13–M15.

## Successor addendum: SNEAK-014-REDTEAM (after origin/main 979a4f7)

While this review ran, the architect (Codex) pushed its own **SNEAK-013**, a BAND handoff. This review is therefore re-identified as **SNEAK-014-REDTEAM** with parent SNEAK-013. RT-01..RT-20 are retained unchanged; RT-21..RT-24 append, and RT-22 and RT-23 supersede RT-19 and RT-13.

- **RT-22 SUPPORTED.** The SNEAK-013 event root `29002d5e…` (3 leaves) reproduces independently (`redteam/verify_band_events.py`). A persistent room, "Sneak — Requirements & Custody", now holds Byron, Tom and Jerry, with a Tom→Jerry @mention handoff and an acknowledgement. Room contents are receipt-only; I did not query BAND.
- **RT-23: HITL still NOT_TESTED.** Decision SNEAK-H01 (MCP-delivered vs CLI-delivered skill review first?) was posted to you by Tom at 19:00:30Z. `human_response` is null. The request is OBSERVED; the decision does not exist yet.
- **RT-24 SUPPORTED at receipt level** for M03, M04, M10, M11 and M12. M01 (BAND **Desktop**) remains NOT_TESTED.
- **Takeover:** the architect is active, with three commits at about 12:10 local, so no takeover is warranted.
