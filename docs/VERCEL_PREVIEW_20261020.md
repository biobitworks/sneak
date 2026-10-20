# SNEAK Vercel evidence preview — read-only deployment lane
Date: 2026-10-20
Repository: private biobitworks/sneak
Parent source commit: 7793cfe684273e55dcadf5ddd98339c6b6ad196a
Branch: deploy/sneak-vercel-preview-20261020

## Scope
Exports only allowlisted source-bound AoK/requirements and sanitized security receipts. Does not deploy the Python HTTP server, BAND credentials, Cognee OSS persistent graph storage, raw Snyk output, local file paths, user identities, or agent-message bodies. Export bytes deterministic for unchanged source state.
Static knowledge graph and audit are PROJECTIONS, not working Cognee backend, signed FCO, canonical MMR, independent new Merkle root, or admission receipt. The source AoK candidate root is retained for provenance; no root is invented for the export. LOMO=NOT_COMPUTED; MMR=NOT_COMPUTED; ANTICUBE=NOT_COMPUTED; DELTA_G_STAR=NOT_COMPUTED.

## Security and acceptance
- Team: biobitworks; Vercel project: sneak-evidence-preview; Vercel Authentication/SSO enabled for ALL deployments on project creation.
- Only preview deployment is authorized in this lane; no production promotion.
- Scanner release gate BLOCKED; latest 2 LOW findings belong to earlier exact commit, not the new deployment commit.
- BAND Desktop/CLI identity, human approval and per-agent sessions/cost remain independent acceptance obligations; predecessor BAND handoff and hosted Cognee R14 receipts on other branches are not silently merged.
- Site has read-only assets; no credentials or code-execution endpoints.
- Build command: python3 -m scripts.build_vercel_preview
- Test command: python3 -m unittest tests.test_vercel_preview tests.test_sneak_mvp -v
- Export manifest: deploy/vercel-preview/EXPORT_MANIFEST.json; SHA-256 file custody, not Merkle root.

## Next acceptance
1. Deploy SSO-protected preview, verify HTTP response and authentication barrier; append observed deployment ID/URL receipt.
2. Bind real BAND room and Cognee memory receipts to authenticated backend separately, never expose secret tokens in static UI.
3. Independently triage scanner findings; production promotion must remain withheld until human permission and release gates.
