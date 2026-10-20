# SNEAK — Final Planner Handoff and Canonical Root Question v1

**Handoff ID:** `SNEAK-CANONICAL-HANDOFF-20261020-001`  
**Date:** 2026-10-20  
**Decision:** `ROOT_QUESTION_V1_APPROVED_BY_USER` (the owner asked to finalize the previously proposed question)  
**Repository:** `biobitworks/sneak` (private)  
**Integration branch:** `deploy/sneak-vercel-preview-20261020`  
**Parent evidence commit:** `fc84c7d15538c6858be95798ade0b9a08c270646`  
**Target BAND agent:** `@biobitworks.sneak-planner` (handle proposed; remote identity not yet independently verified)  
**Target room:** `SNEAK — Orchestration & Evidence` (proposed; room ID not verified)  
**Delivery:** `PREPARED_FOR_BAND_NOT_SENT` until BAND returns a native message ID and readback.

## Canonical root question — v1 (frozen)

> Does every authorized SNEAK agent conversation produce evidence-bound FCO transitions with deterministic inputs and outputs, per-actor and per-model MMR histories, BAND handoffs, and verifiable Cognee recall?

The wording is now ratified as the *evaluation objective*. Keep existing historical FCOs and Merkle/MMR identities unchanged; do not rewrite earlier ledger records to insert this approval retroactively. Any canonical approval event must be an append-only FCO successor with its own committed source bytes and parent identity. A wording revision creates root-question v2, never an in-place replacement.

### Bounds of authorization

Only ingest SNEAK conversations and source materials for which this project has legitimate access and permission. Never assume access to all private ChatGPT conversations, BAND rooms, connected accounts, human source datasets or other people's messages. Complete coverage requires a rights-bound source manifest, pagination, deduplication and independent replay; an absent source is `NOT_IMPORTED`, not silently accepted.

## Implementation contract

For every authorized observed conversation message, planner question, agent answer, model execution, human decision, or task-state change:

1. **Source/input:** bind provider, source URI or room/message ID, rights/authorization, actor identity, measured model ID and version *if observed*, event time and exact-byte input SHA-256. Preserve raw private content only in an authorized access-controlled backend; publish hash-only projections.
2. **Deterministic execution:** bind script identity SHA-256, ordered steps, parameters, context version, parent breakpoint and per-step results. Do not confuse model-generated reasoning with deterministic execution.
3. **FCO:** create a content-addressed immutable observation/decision object, explicit provenance, expected/observed results, exception state, source evidence and independent proof. Include Anticube/ΔG* only with defined inputs and computations; otherwise `NOT_COMPUTED`.
4. **Output:** hash the canonical output, creating an append-only successor referencing the input, script and predecessor FCO.
5. **Custody:** append to the root-question MMR, global actor stream, and an actor-specific MMR. Append to a per-model MMR **only** when an authenticated model+version mapping exists. Compute checkpoint Merkle root and MMR root/peaks/proof using the declared versioned hash construction, retain all predecessor roots and exact leaf ordering.
6. **Verdict and delta:** track `TRUE` (supported by independent tests), `FALSE` (contradicted), or `UNKNOWN` (not established) separately from `custody_replay_bool`. Quality/ROI deltas require comparable measured baselines; changes to hash bits or Merkle roots are not an improvement metric.
7. **Coordination:** use BAND's *native* participant IDs for `@mentions`; require actual room ID, message ID, sender ID and readback. Cognee stores bounded authorized hash/FCO summaries, reads them back in a separate process or independent agent, and binds changed next action to a new FCO. Do not claim downstream planner synchronization merely because Cognee wrote a record.
8. **Security:** run Snyk Code and Snyk Open Source on the exact eligible commit, resolve findings and scanner errors; run Snyk Container only for an identified image. A failed scan is an `ERROR`, never evidence of zero findings. Keep the security release gate `BLOCKED` until full accepted coverage and required decisions are evidenced.

## Current independently replayed baseline

| Evidence family | Observed baseline |
| --- | --- |
| Historical BAND capture | 3 recorded messages in one earlier room, 2 actor streams (Tom/Jerry); **not** all project conversations |
| Conversation FCOs | 3 linked message FCOs and 3 progressive Merkle/MMR breakpoints |
| Per-model MMR | `NOT_COMPUTED`: model/version attribution missing in historic messages |
| Root-question historical MMR | `0f4cb205de724e3b0eba55afedfd6f165f23399f32da7ac656aadb46c3a114d4` |
| Local Cognee OSS | Actual write and separate-process recall; 1 matched recall; deterministic next action requests BAND handoff and Snyk proofs |
| Question MMR after Cognee FCOs | `adbfad2620262d7bb63e8907f84f28def008940a32116d736dfdbf5427e36a3d` |
| Exact-byte Vercel export Merkle root | `d44d9dd6a21f772b673b9286f75ec27948b6d3da52abea6885165dfb5a1a6d1c` |
| Exact-byte Vercel export MMR root | `829acc5e8d9499539bfcbd0d14bfaa8bebf27e3c4de0763207cc882ea8f366f1` |
| Vercel export | 18 declared file leaves, 34 MMR nodes; includes the protected conversation lineage and heatmap |
| Structural LOMO | 80 local synthetic ablation cases; does not demonstrate 80 real actor/model trials |
| Test receipts | 46 Python and 10 Node tests observed passing at predecessor |
| BAND planner / room | CLI previously `NO_ACCOUNT`; new room ID, planner remote identity and real message delivery `NOT_VERIFIED` |
| Security | Snyk Code authentication error, Snyk Open Source dependency-resolution error; Snyk Container `NOT_TESTED` |
| Mandatory acceptance | Not independently established; judge acceptance `NOT_OBSERVED` |

These roots each belong to their **explicit scopes** and are not interchangeable. The canonical approval in this document does **not** claim a newly computed root, MMR, model delta, signature or updated scan.

### Source references

- [Protocol](../docs/SNEAK_CONVERSATION_LINEAGE_PROTOCOL_20261020.md)
- [Historical conversation ledger](../deploy/vercel-preview/data/conversation-lineage.json)
- [Cognee write/recall successor receipt](../receipts/conversations/SNEAK_CONVERSATION_COGNEE_BP001_20261020.json)
- [Previous end-to-end breakpoint](../receipts/conversations/SNEAK_CONVERSATION_END_TO_END_BP002_20261020.json)
- [Remote planner onboarding](../docs/BAND_PLANNER_ROOM_20261020.md)
- [Native handoff proposal](../docs/BAND_PLANNER_CONVERSATION_LINEAGE_HANDOFF_20261020.md)
- [Protected SNEAK conversation viewer](https://sneak-evidence-preview-r97pkjmu2-biobitworks.vercel.app/conversations)
- [Draft integration PR #11](https://github.com/biobitworks/sneak/pull/11)

## BAND planner: first handoff after authentication

To `@biobitworks.sneak-planner` in the **verified room**, using native BAND mention rather than merely typing an `@` string:

> **SNEAK canonical question v1 is approved.** Read `docs/SNEAK_FINAL_PLANNER_HANDOFF_20261020.md` and confirm the exact GitHub commit, root-question text and predecessor roots. Verify your own agent ID, provider runtime and model/version; show the real room ID and participants. Attach the plan and create a shared board with Snyk Code/OSS remediation, Cognee source-bound recall, authorized full-conversation ingestion, independent Merkle/MMR replay, model attribution, real agent LOMO, Flexprice token/agent/model/human ROI, and judged MVP acceptance. `@mention` verified Claude/Codex, Snyk and Cognee agents using native participant IDs. Post an acknowledgment with the actual BAND message ID, claimed task IDs, evidence FCOs, current gate state and next action. **Do not close a task or mark the security gate clear without replayed executed evidence.**

### Required room procedure

Confirm `band preflight` is ready and `band whoami` is the authorized account. Confirm `band room list`, `band room participants <room_id>` and the exact planner participant ID. Attach the Markdown plan via `band plan set ... --snapshot`; read it back. Use `band room send <room_id> <content> --mention <planner_id>` and `band room messages <room_id> --json` for exact delivery/readback. Verify `band work board <room_id>`, assign/take/status changes, and a **planner-authored** response. No step advances to `OBSERVED` solely based on intended commands.

## Task ownership and fail-closed acceptance

| Lane | Handoff owner | Next independently verifiable artifact | Gate |
| --- | --- | --- | --- |
| Planner / BAND | SNEAK Planner | Account + agent + room/member IDs; native mentions, message IDs, plan and board readback | BLOCKED_ON_AUTH |
| Authorized conversation import | Intake + planner | Source/rights manifest with paginated room coverage and exact-message FCOs | NOT_TESTED_FULL_SCOPE |
| Cognee / FCG | Cognee agent | Actual write→read→changed action across *two verified agent runtimes*, with pointer receipts | LOCAL_TEST_PASS; CROSS_AGENT_NOT_TESTED |
| Merkle/MMR | Independent verifier / Codex | Recalculate all scoped sources; root-question and per-actor/model MMR proofs; negative tamper tests | PARTIAL_EXECUTED |
| Security | Snyk reviewer | Authenticated commit-bound Code + OSS results, issue triage, signed scan gate decision; Container only with image | BLOCKED |
| Model/LOMO | Model evaluation agent | Per-model runtime/version, frozen baseline/ablation and measured deltas | NOT_TESTED |
| Flexprice / ROI | Billing evaluator | Grounded per-token, per-agent, per-model, per-human usage and cost comparisons | NOT_ACCEPTED |
| Human & judges | Owner / event judges | Actual human decision and official hackathon submission/evaluation receipt | NOT_OBSERVED |

## Immutable handoff acceptance rules

`PROPOSED → IMPLEMENTED → EXECUTED → OBSERVED → SUPPORTED` are distinct; no inferred upgrades. Preserve `FAILED`, `NULL`, `NEGATIVE`, `DEFERRED`, `NOT_TESTED`, `UNKNOWN`, and `NOT_COMPUTED`. All new evidence objects require exact input, output, script, predecessor and versioned digest commitments. No fabricated Merkle root, MMR root, agent response, Snyk clean score or judge acceptance.

**Handoff completion status:** `GITHUB_DOCUMENT_PREPARED`. BAND room delivery and planner acknowledgment remain `NOT_SENT / NOT_OBSERVED` until authenticated verification. This document should be used verbatim as the handoff source of truth after verification.
