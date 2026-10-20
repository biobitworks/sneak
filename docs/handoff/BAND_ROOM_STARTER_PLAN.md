# BAND room execution plan — PROPOSED, NOT RUN

**Room label (proposed):** SF Startup Challenge — Evidence-Governed Agent Studio

**Product proposal requiring human approval in BAND:** An evidence-governed agent team that turns sourced hackathon, startup, and code-security findings into actionable, reviewable work. BAND coordinates people and agents. Cognee OSS provides memory that affects decisions. The candidate AoK/FCO/FCG ledger is a provenance substrate, not a replacement for Cognee memory. No product decision has yet been approved.

## Agents

- **Architect:** Claude Code or a BAND-supported harness; owns plan and board; never declares done without evidence.
- **Builder:** a distinct agent identity, ideally Codex or OpenCode, claims and implements work items; @mentions architect/reviewer rather than relying on manual relay.
- **Reviewer/security:** separate agent or role that tests proof conditions, runs Snyk if available, and blocks unsupported acceptance claims.
- **Founder/human:** approves a genuinely consequential action through BAND, such as changing the product workflow or applying a code/security fix; record actual approval, not simulated consent.

## Board tasks — all To-do (none executed)

| Task | Priority | Requirement refs | What constitutes Done |
|---|---|---|---|
| T01: Confirm event rubric/deadline | Blocking | UNC-001–005 | Organizer confirmation or recorded UNKNOWN |
| T02: Connect 2 agents in one BAND room | Blocking | BAND-001; SET-001 | Band room ID, agent identities, timestamps |
| T03: Architect posts plan; builder claims a task | Blocking | BAND-002 | Room/board proof of plan + To-do -> Done transition |
| T04: Direct @mention handoff | Blocking | BAND-003 | Agent-to-agent messages from original room |
| T05: Human approves real consequential decision | Blocking | BAND-004 | Pending request + human response + changed action |
| T06: Capture BAND visibility | Blocking | BAND-005 | Room, tasks, sessions, tokens, estimated costs shown |
| T07: Cognee write and cognify | Blocking | COG-001–002; SET-002 | OSS process receipt, memory write/indexing evidence |
| T08: Cognee recall changes decision | Blocking | COG-003 | Before-after behavioral change after restart/agent handoff |
| T09: Deep-integration ablation | Blocking | DEEP-001 | Show essential workflow cannot behave the same without one component |
| T10: Make functioning product and shareable repo | Blocking | CORE-001; SUB-001–002 | Versioned demo + readable code, judges' access verified |
| T11: Flexprice real usage metering | Bonus | FLEX-001–002; SET-003 | Real event influences balance or entitlements |
| T12: Snyk review gate | Bonus | SNYK-001–002; SET-004 | Scan output, finding -> blocker -> remediation receipt |
| T13: Cognee improve/forget or graph backend | Extra credit | COG-X01–02 | Write/read proof of update or Neo4j query |
| T14: Mixed harness collaboration | Extra credit | BAND-X01 | Two distinct harness session receipts |
| T15: Required submission assets | Blocking | SUB-003–004 | 2–3 min video + complete description |
| T16: Optional pitch deck | Optional | SUB-005 | Deck recorded, or explicit DEFERRED |

**Acceptance rule:** No item changes to Done on intent or static mocks alone. Keep MISSING/FAILED/NOT_TESTED/DEFERRED visible. Capture evidence identity, source system, timestamp, observed behavior, and agent/person responsible for every Done transition.

**Escalation:** If human approval is pending, do not auto-approve or silently continue. If any mandatory gate is NOT_TESTED, presentation may say *planned* but may not claim compliance.
