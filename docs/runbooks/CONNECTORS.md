# Connector runbook (BAND / Cognee / Snyk / Flexprice)

## Local contract review

```bash
python3 -m pip install -e . -e apps/security-demo
python3 -m pytest tests -q
python3 scripts/review_connectors.py
```

Receipts: `receipts/connectors/SNEAK-014_*`.

## Live Cognee storage + BAND Claude/ChatGPT

Store credentials **outside** the repo:

```bash
mkdir -p ~/.secrets/sneak && chmod 700 ~/.secrets ~/.secrets/sneak
# providers.env mode 0600 with BAND_USER_API_KEY, COGNEE_BASE_URL, COGNEE_API_KEY
# Optional for live scans: SNYK_TOKEN=...
python3 scripts/live_band_cognee.py
```

- Cognee Cloud is used as working-memory **data storage** (`add_text` → `cognify` → `search` on `sneak_working_memory`).
- BAND Human API messages Claude harness agent **Tom** and ChatGPT harness agent **Jerry** in room `20f1ee5f-…`.
- Receipts: `receipts/connectors/SNEAK-015_*` (no secret values).

