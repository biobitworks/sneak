"""Thin FlexPrice client wrapper (https://github.com/flexprice/flexprice).

Live ingest only when FLEXPRICE_API_KEY is present. Never logs the key.
"""

from __future__ import annotations

import os
from typing import Any, Optional


class FlexpriceClient:
    def __init__(self, api_key: Optional[str] = None, server_url: Optional[str] = None):
        self.api_key = api_key if api_key is not None else os.environ.get("FLEXPRICE_API_KEY")
        self.server_url = server_url or os.environ.get("FLEXPRICE_SERVER_URL")
        self._sdk = None

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _client(self):
        if self._sdk is None:
            from flexprice import Flexprice

            kwargs: dict[str, Any] = {"api_key_auth": self.api_key}
            if self.server_url:
                kwargs["server_url"] = self.server_url
            self._sdk = Flexprice(**kwargs)
        return self._sdk

    def ingest_event(
        self,
        *,
        event_name: str,
        external_customer_id: str,
        event_id: str,
        properties: Optional[dict[str, str]] = None,
        source: str = "sneak",
        timestamp: Optional[str] = None,
    ) -> dict[str, Any]:
        if not self.available:
            return {"ok": False, "observed_outcome": "NOT_TESTED", "reason": "FLEXPRICE_API_KEY missing"}
        try:
            kwargs: dict[str, Any] = {
                "event_name": event_name,
                "external_customer_id": external_customer_id,
                "event_id": event_id,
                "properties": properties or {},
                "source": source,
            }
            if timestamp:
                kwargs["timestamp"] = timestamp
            resp = self._client().events.ingest_event(**kwargs)
            return {
                "ok": True,
                "observed_outcome": "PASS",
                "event_id": event_id,
                "response_type": type(resp).__name__,
                "response_keys": sorted(resp.keys()) if isinstance(resp, dict) else None,
            }
        except Exception as exc:  # noqa: BLE001 — surface provider failure without secrets
            return {
                "ok": False,
                "observed_outcome": "FAIL",
                "event_id": event_id,
                "error_type": type(exc).__name__,
            }

    def get_event(self, event_id: str, *, external_customer_id: str) -> dict[str, Any]:
        if not self.available:
            return {"ok": False, "observed_outcome": "NOT_TESTED", "reason": "FLEXPRICE_API_KEY missing"}
        try:
            resp = self._client().events.get_event(
                id=event_id, external_customer_id=external_customer_id
            )
            return {
                "ok": True,
                "observed_outcome": "PASS",
                "event_id": event_id,
                "response_type": type(resp).__name__,
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "ok": False,
                "observed_outcome": "FAIL",
                "event_id": event_id,
                "error_type": type(exc).__name__,
            }
