# SNEAK main integration — merge review successor (2026-10-20)

## Scope and authorization
The repository owner requested that all work from the SNEAK chat be committed, pushed, and integrated into `main`. The integrated predecessor branch `integration/all-lanes-20261020-r1` at `5e47ca0fa0d913b753b82674e595132d7c73269f` includes the sponsor-traversal, dashboard, R14 custody, breakpoint, conversation-federation, red-team, and teammate handoff lane heads. This document is a human-readable successor, not an acceptance certificate.

## Executed integration checks
- Fresh worktree checkout at the pinned integrated predecessor commit.
- Previously observed: 195 passed, 2 failed, 1 skipped. Failures: merged file identities and stale Vercel export commitment.
- The R5 successor reconciles two changed file occurrences in the R4 manifest without rewriting any R4 bytes.
- The previous Vercel export custody JSON is preserved as `receipts/integrations/VERCEL_EXPORT_PRE_R5_20261020.json`; current projection recompiled against all 38 files.
- Full suite after reconciliation: **197 passed, 1 skipped** (executed in the isolated release worktree).
- Generated import Merkle root: `ae644682d9cb93d640a15ff26d182f61b618a03d5fdb783010deaf879254c5a9`.
- Generated Vercel export Merkle root: `9d00dd45ff858474286c4d81c79c5921221aa484d0367adb9d64211c6c1c1d1b`.
- Generated Vercel export MMR root: `0e1115960e9ef7a3a38f0fb764697babfabc4a0376f7f1810524ac6060d197b8`.
- These identities are for the stated artifact scopes only; global canonical project MMR: **NOT_COMPUTED**.

## Known non-passing gates retained
- Snyk: **BLOCKED**; no authenticated Code plus SCA result for the final merged SHA, no verified zero-app-score bonus.
- Band: posted/read-back provider evidence does **not** prove independent agent coordination, board transitions, or human approval.
- Cognee: hosted exact-address retrieval does **not** prove OSS agent-owned memory use.
- Flexprice: live matched baseline/task metering and financial ROI **NOT_TESTED**; historical session totals lack attributable agent/model cost.
- Requirement acceptance: historical **0/30 mandatory accepted**, absent a newer independently verified requirement decision.
- Release security and judging admission remain **BLOCKED** notwithstanding code integration and passing tests.
- GitHub repository visibility was observed as **PUBLIC** at the time of this merge review; earlier documents stating private are historical and not the current setting.
- Vercel production promotion and SSO-unlocked judge access were not performed as part of this merge.

## Provenance
- Input ancestor: `5e47ca0fa0d913b753b82674e595132d7c73269f`.
- R4 predecessor bytes: `receipts/sneak_mvp/TEAMMATE_IMPORT_20261020_R4.json`.
- R5 successor bytes: `receipts/sneak_mvp/TEAMMATE_IMPORT_20261020_R5.json`.
- Machine-readable change receipt: `receipts/integrations/SNEAK_MAIN_MERGE_RECONCILIATION_R5_20261020.json`.
- Deterministic transformation source: `scripts/reconcile_main_merge_r5_20261020.py`.
- Root validity establishes integrity/identity, not correctness, provenance authenticity, causality, or accepted sponsor performance.
