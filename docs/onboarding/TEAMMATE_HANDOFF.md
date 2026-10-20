# Teammate handoff: contributing to Sneak as an FCO

Status: IMPLEMENTED (tooling and tests). No teammate contribution has been minted yet.
Base: `origin/main` @ `979a4f7` (SNEAK-013 BAND handoff).

## What Sneak is, in one paragraph

Sneak is a private requirements-and-evidence project for the SF Startup Challenge. BAND coordinates the agents, Cognee holds working memory, and Snyk and Flexprice are optional bonuses. Every claim must be backed by a receipt that someone else can recompute. Read `AGENTS.md` and `START_HERE_SNEAK.md` first; they are short and they are the rules.

## Current state (do not assume more than this)

- All 46 requirement atoms: `verified=false`. The entry gate is FALSE.
- BAND: room "Sneak — Requirements & Custody" exists with Byron, Tom and Jerry. A Tom→Jerry handoff is SUPPORTED at receipt level. Human decision SNEAK-H01 is PENDING.
- Cognee, Snyk, Flexprice and LOMO runtime trials: NOT_TESTED. Flexprice self-host install is in progress on magicstudio.
- Open red-team review: draft PR #4 (`redteam/claude-20261020`). It lists 24 findings you should not re-introduce.

## Your work becomes an FCO

An FCO (first-class object) is a ledger entry that binds your **committed** files to a unique ID anyone can recompute.

```
fco_sha256 = SHA256(canonical JSON of: schema, contributor, kind, title,
                    requirement_ids, parent_fco_ids, source_commit,
                    artifacts[path, size_bytes, sha256 read from Git])
fco_id     = "FCO-" + first 16 hex of fco_sha256
```

- The ID covers only immutable fields. States and verdicts are separate append-only `status` records, so a later verdict never changes your ID. This fixes red-team finding RT-07.
- File bytes are read from Git at `source_commit`, not from your working tree. Commit first, then mint.
- `minted_at` and `at` timestamps are stored but are not part of the identity.
- The ledger is `data/contributions/fco_ledger.jsonl`. It is append-only: never edit or delete a line. A correction is a new FCO with `--parent` pointing at the old one.

## Steps

1. **Get access.** Byron adds you to the private repo `biobitworks/sneak` and to the BAND room. Do not accept credentials over chat; use a password manager or env file.
2. **Branch from main.**
   ```
   git clone https://github.com/biobitworks/sneak && cd sneak
   git checkout -b contrib/<your-handle>/<short-topic>
   ```
3. **Do the work, then commit it.** Keep secrets out: no `.env`, keys, tokens or `agent_config.yaml`. The minting tool refuses files that look like secrets, but don't rely on it.
4. **Mint your FCO** (handle = lowercase letters, digits, hyphens):
   ```
   python3 scripts/contribution_fco.py mint \
     --contributor <your-handle> --kind code \
     --title "One-line description of what this adds" \
     --commit HEAD --path path/to/file.py --path tests/test_file.py \
     --requirement REQ-AOK-M24
   ```
   - `--kind`: code, data, doc, test, receipt, finding, notebook or config.
   - `--requirement`: zero or more atom IDs from `data/rules/atomic_acceptance_r5.jsonl` that the work is *meant* to address. Linking is not proof.
   - `--parent`: an earlier FCO this builds on or corrects (repeatable).
   The tool prints your `fco_id`. Your FCO starts as PROPOSED.
5. **Record what actually happened**, one status per real event:
   ```
   python3 scripts/contribution_fco.py status --fco FCO-xxxxxxxxxxxxxxxx \
     --state EXECUTED --actor <your-handle> --evidence receipts/<your-receipt>.json \
     --note "ran X; exit 0"
   ```
   SUPPORTED requires at least one committed evidence file. Do not set SUPPORTED on your own work alone; leave that to an independent verifier.
6. **Verify, commit the ledger, open a PR.**
   ```
   python3 scripts/contribution_fco.py verify
   python3 -m unittest discover -s tests -v
   git add data/contributions/fco_ledger.jsonl && git commit -m "fco: <fco_id> <title>"
   git push -u origin HEAD && gh pr create --draft --base main
   ```
   Put your `fco_id` in the PR title and description. Main changes only with Byron's approval.
7. **Say it in BAND.** Post in "Sneak — Requirements & Custody": your `fco_id`, the PR link, and which work item you are claiming. Claim before you start, so two people or agents don't do the same work.

## State vocabulary (use exactly)

| State | Means |
|---|---|
| PROPOSED | Planned or minted; nothing run |
| IMPLEMENTED | Code or data exists |
| EXECUTED | It ran; exit code recorded |
| OBSERVED | Someone saw a specific effect |
| SUPPORTED | Independently checked against committed evidence |
| FAILED / NEGATIVE | Ran and did not meet expectation / produced a negative result |
| NOT_TESTED / UNKNOWN / NOT_COMPUTED | Not run / cannot tell / value not calculated |

## Rules that will get a PR sent back

- Claiming SIGNED, MMR_COMMITTED, "vulnerability-free", a score, or a bonus without a receipt.
- A human approval that did not come from an actual human. Only a real reply in BAND counts for M13–M15.
- Editing or deleting existing receipts, snapshots or ledger lines. Append successors instead.
- Committing secrets, `SNYK_TOKEN`, or third-party upstream code before licensing is resolved.
- Writing to Overwatch or any live source of truth.

## Where to pick up work

From `docs/superpowers/plans/2026-10-20-sneak-requirements-build-r8.md`, these items have no receipts yet:
- Cognee working memory with a recall that changes an agent's next action (M21–M27).
- A shared BAND board with claimed items moved To-do→Done (M05–M09).
- Snyk scan of the built app with a blocking finding (S01–S07).
- Flexprice usage events read back from the self-hosted instance (F01–F02).
- Fixing red-team findings RT-03 (verifier ignores receipt metadata) and RT-07 for the R5 atoms.

Ask in the BAND room which of these is unclaimed before starting.

## Worked example

This onboarding kit is itself the first FCO in the ledger (contributor `claude-redteam`). Run `python3 scripts/contribution_fco.py verify` to recompute it.
