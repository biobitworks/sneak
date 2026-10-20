"""Deterministic Band Planner runtime (no LLM): presence + plan-track replies.

Credentials load from ~/.secrets/sneak/band_planner_agent_config.yaml
(or BAND_PLANNER_AGENT_ID / BAND_PLANNER_API_KEY). Never print or commit keys.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import yaml

from .secrets import DEFAULT_SECRET_FILE, export_to_environ

DEFAULT_PLANNER_CONFIG = Path.home() / ".secrets" / "sneak" / "band_planner_agent_config.yaml"
PLANNER_HANDLE = "biobitworks/planner"
PLANNER_NAME = "Planner"


def load_planner_credentials(
    config_path: Path | None = None,
) -> tuple[str, str]:
    """Return (agent_id, api_key). Prefer env, then YAML. Never log values."""
    export_to_environ()
    agent_id = os.environ.get("BAND_PLANNER_AGENT_ID", "").strip()
    api_key = os.environ.get("BAND_PLANNER_API_KEY", "").strip()
    if agent_id and api_key:
        return agent_id, api_key

    path = Path(config_path or os.environ.get("BAND_PLANNER_CONFIG", DEFAULT_PLANNER_CONFIG))
    if not path.is_file():
        raise FileNotFoundError(f"planner_config_missing:{path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    block = data.get("planner") or next(iter(data.values()), {})
    agent_id = str(block.get("agent_id") or "").strip()
    api_key = str(block.get("api_key") or "").strip()
    if not agent_id or not api_key:
        raise ValueError("planner_credentials_incomplete")
    return agent_id, api_key


def planner_presence_receipt(*, online: bool, connection_status: Optional[str]) -> dict[str, Any]:
    return {
        "handle": PLANNER_HANDLE,
        "name": PLANNER_NAME,
        "online": bool(online),
        "connection_status": connection_status,
        "secrets_file_configured": DEFAULT_SECRET_FILE.is_file(),
        "config_file_configured": DEFAULT_PLANNER_CONFIG.is_file(),
        "value_inspected": False,
    }


PLAN_TRACK_REPLY = (
    "SNEAK plan track (Planner @biobitworks/planner):\n"
    "- Overall Done = FALSE until human gates + assignee evidence.\n"
    "- CHECKOFF #2 Planner: completed (board keep-current).\n"
    "- #3 Tom / #4 Jerry: need ACK (chat ACK OK if BOARD_TOOL_MISSING).\n"
    "- #6 Chirag / #7 Byron: human-pending — I will not mark Done.\n"
    "- SNEAK-024 custody BPs + model MMR deltas recorded; mmr NOT_COMMITTED.\n"
    "Tom/Jerry: reply ACK with handle. Chirag/Byron: confirm roster/approve."
)


def build_planner_adapter():
    """Lazy-import Band SDK SimpleAdapter so unit tests need no band-sdk."""
    from band.core.simple_adapter import SimpleAdapter
    from band.core.types import Capability, Emit

    class RawHistoryConverter:
        def convert(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
            return list(raw or [])

    class DeterministicPlannerAdapter(SimpleAdapter[list[dict[str, Any]]]):
        """Reply with frozen plan-track status; never auto-complete human gates."""

        SUPPORTED_EMIT = frozenset({Emit.TOOL_CALLS, Emit.TASK_EVENTS})
        SUPPORTED_CAPABILITIES = frozenset({Capability.TASKS})

        def __init__(self) -> None:
            super().__init__(
                history_converter=RawHistoryConverter(),
                emit=Emit.TOOL_CALLS,
                capabilities=Capability.TASKS,
            )
            self.replies_sent = 0
            self.last_error: str | None = None
            self.turns_seen = 0
            self.turn_log: list[dict[str, Any]] = []

        async def on_message(
            self,
            msg,
            tools,
            history,
            participants_msg,
            contacts_msg,
            *,
            is_session_bootstrap: bool,
            room_id: str,
        ) -> None:
            self.turns_seen += 1
            content = (getattr(msg, "content", None) or "").strip()
            sender = getattr(msg, "sender_type", None) or ""
            sender_id = getattr(msg, "sender_id", None)
            entry = {
                "turn": self.turns_seen,
                "room_id": room_id,
                "bootstrap": bool(is_session_bootstrap),
                "sender_type": sender,
                "sender_id": sender_id,
                "content_len": len(content),
                "content_prefix": content[:80],
            }
            try:
                # Agent API requires at least one mention on send_message.
                mention_handles = ["biobitworks", "biobitworks/tom", "biobitworks/jerry"]

                async def _post_track() -> None:
                    await tools.send_message(PLAN_TRACK_REPLY, mentions=mention_handles)
                    self.replies_sent += 1

                # Always answer human mentions with the plan track.
                if sender == "User" or "plan-track" in content.lower() or "CHECKOFF" in content:
                    await _post_track()
                    entry["action"] = "send_plan_track"
                    self.turn_log.append(entry)
                    return
                if is_session_bootstrap or not content:
                    await tools.no_reply(reason="bootstrap_or_empty")
                    entry["action"] = "no_reply_bootstrap"
                    self.turn_log.append(entry)
                    return
                if content.startswith("{"):
                    await tools.no_reply(reason="ignore_tool_noise")
                    entry["action"] = "no_reply_noise"
                    self.turn_log.append(entry)
                    return
                await _post_track()
                entry["action"] = "send_plan_track_default"
                self.turn_log.append(entry)
            except Exception as exc:  # noqa: BLE001 — never crash the socket
                self.last_error = f"{type(exc).__name__}:{exc}"[:200]
                entry["action"] = "error"
                entry["error"] = self.last_error
                self.turn_log.append(entry)
                try:
                    await tools.no_reply(reason=f"handler_error:{type(exc).__name__}")
                except Exception:
                    pass

    return DeterministicPlannerAdapter()
