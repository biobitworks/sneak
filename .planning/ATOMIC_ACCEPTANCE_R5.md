# Atomic event acceptance: R5

Successor to IP-20261020-004. Each obligation has source/context identity and an explicit Boolean gate. verified=false means no qualifying execution evidence yet; it does not convert NOT_TESTED/UNKNOWN into an observed failure. Only the mandatory atoms gate entry. Selected bonus conditions and optional top-mark examples remain distinct. An OR clause is not silently rewritten into requiring every alternative. Identical quote bytes in different requirements retain separate identities.

| Atom | Level | Independently testable requirement | Verified | Observed | Test |
|---|---|---|---|---|---|
| REQ-AOK-M01 | mandatory | Use actual Band Desktop. | FALSE | NOT_TESTED | band-runtime |
| REQ-AOK-M02 | mandatory | Band coordinates the agent team. | FALSE | NOT_TESTED | band-coordination |
| REQ-AOK-M03 | mandatory | Agents share one actual room. | FALSE | NOT_TESTED | band-room |
| REQ-AOK-M04 | mandatory | At least two agents participate. | FALSE | NOT_TESTED | band-two-agents |
| REQ-AOK-M05 | mandatory | Lead/architect writes the plan in the room. | FALSE | NOT_TESTED | band-plan-author |
| REQ-AOK-M06 | mandatory | Team works from one plan. | FALSE | NOT_TESTED | band-one-plan |
| REQ-AOK-M07 | mandatory | Team uses one shared work board. | FALSE | NOT_TESTED | band-one-board |
| REQ-AOK-M08 | mandatory | Agents claim work items. | FALSE | NOT_TESTED | band-claim |
| REQ-AOK-M09 | mandatory | Actual task transitions include To-do and Done. | FALSE | NOT_TESTED | band-board-transition |
| REQ-AOK-M10 | mandatory | Agents address each other with mentions. | FALSE | NOT_TESTED | band-mention |
| REQ-AOK-M11 | mandatory | Agents hand context directly to other agents. | FALSE | NOT_TESTED | band-handoff |
| REQ-AOK-M12 | mandatory | Handoff succeeds without human copying. | FALSE | NOT_TESTED | band-no-copy-paste |
| REQ-AOK-M13 | mandatory | At least one real decision or approval occurs. | FALSE | NOT_TESTED | band-real-decision |
| REQ-AOK-M14 | mandatory | Human receives that decision through Band. | FALSE | NOT_TESTED | band-human-route |
| REQ-AOK-M15 | mandatory | Decision is not hard-coded. | FALSE | NOT_TESTED | band-not-hardcoded |
| REQ-AOK-M16 | mandatory | Demo shows Band Desktop rooms. | FALSE | NOT_TESTED | demo-rooms |
| REQ-AOK-M17 | mandatory | Demo shows the work board. | FALSE | NOT_TESTED | demo-board |
| REQ-AOK-M18 | mandatory | Demo shows per-agent sessions. | FALSE | NOT_TESTED | demo-sessions |
| REQ-AOK-M19 | mandatory | Demo shows token counts. | FALSE | NOT_TESTED | demo-tokens |
| REQ-AOK-M20 | mandatory | Demo shows estimated costs. | FALSE | NOT_TESTED | demo-cost |
| REQ-AOK-M21 | mandatory | Use Cognee Open Source. | FALSE | NOT_TESTED | cognee-oss |
| REQ-AOK-M22 | mandatory | Cognee serves as working memory. | FALSE | NOT_TESTED | cognee-working-memory |
| REQ-AOK-M23 | mandatory | Demonstrate working memory rather than only static storage. | FALSE | NOT_TESTED | cognee-not-static |
| REQ-AOK-M24 | mandatory | Agents write memory while doing the task. | FALSE | NOT_TESTED | cognee-write |
| REQ-AOK-M25 | mandatory | Agents actually recall stored memory. | FALSE | NOT_TESTED | cognee-recall |
| REQ-AOK-M26 | mandatory | Recalled memory changes a subsequent action. | FALSE | NOT_TESTED | cognee-behavior-change |
| REQ-AOK-M27 | mandatory | Demonstrate recall after restart OR between different agents; either is sufficient. | FALSE | NOT_TESTED | cognee-restart-or-agent |
| REQ-AOK-M28 | mandatory | BAND is essential: removing it changes required product behavior. | FALSE | NOT_TESTED | ablation-remove-band |
| REQ-AOK-M29 | mandatory | Cognee is essential: removing it changes required product behavior. | FALSE | NOT_TESTED | ablation-remove-cognee |
| REQ-AOK-M30 | mandatory | Address qualitative deep-integration review; Boolean tests alone do not guarantee qualification. | FALSE | NOT_TESTED | judge-deep-integration |
| REQ-AOK-E01 | scoring_enrichment | Use different agent harnesses for higher-scoring collaboration. | FALSE | NOT_TESTED | bonus-harness-diversity |
| REQ-AOK-E02 | scoring_enrichment | Demonstrate improve OR forget OR graph-backend connection; preserve this alternative choice. | FALSE | NOT_TESTED | bonus-cognee-enhancement |
| REQ-AOK-F01 | bonus_selected | Send and read back actual usage events in Flexprice test mode. | FALSE | NOT_TESTED | flexprice-real-events |
| REQ-AOK-F02 | bonus_selected | Connect those events to a configured test pricing model. | FALSE | NOT_TESTED | flexprice-pricing |
| REQ-AOK-F03 | scoring_enrichment | Demonstrate product behavior driven by metering. | FALSE | NOT_TESTED | flexprice-product-effect |
| REQ-AOK-F04 | scoring_enrichment | Optional example: credits gate a feature. | FALSE | NOT_TESTED | flexprice-credit-gate |
| REQ-AOK-F05 | scoring_enrichment | Optional alternative example: observed BAND costs pass through to test billing. | FALSE | NOT_TESTED | flexprice-cost-pass-through |
| REQ-AOK-S01 | bonus_selected | Use a real Snyk scanning product; alternatives are not all mandatory. | FALSE | NOT_TESTED | snyk-real-scan |
| REQ-AOK-S02 | bonus_selected | Scan the exact artifact built by the agents. | FALSE | NOT_TESTED | snyk-target-binding |
| REQ-AOK-S03 | scoring_enrichment | Give security review an actual team role. | FALSE | NOT_TESTED | snyk-security-role |
| REQ-AOK-S04 | scoring_enrichment | Security reviewer participates in the BAND room. | FALSE | NOT_TESTED | snyk-reviewer-room |
| REQ-AOK-S05 | scoring_enrichment | Security reviewer runs Snyk scans. | FALSE | NOT_TESTED | snyk-reviewer-scan |
| REQ-AOK-S06 | scoring_enrichment | Security reviewer posts actual findings. | FALSE | NOT_TESTED | snyk-post-findings |
| REQ-AOK-S07 | scoring_enrichment | A finding actually blocks completion until a verified fix. | FALSE | NOT_TESTED | snyk-block-until-fixed |
| REQ-AOK-S08 | scoring_enrichment | Store recurring issue evidence in Cognee working memory. | FALSE | NOT_TESTED | snyk-memory-write |
| REQ-AOK-S09 | scoring_enrichment | Demonstrate recalled security memory changes behavior on a repeated task. | FALSE | NOT_TESTED | snyk-recurrence-test |

## Acceptance invariant

entry_gate = all(mandatory_atom.verified is True); currently FALSE. No unexecuted check may become TRUE from an LLM answer, memory recall, zero finding count, or Merkle inclusion alone.

## Required first implementation checks

Bind each test to a real BAND/Cognee/Snyk/Flexprice execution receipt, exact source/app identities, actor, context and independent verifier. Append verdict successors rather than rewriting this R5 intake snapshot.

