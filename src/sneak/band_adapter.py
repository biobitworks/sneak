"""BAND coordination adapter for Claude and ChatGPT harness agents.

Live mode uses the BAND Human API (app.band.ai) to message agents in a shared room.
Pending human decisions are never treated as approved.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .band_client import BandClient
from .contracts import EvidenceRef
from .evidence import EvidenceStore, utc_now


@dataclass
class BandState:
    room_id: Optional[str] = None
    decisions: dict[str, dict[str, Any]] = field(default_factory=dict)
    handoffs: list[dict[str, Any]] = field(default_factory=list)
    executed_request_ids: set[str] = field(default_factory=set)


class BandAdapter:
    def __init__(
        self,
        store: EvidenceStore,
        state: Optional[BandState] = None,
        *,
        live: Optional[bool] = None,
        client: Optional[BandClient] = None,
    ):
        self.store = store
        self.state = state or BandState()
        self.client = client or BandClient()
        self.live_available = self.client.available if live is None else live and self.client.available
        if self.live_available and not self.state.room_id:
            self.state.room_id = self.client.room_id

    def publish_handoff(
        self,
        task_id: str,
        recipient: str,
        evidence: list[EvidenceRef],
        *,
        request_id: Optional[str] = None,
        message: Optional[str] = None,
    ) -> EvidenceRef:
        if request_id and request_id in self.state.executed_request_ids:
            return self.store.append_receipt(
                "band_handoff_duplicate",
                {
                    "task_id": task_id,
                    "recipient": recipient,
                    "request_id": request_id,
                    "observed_outcome": "DEDUPED",
                    "evidence_ids": [e.external_id for e in evidence],
                },
                provider="band",
            )
        if request_id:
            self.state.executed_request_ids.add(request_id)

        live_msg = None
        if self.live_available:
            content = message or (
                f"Handoff task={task_id}. Evidence refs: "
                + ",".join(e.external_id for e in evidence)
                + ". Please acknowledge in this BAND room."
            )
            live_msg = self.client.send_mention(content, [recipient])

        payload = {
            "task_id": task_id,
            "recipient": recipient,
            "request_id": request_id,
            "room_id": self.state.room_id,
            "evidence_ids": [e.external_id for e in evidence],
            "live_available": self.live_available,
            "live_message": (
                {
                    "ok": live_msg.get("ok"),
                    "http_status": live_msg.get("http_status"),
                    "message_id": (live_msg.get("message") or {}).get("id"),
                    "recipients": live_msg.get("recipients"),
                }
                if live_msg
                else None
            ),
            "observed_outcome": (
                "PASS"
                if live_msg and live_msg.get("ok")
                else ("LOCAL_CONTRACT_ONLY" if not self.live_available else "FAIL")
            ),
            "observed_at": utc_now(),
        }
        self.state.handoffs.append(payload)
        return self.store.append_receipt("band_handoff", payload, provider="band")

    def message_claude_and_chatgpt(
        self,
        content: str,
        *,
        room_id: Optional[str] = None,
    ) -> EvidenceRef:
        """Explicit dual-harness mention: Claude (Tom) + ChatGPT (Jerry)."""
        if not self.live_available:
            return self.store.append_receipt(
                "band_dual_harness_message",
                {
                    "observed_outcome": "NOT_TESTED",
                    "reason": "BAND_USER_API_KEY missing",
                    "intended_recipients": ["claude", "chatgpt"],
                },
                provider="band",
            )
        live_msg = self.client.send_mention(
            content, ["claude", "chatgpt"], room_id=room_id or self.state.room_id
        )
        return self.store.append_receipt(
            "band_dual_harness_message",
            {
                "room_id": room_id or self.state.room_id,
                "harnesses": ["claude", "chatgpt"],
                "agents": live_msg.get("recipients"),
                "message_id": (live_msg.get("message") or {}).get("id"),
                "http_status": live_msg.get("http_status"),
                "observed_outcome": "PASS" if live_msg.get("ok") else "FAIL",
            },
            provider="band",
        )

    def read_decision(self, request_id: str) -> dict[str, Any]:
        decision = self.state.decisions.get(request_id)
        if decision is None:
            return {
                "request_id": request_id,
                "human_decision": "PENDING",
                "human_response": None,
                "observed_outcome": "NOT_TESTED",
                "approved": False,
            }
        status = decision.get("human_decision", "PENDING")
        return {
            "request_id": request_id,
            "human_decision": status,
            "human_response": decision.get("human_response"),
            "observed_outcome": decision.get("observed_outcome", "REQUEST_OBSERVED"),
            "approved": status in ("APPROVE", "APPROVED"),
            "reconnect_preserved": True,
        }

    def record_decision(
        self,
        request_id: str,
        human_decision: str,
        human_response: Optional[str] = None,
    ) -> EvidenceRef:
        self.state.decisions[request_id] = {
            "human_decision": human_decision,
            "human_response": human_response,
            "observed_outcome": (
                "PASS" if human_decision in ("APPROVE", "APPROVED", "REJECT") else "PENDING"
            ),
        }
        return self.store.append_receipt(
            "band_decision",
            {"request_id": request_id, **self.state.decisions[request_id]},
            provider="band",
        )

    def load_room_receipt(self, path: Path) -> dict[str, Any]:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        room = None
        if "leaves" in data:
            for leaf in data.get("leaves", []):
                event = leaf.get("event", {})
                payload = event.get("payload", {})
                if payload.get("room_id"):
                    room = payload["room_id"]
                    break
        self.state.room_id = room or data.get("room_id") or self.state.room_id
        return {
            "room_id": self.state.room_id,
            "receipt_id": data.get("id"),
            "human_decision": data.get("human_decision", "UNKNOWN"),
            "observed_outcome": "LOADED_RECEIPT",
            "live_session": self.live_available,
        }

    def availability(self) -> dict[str, Any]:
        me = self.client.me() if self.live_available else {"ok": False}
        parts = self.client.list_participants() if self.live_available and me.get("ok") else {}
        online_agents = [
            p
            for p in parts.get("participants", [])
            if p.get("type") == "Agent" and p.get("online")
        ]
        return {
            "provider": "band",
            "live_available": bool(self.live_available and me.get("ok")),
            "room_id": self.state.room_id,
            "user_handle": me.get("handle"),
            "online_agents": online_agents,
            "harness_map": {
                "claude": self.client.agents["claude"]["name"],
                "chatgpt": self.client.agents["chatgpt"]["name"],
            },
            "observed_outcome": "READY" if (self.live_available and me.get("ok")) else "NOT_TESTED",
        }
