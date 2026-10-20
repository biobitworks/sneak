# SNEAK — human acceptance and judge readiness review

**Date:** 20 October 2026. **Source:** official SF Startup Challenge problem statement intake and machine acceptance registry.
**Machine acceptance:** **0/30 mandatory verified**. Extra atoms: 4 selected bonus + 12 scoring enrichment, all unverified in baseline. Official source extraction: **56 separate requirement/option statements**; the inventories overlap but are **not deduplicated into 56+46 distinct obligations**.

**Human instructions:** For every row, fill decision YES/NO/NEEDS_WORK/UNREVIEWED, name, dated proof link or receipt ID, and notes. Never mark a machine atom verified solely because you checked YES: a new appended, independently validated acceptance receipt is required. The deployed Vercel reviewer can export your annotations as JSON for that next step.

## Evidence-to-judging translation

| Judging claim | Source-bound reality | What the human must inspect |
|---|---|---|
| Real multi-agent collaboration in BAND | Historical Tom/Jerry room messages captured, current CLI account not authenticated | Live room, agent IDs, board actions, native mentions, message readback |
| Agent memory that changes action | Cognee OSS local write and separate-process recall executed and changed deterministic gate proposal | Planner/second agent recalls memory and performs changed real task in BAND |
| Merkle/MMR trust layer | Export and historical FCO/actor and question roots independently replayed | Exact receipt, algorithm, inclusion proof and tamper test |
| Secure shipping | Prior Snyk Code findings remain; current CLI auth error and OSS dependency resolution failure | Exact target-commit Code/OSS report, triage, verified rescans and zero/score conditions |
| Live product | Protected Vercel snapshot showing graph, heatmap and conversation lineage | Confirm rendered UI; distinguish read-only snapshot from live relay |
| Flexprice bonus | Test billing API events/pricing not fully verified | Real test-mode event receipt and pricing/entitlement effect |
| Submission | 2–3 minute video required by brief | Recording link, current submission URL/deadline and judge access |

## Machine acceptance checklist (46 atomic rows)

| ID | Level | Requirement | Machine outcome | Human decision | Reviewer | Evidence / receipt | Follow-up |
|---|---|---|---|---|---|---|---|
| REQ-AOK-M01 | mandatory | Use actual Band Desktop. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-M02 | mandatory | Band coordinates the agent team. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-M03 | mandatory | Agents share one actual room. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-M04 | mandatory | At least two agents participate. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-M05 | mandatory | Lead/architect writes the plan in the room. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-M06 | mandatory | Team works from one plan. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-M07 | mandatory | Team uses one shared work board. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-M08 | mandatory | Agents claim work items. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-M09 | mandatory | Actual task transitions include To-do and Done. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-M10 | mandatory | Agents address each other with mentions. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-M11 | mandatory | Agents hand context directly to other agents. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-M12 | mandatory | Handoff succeeds without human copying. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-M13 | mandatory | At least one real decision or approval occurs. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-M14 | mandatory | Human receives that decision through Band. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-M15 | mandatory | Decision is not hard-coded. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-M16 | mandatory | Demo shows Band Desktop rooms. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-M17 | mandatory | Demo shows the work board. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-M18 | mandatory | Demo shows per-agent sessions. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-M19 | mandatory | Demo shows token counts. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-M20 | mandatory | Demo shows estimated costs. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-M21 | mandatory | Use Cognee Open Source. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-M22 | mandatory | Cognee serves as working memory. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-M23 | mandatory | Demonstrate working memory rather than only static storage. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-M24 | mandatory | Agents write memory while doing the task. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-M25 | mandatory | Agents actually recall stored memory. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-M26 | mandatory | Recalled memory changes a subsequent action. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-M27 | mandatory | Demonstrate recall after restart OR between different agents; either is sufficient. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-M28 | mandatory | BAND is essential: removing it changes required product behavior. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-M29 | mandatory | Cognee is essential: removing it changes required product behavior. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-M30 | mandatory | Address qualitative deep-integration review; Boolean tests alone do not guarantee qualification. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-E01 | scoring_enrichment | Use different agent harnesses for higher-scoring collaboration. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-E02 | scoring_enrichment | Demonstrate improve OR forget OR graph-backend connection; preserve this alternative choice. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-F01 | bonus_selected | Send and read back actual usage events in Flexprice test mode. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-F02 | bonus_selected | Connect those events to a configured test pricing model. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-F03 | scoring_enrichment | Demonstrate product behavior driven by metering. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-F04 | scoring_enrichment | Optional example: credits gate a feature. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-F05 | scoring_enrichment | Optional alternative example: observed BAND costs pass through to test billing. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-S01 | bonus_selected | Use a real Snyk scanning product; alternatives are not all mandatory. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-S02 | bonus_selected | Scan the exact artifact built by the agents. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-S03 | scoring_enrichment | Give security review an actual team role. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-S04 | scoring_enrichment | Security reviewer participates in the BAND room. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-S05 | scoring_enrichment | Security reviewer runs Snyk scans. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-S06 | scoring_enrichment | Security reviewer posts actual findings. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-S07 | scoring_enrichment | A finding actually blocks completion until a verified fix. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-S08 | scoring_enrichment | Store recurring issue evidence in Cognee working memory. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |
| REQ-AOK-S09 | scoring_enrichment | Demonstrate recalled security memory changes behavior on a repeated task. | NOT_TESTED | ⬜ UNREVIEWED | — | — | — |

## Official source extraction (56 statements — including optional, judging, bonus, setup)

| ID | Source classification | Requirement or topic | Page | Proposed evidence | Human review |
|---|---|---|---|---|---|
| EV-001 | EVENT | Date, place, and theme | 1 | Retain as source-derived planning reference | ⬜ UNREVIEWED |
| CORE-001 | MANDATORY | Build and ship a startup product or agent-powered workflow | 1 | Working product serves a stated user problem and runs end-to-end | ⬜ UNREVIEWED |
| CORE-002 | MANDATORY | Use BAND as coordination layer | 1 | Real room/board/handoff/human decision receipts | ⬜ UNREVIEWED |
| CORE-003 | MANDATORY | Use persistent Cognee memory | 1 | Agent uses stored knowledge after restart or across agents | ⬜ UNREVIEWED |
| CORE-004 | BONUS | Flexprice billing as product workflow | 1 | Usage events affect entitlements or billing | ⬜ UNREVIEWED |
| CORE-005 | BONUS | Snyk vulnerability scanning | 1 | Scan findings attached to issue/board | ⬜ UNREVIEWED |
| BAND-001 | MANDATORY | Two live collaborating agents in one Band room | 2 | Record simultaneous/overlapping agents and room ID | ⬜ UNREVIEWED |
| BAND-X01 | EXTRA_CREDIT | Mixed harnesses | 2 | Two different harnesses demonstrated | ⬜ UNREVIEWED |
| BAND-002 | MANDATORY | Agent-created plan and moving board tasks | 2 | Record plan event, claim, in-progress, done | ⬜ UNREVIEWED |
| BAND-003 | MANDATORY | Direct @mention handoffs | 2 | Room messages show agent A -> B transfer without manual copying | ⬜ UNREVIEWED |
| BAND-004 | MANDATORY | Genuine human approval through BAND | 2 | Capture pending approval and explicit human decision then task proceeds | ⬜ UNREVIEWED |
| BAND-005 | MANDATORY | Room, board, per-agent tokens and cost views | 2 | Recorded demo frames show room, tasks, sessions, token/cost estimates | ⬜ UNREVIEWED |
| COG-001 | MANDATORY | Cognee OSS working memory not a document dump | 2 | Import into OSS and demonstrate retrieval and behavior-change | ⬜ UNREVIEWED |
| COG-002 | MANDATORY | Agents write operational memory during build | 2 | Capture Cognee add/cognify/write receipt and relevant content | ⬜ UNREVIEWED |
| COG-003 | MANDATORY | Recall changes behavior across session/agents | 2 | Controlled before/after or restart demonstration with changed plan/action | ⬜ UNREVIEWED |
| COG-X01 | EXTRA_CREDIT | Cognee improve or forget operation | 2 | Execute and record update/forget with changed retrieval | ⬜ UNREVIEWED |
| COG-X02 | EXTRA_CREDIT | Graph backend such as Neo4j | 2 | Record graph backend configured and query | ⬜ UNREVIEWED |
| DEEP-001 | MANDATORY | Deep non-bolted-on integration | 2 | Ablate BAND vs COGNEE and show loss of essential behavior | ⬜ UNREVIEWED |
| FLEX-001 | BONUS | Meter real usage and create a priced unit | 3 | Test end-to-end usage event -> meter -> bill/credits | ⬜ UNREVIEWED |
| FLEX-002 | BONUS | Feature gating or pass-through agent costs | 3 | Test exhausted credit changes allowed operation and receipt | ⬜ UNREVIEWED |
| SNYK-001 | BONUS | Snyk scan integrated in workflow | 3 | Scan code/dependencies/container with versioned receipt | ⬜ UNREVIEWED |
| SNYK-002 | BONUS | Security agent blocks unsafe work and stores lessons | 3 | Seed vulnerability; scan catches; board blocked; repaired; Cognee recalls | ⬜ UNREVIEWED |
| PR-001 | PRIMER | Band architecture primer | 3 | Retain as source-derived planning reference | ⬜ UNREVIEWED |
| PR-002 | PRIMER | Cognee working-memory primer | 3 | Retain as source-derived planning reference | ⬜ UNREVIEWED |
| PR-003 | PRIMER | Flexprice options primer | 3 | Retain as source-derived planning reference | ⬜ UNREVIEWED |
| PR-004 | PRIMER | Snyk options primer | 3 | Retain as source-derived planning reference | ⬜ UNREVIEWED |
| TR-001 | TRACK | One-Founder Software Studio | 4 | Retain as source-derived planning reference | ⬜ UNREVIEWED |
| TR-002 | TRACK | Autonomous GTM Team | 4 | Retain as source-derived planning reference | ⬜ UNREVIEWED |
| TR-003 | TRACK | AI Customer Success Squad | 4 | Retain as source-derived planning reference | ⬜ UNREVIEWED |
| TR-004 | TRACK | Secure Ship Pipeline | 4 | Retain as source-derived planning reference | ⬜ UNREVIEWED |
| TR-005 | TRACK | Usage-Billed AI API in a Day | 5 | Retain as source-derived planning reference | ⬜ UNREVIEWED |
| TR-006 | TRACK | Investor & Fundraise Copilot | 5 | Retain as source-derived planning reference | ⬜ UNREVIEWED |
| TR-007 | TRACK | Incident War Room | 5 | Retain as source-derived planning reference | ⬜ UNREVIEWED |
| TR-008 | TRACK | Startup Knowledge OS (LLM Wiki) | 5 | Retain as source-derived planning reference | ⬜ UNREVIEWED |
| TR-009 | TRACK | Open Innovation | 5 | Retain as source-derived planning reference | ⬜ UNREVIEWED |
| J-001 | JUDGING | BAND — 25% | 5 | Retain as source-derived planning reference | ⬜ UNREVIEWED |
| J-002 | JUDGING | Cognee — 25% | 6 | Retain as source-derived planning reference | ⬜ UNREVIEWED |
| J-003 | JUDGING | Viability — 20% | 6 | Retain as source-derived planning reference | ⬜ UNREVIEWED |
| J-004 | JUDGING | Technical execution — 20% | 6 | Retain as source-derived planning reference | ⬜ UNREVIEWED |
| J-005 | JUDGING | Innovation — 10% | 6 | Retain as source-derived planning reference | ⬜ UNREVIEWED |
| J-006 | JUDGING | Flexprice bonus up to +10% | 6 | Retain as source-derived planning reference | ⬜ UNREVIEWED |
| J-007 | JUDGING | Snyk bonus up to +10% | 6 | Retain as source-derived planning reference | ⬜ UNREVIEWED |
| SUB-001 | MANDATORY | Working local or live prototype | 6 | Demo run with exact version, success receipt | ⬜ UNREVIEWED |
| SUB-002 | MANDATORY | Provide repository link | 6 | Provide working access path for judges | ⬜ UNREVIEWED |
| SUB-003 | MANDATORY | Required two-to-three-minute demo video | 6 | Validate duration and BAND/Cognee moments | ⬜ UNREVIEWED |
| SUB-004 | MANDATORY | Project description with agents, memory, sponsor usage | 6 | Check all fields listed against README/pitch | ⬜ UNREVIEWED |
| SUB-005 | OPTIONAL | Pitch deck | 6 | If selected, attach deck and record receipt | ⬜ UNREVIEWED |
| SET-001 | SETUP | Set up BAND Desktop and 2 agents | 6 | Run current official onboarding and readiness checks | ⬜ UNREVIEWED |
| SET-002 | SETUP | Set up Cognee OSS and storage | 6 | Install/config; test write, cognify, recall | ⬜ UNREVIEWED |
| SET-003 | SETUP | Flexprice trial setup | 6 | Create meter and send test usage event | ⬜ UNREVIEWED |
| SET-004 | SETUP | Snyk CLI login and scans | 6 | Capture `snyk test`, `snyk code test` result IDs | ⬜ UNREVIEWED |
| UNC-001 | UNCONFIRMED | Deadline, submission link, support channel | 6 | Verify with organizer/source authority | ⬜ UNREVIEWED |
| UNC-002 | UNCONFIRMED | Credits and sponsor codes | 7 | Obtain organizer or sponsor confirmation | ⬜ UNREVIEWED |
| UNC-003 | UNCONFIRMED | Possible sponsor-specific judging changes | 7 | Confirm rubric with judges | ⬜ UNREVIEWED |
| UNC-004 | UNCONFIRMED | Feature expectation confirmation | 7 | Confirm required screenshots or feature scope with BAND | ⬜ UNREVIEWED |
| UNC-005 | UNCONFIRMED | Naming/version drift: Jam -> Band | 7 | Use version-pinned current docs and CLI discovery | ⬜ UNREVIEWED |

## Human submission signoff — fill after reviewing live evidence

Reviewer: ____________________    Reviewed at (timezone): ____________________

BAND room ID: ____________________     Planner agent ID: ____________________

Cognee memory dataset and readback receipt: ____________________

Snyk Code/OSS exact commit and complete scan evidence: ____________________

Video URL and length: ____________________    Submission/organizer confirmation: ____________________

Human recommendation (not a machine PASS): ☐ HOLD  ☐ READY_FOR_JUDGES  ☐ NEEDS_REVIEW

Known NOT_TESTED/UNKNOWN/ERROR evidence stays preserved. No Anticube/ΔG* or additional canonical global MMR claimed for this review sheet.
