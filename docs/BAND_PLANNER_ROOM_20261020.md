# SNEAK Planner — BAND Remote Agent onboarding and room verification
Date: 2026-10-20
Predecessor: SNEAK-AUTH-20261020-BP-003
Repository: private biobitworks/sneak

## Profile — PROPOSED, not registered
Name: SNEAK Planner
Handle input: sneak-planner; expected full handle @biobitworks.sneak-planner
Description: Orchestrates SNEAK agents across BAND, Cognee, Snyk, GitHub, and Vercel. Assigns work, verifies task completion against source-bound evidence, tracks FCO/AoK provenance and Merkle/MMR breakpoints, coordinates security reviews, and escalates failures or missing evidence for human approval. Never treats proposed or untested work as completed.
Tag: orchestration; automatic contacts: all owner's agents; public-directory discovery: OFF.
Remote-agent identity registration alone is not proof that the remote runtime is connected.

## New room — PROPOSED
Name: SNEAK — Orchestration & Evidence
Members: human owner, planner, verified Claude/Codex/Snyk/Cognee identities where authorized.
Use Band native @ mention picker or exact participant ID. Literal @text alone does not prove delivered mention.

## Observable acceptance checkpoints
1. Registration: human clicks Create/Connect on Band web form. Inspect created card and confirm actual agent ID, exact handle, owner. State NOT_OBSERVED until verified.
2. CLI: band preflight must show account OK; band whoami must resolve the intended account. Do not expose credentials.
3. Room: band room list; confirm actual new room ID and name; band room participants <room_id> confirms planner and second independently identified agent.
4. Plan: band plan set <room_id> docs/BAND_PLANNER_ROOM_20261020.md --snapshot; band plan show confirms attached source.
5. Board: band work assign <room_id> <task> for Snyk Code/OSS, Cognee recall, custody verification, real LOMO trials and human approval; band work board <room_id> confirms actual IDs/status changes.
6. Native @ mention: band room send <room_id> <message> --mention <planner_participant_id>; verify returned server message ID and read back with band room messages <room_id> --json.
7. Actual acknowledgment: planner posts its own reply citing source/next-action; distinguish identity CREATED, runtime CONNECTED, reply OBSERVED.
8. Planner @mentions Claude/Codex and Snyk reviewer using actual IDs, not merely a textual handle. Require returned message IDs.
9. Security: Code/OSS only PASS with authenticated scans bound to exact git commit, correct scope and outputs. Container remains NOT_TESTED without a real image.
10. Submission acceptance: owner authorizes work but real tests/mandatory and external judge acceptance remain independent proof gates.

## Initial room message — PROPOSED, NOT SENT
@biobitworks.sneak-planner: You are SNEAK orchestration lead. Verify room ID, members, and plan first. Open shared tasks for (A) Claude architectural review, (B) Codex independent source and Merkle/MMR verification, (C) Snyk Code/OSS checks and failure triage, (D) Cognee write -> recall -> changed action across agents, (E) structural LOMO fixtures vs separate live agent tests, (F) owner HITL approval. Preserve distinctions PROPOSED / IMPLEMENTED / EXECUTED / OBSERVED / SUPPORTED and FAILED / NULL / NEGATIVE / DEFERRED / NOT_TESTED / UNKNOWN. Never claim posted unless BAND returns a message ID; never invent a new root. @mention other collaborators with actual participant IDs. Report each receipt and blocker.

## Current observed status
BAND CLI 0.4.16, daemon and Claude plugin installed. The default CLI profile previously reported NO_ACCOUNT; device authentication pending user. Web agent registration, runtime connectivity, new room and message posting remain NOT_OBSERVED. This proposal is not a computed Merkle/MMR root.
