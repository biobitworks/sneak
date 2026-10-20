# All-lanes integration — 2026-10-20

Integration source: `d88d71d607f1f756842f94440db2edddd6637a8d`. Main predecessor: `3faae0d8ec89598064806398b75a0a0f4508855f`.

All 19 pinned work-lane heads are verified ancestors. Original branches and predecessor receipts are retained. Three-way conflict resolutions combine recent planner/model/metering features, FCG registration, token UI, source audit, security hardening and licensing. Alternate receipt and generated snapshot bytes are stored under `receipts/merge_variants/`.

Validation: 196 Python tests and 13 subtests PASS; 2 skipped (official pinned dataset absent, BAND SDK not installed). All 12 Node checks PASS. Nine export contract checks and `uv lock --check` PASS. Imported-byte manifests R3 → R4 → R5 are append-only successors; final R5 binds 107 current file identities.

The initial combined suite failed four integration checks. Corrections append new import manifests, regenerate exact export custody, and retain both CLI receipt-validation contracts. An intermediate merge-hunk reconciliation defect was corrected before the final suite. Dependency resolution failed with the inherited Python 3.10 declaration; Python 3.12 and the agent optional extra now match the regenerated lock.

Snyk authentication and full merged-source scan remain NOT_TESTED; app score NOT_COMPUTED; security ship gate BLOCKED. Source integration does not establish production release or sponsor acceptance. A new deployment was NOT_EXECUTED during this merge turn.

See `receipts/merges/SNEAK-ALL-LANES-MERGE-R1-20261020.json` for all immutable lane heads and resolutions, and its observed successor for the completed main update.
