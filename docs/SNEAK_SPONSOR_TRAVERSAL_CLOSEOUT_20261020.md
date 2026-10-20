# SNEAK — Sponsor traversal evidence closeout (2026-10-20)
This document describes a **partial observed** live traversal, not a fully accepted hackathon workflow.

## Root-question/source anchor
The exact canonical identity bytes are defined in `scripts/verify_sponsor_evidence.py`; includes the source Git commit, SHA-256 of the 26 original atom definitions file, test question and intended sponsor set.
- Shared SHA-256 address: `5a767b826c15cdf31050e18322c0959a2b24abdd01474fd55b1f983c2b38279e`.
- Input/identity digest is not a proof of model correctness, completion, or privacy.
- The three-leaf **local attempt receipt Merkle root** is `f31a9f12fc299383b3942dfc5817d7fd7d3e8200a13b8c84145c629d6ef3dbe9`, computed from the actual serialized three attempt leaves (Band, Cognee, Snyk); not the global project MMR.

## EXECUTED, OBSERVED, FAILED
1. **Band** human API: exact address in posted content (201), message ID `9d21c550-6317-488b-8488-676d4c5e471b`, and exact address found in GET messages (200). Three mention targets were included. Bot agent ACK, agent-to-agent transfer and live board changes: **NOT_OBSERVED**; CLI local account preflight: **FAILED**.
2. **Cognee SaaS**: corrected API `POST /api/v1/add_text` (200), cognify (200), initial CHUNKS search returned HTTP 200 but did not include target address. A later independently executed CHUNKS_LEXICAL and CHUNKS retrieval each returned HTTP 200 with the **exact address**. The initial negative and successor positive are both preserved. This proves bounded storage/retrieval, not Cognee OSS agent owned runtime.
3. **Snyk**: code test performed on predecessor source commit and **FAILED with auth error (exit 2)**. Complete SAST, SCA, and signed exact-commit clearance **NOT_VERIFIED**. Same address not observed in Snyk as a provider-side correlated receipt.
4. **GitHub**: versioned code and append-only JSON receipts committed on a draft PR lane; no release merge.
5. **Band usage archive**: real historical token totals captured, but room/agent attribution empty. `real usage != measured SNEAK ROI`; Flexprice live meters still **NOT_TESTED**.

## Source of truth and acceptance
- Original mandatory atom status `receipts/sneak_mvp/ATOM_STATUS_20261020.json` stays unchanged, 0/30 accepted.
- Successor `receipts/requirements/SNEAK_AOK_M01_M30_CLOSEOUT_20261020.json` has attempted/status/evidence fields for all 30 atoms, **acceptance_verified=false** on each.
- `scripts/verify_closeout_evidence.py` recomputes exact byte-link predecessors, address identity and attempt Merkle, and fails on drift. Does not verify provider-caused behavior.
- A source hash in a search response does not establish causation or that an agent acted. Human signoff, separate agent-owned acknowledgment, actual Band board transition, local Cognee OSS memory-dependent behavior, exact commit Snyk authenticated Code+OSS scan, and comparable measured Flexprice usage must be recorded before FULL PASS.

## Needed human actions
1. Authenticate Band CLI with `band init` on intended account; verify `band whoami` and live board/agent activity, record message/plan/transition/approval IDs.
2. Authenticate Snyk via secure credential store (do not paste keys in chat or commit); run `snyk code test` and `snyk test --all-projects` on exact candidate SHA; triage findings and rerun.
3. Execute agent A -> Band -> Cognee OSS -> agent B -> Band reply with the same address, restart/ablation control, record model-version MMR and output digests.
4. Run matched real tasks before/after Cognee memory, capture provider token reports, model ID, pass/fail and human active time; then ingest live metering into Flexprice test customer.
5. Review protected Vercel `/trace`, `/judge`, `/economics` and mark acceptance only from new independently verified receipts.
