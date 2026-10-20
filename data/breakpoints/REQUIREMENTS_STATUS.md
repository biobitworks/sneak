# Breakpoint pipeline requirements status

Ledger verify: **PASS**, 57 entries, global root `13f9023d76f9c827f5bf3306287834ecd8d3cdb228ce450e83a3ef7903c265e2`.

| ID | Requirement | State | Evidence |
|---|---|---|---|
| BPR-01 | Every conversation turn and step has a unique Merkle breakpoint | EXECUTED | 57 entries, all ids unique and recomputed; this chat session recorded (9 messages). BAND conversations not yet captured |
| BPR-02 | A breakpoint can be TRUE or FALSE | OBSERVED | 4 TRUE, 20 FALSE step breakpoints |
| BPR-03 | Each model has its own MMR | EXECUTED | model:lfm2-1.2b-longevity-q4km:latest@3839bfb14341 size 16; model:longhorizon-liquid-230m:latest@fea00095c205 size 16; model:qwen2.5:0.5b@a8b0c5157701 size 16; model:qwen2.5:1.5b@65ec06548149 size 16 |
| BPR-04 | Each model is compared to the root question | EXECUTED | 1 root question(s): BP-c1fa73944d419246 |
| BPR-05 | Delta over time for each model | OBSERVED | delta kinds seen: ['FIRST', 'SAME', 'TURNED_TRUE'] |
| BPR-06 | Input is hashed | EXECUTED | 36 steps with input_sha256 |
| BPR-07 | Deterministic script steps | FAILED | script_sha256 on every step; within-run replay 4/4 identical; cross-run 11/12 identical, differing: ['model:qwen2.5:0.5b|r1'] |
| BPR-08 | Steps are FCO-style identities (hash of immutable fields) | EXECUTED | bp_sha256 = SHA256(canonical identity); verify recomputes all |
| BPR-09 | Output is hashed | EXECUTED | output_sha256 on every step; breakpoint computed only when text matches hash |
| BPR-10 | Updates are hashed through FCO tracking | EXECUTED | 3 link(s) from breakpoints to contribution FCOs: FCO-8b904d2cf8f265d9, FCO-cb3b6ef299f35553, FCO-4f0478a0b1982b9a |
| BPR-11 | BAND is used to ask | NOT_TESTED | 1 question(s) queued, 0 sent (Claude not yet connected to BAND) |
| BPR-12 | BAND responses are recorded as breakpoints | NOT_TESTED | no BAND reply captured yet |
| BPR-13 | Cognee captures everything | NOT_TESTED | 34 memory item(s) queued, 0 sent (Cognee OSS not yet running) |
| BPR-14 | All agents are updated | NOT_TESTED | requires BAND delivery to every agent plus acknowledgements |
| BPR-15 | Planner is in the conversation and checked via BAND chat | NOT_TESTED | question to @planner queued as BP-1240e7e97ab1d2b5 |
| BPR-16 | Everything connects at the end (one project root) | EXECUTED | global MMR root now 13f9023d76f9c827f5bf3306287834ecd8d3cdb228ce450e83a3ef7903c265e2 over 57 entries; final project root NOT_COMPUTED until project end |
| BPR-17 | Each step is checked with Snyk | NOT_TESTED | branch-level Snyk Code scans exist (RT-29); per-step scanning not wired |
| BPR-18 | Flexprice analyses ROI per token | NOT_TESTED | 12 token event(s) queued, 0 sent; ROI NOT_COMPUTED (value definition pending) |
| BPR-19 | Snyk API key set up from iPad and stored outside chat | NOT_TESTED | human action pending |
| BPR-20 (optional) | Claude, Cursor and the teammate each acknowledge in BAND by @mention | NOT_TESTED | Claude not connected; Cursor and teammate not seen in the room |
| BPR-21 (optional) | Cognee OSS: raw upload vs SeedGraph LongMemEval comparison (30 questions) | NOT_TESTED | paused before setup; dataset sha256 d6f21ea9... verified |
