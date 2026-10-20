# SNEAK: root-question conversation custody and cross-agent continuation

## Objective and scoped acceptance
Canonical root-question candidate (PROPOSED, awaiting owner selection):
> Does every authorized SNEAK agent conversation produce evidence-bound FCO transitions with deterministic inputs and outputs, per-actor and per-model MMR histories, BAND handoffs, and verifiable Cognee recall?

Scope is opted-in SNEAK project rooms and receipts, not every private ChatGPT conversation, external BAND room, or connected app. Do not index personal chats or message content without explicit source authority. Source permissions and rights accompany each FCO. A missing conversation source is a coverage gap; it must never be inferred from gaps in an MMR.

## Event transformation contract
An event enters as authenticated BAND message ID, room ID, actor identity, timestamp, exact raw bytes in local-only transient memory, provider and exact model/version when independently evidenced. User-controlled and tool text is untrusted. Never grant instructions or security permissions based only on a model-generated event.
1. INPUT: SHA-256 of exact source message UTF-8 bytes; source capture receipt SHA-256; source event root (receipt-level Merkle), plus PARENT FCO and immutable context version.
2. STEPS: deterministic, named operations with immutable script-byte SHA-256, ordered parameters and outputs. Reject missing input, invalid source leaf/root, tampered canonicalization, incompatible lineage, unauthorized scope, and unsigned claimed approvals.
3. FCO: content-addressed SHA-256(0x00 || canonical FCO body), explicit actor vs actual model/version. Include each decision, classification, observation, result, predecessor, evidence references and Anticube/ΔG* fields where defined.
4. OUTPUT: SHA-256 over canonical output record; task verdict and proof state are distinct. Hash identity is not correctness.
5. CHECKPOINT: append FCO to global question MMR, agent-specific MMR, and (only with provider-model-version evidence) per-model MMR; compute question-event Merkle root, MMR size/peaks/proof; retain every predecessor and negative outcome.
6. SYNC: BAND agent @mentions and human approvals must be observed by server IDs and readback. Cognee OSS adds a least-privilege, hash-only digest of authorized FCOs then recalls it in an independent process; a recalled policy can alter next actions only after exact content checks. Update the planner's room with the receipt ID and root; no assumed delivery.

## Truth and delta semantics
At any time t, evidence integrity is TRUE only after exact independent replay, FALSE if tampered/contradicted, UNKNOWN when replay is unavailable. Root-question claim state TRUE (supported), FALSE (contradicted), or UNKNOWN (insufficient evidence). Use NULL for unavailable literal boolean, not FALSE. Performance deltas require frozen task/evaluation baseline with comparable measurements and elapsed time. A changed hash/MMR root is only evidence of changed data, never an accuracy, learning or improvement score.
For each actor/model stream, record (root_t, size_t, parent_breakpoint, action_t, verdict_t, independent_evidence_t, latency/usage if sourced). Compare verdict transitions and evaluated measurements across t. Unidentified model versions remain UNKNOWN and may not be assigned the agent's actor MMR.

## Implemented bounded replay (Oct 20, 2026)
- Source receipts/band/SNEAK-013_HANDOFF.json: three captured authenticated-source messages from an archived single BAND room, two actor streams (Tom/Jerry), no authenticated model-version metadata.
- scripts/sneak_conversation_ledger.py validates source Merkle and leaf bytes, derives event FCOs and three progressive question breakpoints, computes per-actor/global/root-question MMRs, writes no raw conversation text, and fails closed on mutation.
- scripts/cognee_sync_lineage.py executed Cognee OSS 1.6.5 local write and separate-process recall using Ollama. Source-bound FCO successor receipts record both operations and a new question MMR; no BAND room send was observed.
- Vercel SSO preview: /conversations shows only hashed lineage, per-actor streams and explicitly missing model lanes. /heatmap hosts separate 80 synthetic LOMO structural trials; neither substitutes for full cross-agent acceptance.

## Remaining controls (NOT_TESTED or BLOCKED)
- Authenticate BAND Desktop CLI account, collect authoritative room IDs, register @biobitworks.sneak-planner, verify member IDs and runtime liveness. User must approve connection; previous temporary device codes expired.
- Attach room plan and shared board, record native @mentions, actual task claim/status transitions, planner reply and HITL answer with exact source IDs; poll/read back in BAND.
- Execute per-model provenance extraction from authenticated runtime host-session and token telemetry, not guessed display names. Import all explicitly authorized room pages with pagination, signed/identified sources, dedupe and rights enforcement; do not claim all conversations until manifest coverage verified.
- Connect Cognee to *every newly admitted, authorized* FCO, not indiscriminate raw messages. Verify changed downstream action and replay after restart/alternate agent.
- Independently rerun Snyk CLI Code+Open Source against exact committed source; preserve auth and dependency scan errors. Container only with a concrete image identity. Compute Anticube/ΔG* only with defined formula and real inputs. Preserve NOT_COMPUTED otherwise.
- Final MMR aggregation must name the precise root question, ordered included streams and exclusions, commit and context version. Do not merge incompatible MMR recipes, pretend a root equality is validation, or auto-accept all requirements.

## Reproduction
1. python3 -m scripts.sneak_conversation_ledger build
2. python3 -m scripts.sneak_conversation_ledger verify
3. python3 -m unittest tests.test_conversation_ledger tests.test_cognee_lineage_receipt
4. node --test tests/test_conversation_ledger_node.mjs
5. python3 -m scripts.build_vercel_preview; node --test tests/test_export_mmr_node.mjs

Output statuses PROPOSED, IMPLEMENTED, EXECUTED, OBSERVED, SUPPORTED, FAILED, NOT_TESTED, UNKNOWN and NOT_COMPUTED remain distinct. Explicit user authorization to proceed is not equivalent to live message acceptance or judge qualification.
