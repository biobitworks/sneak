#!/usr/bin/env python3
"""Authenticate BAND Human API and verify live room / board / agent identities.

Desktop `band` CLI requires Band Desktop + jamd (localhost). This cloud agent
authenticates with BAND_USER_API_KEY against app.band.ai Human API instead.
Does not claim SIGNED or MMR_COMMITTED.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.band_client import DEFAULT_AGENTS, DEFAULT_ROOM_ID, BandClient
from sneak.evidence import EvidenceStore, digest_payload
from sneak.merkle import breakpoint_receipt
from sneak.secrets import export_to_environ, presence_receipt


def main() -> int:
    export_to_environ()
    out = ROOT / "receipts/connectors"
    out.mkdir(parents=True, exist_ok=True)
    store = EvidenceStore(ROOT / "local-runs/evidence-band-verify")

    client = BandClient()
    me = client.me()
    agents = client.list_agents()
    chats = client.list_chats()

    # Prefer newest room that already has Tom/Jerry (tasks room), else DEFAULT.
    target_room = DEFAULT_ROOM_ID
    for ch in sorted(chats.get("chats") or [], key=lambda c: c.get("inserted_at") or "", reverse=True):
        handles = {a.get("handle") for a in (ch.get("agents") or [])}
        if "biobitworks/tom" in handles and "biobitworks/jerry" in handles:
            target_room = ch["id"]
            break

    parts = client.list_participants(target_room)
    tasks_before = client.list_tasks(target_room)
    board = client.get_board(target_room)

    created = None
    if tasks_before.get("active_count", 0) == 0:
        created = client.create_task(
            "SNEAK-022 authenticate and verify room/board/agents",
            detail=(
                "Filed by cloud agent after Human API auth. "
                "UI showed No active tasks; verifying room/board/agent identities."
            ),
            room_id=target_room,
        )
    tasks_after = client.list_tasks(target_room)

    # Also ensure Sneak custody room has a visible task if empty.
    sneak_tasks = client.list_tasks(DEFAULT_ROOM_ID)
    sneak_created = None
    if sneak_tasks.get("active_count", 0) == 0:
        sneak_created = client.create_task(
            "SNEAK-022 authenticate and verify room/board/agents",
            detail="Mirror task on Sneak — Requirements & Custody room.",
            room_id=DEFAULT_ROOM_ID,
        )
        sneak_tasks = client.list_tasks(DEFAULT_ROOM_ID)

    band_msg = None
    if client.available:
        client.room_id = target_room
        band_msg = client.send_mention(
            "SNEAK-022 identity verification: Human API auth as biobitworks. "
            f"Target room={target_room}. Active tasks now={tasks_after.get('active_count')}. "
            "Please ACK with your agent id/handle. Do not print secrets.",
            ["claude", "chatgpt"],
        )

    # Map configured DEFAULT_AGENTS against live roster.
    live_by_id = {a.get("id"): a for a in (agents.get("agents") or [])}
    identity_checks = []
    for harness, cfg in DEFAULT_AGENTS.items():
        live = live_by_id.get(cfg["id"])
        identity_checks.append(
            {
                "harness": harness,
                "configured": cfg,
                "live_agent_record": live,
                "id_match": bool(live),
                "name_match": bool(live and live.get("name") == cfg["name"]),
            }
        )

    package = {
        "id": "SNEAK-022-BAND-IDENTITY-VERIFY",
        "parent": "SNEAK-021",
        "auth": {
            "method": "BAND_USER_API_KEY via Human API (app.band.ai/api/v1/me)",
            "desktop_band_cli": {
                "available_in_cloud_vm": False,
                "reason": "band CLI is bundled with Band Desktop/jamd (localhost); not installed on this Linux cloud agent",
                "docs": "https://docs.band.ai/jam",
            },
            "me": me,
            "api_key_present": client.available,
        },
        "target_room_id": target_room,
        "default_sneak_room_id": DEFAULT_ROOM_ID,
        "chats": chats.get("chats"),
        "owned_agents": agents.get("agents"),
        "participants_target_room": parts.get("participants"),
        "identity_checks": identity_checks,
        "board_goal": board,
        "tasks_before": tasks_before,
        "task_created": created,
        "tasks_after": tasks_after,
        "sneak_room_tasks": sneak_tasks,
        "sneak_task_created": sneak_created,
        "mention": {
            "ok": bool(band_msg and band_msg.get("ok")),
            "http_status": (band_msg or {}).get("http_status"),
            "message_id": ((band_msg or {}).get("message") or {}).get("id"),
            "recipients": (band_msg or {}).get("recipients"),
        },
        "empty_board_explanation": (
            "UI 'No active tasks' matches GET /chats/{id}/tasks returning []. "
            "Filing POST {subject,detail} creates an active shared board task."
        ),
        "secrets": presence_receipt(),
        "meaning": "Live BAND room/board/agent identity verification; not SIGNED/MMR",
    }
    package["artifact_digest"] = digest_payload(package)
    store.append_receipt("band_identity_verify", package, provider="band")

    receipt = breakpoint_receipt(
        schema="sneak.band-identity-verify.v1",
        breakpoint_id="SNEAK-022",
        parent_id="SNEAK-021",
        records=[
            {
                "id": "SNEAK-022-AUTH",
                "kind": "band_human_api_auth",
                "payload": {
                    "ok": me.get("ok"),
                    "user_id": me.get("user_id"),
                    "handle": me.get("handle"),
                    "desktop_cli": False,
                },
            },
            {
                "id": "SNEAK-022-ROOM",
                "kind": "band_room",
                "payload": {
                    "target_room_id": target_room,
                    "sneak_room_id": DEFAULT_ROOM_ID,
                    "chat_count": len(chats.get("chats") or []),
                },
            },
            {
                "id": "SNEAK-022-AGENTS",
                "kind": "band_agents",
                "payload": {"identity_checks": identity_checks, "participants": parts.get("participants")},
            },
            {
                "id": "SNEAK-022-BOARD",
                "kind": "band_tasks_board",
                "payload": {
                    "tasks_before_count": tasks_before.get("active_count"),
                    "tasks_after_count": tasks_after.get("active_count"),
                    "created_task_id": (created or {}).get("task", {}).get("id") if created else None,
                    "board_goal_outcome": board.get("observed_outcome"),
                },
            },
        ],
        meaning="BAND Human API auth + verified room/agent IDs + filed shared task on empty board",
    )
    receipt["mmr"] = "NOT_COMMITTED"
    receipt["package_digest"] = package["artifact_digest"]

    (out / "SNEAK-022_BAND_IDENTITY_VERIFY.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "SNEAK-022_BAND_IDENTITY_PACKAGE.json").write_text(
        json.dumps(package, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    md = [
        "# SNEAK-022 BAND identity verification",
        "",
        f"- Auth: Human API as `{me.get('handle')}` (`{me.get('user_id')}`) — **{me.get('ok')}**",
        f"- Desktop `band` CLI on this VM: **False** (needs Band Desktop/jamd)",
        f"- Target room: `{target_room}`",
        f"- Sneak room: `{DEFAULT_ROOM_ID}`",
        f"- Active tasks (target) before→after: "
        f"**{tasks_before.get('active_count')} → {tasks_after.get('active_count')}**",
        f"- Board goal endpoint (Human API): **{board.get('observed_outcome')}**",
        f"- Tom/Jerry mention: **{(band_msg or {}).get('ok')}**",
        "",
        "## Agent identities",
        "",
        "| Harness | Configured id | Live name | Match |",
        "|---|---|---|---|",
    ]
    for row in identity_checks:
        cfg = row["configured"]
        live = row["live_agent_record"] or {}
        md.append(
            f"| {row['harness']} | `{cfg['id']}` | {live.get('name')} | **{row['id_match']}** |"
        )
    md.extend(
        [
            "",
            "Empty Tasks UI = zero active shared tasks. Filing `POST /chats/{id}/tasks` with "
            "`{subject, detail}` populates the board.",
            "",
        ]
    )
    (out / "SNEAK-022_BAND_IDENTITY_VERIFY.md").write_text("\n".join(md), encoding="utf-8")

    print(
        json.dumps(
            {
                "id": "SNEAK-022",
                "auth_ok": me.get("ok"),
                "handle": me.get("handle"),
                "target_room_id": target_room,
                "tasks_before": tasks_before.get("active_count"),
                "tasks_after": tasks_after.get("active_count"),
                "created_task": (created or {}).get("task"),
                "identity_checks_ok": all(r["id_match"] for r in identity_checks),
                "mention_ok": bool(band_msg and band_msg.get("ok")),
                "root": receipt.get("root"),
                "package_digest": package["artifact_digest"],
                "mmr": "NOT_COMMITTED",
            },
            indent=2,
        )
    )
    return 0 if me.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
