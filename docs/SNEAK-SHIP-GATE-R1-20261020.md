# SNEAK ship gate audit
ID: SNEAK-SHIP-GATE-R1-20261020; parent: `517f630866834ddbe2e4dcee74f1213271055bbc`; source: `2bc13fee71cb71b4f217eb0d4286f76a4383d9c5`.
Gate: **BLOCKED**. Custody replay executed; live providers NOT_TESTED this turn.
| Claim | Status | Failure/evidence location | Interpretation |
|---|---|---|---|
| Snyk clean scan / score zero | FAILED | receipts/integrations/SNEAK_SPONSOR_TRAVERSAL_V1_20261020.json → snyk.scan | Exit 2 authentication failure; findings UNKNOWN; security app score NOT_COMPUTED. SCA and Code coverage of successor NOT_TESTED. |
| History actor | IMPLEMENTED | apps/sneak_mvp/web/app.js; scripts/build_vercel_preview.py | Export intentionally removes actor; UI now displays source or UNKNOWN. Regression test executed. All predecessor actions shown. |
| Band exact digest | SUPPORTED | receipts/integrations/SNEAK_SPONSOR_TRAVERSAL_V1_20261020.json → band | Stored receipt digest and linkage verified offline; live provider recheck NOT_TESTED this turn. Human API readback does not establish autonomous participation. |
| Cognee exact digest | SUPPORTED | receipts/integrations/SNEAK_SPONSOR_TRAVERSAL_V2_20261020.json | Separate hosted search recorded; custody reverified offline. Agent-owned OSS recall and behavior change NOT_VERIFIED. |
| Human decision | NOT_TESTED | EV-020-HUMAN-DECISION | No actual decision receipt verified. Original event retained. |
| EV-030 / EV-040 proposal status | PROPOSED | receipts/sneak_mvp/AOK_MVP_20261020.json | Historical proposal leaves unchanged. Later hosted Cognee receipt and Snyk failure are separate attempt evidence on /trace. |
| Mandatory acceptance | NEGATIVE | receipts/requirements/SNEAK_AOK_M01_M30_CLOSEOUT_20261020.json | 0 of 30 accepted. Every source requirement and blocker is listed below. |
| Measured savings / Flexprice | NOT_TESTED | receipts/flexprice/SNEAK_BAND_REAL_USAGE_UNATTRIBUTED_20261020.json | Historical token usage is UNATTRIBUTED_NOT_SNEAK_ROI; economics fixture simulated. Live Flexprice billing NOT_TESTED. |
| Merkle / MMR | SUPPORTED | scripts/verify_closeout_evidence.py; data/export-custody.json | Local attempt custody replay passes. Export roots apply only to declared static file bytes. Project/model global MMR, Anticube and delta G*: NOT_COMPUTED. |
| Live application / production release | DEFERRED | Vercel project sneak-evidence-preview | Protected static projection; target preview. Live APIs false. Production release remains BLOCKED. |
| Public judge repository | NEGATIVE | GitHub repository metadata | biobitworks/sneak is private; no visibility change authorized or executed. |

Run on a clean authenticated checkout:
```bash
snyk auth
python scripts/recheck_ship_gate.py --allow-code-upload
python scripts/verify_closeout_evidence.py
```
The scan runner appends new receipts after both scans; it never promotes a deployment. Scan PASS does not establish score zero or sponsor acceptance. The historical verifier audits the preserved attempt, not a later live rescan.

| Requirement | Attempt | Blocker |
|---|---|---|
| REQ-AOK-M01 — Use actual Band Desktop. | FAILED | Band CLI account unavailable; human API distinct |
| REQ-AOK-M02 — Band coordinates the agent team. | NOT_TESTED | No new acceptance-bound execution receipt inspected |
| REQ-AOK-M03 — Agents share one actual room. | OBSERVED | Band live room and participant registry (agent activity not observed) |
| REQ-AOK-M04 — At least two agents participate. | NOT_OBSERVED | Room contains agents but participation is inactive/unverified |
| REQ-AOK-M05 — Lead/architect writes the plan in the room. | NOT_TESTED | No new acceptance-bound execution receipt inspected |
| REQ-AOK-M06 — Team works from one plan. | NOT_TESTED | No new acceptance-bound execution receipt inspected |
| REQ-AOK-M07 — Team uses one shared work board. | NOT_TESTED | No new acceptance-bound execution receipt inspected |
| REQ-AOK-M08 — Agents claim work items. | NOT_TESTED | No new acceptance-bound execution receipt inspected |
| REQ-AOK-M09 — Actual task transitions include To-do and Done. | NOT_TESTED | No new acceptance-bound execution receipt inspected |
| REQ-AOK-M10 — Agents address each other with mentions. | PARTIAL | Human API mention payload succeeded; agent-owned mentions not attested |
| REQ-AOK-M11 — Agents hand context directly to other agents. | PARTIAL | Human API handoff delivered; no agent to agent handoff observed |
| REQ-AOK-M12 — Handoff succeeds without human copying. | NOT_OBSERVED | Automated agent-owned independent handoff not proven |
| REQ-AOK-M13 — At least one real decision or approval occurs. | NOT_TESTED | No new acceptance-bound execution receipt inspected |
| REQ-AOK-M14 — Human receives that decision through Band. | NOT_TESTED | No new acceptance-bound execution receipt inspected |
| REQ-AOK-M15 — Decision is not hard-coded. | NOT_TESTED | No new acceptance-bound execution receipt inspected |
| REQ-AOK-M16 — Demo shows Band Desktop rooms. | NOT_TESTED | No new acceptance-bound execution receipt inspected |
| REQ-AOK-M17 — Demo shows the work board. | NOT_TESTED | No new acceptance-bound execution receipt inspected |
| REQ-AOK-M18 — Demo shows per-agent sessions. | NOT_TESTED | No new acceptance-bound execution receipt inspected |
| REQ-AOK-M19 — Demo shows token counts. | PARTIAL | Band historical real token usage exists, not native judge demo per-agent sessions |
| REQ-AOK-M20 — Demo shows estimated costs. | PARTIAL | Band estimates exist but are unattributed, not demonstrated per agent |
| REQ-AOK-M21 — Use Cognee Open Source. | PARTIAL | Earlier local Cognee OSS receipt; current live probe is hosted Cognee, not OSS |
| REQ-AOK-M22 — Cognee serves as working memory. | PARTIAL | Hosted add+cognify+separate hash search; agent use unproven |
| REQ-AOK-M23 — Demonstrate working memory rather than only static storage. | NOT_VERIFIED | Memory retrieval observed; behavior change under live multi-agent conditions not proven |
| REQ-AOK-M24 — Agents write memory while doing the task. | NOT_OBSERVED | Human probe writes memory, not agent task execution |
| REQ-AOK-M25 — Agents actually recall stored memory. | NOT_OBSERVED | Independent script queries; not agent-initiated recall |
| REQ-AOK-M26 — Recalled memory changes a subsequent action. | NOT_OBSERVED | No observed agent behavior change |
| REQ-AOK-M27 — Demonstrate recall after restart OR between different agents; either is sufficient. | PARTIAL | Separate-process historical OSS recall exists; does not establish agent execution in same room |
| REQ-AOK-M28 — BAND is essential: removing it changes required product behavior. | NOT_TESTED | No new acceptance-bound execution receipt inspected |
| REQ-AOK-M29 — Cognee is essential: removing it changes required product behavior. | NOT_TESTED | No new acceptance-bound execution receipt inspected |
| REQ-AOK-M30 — Address qualitative deep-integration review; Boolean tests alone do not guarantee qualification. | NOT_TESTED | No new acceptance-bound execution receipt inspected |
