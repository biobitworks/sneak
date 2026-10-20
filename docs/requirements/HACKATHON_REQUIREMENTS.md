# SF Startup Challenge — requirements successor

- **Checkpoint:** IP-20261020-003-REQ (candidate, non-canonical)
- **Predecessor:** IP-20261020-002-AOK (user-reported; original 15-file handoff not present in this runtime)
- **Source:** original seven-page PDF, SHA-256: `f9c730d4c6464cdfeedb540e0d4b6080b7bfcde9fab496a1eac0dbc15b0aa1cc`
- **Build status:** IMPLEMENTED local intake; EXECUTED local validation; NOT_TESTED live BAND/Cognee/Flexprice/Snyk
- **Anticube & ΔG*:** NOT_COMPUTED; per-object placeholders are not scores or decisions
- **Organizer status:** PDF contains unresolved publication checklist; web evidence of an Oct 20 event does not independently confirm sponsor-specific rubric

## Counts
- 56 source-anchored requirements/option AoKs
- 112 contextual candidate FCOs (two per AoK)
- 307 candidate FCG typed edges
- Classification counts: `{"BONUS": 6, "EVENT": 1, "EXTRA_CREDIT": 3, "JUDGING": 7, "MANDATORY": 16, "OPTIONAL": 1, "PRIMER": 4, "SETUP": 4, "TRACK": 9, "UNCONFIRMED": 5}`
- Candidate RFC9162-style root: `db15c9ab0b5a353f1d8346509ffcc332625f4ab94a9728acc1be567a37945167`

## Acceptance and source support
Every registry row has a source page, extraction offsets, normalized exact span, classification, submission gate, a proposed acceptance test, and current status. The evidence status is NOT_TESTED for execution; the PDF statements are source-attested only.

## Source-priority cautions
- No deadline or submission portal has been confirmed from the PDF. Check organizer directly.
- The source names `jam` in the setup instructions; Band official docs now describe the `band` CLI. Do not execute legacy syntax without verifying installed version.
- The 9 tracks are suggestions; all are retained without being falsely required.
- Flexprice, Snyk, mixed harnesses, Cognee improve/forget, graph backend, and pitch deck have separate optional scoring states.
- `IP-20261020-002-AOK` counts (54 AoKs, 124 FCOs, 497 edges) and its root are historical user-reported values, NOT independently recomputed here. Do not merge hashes/IDs until original predecessor package is accessible.

## Requirements matrix
| ID | Kind | Topic | Page | Acceptance / evidence | Status |
|---|---|---|---:|---|---|
| EV-001 | EVENT | Date, place, and theme | 1 | Retain as source-derived planning reference | NOT_TESTED |
| CORE-001 | MANDATORY | Build and ship a startup product or agent-powered workflow | 1 | Working product serves a stated user problem and runs end-to-end | NOT_TESTED |
| CORE-002 | MANDATORY | Use BAND as coordination layer | 1 | Real room/board/handoff/human decision receipts | NOT_TESTED |
| CORE-003 | MANDATORY | Use persistent Cognee memory | 1 | Agent uses stored knowledge after restart or across agents | NOT_TESTED |
| CORE-004 | BONUS | Flexprice billing as product workflow | 1 | Usage events affect entitlements or billing | NOT_TESTED |
| CORE-005 | BONUS | Snyk vulnerability scanning | 1 | Scan findings attached to issue/board | NOT_TESTED |
| BAND-001 | MANDATORY | Two live collaborating agents in one Band room | 2 | Record simultaneous/overlapping agents and room ID | NOT_TESTED |
| BAND-X01 | EXTRA_CREDIT | Mixed harnesses | 2 | Two different harnesses demonstrated | NOT_TESTED |
| BAND-002 | MANDATORY | Agent-created plan and moving board tasks | 2 | Record plan event, claim, in-progress, done | NOT_TESTED |
| BAND-003 | MANDATORY | Direct @mention handoffs | 2 | Room messages show agent A -> B transfer without manual copying | NOT_TESTED |
| BAND-004 | MANDATORY | Genuine human approval through BAND | 2 | Capture pending approval and explicit human decision then task proceeds | NOT_TESTED |
| BAND-005 | MANDATORY | Room, board, per-agent tokens and cost views | 2 | Recorded demo frames show room, tasks, sessions, token/cost estimates | NOT_TESTED |
| COG-001 | MANDATORY | Cognee OSS working memory not a document dump | 2 | Import into OSS and demonstrate retrieval and behavior-change | NOT_TESTED |
| COG-002 | MANDATORY | Agents write operational memory during build | 2 | Capture Cognee add/cognify/write receipt and relevant content | NOT_TESTED |
| COG-003 | MANDATORY | Recall changes behavior across session/agents | 2 | Controlled before/after or restart demonstration with changed plan/action | NOT_TESTED |
| COG-X01 | EXTRA_CREDIT | Cognee improve or forget operation | 2 | Execute and record update/forget with changed retrieval | NOT_TESTED |
| COG-X02 | EXTRA_CREDIT | Graph backend such as Neo4j | 2 | Record graph backend configured and query | NOT_TESTED |
| DEEP-001 | MANDATORY | Deep non-bolted-on integration | 2 | Ablate BAND vs COGNEE and show loss of essential behavior | NOT_TESTED |
| FLEX-001 | BONUS | Meter real usage and create a priced unit | 3 | Test end-to-end usage event -> meter -> bill/credits | NOT_TESTED |
| FLEX-002 | BONUS | Feature gating or pass-through agent costs | 3 | Test exhausted credit changes allowed operation and receipt | NOT_TESTED |
| SNYK-001 | BONUS | Snyk scan integrated in workflow | 3 | Scan code/dependencies/container with versioned receipt | NOT_TESTED |
| SNYK-002 | BONUS | Security agent blocks unsafe work and stores lessons | 3 | Seed vulnerability; scan catches; board blocked; repaired; Cognee recalls | NOT_TESTED |
| PR-001 | PRIMER | Band architecture primer | 3 | Retain as source-derived planning reference | NOT_TESTED |
| PR-002 | PRIMER | Cognee working-memory primer | 3 | Retain as source-derived planning reference | NOT_TESTED |
| PR-003 | PRIMER | Flexprice options primer | 3 | Retain as source-derived planning reference | NOT_TESTED |
| PR-004 | PRIMER | Snyk options primer | 3 | Retain as source-derived planning reference | NOT_TESTED |
| TR-001 | TRACK | One-Founder Software Studio | 4 | Retain as source-derived planning reference | NOT_TESTED |
| TR-002 | TRACK | Autonomous GTM Team | 4 | Retain as source-derived planning reference | NOT_TESTED |
| TR-003 | TRACK | AI Customer Success Squad | 4 | Retain as source-derived planning reference | NOT_TESTED |
| TR-004 | TRACK | Secure Ship Pipeline | 4 | Retain as source-derived planning reference | NOT_TESTED |
| TR-005 | TRACK | Usage-Billed AI API in a Day | 5 | Retain as source-derived planning reference | NOT_TESTED |
| TR-006 | TRACK | Investor & Fundraise Copilot | 5 | Retain as source-derived planning reference | NOT_TESTED |
| TR-007 | TRACK | Incident War Room | 5 | Retain as source-derived planning reference | NOT_TESTED |
| TR-008 | TRACK | Startup Knowledge OS (LLM Wiki) | 5 | Retain as source-derived planning reference | NOT_TESTED |
| TR-009 | TRACK | Open Innovation | 5 | Retain as source-derived planning reference | NOT_TESTED |
| J-001 | JUDGING | BAND — 25% | 5 | Retain as source-derived planning reference | NOT_TESTED |
| J-002 | JUDGING | Cognee — 25% | 6 | Retain as source-derived planning reference | NOT_TESTED |
| J-003 | JUDGING | Viability — 20% | 6 | Retain as source-derived planning reference | NOT_TESTED |
| J-004 | JUDGING | Technical execution — 20% | 6 | Retain as source-derived planning reference | NOT_TESTED |
| J-005 | JUDGING | Innovation — 10% | 6 | Retain as source-derived planning reference | NOT_TESTED |
| J-006 | JUDGING | Flexprice bonus up to +10% | 6 | Retain as source-derived planning reference | NOT_TESTED |
| J-007 | JUDGING | Snyk bonus up to +10% | 6 | Retain as source-derived planning reference | NOT_TESTED |
| SUB-001 | MANDATORY | Working local or live prototype | 6 | Demo run with exact version, success receipt | NOT_TESTED |
| SUB-002 | MANDATORY | Provide repository link | 6 | Provide working access path for judges | NOT_TESTED |
| SUB-003 | MANDATORY | Required two-to-three-minute demo video | 6 | Validate duration and BAND/Cognee moments | NOT_TESTED |
| SUB-004 | MANDATORY | Project description with agents, memory, sponsor usage | 6 | Check all fields listed against README/pitch | NOT_TESTED |
| SUB-005 | OPTIONAL | Pitch deck | 6 | If selected, attach deck and record receipt | NOT_TESTED |
| SET-001 | SETUP | Set up BAND Desktop and 2 agents | 6 | Run current official onboarding and readiness checks | NOT_TESTED |
| SET-002 | SETUP | Set up Cognee OSS and storage | 6 | Install/config; test write, cognify, recall | NOT_TESTED |
| SET-003 | SETUP | Flexprice trial setup | 6 | Create meter and send test usage event | NOT_TESTED |
| SET-004 | SETUP | Snyk CLI login and scans | 6 | Capture `snyk test`, `snyk code test` result IDs | NOT_TESTED |
| UNC-001 | UNCONFIRMED | Deadline, submission link, support channel | 6 | Verify with organizer/source authority | NOT_TESTED |
| UNC-002 | UNCONFIRMED | Credits and sponsor codes | 7 | Obtain organizer or sponsor confirmation | NOT_TESTED |
| UNC-003 | UNCONFIRMED | Possible sponsor-specific judging changes | 7 | Confirm rubric with judges | NOT_TESTED |
| UNC-004 | UNCONFIRMED | Feature expectation confirmation | 7 | Confirm required screenshots or feature scope with BAND | NOT_TESTED |
| UNC-005 | UNCONFIRMED | Naming/version drift: Jam -> Band | 7 | Use version-pinned current docs and CLI discovery | NOT_TESTED |

## Suggested minimum sprint order
1. Confirm participant login, working repo, correct submission URL, and event-specific rubric with organizer.
2. Initialize BAND Desktop with two separate agent identities; add lead/implementer; create one room and a single task board.
3. Run Cognee OSS and demonstrate memory add/cognify/search changing a second agent decision after a restart.
4. Build product path around this collaboration; capture a real human approval and per-agent cost view.
5. Run Flexprice metering and Snyk security gating as bonuses if time permits; do not misclassify them as eligibility prerequisites.
6. Run negative ablation (remove BAND or Cognee) to show product behavior degrades, and capture the required 2–3 minute video.
7. Verify repository visibility to judges and submit working prototype, video, and project description.
