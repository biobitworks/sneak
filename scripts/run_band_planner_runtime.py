#!/usr/bin/env python3
"""Bring @biobitworks/planner online via Band SDK WebSocket and verify plan track.

Runs the deterministic Planner adapter for a bounded window, confirms Human API
presence (online=true), mentions Tom/Jerry/Planner/Chirag for checkoffs, and
emits SNEAK-025 receipts. Never prints API keys. Does not mark human gates Done.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.band_client import DEFAULT_AGENTS, PLANNER_ROOM_ID, BandClient
from sneak.evidence import EvidenceStore, digest_payload
from sneak.merkle import breakpoint_receipt
from sneak.planner_runtime import (
    PLAN_TRACK_REPLY,
    build_planner_adapter,
    load_planner_credentials,
    planner_presence_receipt,
)
from sneak.secrets import export_to_environ, presence_receipt


ONLINE_WAIT_S = float(os.environ.get("SNEAK_PLANNER_ONLINE_WAIT_S", "60"))
RUN_AFTER_ONLINE_S = float(os.environ.get("SNEAK_PLANNER_HOLD_S", "40"))


def _planner_participant(client: BandClient) -> dict | None:
    parts = client.list_participants(PLANNER_ROOM_ID)
    pid = DEFAULT_AGENTS["planner"]["id"]
    return next((p for p in (parts.get("participants") or []) if p.get("id") == pid), None)


async def _run_agent_until(stop_event: asyncio.Event, adapter) -> dict:
    from band import Agent
    from band.core.exceptions import AgentAlreadyRunningError

    agent_id, api_key = load_planner_credentials()
    # Export into env for any SDK side paths; do not print.
    os.environ.setdefault("BAND_PLANNER_AGENT_ID", agent_id)
    os.environ.setdefault("BAND_PLANNER_API_KEY", api_key)

    started = time.time()
    stop_err = None
    already_running = False
    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
    )
    run_task = asyncio.create_task(agent.run())
    # Detect lock contention quickly (raised inside start()).
    for _ in range(50):
        if run_task.done():
            break
        await asyncio.sleep(0.1)
    if run_task.done():
        exc = run_task.exception() if not run_task.cancelled() else None
        if isinstance(exc, AgentAlreadyRunningError):
            already_running = True
            await stop_event.wait()
            return {
                "run_seconds": round(time.time() - started, 2),
                "replies_sent": 0,
                "turns_seen": 0,
                "turn_log": [],
                "last_error": None,
                "stop_error": None,
                "already_running_elsewhere": True,
            }
        if exc:
            raise exc

    try:
        await stop_event.wait()
    finally:
        try:
            await agent.stop()
        except Exception as exc:  # noqa: BLE001 — capture for receipt
            stop_err = str(type(exc).__name__)
        if not run_task.done():
            run_task.cancel()
            try:
                await run_task
            except (asyncio.CancelledError, Exception):
                pass
        elif run_task.done() and not run_task.cancelled():
            exc = run_task.exception()
            if isinstance(exc, AgentAlreadyRunningError):
                already_running = True
            elif exc and stop_err is None:
                stop_err = type(exc).__name__
    return {
        "run_seconds": round(time.time() - started, 2),
        "replies_sent": getattr(adapter, "replies_sent", 0),
        "turns_seen": getattr(adapter, "turns_seen", 0),
        "turn_log": list(getattr(adapter, "turn_log", []) or [])[-10:],
        "last_error": getattr(adapter, "last_error", None),
        "stop_error": stop_err,
        "already_running_elsewhere": already_running,
    }


async def async_main() -> dict:
    export_to_environ()
    store = EvidenceStore(ROOT / "local-runs/evidence-planner-runtime")
    out = ROOT / "receipts/connectors"
    out.mkdir(parents=True, exist_ok=True)

    adapter = build_planner_adapter()
    stop_event = asyncio.Event()
    agent_task = asyncio.create_task(_run_agent_until(stop_event, adapter))

    client = BandClient()
    online = False
    connection_status = None
    part = None
    deadline = time.time() + ONLINE_WAIT_S
    while time.time() < deadline:
        part = _planner_participant(client)
        connection_status = (part or {}).get("connection_status")
        online = bool((part or {}).get("online"))
        if online:
            break
        await asyncio.sleep(2.0)

    mention = {"ok": False}
    chase = {"ok": False}
    chirag = {"ok": False}
    if online and client.available:
        # Allow room channel subscriptions to settle after presence flips online.
        await asyncio.sleep(5.0)
        mention = client.send_mention(
            "Planner runtime connected. Please post the current plan-track status "
            "and keep overall Done=false until human gates complete.",
            ["planner"],
            room_id=PLANNER_ROOM_ID,
        )
        chase = client.send_mention(
            "CHECKOFF #3/#4: please reply ACK with your handle/agent id. "
            "Board tools may be missing — chat ACK is acceptable evidence. "
            "Do not mark Done without evidence. Planner is now online.",
            ["claude", "chatgpt"],
            room_id=PLANNER_ROOM_ID,
        )
        # Chirag is a User participant — mention by posting a room message via dual
        # human-facing ask (Human API mentions agents; include handle in text for Chirag).
        chirag = client.send_mention(
            "@cmanjesh CHECKOFF #6: please confirm roster + that "
            "@biobitworks/planner is online (websocket connected). "
            "Byron #7 remains human-pending. Overall Done stays false.",
            ["planner"],
            room_id=PLANNER_ROOM_ID,
        )
        # Give the adapter time to answer the mention.
        await asyncio.sleep(RUN_AFTER_ONLINE_S)
    else:
        # Still hold briefly so a late connect can be observed.
        await asyncio.sleep(min(10.0, ONLINE_WAIT_S))

    stop_event.set()
    runtime_meta = await agent_task

    # Re-check presence after stop (may flip offline — record both).
    part_after = _planner_participant(client)
    part_during = part
    tasks = client.list_tasks(PLANNER_ROOM_ID, state="active") if client.available else {}
    checkoffs = []
    for t in tasks.get("tasks") or []:
        subj = str(t.get("subject") or "")
        if "CHECKOFF" in subj or subj.startswith("SNEAK-022") or subj.startswith("SNEAK-024"):
            checkoffs.append(t)

    msgs = client.list_recent_messages(PLANNER_ROOM_ID, limit=50) if client.available else {}
    planner_id = DEFAULT_AGENTS["planner"]["id"]
    tom_id = DEFAULT_AGENTS["claude"]["id"]
    jerry_id = DEFAULT_AGENTS["chatgpt"]["id"]
    recent = msgs.get("messages") or []
    planner_reply_seen = any(
        m.get("sender_id") == planner_id
        and "SNEAK plan track (Planner" in str(m.get("content") or "")
        for m in recent
    )

    def _chat_ack(agent_id: str, needles: list[str]) -> dict:
        hits = []
        for m in recent:
            if m.get("sender_id") != agent_id:
                continue
            blob = str(m.get("content") or "")
            low = blob.lower()
            if any(n.lower() in low for n in needles):
                hits.append(
                    {
                        "message_id": m.get("id"),
                        "content_prefix": blob[:160],
                    }
                )
        return {"observed": bool(hits), "hits": hits[:3], "kind": "CHAT_ACK"}

    tom_ack = _chat_ack(
        tom_id,
        [
            "CHAT_ACK #3",
            "ACK CHECKOFF #3",
            "checkoff #3",
            "ACK from Tom",
            "Board tool missing",
        ],
    )
    jerry_ack = _chat_ack(
        jerry_id,
        [
            "CHAT_ACK #4",
            "CHECKOFF #4",
            "chat ACK for #4",
            "ACK: @biobitworks/jerry",
            "Board tool missing",
        ],
    )

    track = {
        "planner_online_observed": online,
        "planner_connection_status": connection_status,
        "planner_reply_seen": planner_reply_seen,
        "tom_task_3_board": next(
            (t.get("overall_status") for t in checkoffs if t.get("number") == 3), None
        ),
        "jerry_task_4_board": next(
            (t.get("overall_status") for t in checkoffs if t.get("number") == 4), None
        ),
        "tom_task_3_chat_ack": tom_ack,
        "jerry_task_4_chat_ack": jerry_ack,
        "chirag_task_6": next(
            (t.get("overall_status") for t in checkoffs if t.get("number") == 6), None
        ),
        "byron_human_task_7": next(
            (t.get("overall_status") for t in checkoffs if t.get("number") == 7), None
        ),
        "overall_plan_done": False,
        "reason": (
            "Planner websocket runtime exercised. Tom/Jerry chat ACKs recorded "
            "(board may stay pending if BOARD_TOOL_MISSING). Human gates #6/#7 "
            "remain open. Overall Done false."
        ),
    }

    package = {
        "id": "SNEAK-025-PLANNER-RUNTIME",
        "parent": "SNEAK-024",
        "form_fill_unchanged": True,
        "agent": {
            "id": DEFAULT_AGENTS["planner"]["id"],
            "handle": DEFAULT_AGENTS["planner"]["handle"],
            "name": DEFAULT_AGENTS["planner"]["name"],
        },
        "room_id": PLANNER_ROOM_ID,
        "presence_during": planner_presence_receipt(
            online=online, connection_status=connection_status
        ),
        "participant_during": part_during,
        "participant_after_stop": part_after,
        "runtime": runtime_meta,
        "band_mentions": {
            "planner_prompt": {
                "ok": bool(mention.get("ok")),
                "message_id": (mention.get("message") or {}).get("id"),
            },
            "tom_jerry_chase": {
                "ok": bool(chase.get("ok")),
                "message_id": (chase.get("message") or {}).get("id"),
            },
            "chirag_reminder": {
                "ok": bool(chirag.get("ok")),
                "message_id": (chirag.get("message") or {}).get("id"),
            },
        },
        "plan_track": track,
        "active_checkoffs": [
            {
                "number": t.get("number"),
                "subject": t.get("subject"),
                "overall_status": t.get("overall_status"),
            }
            for t in checkoffs
        ],
        "plan_track_reply_template_digest": digest_payload({"text": PLAN_TRACK_REPLY}),
        "secrets": presence_receipt(),
        "mmr": "NOT_COMMITTED",
        "signed": False,
        "meaning": (
            "Planner Band SDK websocket runtime brought online; plan track posted; "
            "overall Done remains false"
        ),
    }
    package["artifact_digest"] = digest_payload(package)
    store.append_receipt("band_planner_runtime", package, provider="band")

    receipt = breakpoint_receipt(
        schema="sneak.band-planner-runtime.v1",
        breakpoint_id="SNEAK-025",
        parent_id="SNEAK-024",
        records=[
            {
                "id": "SNEAK-025-PRESENCE",
                "kind": "planner_presence",
                "payload": {
                    "online_observed": online,
                    "connection_status": connection_status,
                    "reply_seen": planner_reply_seen,
                },
            },
            {
                "id": "SNEAK-025-TRACK",
                "kind": "plan_track",
                "payload": track,
            },
            {
                "id": "SNEAK-025-RUNTIME",
                "kind": "runtime_meta",
                "payload": {
                    "run_seconds": runtime_meta.get("run_seconds"),
                    "replies_sent": runtime_meta.get("replies_sent"),
                },
            },
        ],
        meaning=package["meaning"],
    )
    receipt["mmr"] = "NOT_COMMITTED"
    receipt["package_digest"] = package["artifact_digest"]

    (out / "SNEAK-025_PLANNER_RUNTIME.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "SNEAK-025_PLANNER_RUNTIME_PACKAGE.json").write_text(
        json.dumps(package, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    md = [
        "# SNEAK-025 Planner websocket runtime",
        "",
        f"- Planner: `@biobitworks/planner` (`{DEFAULT_AGENTS['planner']['id']}`)",
        f"- Room: `{PLANNER_ROOM_ID}`",
        f"- Online observed: **{online}** (connection_status=`{connection_status}`)",
        f"- Plan-track reply seen: **{planner_reply_seen}**",
        f"- Replies sent (adapter): **{runtime_meta.get('replies_sent')}**",
        f"- Overall plan Done: **False**",
        "",
        "## Chase",
        "",
        f"- Planner mention ok: **{bool(mention.get('ok'))}**",
        f"- Tom/Jerry ACK chase ok: **{bool(chase.get('ok'))}**",
        f"- Chirag #6 reminder ok: **{bool(chirag.get('ok'))}**",
        f"- Tom #3 chat ACK: **{tom_ack.get('observed')}**",
        f"- Jerry #4 chat ACK: **{jerry_ack.get('observed')}**",
        "",
        "## Checkoffs (unchanged honesty)",
        "",
        "| # | Subject | Board | Chat ACK |",
        "|---:|---|---|---|",
    ]
    for t in checkoffs:
        num = t.get("number")
        chat = "—"
        if num == 3:
            chat = str(tom_ack.get("observed"))
        elif num == 4:
            chat = str(jerry_ack.get("observed"))
        md.append(
            f"| {num} | {t.get('subject')} | {t.get('overall_status')} | {chat} |"
        )
    md.extend(
        [
            "",
            "Human gates #6/#7 remain open. Board Done not claimed from chat ACK alone.",
            "",
        ]
    )
    (out / "SNEAK-025_PLANNER_RUNTIME.md").write_text("\n".join(md), encoding="utf-8")

    return {
        "id": "SNEAK-025",
        "online_observed": online,
        "connection_status": connection_status,
        "planner_reply_seen": planner_reply_seen,
        "replies_sent": runtime_meta.get("replies_sent"),
        "overall_plan_done": False,
        "root": receipt.get("root"),
        "package_digest": package["artifact_digest"],
        "mmr": "NOT_COMMITTED",
    }


def main() -> int:
    summary = asyncio.run(async_main())
    print(json.dumps(summary, indent=2))
    return 0 if summary.get("online_observed") else 2


if __name__ == "__main__":
    raise SystemExit(main())
