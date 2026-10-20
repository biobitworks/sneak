# SNEAK-028 AoK MVP requirement ledger (M01–M20)

Source status from receipts + live Band observation — **never** from graph links.
Predecessor registry: `data/rules/atomic_acceptance_r5.jsonl` (unchanged).
Successor JSONL: `data/verification/requirements_sneak_028.jsonl`.

- entry_gate: **False** (verified 10/20)
- PASS=10 FAIL=1 NOT_TESTED=9 tried=17
- Live online agents: **7** `['cmanjesh/jerry', 'biobitworks/tom', 'cmanjesh/tom', 'cmanjesh/coolagent', 'biobitworks/planner', 'biobitworks/jerry', 'cmanjesh/planner']`
- MMR: **NOT_COMMITTED**

## M01–M15 (Band coordination MVP)

| ID | Requirement | Tried | Outcome | Verified |
|---|---|---|---|---|
| REQ-AOK-M01 | Use actual Band Desktop. | True | **NOT_TESTED** | False |
| REQ-AOK-M02 | Band coordinates the agent team. | True | **PASS** | True |
| REQ-AOK-M03 | Agents share one actual room. | True | **PASS** | True |
| REQ-AOK-M04 | At least two agents participate. | True | **PASS** | True |
| REQ-AOK-M05 | Lead/architect writes the plan in the room. | True | **PASS** | True |
| REQ-AOK-M06 | Team works from one plan. | True | **PASS** | True |
| REQ-AOK-M07 | Team uses one shared work board. | True | **PASS** | True |
| REQ-AOK-M08 | Agents claim work items. | True | **FAIL** | False |
| REQ-AOK-M09 | Actual task transitions include To-do and Done. | True | **PASS** | True |
| REQ-AOK-M10 | Agents address each other with mentions. | True | **PASS** | True |
| REQ-AOK-M11 | Agents hand context directly to other agents. | True | **PASS** | True |
| REQ-AOK-M12 | Handoff succeeds without human copying. | True | **PASS** | True |
| REQ-AOK-M13 | At least one real decision or approval occurs. | True | **NOT_TESTED** | False |
| REQ-AOK-M14 | Human receives that decision through Band. | True | **NOT_TESTED** | False |
| REQ-AOK-M15 | Decision is not hard-coded. | True | **NOT_TESTED** | False |

## M16–M20 (Desktop demo visibility)

| ID | Requirement | Tried | Outcome | Verified |
|---|---|---|---|---|
| REQ-AOK-M16 | Demo shows Band Desktop rooms. | True | **NOT_TESTED** | False |
| REQ-AOK-M17 | Demo shows the work board. | True | **NOT_TESTED** | False |
| REQ-AOK-M18 | Demo shows per-agent sessions. | False | **NOT_TESTED** | False |
| REQ-AOK-M19 | Demo shows token counts. | False | **NOT_TESTED** | False |
| REQ-AOK-M20 | Demo shows estimated costs. | False | **NOT_TESTED** | False |

## Missed / still open

- **M01** Band Desktop — not used (Human API/SDK substitute only)
- **M08** board claims — FAIL (BOARD_TOOL_MISSING)
- **M13–M15** real human decision path — NOT_TESTED (#7 pending)
- **M16–M20** Desktop demo panels — NOT_TESTED
