"""Live BAND Human API client for coordinating Claude and ChatGPT agents."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Optional

from .secrets import export_to_environ

BAND_BASE = "https://app.band.ai/api/v1/me"

# Existing Sneak room agents (from SNEAK-012/013). Harness mapping is explicit.
DEFAULT_AGENTS = {
    "claude": {
        "id": "3926218d-8342-4667-9f07-5b556b50fb7f",
        "name": "Tom",
        "handle": "biobitworks/tom",
        "harness": "claude",
        "role": "architect",
    },
    "chatgpt": {
        "id": "8b51f295-c2e7-4aaa-99dd-5f2335dcab49",
        "name": "Jerry",
        "handle": "biobitworks/jerry",
        "harness": "chatgpt",
        "role": "builder",
    },
}

DEFAULT_ROOM_ID = "20f1ee5f-6f5b-46c5-9271-0ba536d322fd"


class BandClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = BAND_BASE):
        export_to_environ()
        env_key = os.environ.get("BAND_USER_API_KEY", "")
        self.api_key = env_key if api_key is None else api_key
        self.base_url = base_url.rstrip("/")
        self.agents = dict(DEFAULT_AGENTS)
        self.room_id = DEFAULT_ROOM_ID

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _request(self, method: str, path: str, data: Any = None) -> tuple[int, Any]:
        headers = {
            "X-API-Key": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        body = None if data is None else json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            self.base_url + path, data=body, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read().decode("utf-8")
                return resp.status, json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(err)
            except json.JSONDecodeError:
                parsed = {"error": err[:500]}
            return e.code, parsed

    def me(self) -> dict[str, Any]:
        status, body = self._request("GET", "")
        user = (body or {}).get("data", {}).get("user", {}) if isinstance(body, dict) else {}
        return {
            "http_status": status,
            "user_id": user.get("id"),
            "handle": user.get("handle"),
            "ok": status == 200,
        }

    def list_agents(self) -> dict[str, Any]:
        status, body = self._request("GET", "/agents")
        agents = (body or {}).get("data", []) if isinstance(body, dict) else []
        safe = [
            {k: a.get(k) for k in ("id", "name", "slug", "is_external", "handle")}
            for a in agents
            if isinstance(a, dict)
        ]
        return {"http_status": status, "agents": safe, "ok": status == 200}

    def list_participants(self, room_id: Optional[str] = None) -> dict[str, Any]:
        rid = room_id or self.room_id
        status, body = self._request("GET", f"/chats/{rid}/participants")
        parts = (body or {}).get("data", []) if isinstance(body, dict) else []
        safe = [
            {k: p.get(k) for k in ("id", "name", "handle", "type", "connection_status", "online")}
            for p in parts
            if isinstance(p, dict)
        ]
        return {"http_status": status, "participants": safe, "ok": status == 200}

    def send_mention(
        self,
        content: str,
        recipients: list[str],
        *,
        room_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Send a room message mentioning Claude and/or ChatGPT harness agents.

        recipients: harness keys ('claude', 'chatgpt') or agent names ('Tom', 'Jerry').
        """
        rid = room_id or self.room_id
        mentions = []
        mention_labels = []
        for r in recipients:
            key = r.lower()
            agent = None
            if key in self.agents:
                agent = self.agents[key]
            else:
                for a in self.agents.values():
                    if a["name"].lower() == key or a["handle"].endswith("/" + key):
                        agent = a
                        break
            if not agent:
                return {"ok": False, "error": f"unknown_recipient:{r}"}
            mentions.append(
                {"id": agent["id"], "name": agent["name"], "handle": agent["handle"]}
            )
            mention_labels.append(f"@{agent['name']}")
        # Prefer explicit [[uuid]] style used in prior Sneak room receipts, plus mentions[].
        prefix = " ".join(f"@[[{m['id']}]]" for m in mentions)
        payload = {
            "message": {
                "content": f"{prefix} {content}".strip(),
                "mentions": mentions,
            }
        }
        status, body = self._request("POST", f"/chats/{rid}/messages", payload)
        msg = None
        if isinstance(body, dict):
            msg = body.get("data") or body.get("message") or body
        safe_msg = None
        if isinstance(msg, dict):
            safe_msg = {
                k: msg.get(k)
                for k in ("id", "content", "inserted_at", "sender_id", "message_type")
            }
        return {
            "http_status": status,
            "ok": status in (200, 201),
            "room_id": rid,
            "recipients": [
                {"harness": self._harness_for(m["id"]), "name": m["name"], "id": m["id"]}
                for m in mentions
            ],
            "message": safe_msg,
            "mention_labels": mention_labels,
        }

    def _harness_for(self, agent_id: str) -> str:
        for a in self.agents.values():
            if a["id"] == agent_id:
                return a["harness"]
        return "unknown"

    def list_recent_messages(self, room_id: Optional[str] = None, limit: int = 10) -> dict[str, Any]:
        rid = room_id or self.room_id
        status, body = self._request("GET", f"/chats/{rid}/messages?limit={limit}")
        data = (body or {}).get("data", []) if isinstance(body, dict) else []
        safe = []
        for m in data[:limit]:
            if not isinstance(m, dict):
                continue
            safe.append(
                {
                    k: m.get(k)
                    for k in ("id", "content", "inserted_at", "sender_id", "message_type")
                }
            )
        return {"http_status": status, "messages": safe, "ok": status == 200}

    def list_chats(self) -> dict[str, Any]:
        status, body = self._request("GET", "/chats")
        chats = (body or {}).get("data", []) if isinstance(body, dict) else []
        safe = []
        for ch in chats:
            if not isinstance(ch, dict):
                continue
            safe.append(
                {
                    "id": ch.get("id"),
                    "title": ch.get("title"),
                    "type": ch.get("type"),
                    "status": ch.get("status"),
                    "work_status": ch.get("work_status"),
                    "task_counts": ch.get("task_counts"),
                    "task_id": ch.get("task_id"),
                    "agents": [
                        {k: a.get(k) for k in ("id", "name", "handle", "type")}
                        for a in (ch.get("agents") or [])
                        if isinstance(a, dict)
                    ],
                    "inserted_at": ch.get("inserted_at"),
                    "last_message_at": ch.get("last_message_at"),
                }
            )
        return {"http_status": status, "chats": safe, "ok": status == 200}

    def list_tasks(self, room_id: Optional[str] = None, *, state: str = "active") -> dict[str, Any]:
        """List shared tasks on a room board (Human API). Empty list = 'No active tasks'."""
        rid = room_id or self.room_id
        status, body = self._request("GET", f"/chats/{rid}/tasks?state={state}")
        tasks = (body or {}).get("data", []) if isinstance(body, dict) else []
        safe = []
        for t in tasks:
            if not isinstance(t, dict):
                continue
            safe.append(
                {
                    k: t.get(k)
                    for k in (
                        "id",
                        "number",
                        "subject",
                        "detail",
                        "overall_status",
                        "state",
                        "chat_room_id",
                        "created_by",
                        "assignments",
                        "inserted_at",
                        "updated_at",
                    )
                }
            )
        return {
            "http_status": status,
            "room_id": rid,
            "tasks": safe,
            "active_count": len(safe),
            "ok": status == 200,
            "observed_outcome": "EMPTY_BOARD" if status == 200 and not safe else ("PASS" if status == 200 else "FAIL"),
        }

    def create_task(
        self,
        subject: str,
        *,
        detail: Optional[str] = None,
        room_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """File a shared task on the room board (subject/detail schema)."""
        rid = room_id or self.room_id
        payload: dict[str, Any] = {"subject": subject}
        if detail is not None:
            payload["detail"] = detail
        status, body = self._request("POST", f"/chats/{rid}/tasks", payload)
        task = (body or {}).get("data") if isinstance(body, dict) else None
        safe = None
        if isinstance(task, dict):
            safe = {
                k: task.get(k)
                for k in (
                    "id",
                    "number",
                    "subject",
                    "detail",
                    "overall_status",
                    "state",
                    "chat_room_id",
                    "created_by",
                    "assignments",
                )
            }
        return {
            "http_status": status,
            "ok": status in (200, 201),
            "room_id": rid,
            "task": safe,
            "observed_outcome": "PASS" if status in (200, 201) else "FAIL",
        }

    def get_board(self, room_id: Optional[str] = None) -> dict[str, Any]:
        """Room goal/board. Human API may 404 while Agent API supports /board."""
        rid = room_id or self.room_id
        status, body = self._request("GET", f"/chats/{rid}/board")
        data = (body or {}).get("data") if isinstance(body, dict) else None
        return {
            "http_status": status,
            "ok": status == 200,
            "room_id": rid,
            "board": data if isinstance(data, dict) else None,
            "observed_outcome": (
                "PASS"
                if status == 200
                else ("NOT_EXPOSED_ON_HUMAN_API" if status == 404 else "FAIL")
            ),
            "note": "Goal/board GET is documented on Agent API; Human API may return 404",
        }
