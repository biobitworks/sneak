# Agent failures despite being asked

Branches scanned: 18. Script sha256 `a46420c8f712b78b…`. Every row cites a file blob hash on GitHub.

## claude: YES (7 failure records, evidence root `410a13775e415bc5…`, proof BP-08c217ed08ec600c)

| File | Kind | Asked for | Example markers |
|---|---|---|---|
| `data/breakpoints/FAILURE_PROOFS.json#F2` | wrong | Owner request in this session | self-disclosed=Cognee tenant API called with the pasted key from magicstudio before the owner confirmed key use. |
| `data/breakpoints/FAILURE_PROOFS.json#F3` | wrong | Owner request in this session | self-disclosed=Marked M03/M04/M10-M12 SUPPORTED from a receipt-hash check only. |
| `data/breakpoints/FAILURE_PROOFS.json#F4` | wrong | Owner request in this session | self-disclosed=Claude's commits carry Byron's name and email, unsigned. |
| `data/breakpoints/FAILURE_PROOFS.json#F5` | wrong | Owner request in this session | self-disclosed=Claude's GitHub comments were posted from the owner's account. |
| `data/breakpoints/FAILURE_PROOFS.json#F6` | wrong | Owner request in this session | self-disclosed=Proof-of-work labelled SUPPORTED though checker and checked work share one author. |
| `data/breakpoints/FAILURE_PROOFS.json#F8` | wrong | Owner request in this session | self-disclosed=Engineering failures: cross-run nondeterminism, secret check hit own test, Flexprice attempt 1 failed, two ledger bugs. |
| `data/breakpoints/FAILURE_PROOFS.json#F9` | wrong | Owner request in this session | self-disclosed=Successor IDs collided with the architect's numbering twice. |

## codex-or-byron: YES (36 failure records, evidence root `9cea790b127dd4df…`, proof BP-c12d741ad9d9a7a5)

| File | Kind | Asked for | Example markers |
|---|---|---|---|
| `receipts/NOTEBOOK_R5_EXECUTION.json` | error | AGENTS.md: reproducible notebooks | .execution=FAILED |
| `receipts/VERIFIER_CORRECTION_R6.json` | error | AGENTS.md / plan | .predecessor_verification=FAILED |
| `receipts/integrations/SNEAK-014_CUSTODY.json` | error | Snyk S01-S09 | .leaves[3].event.payload.sast.exit=exit 1; .leaves[4].event.payload.green[0].text=Process started with PID 54506 (shell: /bin/sh)
Initial output:
{"phase": "GREEN", "exit": 0, "output": "test_all_proofs |
| `receipts/integrations/SNEAK-014_EVIDENCE.json` | error | Snyk S01-S09 | .events[2].payload.sast.exit=exit 1; .events[3].payload.green[0].text=Process started with PID 54506 (shell: /bin/sh)
Initial output:
{"phase": "GREEN", "exit": 0, "output": "test_all_proofs |
| `receipts/integrations/SNEAK-014_NOTEBOOK_FAILURE.json` | error | AGENTS.md: reproducible notebooks | .observed=FAILED |
| `receipts/integrations/divergent-local-20261020/SNEAK-014_CUSTODY.json` | error | Snyk S01-S09 | .leaves[3].event.payload.sast.exit=exit 1; .leaves[4].event.payload.green[0].text=Process started with PID 54506 (shell: /bin/sh)
Initial output:
{"phase": "GREEN", "exit": 0, "output": "test_all_proofs |
| `receipts/band/SNEAK_PLANNER_ONBOARDING_STEP001_20261020.json` | error | BAND M01-M20 | .evidence.band_room_list.exit_code=exit 1; .evidence.band_room_list.outcome=BLOCKED_AUTH; .evidence.band_whoami.exit_code=exit 1 |
| `receipts/conversations/SNEAK_CANONICAL_HANDOFF_BP003_20261020.json` | gate_blocked | Snyk S01-S09 | .fco.security_release_gate=BLOCKED; .snyk_gate=BLOCKED |
| `receipts/conversations/SNEAK_CONVERSATION_COGNEE_BP001_20261020.json` | gate_blocked | Cognee M21-M27, Snyk S01-S09 | .fco_transitions[0].snyk_gate=BLOCKED; .fco_transitions[1].snyk_gate=BLOCKED |
| `receipts/conversations/SNEAK_CONVERSATION_END_TO_END_BP002_20261020.json` | error | Snyk S01-S09 | .observed.security_release_gate=BLOCKED; .observed.snyk_latest=AUTH_ERROR_OR_DEPENDENCY_ERROR |
| `receipts/sneak_mvp/TURN_BREAKPOINT_MVP_20261020_001.json` | gate_blocked | Snyk S01-S09 | .OBSERVED.snyk_gate=BLOCKED |
| `receipts/sneak_mvp/scans/SNYK_20261020T192812.json` | error | Snyk S01-S09 | .exit_code=exit 1; .gate=BLOCKED |
| `receipts/sneak_mvp/scans/SNYK_20261020T193617.json` | error | Snyk S01-S09 | .exit_code=exit 1; .gate=BLOCKED |
| `receipts/sneak_mvp/scans/SNYK_20261020T205559.json` | error | Snyk S01-S09 | .exit_code=exit 2; .gate=BLOCKED; .outcome=ERROR |
| `receipts/vercel/SNEAK_AUTH_RETRY_BP003_20261020.json` | error | Owner request: deploy preview, Snyk S01-S09 | .OBSERVED.security_gate=BLOCKED; .OBSERVED.snyk_code_scan=ERROR_AUTHENTICATION; .OBSERVED.snyk_oauth=FAILED_TIMEOUT |
| `receipts/vercel/SNEAK_EXPORT_HEATMAP_BP002_20261020.json` | error | Owner request: deploy preview, Snyk S01-S09 | .OBSERVED.snyk_code_scan.exit_code=exit 2; .OBSERVED.snyk_code_scan.gate=BLOCKED; .OBSERVED.snyk_code_scan.result=ERROR |
| `receipts/vercel/SNEAK_VERCEL_20261020_001.json` | wrong | Owner request: deploy preview, Snyk S01-S09 | .deployments[0].classification=UNINTENDED_INITIAL_PRODUCTION_ASSIGNMENT; SSO_PROTECTED; .observed.snyk_gate=BLOCKED |
| `receipts/connectors/SNEAK-018_R15_LIVE_REVIEW.json` | error | Snyk S01-S09 | .payload.security.sca=FAILED dependency resolution; exit 2; .payload.security.security_gate=DENY |
| `receipts/evaluations/LMEV2_20261020_PILOT.json` | gate_blocked | AGENTS.md / plan | .security_admission=DENY |
| `receipts/evaluations/LMEV2_20261020_SECURITY.json` | error | Snyk S01-S09 | .security_gate=DENY; .snyk_code_exit=exit 1; .snyk_sca_exit=exit 2 |
| `receipts/evaluations/LMEV2_20261020_SNYK_AUTH_FAILURE.json` | error | Snyk S01-S09 | .accepted_security=DENY; .scanner_result=FAILED_AUTH |
| `receipts/evaluations/SNEAK_20261020_CONVERSATION_FEDERATION_V1_CORRECTED.json` | gate_blocked | AGENTS.md / plan | .security_admission=DENY |
| `receipts/integrations/SNEAK_SPONSOR_TRAVERSAL_V1_20261020.json` | error | Snyk S01-S09 | .provider_e2e_verdict=FAILED_OR_PARTIAL; .snyk.scan.exit_code=exit 2 |
| `receipts/integrations/SNEAK_SPONSOR_TRAVERSAL_V2_20261020.json` | error | Snyk S01-S09 | .snyk_exact_target_scan=FAILED_AUTHENTICATION |
| `receipts/requirements/SNEAK_AOK_M01_M30_CLOSEOUT_20261020.json` | error | AGENTS.md / plan | .records[0].attempt_evidence_status=FAILED |
| `receipts/integration/SNEAK-20261020-INTEGRATION-001.json` | error | Snyk S01-S09 | .sast_exit=exit 1; .sca_exit=exit 3 |
| `receipts/integration/SNEAK-20261020-INTEGRATION-002.json` | error | Snyk S01-S09 | .interpretation=DENY; no clean SCA evidence; three of eight SAST results are test-fixture secret-pattern detections; remainder PT rules;; .sast_exit=exit 1; .sca_exit=exit 3 |
| `receipts/integration/SNEAK-20261020-INTEGRATION-003.json` | error | Snyk S01-S09 | .sast_exit=exit 1; .sca_exit=exit 2; .security_gate=DENY |
| `receipts/connectors/SNEAK-021_REGISTERED_LOMO.json` | gate_blocked | AGENTS.md / plan | .security_admission=DENY |
| `receipts/connectors/SNEAK-022_SECURITY_REVIEW.json` | error | Snyk S01-S09 | .statement.classification.gate=DENY; .statement.sast.exit_code=exit 1; .statement.sca.exit_code=exit 2 |
| `receipts/sneak_mvp/TURN_BREAKPOINT_MVP_20261020_002.json` | error | Snyk S01-S09 | .OBSERVED.snyk_code.gate=BLOCKED; .OBSERVED.snyk_manifest.exit_code=exit 2; .OBSERVED.snyk_manifest.status=ERROR |
| `receipts/sneak_mvp/TURN_BREAKPOINT_MVP_20261020_003.json` | gate_blocked | Snyk S01-S09 | .OBSERVED.snyk_successor.gate=BLOCKED |
| `receipts/sneak_mvp/scans/SCA_INTEGRATION_MANIFEST_20261020.json` | error | Snyk S01-S09 | .exit_code=exit 2; .gate=BLOCKED |
| `receipts/sneak_mvp/scans/SNYK_20261020T202526.json` | error | Snyk S01-S09 | .exit_code=exit 1; .gate=BLOCKED |
| `receipts/sneak_mvp/scans/SNYK_20261020T202556.json` | error | Snyk S01-S09 | .exit_code=exit 3; .gate=BLOCKED; .outcome=ERROR |
| `receipts/sneak_mvp/scans/SNYK_20261020T203453.json` | error | Snyk S01-S09 | .exit_code=exit 1; .gate=BLOCKED |

## cursor: YES (3 failure records, evidence root `aed7ddd4095f0e3e…`, proof BP-cc01c51e6831dd51)

| File | Kind | Asked for | Example markers |
|---|---|---|---|
| `receipts/connectors/SNEAK-017B_BAND_RELAY.json` | gate_blocked | BAND M01-M20, Owner request: Ollama on magicstudio | .leaves[1].record.payload.ollama=BLOCKED_NEEDS_HUMAN_SHELL_APPROVAL; .leaves[2].record.payload.ollama=BLOCKED_NEEDS_HUMAN_SHELL_APPROVAL |
| `scripts/run_lomo_snyk_breakpoints.py` | wrong | Human decision M13-M15 | source=hard-coded human APPROVE (RT-30) |
| `receipts/connectors/SNEAK-028_AOK_MVP_LEDGER.json` | gate_blocked | AGENTS.md / plan | .requirements[13].reason=Blocked on M13: no qualifying human decision to route through Band yet. |

## Integrations (evidence-based)

| Integration | State | Note |
|---|---|---|
| snyk_in_github | NOT_TESTED | No Snyk check/status on any PR head; Snyk ran only as local CLI, with recorded auth and dependency errors. |
| snyk_local_cli | EXECUTED | Real snyk code test runs exist (RT-29; PR #3 receipts); SCA never completed; recent runs failed auth. |
| band | OBSERVED (receipt-level) | Room 20f1ee5f with Byron/Tom/Jerry captured in SNEAK-013/015 receipts; no human decision; BAND Desktop board NOT_TESTED. |
| cognee | OBSERVED (receipt-level, Cognee Cloud) | Cloud writes/recalls in PR #3/#5 receipts; Cognee Open Source (required M21) NOT_TESTED. |
| flexprice | EXECUTED (self-host up, RT-27) | No usage event sent and read back; ROI NOT_COMPUTED. |
| vercel | OBSERVED | Claude curl: 5 sneak-evidence-preview URLs incl. production alias return 302 to Vercel SSO; content not viewable without login. |
