# Requirements review (2026-10-20T22:00Z)

Reviewer: claude-redteam (Claude Opus 5.5) on magicSTUDIObox / magicPRObox. Proposed states, not verdicts. Mandatory SUPPORTED: **0/30**. Entry gate: **FALSE**. Security app score: **NOT_COMPUTED**.

| Atom | Level | Requirement | Reviewed state | Evidence / note |
|---|---|---|---|---|
| M01 | mandatory | Use actual Band Desktop. | OBSERVED | Desktop app runs; agents connect through band-sdk, not shown as Desktop-coordinated. band-desktop process observed on magicPRObox (pid 64146) |
| M02 | mandatory | Band coordinates the agent team. | NOT_TESTED | no receipt found. — |
| M03 | mandatory | Agents share one actual room. | OBSERVED | CORRECTED from SUPPORTED: only the captured record's hash was recomputed; BAND was not queried and no verdict successor exists. receipt-level. receipts/band/SNEAK-013_HANDOFF.json (root 29002d5e…, recomputed RT-22) |
| M04 | mandatory | At least two agents participate. | OBSERVED | CORRECTED from SUPPORTED: only the captured record's hash was recomputed; BAND was not queried and no verdict successor exists. receipt-level. receipts/band/SNEAK-013_HANDOFF.json (root 29002d5e…, recomputed RT-22) |
| M05 | mandatory | Lead/architect writes the plan in the room. | NOT_TESTED | no receipt found. — |
| M06 | mandatory | Team works from one plan. | NOT_TESTED | no receipt found. — |
| M07 | mandatory | Team uses one shared work board. | NOT_TESTED | no receipt found. — |
| M08 | mandatory | Agents claim work items. | NOT_TESTED | no receipt found. — |
| M09 | mandatory | Actual task transitions include To-do and Done. | NOT_TESTED | no receipt found. — |
| M10 | mandatory | Agents address each other with mentions. | OBSERVED | CORRECTED from SUPPORTED: only the captured record's hash was recomputed; BAND was not queried and no verdict successor exists. receipt-level. receipts/band/SNEAK-013_HANDOFF.json (root 29002d5e…, recomputed RT-22) |
| M11 | mandatory | Agents hand context directly to other agents. | OBSERVED | CORRECTED from SUPPORTED: only the captured record's hash was recomputed; BAND was not queried and no verdict successor exists. receipt-level. receipts/band/SNEAK-013_HANDOFF.json (root 29002d5e…, recomputed RT-22) |
| M12 | mandatory | Handoff succeeds without human copying. | OBSERVED | CORRECTED from SUPPORTED: only the captured record's hash was recomputed; BAND was not queried and no verdict successor exists. receipt-level; handoff initiated by an agent via API. receipts/band/SNEAK-013_HANDOFF.json (root 29002d5e…, recomputed RT-22) |
| M13 | mandatory | At least one real decision or approval occurs. | NOT_TESTED | request exists; no human response; PR #5 APPROVE is hard-coded, rejected. SNEAK-H01 request in BAND room 20f1ee5f…, human_response=null; PR #5 (merged to main a67be28) scripts/run_lomo_snyk_breakpoints.py hard-codes APPROVE (RT-30) |
| M14 | mandatory | Human receives that decision through Band. | NOT_TESTED | as M13. SNEAK-H01 request in BAND room 20f1ee5f…, human_response=null; PR #5 (merged to main a67be28) scripts/run_lomo_snyk_breakpoints.py hard-codes APPROVE (RT-30) |
| M15 | mandatory | Decision is not hard-coded. | NOT_TESTED | the only 'approval' on record is hard-coded, which is what M15 forbids. PR #5 (merged to main a67be28) scripts/run_lomo_snyk_breakpoints.py hard-codes APPROVE (RT-30) |
| M16 | mandatory | Demo shows Band Desktop rooms. | NOT_TESTED | no receipt found. — |
| M17 | mandatory | Demo shows the work board. | NOT_TESTED | no receipt found. — |
| M18 | mandatory | Demo shows per-agent sessions. | NOT_TESTED | no receipt found. — |
| M19 | mandatory | Demo shows token counts. | NOT_TESTED | no receipt found. — |
| M20 | mandatory | Demo shows estimated costs. | NOT_TESTED | no receipt found. — |
| M21 | mandatory | Use Cognee Open Source. | NOT_TESTED | only Cognee Cloud exercised; rule requires Cognee Open Source. PR #3 receipts/integration/SNEAK-20261020-INTEGRATION-001.json (Cognee Cloud add/cognify/search 200) |
| M22 | mandatory | Cognee serves as working memory. | NOT_TESTED | no receipt found. — |
| M23 | mandatory | Demonstrate working memory rather than only static storage. | NOT_TESTED | no receipt found. — |
| M24 | mandatory | Agents write memory while doing the task. | OBSERVED | receipt-level writes on Cognee Cloud. PR #3 receipts/integration/SNEAK-20261020-INTEGRATION-001.json (Cognee Cloud add/cognify/search 200); PR #5 receipts/connectors/SNEAK-015_LIVE_BAND_COGNEE.json (3 recall hits) |
| M25 | mandatory | Agents actually recall stored memory. | OBSERVED | receipt-level recall on Cognee Cloud. PR #3 receipts/integration/SNEAK-20261020-INTEGRATION-001.json (Cognee Cloud add/cognify/search 200); PR #5 receipts/connectors/SNEAK-015_LIVE_BAND_COGNEE.json (3 recall hits) |
| M26 | mandatory | Recalled memory changes a subsequent action. | NOT_TESTED | cross_agent_changed_behavior NOT_TESTED. PR #3 receipts/integration/SNEAK-20261020-INTEGRATION-001.json (Cognee Cloud add/cognify/search 200) |
| M27 | mandatory | Demonstrate recall after restart OR between different agents; either is sufficient. | NOT_TESTED | no restart or cross-agent behaviour diff. PR #3 receipts/integration/SNEAK-20261020-INTEGRATION-001.json (Cognee Cloud add/cognify/search 200) |
| M28 | mandatory | BAND is essential: removing it changes required product behavior. | NOT_TESTED | no receipt found. — |
| M29 | mandatory | Cognee is essential: removing it changes required product behavior. | NOT_TESTED | no receipt found. — |
| M30 | mandatory | Address qualitative deep-integration review; Boolean tests alone do not guarantee qualification. | NOT_TESTED | no receipt found. — |
| E01 | scoring_enrichment | Use different agent harnesses for higher-scoring collaboration. | UNKNOWN | both live BAND agents run Claude SDK; other-harness authorship unverified. RT-33: Jerry process runs ClaudeSDKAdapter; 'ChatGPT→Jerry' authorship UNKNOWN |
| E02 | scoring_enrichment | Demonstrate improve OR forget OR graph-backend connection; preserve this alternative choice. | NOT_TESTED | no receipt found. — |
| F01 | bonus_selected | Send and read back actual usage events in Flexprice test mode. | NOT_TESTED | no usage event sent and read back. RT-27: Flexprice v2.17 running, no meter/plan/event |
| F02 | bonus_selected | Connect those events to a configured test pricing model. | NOT_TESTED | no pricing model configured. RT-27: Flexprice v2.17 running, no meter/plan/event |
| F03 | scoring_enrichment | Demonstrate product behavior driven by metering. | NOT_TESTED | no receipt found. — |
| F04 | scoring_enrichment | Optional example: credits gate a feature. | NOT_TESTED | no receipt found. — |
| F05 | scoring_enrichment | Optional alternative example: observed BAND costs pass through to test billing. | NOT_TESTED | no receipt found. — |
| S01 | bonus_selected | Use a real Snyk scanning product; alternatives are not all mandatory. | EXECUTED | real Snyk Code scans ran; SCA never completed. Snyk Code 1.1307.2 scans of main 979a4f7, PR#4 3d7c9f0, PR#8 edf9cbe: 4 low (PT) each (RT-29); PR #3 INTEGRATION-001..003: SCA exit 3 / exit 2, no report |
| S02 | bonus_selected | Scan the exact artifact built by the agents. | EXECUTED | scanned repository commits; no agent-built app yet. Snyk Code 1.1307.2 scans of main 979a4f7, PR#4 3d7c9f0, PR#8 edf9cbe: 4 low (PT) each (RT-29) |
| S03 | scoring_enrichment | Give security review an actual team role. | NOT_TESTED | no receipt found. — |
| S04 | scoring_enrichment | Security reviewer participates in the BAND room. | NOT_TESTED | no receipt found. — |
| S05 | scoring_enrichment | Security reviewer runs Snyk scans. | NOT_TESTED | no receipt found. — |
| S06 | scoring_enrichment | Security reviewer posts actual findings. | NOT_TESTED | no receipt found. — |
| S07 | scoring_enrichment | A finding actually blocks completion until a verified fix. | NOT_TESTED | no receipt found. — |
| S08 | scoring_enrichment | Store recurring issue evidence in Cognee working memory. | NOT_TESTED | no receipt found. — |
| S09 | scoring_enrichment | Demonstrate recalled security memory changes behavior on a repeated task. | NOT_TESTED | no receipt found. — |
