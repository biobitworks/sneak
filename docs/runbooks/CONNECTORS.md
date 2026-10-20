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

## BAND auth + room/board/agent identity verify

Desktop `band` CLI needs Band Desktop + `jamd` on the local machine. Cloud agents
authenticate with `BAND_USER_API_KEY` against the Human API instead:

```bash
python3 scripts/verify_band_identities.py
```

- Lists chats, participants, owned agents (Tom/Jerry IDs).
- Explains UI **No active tasks** = `GET /chats/{id}/tasks` → `[]`.
- Files a shared board task via `POST {subject, detail}` when the board is empty.
- Receipts: `SNEAK-022_*`.

## Planner remote agent + plan checkoffs

Form fill + registration notes: [`BAND_PLANNER_REMOTE_AGENT.md`](BAND_PLANNER_REMOTE_AGENT.md).

```bash
python3 scripts/run_band_planner_checkoffs.py
```

- Agent: `@biobitworks/planner` in room `7e218ad7-…`
- Per-role CHECKOFF tasks; overall Done stays false until the correct assignees complete them
- Receipts: `SNEAK-023_*`

## Conversation custody (unique merkle BPs + model MMR deltas)

```bash
python3 scripts/run_conversation_custody.py
```

- Unique conversation merkle breakpoints with `pass: true|false`
- Per-model candidate MMR peaks vs root-question leaf (XOR deltas over time); project MMR stays `NOT_COMMITTED`
- Pipeline: `input_hash` → deterministic step FCOs → `output_hash`; updates via UpdateTrackingFCO
- BAND ask/respond to Tom + Jerry + Planner in planner room; Cognee `@Data` capture
- Verifies REQ-CUSTODY-01..11 (mandatory + optional) independently
- Receipts: `SNEAK-024_*`; requirements: `data/verification/requirements_sneak_024.jsonl`

## Planner websocket runtime (online presence)

```bash
python3 -m pip install band-sdk
python3 scripts/run_band_planner_runtime.py
```

- Loads `BAND_PLANNER_*` / `~/.secrets/sneak/band_planner_agent_config.yaml` (never printed)
- Deterministic Planner adapter (no LLM): posts plan-track status; never marks human Done
- Verifies Human API `online=true` for `@biobitworks/planner`, chases Tom/Jerry ACK + Chirag #6
- Receipts: `SNEAK-025_*`

## Lanes wrap-up + Desktop CLI hosts

```bash
# Read-only status: receipts/connectors/SNEAK-027_LANES_WRAPUP.md
```

- magicstudio: no `band` CLI / Band.app (operator-observed)
- magicpro: CLI present, Desktop running, **not signed in** (`band whoami` → record not found) → run `band init`
- Tom/Jerry chat ACKs cover plan CHECKOFF #3/#4 only; they have **not** weighed in on Desktop host choice
- Do not post as the human account for red-team status (SNEAK-H01 risk); use a dedicated agent after `band init`
- Receipts: `SNEAK-027_*`

## AoK MVP requirement ledger (REQ-AOK-M01–M20)

```bash
python3 scripts/verify_aok_mvp_ledger.py
```

- Successor only: does **not** rewrite `data/rules/atomic_acceptance_r5.jsonl`
- Scores from receipts + live Band observation — never graph-link inference
- Band Desktop atoms (M01, M16–M20) stay NOT_TESTED until Desktop is signed in
- Receipts: `SNEAK-028_*`; JSONL: `data/verification/requirements_sneak_028.jsonl`

## MVP hash travel (sponsors + optionals + agent→Snyk)

```bash
python3 scripts/run_mvp_hash_travel.py
```

- One leaf per sponsor **REQ-AOK-M01–M15**, each optional E/F/S atom, and each agent→Snyk binding
- Single `mvp_root`; every leaf has a merkle proof (`hash_travels`) that verifies to that root
- BAND @mentions Tom/Jerry/Planner: every agent connects to the shared Snyk connector digest (live scan still NOT_TESTED)
- Receipts: `SNEAK-029_*`; JSONL: `data/verification/mvp_hash_travel_sneak_029.jsonl`

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

**Baseline models: Liquid AI LFM + OpenJev. Qwen 2.5 is retired.**

```bash
# On MagicStudio (Desktop Commander or approved agent shell):
python3 scripts/probe_magicstudio_ollama.py
# or the zsh probe embedded in receipts/connectors/SNEAK-017_MAGICSTUDIO_OLLAMA.json
```

Receipts: `SNEAK-017_*`, `SNEAK-017B_*`.

## Liquid AI + OpenJev × LongMemEval (conversation FCOs)

```bash
# Optional live keys in ~/.secrets/sneak/providers.env:
# LIQUID_API_KEY=...  OPENJEV_API_KEY=...  OPENJEV_BASE_URL=https://api.codiv.ai/v1
python3 scripts/run_liquid_openjev_longmemeval.py
```

- Each model conversation → `ConversationFCO`
- Each answer vs LongMemEval gold → `LongMemEvalDiffFCO`
- Per-token ROI for each model/agent/scenario (deterministic unit costs)
- Fixture: `data/fixtures/longmemeval_oracle_sample.json` (full corpus stays under `sources/`, gitignored)

Receipts: `SNEAK-021_*`.
