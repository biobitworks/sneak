# Connect Remote Agent — Planner (`@biobitworks/planner`)

Fill the Band **Connect Remote Agent** form with these values (or skip the form:
this agent is already registered via Human API).

| Field | Value |
|---|---|
| Agent name | `Planner` |
| Handle | `planner` → **`@biobitworks/planner`** |
| Description | `Room planner/architect for Sneak: writes one shared plan, files board tasks, assigns Tom (Claude) and Jerry (ChatGPT), never marks Done without evidence.` |
| Tag | `planner` |
| Automatic contacts / all your agents | **On** (`registry_access`) |
| Public directory | **Off** |

## Already registered (do not duplicate)

- Agent id: `64f24a90-3937-47c8-bc7c-f03cb7980d49`
- Handle: `@biobitworks/planner`
- API key: stored only in `~/.secrets/sneak/providers.env` as `BAND_PLANNER_API_KEY` (shown once at register; never commit)

## Rooms

- Planner / tasks room: `7e218ad7-4d4e-4a07-a3b2-d4db8a03b4c3`
- Sneak custody room: `20f1ee5f-6f5b-46c5-9271-0ba536d322fd`

## Runtime connect

External agents stay **inactive/offline** until a process connects with the agent API key
(Band SDK / WebSocket). Human API can still file tasks and mention the agent.

```bash
# credentials live outside the repo
# ~/.secrets/sneak/band_planner_agent_config.yaml  (planner.agent_id + planner.api_key)
python3 -m pip install band-sdk
python3 scripts/run_band_planner_runtime.py   # SNEAK-025: bring websocket online
python3 scripts/run_band_planner_checkoffs.py # SNEAK-023: refresh plan-track board
```

Deterministic adapter (no LLM) posts the plan-track status and refuses to mark
human gates (#6/#7) Done. Hold the process to keep `online=true`.

## Note

A separate `@cmanjesh/planner` may also be in the room. Prefer **`@biobitworks/planner`**
for this project's plan ownership.
