# Remote human verification checkpoints
Each step: show action and expected screen -> perform authorized action -> inspect real result -> troubleshoot -> append evidence -> then continue dependent step.
A human statement is HUMAN_REPORTED; screen/provider/command evidence can support INDEPENDENTLY_OBSERVED. Neither is fabricated as a signed statement.
No user action has been recorded by this checklist.

| Checkpoint | Human action | Independent corroboration | Requirement link |
|---|---|---|---|
| H01 Repository access | Open private biobitworks/sneak and confirm visible commit | GitHub visibility, HEAD and tree | Handoff prerequisite, not an event atom |
| H02 BAND sign-in | Sign in and show actual workspace | User screenshot + actual room/session IDs | M01-M04 require Desktop next |
| H03 BAND Desktop/team | Inspect room, plan, board and agents | Direct handoff, board history, sessions/tokens/cost | M01-M20, E01 |
| H04 Real decision | Approve/reject a consequential synthetic repair scope in BAND | Request, actual human response, resulting action | M13-M15 |
| H05 Cognee memory | Inspect written finding and recalled successor action | OSS version, write/query IDs, action diff across agents/restart | M21-M27 |
| H06 Security gate | Inspect actual blocked finding and repaired rescan | Exact app digest, raw SCA/SAST reports, denial/allow receipts | S01-S09 |
| H07 Usage | Inspect synthetic customer usage and credit balance | Real event readback and dedupe totals | F01-F04 |
| H08 Integration removal | Observe disabled BAND and Cognee trials separately | Expected required behavior unavailable, real receipts | M28-M30 |
| H09 Final evidence | Inspect all requirement verdicts and demo | Exact app commit, reproducible notebooks and coverage | Mandatory entry gate |

Store future human events as append-only JSONL records with id, predecessor_event_id, checkpoint_id, requirement_ids, requested_action, requested_at, actor, channel, response, response_at, evidence_refs, verification_state and observed_outcome. Leave response null until a real response exists.
A planned request is not SENT, a clicked button is not necessarily a successful provider effect, and a screenshot does not prove an unseen backend operation.
