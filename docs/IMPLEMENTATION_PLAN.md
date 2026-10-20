# Skill Custody Lab implementation plan

Goal: implement the requirements in .planning/REQUIREMENTS.md after review.
Architecture: isolated candidate execution, independent deterministic custody/authorization and source-bound scanner/memory receipts.
Execution method: native task-by-task; Claude Code is the requested external red-team lane, not a silently launched session.
Status: PROPOSED; application implementation NOT_EXECUTED.

1. Source intake: review every RULE atom against its page, resolve table/visual extraction gaps, approve requirements and phase ownership.
   Deliverable: frozen source manifest and requirement mapping. Validate exact source hash, full page coverage and reconstruction.
2. Isolation and capabilities: provision/pin a dedicated disposable guest and narrow gateway.
   Deliverable: VM manifest and capability contract. Test no host mounts/secrets, unauthorized read/write denial, teardown and egress controls.
3. Scanner adapter: invoke pinned Javier tool in the guest and pin Agent Scan.
   Deliverable: raw reports plus validated normalized receipts. Test zero findings with complete coverage, failed/partial scans, unknown schema, stale target hash and scanner-stage code execution.
4. BAND and Cognee: use references/sanitized task state; separate candidate from admitted memory.
   Deliverable: actual cross-agent handoff and restart-dependent recall. Test removal of either changes behavior and recalled poison cannot grant permissions.
5. Replicable experiment: add model runner and notebooks, actor x component LOMO replay, independent Python/Node verification.
   Deliverable: executed notebooks/results with full denominators. Test tamper rejection, replay denial and neutral false rejections.
6. Judge demonstration: perform controlled poison -> deny -> independent repair -> rescan -> authorize successor.
   Deliverable: exact scanned app commit, complete coverage, scored report, 2-3 minute walkthrough and rights decision.
   Public release is a separate gate. A numerical 10/10 is not an awarded event bonus.

Review focus: malformed skill encodings; changed MCP tool definitions after scanning; scanner JSON error envelopes; capability-token replay;
mobile reconnect/session expiry. Each belongs in the corresponding isolation/scanner/runner tests.
Each implementation increment must add a failing meaningful test, confirm failure, implement, pass the test, then commit the scoped increment.
