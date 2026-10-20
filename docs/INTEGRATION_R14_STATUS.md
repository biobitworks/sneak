# Sneak integration R14
Parent: SNEAK-013. Implementation branch: integration/cognee-flexprice-r14.
Source scanned: 1199675accec5294d056de16b2538b58850f3bc3.

| Component | Observed result | Remaining gate |
|---|---|---|
| Hosted Cognee | authenticated ingest, graph completion, exact-text recall; bounded graph 12 nodes/16 edges | Mandatory OSS runtime not verified |
| BAND memory relay | Jerry UNKNOWN before recall, exact review label and QUARANTINE_RESCAN proposal after relay | Supervised transport; agent-owned memory MCP tool not implemented |
| Flexprice | SDK 2.1.40 installed/imported in isolated environments | No test credential/customer/meter/events yet |
| Snyk Code | 4 LOW findings, 0 ignores; 18 Python/7 MJS files covered | Path-traversal review/hardening and rescan |
| Snyk Open Source | 12 integration dependencies; 0 known vulnerable paths | Full corpus dependency audit not executed |
| Javier scorer | Not executed | Do not infer a 10/10 or awarded bonus |
| Previous Jupyter handoff | Three code cells PASS on recovered output | Visual notebook inspection not performed |

## Human web checks
1. In Cognee, select dataset sneak_custody_r14 and inspect the graph and original synthetic record SNEAK-MEMORY-014. Confirm review label REVIEW-4a8a4bd598.
2. In BAND Chats, open Sneak — Requirements & Custody. Compare Jerry's UNKNOWN baseline, subsequent source-cited proposal, and Tom's security summary. The security summary is a message, not a proven board-state change.
3. Answer the existing SNEAK-H01 A/B question in BAND when ready. Supplying API credentials does not answer it.
4. In Flexprice, use the test workspace before configuring a private FLEXPRICE_API_KEY. No live invoice/payment actions are part of this increment.

## Reproduction
- python3 -m unittest discover -s tests -v (16 tests observed PASS).
- Jupyter: notebooks/08_cognee_band_snyk_r14.ipynb. Offline, no keys required; reads captured evidence and independently verifies event custody in Python and Node.
- Live Cognee uses COGNEE_BASE_URL and COGNEE_API_KEY from the caller's environment. Never put keys into prompts, notebooks, commits or reports.
- Flexprice runtime dependency is pinned in requirements-integrations.txt.
- Snyk raw reports and their source target are retained under receipts/integrations. No findings were ignored.

## Source security triage limit
The scanner establishes source-to-sink paths from CLI arguments to filesystem operations in scripts/custody_snapshot.py and scripts/verify_custody_snapshot.mjs. These are currently operator-run CLIs. A lower-trust caller crossing a deployed privilege boundary has not been established; keep all four claims needs_review rather than asserting exploitation. Repository containment remains a required hardening boundary before these CLIs become agent tools.
The security skill's shared assessment/policy reference resources were unavailable. This is a bounded source review using the actual report and retrieved code, not an exhaustive security audit.
No receipt or canonical record has been rewritten. Snyk findings and pending coverage deny a zero-finding claim. No gateway admission is claimed.
