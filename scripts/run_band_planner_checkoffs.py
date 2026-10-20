#!/usr/bin/env python3
"""Verify Planner room plan track and per-role checkoff tasks.

Uses BAND_USER_API_KEY + optional BAND_PLANNER_API_KEY (never printed).
Does not claim overall plan Done while human/agent board checkoffs remain open.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.band_client import PLANNER_ROOM_ID, DEFAULT_AGENTS, BandClient
from sneak.evidence import EvidenceStore, digest_payload
from sneak.merkle import breakpoint_receipt
from sneak.secrets import export_to_environ, presence_receipt


def main() -> int:
    export_to_environ()
    # Ensure planner secrets loaded even if older allowlist caches linger.
    for ln in Path.home().joinpath(".secrets/sneak/providers.env").read_text().splitlines():
        if ln.startswith("BAND_PLANNER_") and "=" in ln:
            k, v = ln.split("=", 1)
            os.environ.setdefault(k, v)

    out = ROOT / "receipts/connectors"
    out.mkdir(parents=True, exist_ok=True)
    store = EvidenceStore(ROOT / "local-runs/evidence-band-planner")

    client = BandClient()
    room = PLANNER_ROOM_ID
    me = client.me()
    chats = client.list_chats()
    parts = client.list_participants(room)
    tasks = client.list_tasks(room, state="active")
    agents = client.list_agents()

    planner_cfg = DEFAULT_AGENTS["planner"]
    live_planner = next(
        (a for a in (agents.get("agents") or []) if a.get("id") == planner_cfg["id"]),
        None,
    )
    part_planner = next(
        (p for p in (parts.get("participants") or []) if p.get("id") == planner_cfg["id"]),
        None,
    )

    checkoffs = []
    for t in tasks.get("tasks") or []:
        subj = str(t.get("subject") or "")
        if "CHECKOFF" in subj or subj.startswith("SNEAK-022"):
            checkoffs.append(t)

    # Classify track status honestly.
    def status_of(num: int) -> str | None:
        for t in checkoffs:
            if t.get("number") == num:
                return t.get("overall_status")
        return None

    track = {
        "planner_task_2": status_of(2),
        "tom_task_3": status_of(3),
        "jerry_task_4": status_of(4),
        "byron_task_5_planner_mistaken": status_of(5),
        "chirag_task_6": status_of(6),
        "byron_human_task_7": status_of(7),
        "tom_jerry_board_tools": "MISSING_CHAT_ACK_ONLY",
        "overall_plan_done": False,
        "reason": (
            "Tom/Jerry harnesses lack Tasks board tools (BOARD_TOOL_MISSING). "
            "Human gates #7/#6 still pending. Do not declare Done."
        ),
    }

    package = {
        "id": "SNEAK-023-PLANNER-PLAN-TRACK",
        "parent": "SNEAK-022",
        "form_fill": {
            "agent_name": "Planner",
            "handle": "planner",
            "handle_full": "@biobitworks/planner",
            "description": (
                "Room planner/architect for Sneak: writes one shared plan, files board tasks, "
                "assigns Tom (Claude) and Jerry (ChatGPT), never marks Done without evidence."
            ),
            "tag": "planner",
            "automatic_contacts_all_own_agents": True,
            "public_directory": False,
            "already_registered": True,
            "agent_id": planner_cfg["id"],
        },
        "auth": {"me": me, "planner_api_key_present": bool(os.environ.get("BAND_PLANNER_API_KEY"))},
        "room_id": room,
        "planner_live_record": live_planner,
        "planner_participant": part_planner,
        "participants": parts.get("participants"),
        "active_tasks": checkoffs,
        "plan_track": track,
        "chat_count": len(chats.get("chats") or []),
        "secrets": presence_receipt(),
        "meaning": "Planner remote agent + plan-track checkoffs; overall Done remains false",
    }
    package["artifact_digest"] = digest_payload(package)
    store.append_receipt("band_planner_plan_track", package, provider="band")

    receipt = breakpoint_receipt(
        schema="sneak.band-planner-plan-track.v1",
        breakpoint_id="SNEAK-023",
        parent_id="SNEAK-022",
        records=[
            {
                "id": "SNEAK-023-PLANNER",
                "kind": "remote_agent",
                "payload": {
                    "id": planner_cfg["id"],
                    "handle": planner_cfg["handle"],
                    "in_room": bool(part_planner),
                    "online": bool((part_planner or {}).get("online")),
                },
            },
            {
                "id": "SNEAK-023-TRACK",
                "kind": "plan_track",
                "payload": track,
            },
            {
                "id": "SNEAK-023-TASKS",
                "kind": "checkoff_tasks",
                "payload": {
                    "count": len(checkoffs),
                    "numbers": [t.get("number") for t in checkoffs],
                },
            },
        ],
        meaning="Planner connected to room; plan checkoffs tracked; not overall Done",
    )
    receipt["mmr"] = "NOT_COMMITTED"
    receipt["package_digest"] = package["artifact_digest"]

    (out / "SNEAK-023_PLANNER_PLAN_TRACK.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "SNEAK-023_PLANNER_PACKAGE.json").write_text(
        json.dumps(package, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    md = [
        "# SNEAK-023 Planner remote agent + plan track checkoffs",
        "",
        f"- Planner: `@biobitworks/planner` (`{planner_cfg['id']}`)",
        f"- Room: `{room}`",
        f"- In room: **{bool(part_planner)}**; websocket online: **{(part_planner or {}).get('online')}**",
        f"- Overall plan Done: **False**",
        "",
        "## Connect Remote Agent form",
        "",
        "- Name: `Planner`",
        "- Handle: `planner`",
        "- Tag: `planner`",
        "- All-own-agents contacts: on; public directory: off",
        "- Already registered — do not create a duplicate",
        "",
        "## Checkoffs",
        "",
        "| # | Subject | Status | Assignees |",
        "|---:|---|---|---|",
    ]
    for t in checkoffs:
        assigns = ", ".join(
            f"{(a.get('assignee') or {}).get('handle')}:{a.get('status')}"
            for a in (t.get("assignments") or [])
        ) or "—"
        md.append(
            f"| {t.get('number')} | {t.get('subject')} | {t.get('overall_status')} | {assigns} |"
        )
    md.extend(
        [
            "",
            "Tom/Jerry: chat ACK only (`BOARD_TOOL_MISSING`). Byron #7 + Chirag #6 still need humans.",
            "",
        ]
    )
    (out / "SNEAK-023_PLANNER_PLAN_TRACK.md").write_text("\n".join(md), encoding="utf-8")

    print(
        json.dumps(
            {
                "id": "SNEAK-023",
                "planner_id": planner_cfg["id"],
                "room_id": room,
                "in_room": bool(part_planner),
                "online": bool((part_planner or {}).get("online")),
                "checkoffs": len(checkoffs),
                "overall_plan_done": False,
                "root": receipt.get("root"),
                "package_digest": package["artifact_digest"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
