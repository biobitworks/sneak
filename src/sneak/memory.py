"""Cognee working-memory adapter with permission boundaries.

Live mode uses Cognee Cloud as data storage (add_text → cognify → search).
Candidate memory cannot enter the admitted namespace without authorization.
Recalled instructions remain data and cannot replace policy.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional

from .cognee_client import CogneeClient
from .contracts import EvidenceRef
from .evidence import EvidenceStore, utc_now

ADMITTED = "admitted"
CANDIDATE = "candidate"


@dataclass
class MemoryRecord:
    dataset: str
    content: dict[str, Any]
    writer: str
    record_id: str


@dataclass
class MemoryState:
    records: list[MemoryRecord] = field(default_factory=list)
    provider_up: bool = True
    next_id: int = 1


class MemoryAdapter:
    def __init__(
        self,
        store: EvidenceStore,
        state: Optional[MemoryState] = None,
        *,
        live: Optional[bool] = None,
        cognee: Optional[CogneeClient] = None,
    ):
        self.store = store
        self.state = state or MemoryState()
        self.cognee = cognee or CogneeClient()
        self.live_cognee = self.cognee.available if live is None else live and self.cognee.available

    def remember(self, record: dict[str, Any]) -> EvidenceRef:
        dataset = record.get("dataset", CANDIDATE)
        if dataset not in (ADMITTED, CANDIDATE):
            raise ValueError("unknown_dataset")
        if not self.state.provider_up and self.live_cognee:
            return self.store.append_receipt(
                "cognee_remember",
                {"observed_outcome": "PENDING", "reason": "provider_outage"},
                provider="cognee",
            )

        rid = f"mem-{self.state.next_id}"
        self.state.next_id += 1
        content = dict(record.get("content", record))
        stored = MemoryRecord(
            dataset=dataset,
            content=content,
            writer=str(record.get("writer", "unknown")),
            record_id=rid,
        )
        self.state.records.append(stored)

        live_result = None
        if self.live_cognee:
            # Map logical namespaces onto Cognee datasets; candidate stays separate.
            cognee_dataset = (
                "sneak_working_memory"
                if dataset == ADMITTED
                else "sneak_candidate_memory"
            )
            text = json.dumps(
                {
                    "record_id": rid,
                    "dataset": dataset,
                    "writer": stored.writer,
                    "content": content,
                },
                sort_keys=True,
            )
            live_result = self.cognee.remember_and_wait(
                text,
                dataset=cognee_dataset,
                wait_seconds=float(record.get("wait_seconds", 45)),
                query=str(content.get("finding") or content.get("text") or rid),
            )

        return self.store.append_receipt(
            "cognee_remember",
            {
                "record_id": rid,
                "dataset": dataset,
                "writer": stored.writer,
                "live_cognee": self.live_cognee,
                "live": (
                    {
                        "dataset": live_result.get("dataset"),
                        "observed_outcome": live_result.get("observed_outcome"),
                        "hit_count": live_result.get("search", {}).get("hit_count"),
                        "add_ok": live_result.get("add", {}).get("ok"),
                        "cognify_ok": live_result.get("cognify", {}).get("ok"),
                    }
                    if live_result
                    else None
                ),
                "observed_outcome": (
                    live_result.get("observed_outcome")
                    if live_result
                    else ("LOCAL_CONTRACT_ONLY")
                ),
                "observed_at": utc_now(),
            },
            provider="cognee",
        )

    def recall(self, query: str, allowed_dataset: str) -> list[dict[str, Any]]:
        if allowed_dataset not in (ADMITTED, CANDIDATE):
            raise ValueError("unknown_dataset")
        if not self.state.provider_up:
            return [{"observed_outcome": "PENDING", "reason": "provider_outage", "query": query}]

        out: list[dict[str, Any]] = []
        if self.live_cognee:
            cognee_dataset = (
                "sneak_working_memory"
                if allowed_dataset == ADMITTED
                else "sneak_candidate_memory"
            )
            result = self.cognee.search(query, dataset=cognee_dataset, search_type="CHUNKS")
            for hit in result.get("hits") or []:
                out.append(
                    {
                        "record_id": hit.get("id"),
                        "dataset": allowed_dataset,
                        "content": {"text": hit.get("text")},
                        "writer": "cognee",
                        "authority": "DATA_ONLY",
                        "provider": "cognee",
                    }
                )

        # Always include local namespace filter results for contract tests.
        q = query.lower()
        for rec in self.state.records:
            if rec.dataset != allowed_dataset:
                continue
            blob = json_safe(rec.content).lower()
            if q in blob or not q:
                out.append(
                    {
                        "record_id": rec.record_id,
                        "dataset": rec.dataset,
                        "content": rec.content,
                        "writer": rec.writer,
                        "authority": "DATA_ONLY",
                        "provider": "local",
                    }
                )
        return out

    def promote_candidate(self, record_id: str, *, authorized: bool) -> dict[str, Any]:
        if not authorized:
            return {"observed_outcome": "DENIED", "reason": "unauthorized_promotion"}
        for rec in self.state.records:
            if rec.record_id == record_id:
                rec.dataset = ADMITTED
                return {"observed_outcome": "PASS", "record_id": record_id, "dataset": ADMITTED}
        return {"observed_outcome": "UNKNOWN", "reason": "missing_record"}

    def availability(self) -> dict[str, Any]:
        health = self.cognee.health() if self.cognee.available else {"live": False}
        return {
            "provider": "cognee",
            "live_available": bool(self.live_cognee and health.get("live")),
            "base_url_configured": bool(self.cognee.base_url),
            "dataset": self.cognee.dataset,
            "observed_outcome": "READY" if (self.live_cognee and health.get("live")) else "NOT_TESTED",
            "datasets": [ADMITTED, CANDIDATE],
        }


def json_safe(obj: Any) -> str:
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        return " ".join(f"{k} {json_safe(v)}" for k, v in obj.items())
    if isinstance(obj, list):
        return " ".join(json_safe(x) for x in obj)
    return str(obj)
