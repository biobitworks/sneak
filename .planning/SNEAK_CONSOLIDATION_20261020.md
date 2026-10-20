# SNEAK consolidation · GSD successor · 2026-10-20

ID: SNEAK-CON-20261020-001
PARENT: SNEAK-MVP-20261020-BP-001; parent Git `7793cfe684273e55dcadf5ddd98339c6b6ad196a`.
Working branch: `integration/sneak-consolidation-20261020`. Preserve all predecessor commits and receipts, including failed/not-tested outcomes.

## Product
SNEAK (So Now Every Agent Knows) is an evidence-governed security/retrieval framework.
Product-facing local interface: `python3 -m apps.sneak_mvp.server --port 8773`.
Audit-only interface: `/audit`, `/api/audit`, `/api/check`, and `/api/stack`.
A graph node is an occurrence or recorded integration candidate, never proof that a provider action occurred. Invariant: hashes establish byte identity, not truth; Merkle integrity is not scientific validation or security authorization.

## Ingested predecessor branches (source-identified, no merge of remote histories)
- `origin/cursor/connector-custody-review-0c2f`: SNEAK security/connector framework and tests.
- `origin/integration/cognee-flexprice-r14`: hosted Cognee, Snyk, notebook and Flexprice candidate receipts.
- `origin/integration/band-cognee-snyk-20261020`: BAND role scaffolding, scanner guard and runbooks; skipped conflicting Cognee implementation.
- `origin/docs/merkle-mmr-knowledge-base`: Merkle/MMR reference code and documentation.
- `origin/redteam/claude-20261020`: red-team findings and audit artifacts.
- Full original branch histories remain on GitHub. The consolidated manifest binds import paths to their source commit and SHA-256 (see `receipts/sneak_mvp/TEAMMATE_IMPORT_20261020.json`). Preserved exact source bytes where unchanged; the compatibility client and hardening scripts are recorded as successors.

## Checked
- Import candidate: 107 files, 101 exact copies, 4 compatibility successors, 1 new implementation, 1 patched predecessor. Candidate Merkle root computed and verified. NOT a canonical MMR.
- 114 Python unit/integration-contract tests PASS (real external providers not inferred from mocks).
- 5 Node path and unbound-receipt-metadata tests PASS.
- Both prior snapshot receipts still recompute exactly from frozen source commits; working tree differs by design after implementation.
- SNEAK main graph includes integration candidate nodes and exposes strict read-only provider checks, with no API keys or arbitrary executable tool endpoint.

## Next acceptance gates (must independently execute)
1. BAND Desktop local account: `band whoami` must pass. Create/inspect a genuine room with Claude and Codex different harnesses, live direct handoff, shared plan/board and human answered approval.
2. Verify Cognee OSS memory write, restart/agent recall and observed subsequent dispatched action within BAND. Existing process-level recall is real, but does not prove agent-owned end-to-end action.
3. Scan exact clean consolidation commit with Snyk Code/SCA; classify and remediate findings, never claim a clean scan on an older target.
4. Execute secure context-replay and negative-path tests, independently evaluate human-approved gate and authenticity of event receipts. Keep malicious remembered text non-authoritative.
5. Record per-agent session/token/cost Band Desktop screenshots and final required 2–3 minute demo. Flexprice live metering optional and not yet established.

Current mandatory atom gate: 0/30 accepted. Do not mark completed from code presence or imported receipts alone; append only a successor after actual verification.

## Claim states
IMPLEMENTED: Consolidation code, adapter compatibility, read-only web-stack checks, provenance manifest, metadata tamper guards.
EXECUTED/OBSERVED: 114 Python and 5 Node local tests, manifest verification.
NOT_TESTED: Live BAND Desktop room/board/approval/tokens, new cross-provider runtime, Flexprice meter and billing.
FAILED/BLOCKED: Latest Snyk prior branch found 2 low issues, and target is stale for new consolidation code; release gate BLOCKED.
MMR: NOT_COMPUTED. SIGNED: NO. Anticube/DeltaG*: NOT_COMPUTED for this increment.
