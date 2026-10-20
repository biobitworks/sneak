#!/usr/bin/env bash
# Keep @biobitworks/planner websocket-online in a tmux session.
# Credentials: ~/.secrets/sneak/band_planner_agent_config.yaml (never printed).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SESSION="sneak-planner"
export SNEAK_PLANNER_ONLINE_WAIT_S="${SNEAK_PLANNER_ONLINE_WAIT_S:-30}"
# Hold forever by running agent.run() only (no stop). Use Python one-shot daemon.
tmux -f /exec-daemon/tmux.portal.conf has-session -t "=$SESSION" 2>/dev/null && {
  echo "session_exists:$SESSION"
  exit 0
}
tmux -f /exec-daemon/tmux.portal.conf new-session -d -s "$SESSION" -c "$ROOT" -- bash -lc '
  cd "'"$ROOT"'"
  python3 - <<PY
import asyncio, os, sys
sys.path.insert(0, "src")
from sneak.planner_runtime import build_planner_adapter, load_planner_credentials
from band import Agent

async def main():
    agent_id, api_key = load_planner_credentials()
    os.environ.setdefault("BAND_PLANNER_AGENT_ID", agent_id)
    os.environ.setdefault("BAND_PLANNER_API_KEY", api_key)
    agent = Agent.create(adapter=build_planner_adapter(), agent_id=agent_id, api_key=api_key)
    await agent.run()

asyncio.run(main())
PY
'
echo "started:$SESSION"
