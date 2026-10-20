"""Cognee-backed @Data store.

BAND communicates; Cognee is the durable data backend addressed as @Data.
Candidate vs admitted namespaces remain separate; recalled content is DATA_ONLY.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from .cognee_client import CogneeClient
from .contracts import EvidenceRef
from .evidence import EvidenceStore, utc_now

DATA_DATASET = "Data"  # Cognee dataset backing @Data


class DataBackend:
    """@Data facade over Cognee Cloud."""

    def __init__(
        self,
        store: EvidenceStore,
        *,
        client: Optional[CogneeClient] = None,
        live: Optional[bool] = None,
    ):
        self.store = store
        self.client = client or CogneeClient(dataset=DATA_DATASET)
        self.live = self.client.available if live is None else live and self.client.available

    def availability(self) -> dict[str, Any]:
        health = self.client.health() if self.client.available else {"live": False}
        return {
            "provider": "cognee",
            "alias": "@Data",
            "dataset": DATA_DATASET,
            "live_available": bool(self.live and health.get("live")),
            "observed_outcome": "READY" if (self.live and health.get("live")) else "NOT_TESTED",
        }

    def write_breakpoint(
        self,
        *,
        breakpoint_id: str,
        merkle_root: str,
        payload: dict[str, Any],
        wait_seconds: float = 45.0,
    ) -> EvidenceRef:
        text = json.dumps(
            {
                "alias": "@Data",
                "breakpoint_id": breakpoint_id,
                "merkle_root": merkle_root,
                "payload": payload,
                "observed_at": utc_now(),
            },
            sort_keys=True,
        )
        live = None
        if self.live:
            if wait_seconds and wait_seconds > 0:
                live = self.client.remember_and_wait(
                    text,
                    dataset=DATA_DATASET,
                    wait_seconds=wait_seconds,
                    query=f"{breakpoint_id} {merkle_root[:16]}",
                )
            else:
                added = self.client.add_text([text], dataset=DATA_DATASET)
                cognified = self.client.cognify(dataset=DATA_DATASET)
                live = {
                    "dataset": DATA_DATASET,
                    "add": {"ok": added.get("ok"), "http_status": added.get("http_status")},
                    "cognify": {
                        "ok": cognified.get("ok"),
                        "http_status": cognified.get("http_status"),
                    },
                    "search": {"hit_count": 0, "hits": [], "ok": False},
                    "observed_outcome": "PASS" if added.get("ok") else "FAIL",
                }
        return self.store.append_receipt(
            "data_breakpoint",
            {
                "alias": "@Data",
                "dataset": DATA_DATASET,
                "breakpoint_id": breakpoint_id,
                "merkle_root": merkle_root,
                "live": (
                    {
                        "observed_outcome": live.get("observed_outcome"),
                        "hit_count": live.get("search", {}).get("hit_count"),
                        "add_ok": live.get("add", {}).get("ok"),
                        "cognify_ok": live.get("cognify", {}).get("ok"),
                    }
                    if live
                    else None
                ),
                "observed_outcome": (
                    live.get("observed_outcome") if live else "LOCAL_CONTRACT_ONLY"
                ),
            },
            provider="cognee.@Data",
        )

    def recall(self, query: str) -> list[dict[str, Any]]:
        if not self.live:
            return []
        result = self.client.search(query, dataset=DATA_DATASET, search_type="CHUNKS")
        out = []
        for hit in result.get("hits") or []:
            out.append(
                {
                    "record_id": hit.get("id"),
                    "text": hit.get("text"),
                    "authority": "DATA_ONLY",
                    "alias": "@Data",
                    "provider": "cognee",
                }
            )
        return out
