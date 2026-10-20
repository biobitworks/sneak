# SNEAK main + Vercel production release — 2026-10-20

## GitHub

- Default `main` merge commit: `9dd7bb7c9c5f5d43952a8722045410f21c97b5a3`.
- Refreshed static snapshot commit: `3faae0d8ec89598064806398b75a0a0f4508855f`.
- Production source snapshot generated from the merge commit; the snapshot commit adds the rebuilt immutable export files.
- Implementation repository: https://github.com/biobitworks/sneak (`public` as observed 2026-10-20).
- Public judging kit: https://github.com/biobitworks/sneak-judges.
- Development review: https://github.com/biobitworks/sneak/pull/11; teammate security task: https://github.com/biobitworks/sneak/issues/21.

## Live verified production

- Production: https://sneak-evidence-preview.vercel.app
- Video/Q&A/tokens: https://sneak-evidence-preview.vercel.app/tokens
- Human judge review: https://sneak-evidence-preview.vercel.app/judge
- Conversation FCO/MMR: https://sneak-evidence-preview.vercel.app/conversations
- LOMO heatmap: https://sneak-evidence-preview.vercel.app/heatmap
- Simulated economics: https://sneak-evidence-preview.vercel.app/economics
- Deployment ID: `dpl_GEt7AfGzBjPAuj9Ho2rqTgJZKcDh`, READY, `production`, alias assigned.
- Deployment body byte-verified (five files) against the merged-main rebuilt snapshot: `EXPORT_MANIFEST.json`, `data/export-custody.json`, `data/token-journeys.json`, `data/graph.json`, `data/judge-links.json`.
- Export Merkle root: `6c355139a0889c14fd619350c2f88fdd55f0c85b5c0e945582f0cade01e4816a`.
- Export MMR root: `1842bc3f6f80c2ac3cd2f862a58ea860d36db1885741035ea83f92d8f1126d1f`.
- 31 declared export files, 57 MMR nodes; the self-referential export manifest/custody fields are excluded from the root construction.
- Post-merge suite: 129 Python test cases, 1 skipped; 10 Node tests passed.

## Explicit release blockers

- Vercel Authentication is enabled for all deployments; unauthenticated `/tokens` returned HTTP 302 to Vercel SSO, so production is NOT publicly viewable without Vercel authorization.
- Snyk CLI `whoami` returned 401 authentication error. No successful current-main Snyk Code/OSS gate evidence is asserted. Security gate remains `BLOCKED`, teammate score `NOT_COMPUTED`.
- The site is a static, source-bound evidence projection; the three captured historic BAND messages have no attested model token counts; six model-attributed Flexprice rows are SIMULATED, not measured customer ROI.
- Official hackathon/judge acceptance and real-time BAND planner participation remain separately unverified.
- A successful merge/deployment proves code integration and served artifact identity, NOT vulnerability clearance or scientific model improvement.

Release receipt: `receipts/release/SNEAK_MAIN_VERCEL_BP005_20261020.json` (append-only successor, scoped separately from the export Merkle/MMR).
