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

## LOMO × merkle breakpoint → @Data → Snyk + score

Operator-approved path (SNEAK-016):

```bash
export SNYK_CLI=/path/to/snyk   # optional if snyk is on PATH
python3 scripts/run_lomo_snyk_breakpoints.py
```

After **each** LOMO merkle root breakpoint the pipeline:

1. Writes the breakpoint into Cognee dataset **`Data`** (alias **@Data**)
2. Notifies BAND Claude/ChatGPT on ablated successors
3. Runs Snyk SCA+SAST when `SNYK_TOKEN` + CLI are present (otherwise `NOT_TESTED`, never a fake clean 10/10)
4. Computes Javier app-security-score with coverage rejection

Receipts: `receipts/connectors/SNEAK-016_*`.

Desktop UI board/cost views still need operator checkpoints.

## Live providers (atom verified=true)

| Connector | Mandatory? | Live proof needed |
|---|---|---|
| BAND Desktop | Yes (M01–M20, M28) | Room/board/handoff/human decision IDs |
| Cognee (OSS or Cloud storage used here) | Yes (M21–M27, M29) | Write/cognify/recall + behavior change |
| Snyk + app-security-score | Bonus (S01–S09) | SCA+SAST on exact staged digest; pin Javier `@6e1f276` |
| Flexprice | Bonus (F01–F05) | Test-mode usage ingest/readback |

Local adapters fail closed: missing credentials stay `NOT_TESTED` / `BLOCKED`. Never export `SNYK_TOKEN` into candidate environments, git, notebooks, or receipts.

## FlexPrice actor audit (FCO / FCG / deterministic ROI)

Upstream: https://github.com/flexprice/flexprice

```bash
# Optional live ingest:
# FLEXPRICE_API_KEY=... in ~/.secrets/sneak/providers.env
python3 scripts/run_flexprice_actor_audit.py
```

Each actor action becomes an `ActorEventFCO` with `fco_candidate_sha256`. Typed
`FCGEdge`s link actors, sequence, and ROI. A candidate Merkle root over those
FCOs is recorded with **`mmr: NOT_COMMITTED`**. Deterministic ROI =

`(benefit_units − cost_units) / cost_units` with `ROUND_HALF_EVEN` to 6 dp.

Receipts: `SNEAK-020_*`.

## MagicStudio Ollama via Desktop Commander

Cloud agents cannot reach `magicSTUDIObox.local` without Desktop Commander MCP.
Self-hosted MacBook Pro workers are visible; MagicStudio still needs Desktop Commander or BAND shell approval.

```bash
# On MagicStudio (Desktop Commander or approved agent shell):
python3 scripts/probe_magicstudio_ollama.py
# or the zsh probe embedded in receipts/connectors/SNEAK-017_MAGICSTUDIO_OLLAMA.json
```

Receipts: `SNEAK-017_*`, `SNEAK-017B_*`.
