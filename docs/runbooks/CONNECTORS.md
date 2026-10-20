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
python3 scripts/live_band_cognee.py
```

- Cognee Cloud is used as working-memory **data storage** (`add_text` → `cognify` → `search` on `sneak_working_memory`).
- BAND Human API messages Claude harness agent **Tom** and ChatGPT harness agent **Jerry** in room `20f1ee5f-…`.
- Receipts: `receipts/connectors/SNEAK-015_*` (no secret values).

Desktop UI board/cost views and human approval still need operator checkpoints.

## Live providers (atom verified=true)

| Connector | Mandatory? | Live proof needed |
|---|---|---|
| BAND Desktop | Yes (M01–M20, M28) | Room/board/handoff/human decision IDs |
| Cognee (OSS or Cloud storage used here) | Yes (M21–M27, M29) | Write/cognify/recall + behavior change |
| Snyk + app-security-score | Bonus (S01–S09) | SCA+SAST on exact staged digest; pin Javier `@6e1f276` |
| Flexprice | Bonus (F01–F05) | Test-mode usage ingest/readback |

Local adapters fail closed: missing credentials stay `NOT_TESTED` / `BLOCKED`. Never export `SNYK_TOKEN` into candidate environments, git, notebooks, or receipts.
