"""Flexprice metering adapter.

Credits never override security DENY.
Duplicate usage events have one billable effect.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Optional

from .contracts import EvidenceRef
from .evidence import EvidenceStore, utc_now


@dataclass
class MeterState:
    events: dict[str, dict[str, Any]] = field(default_factory=dict)
    credits: int = 0
    price_per_scan: int = 1
    provider_up: bool = True


class MeteringAdapter:
    def __init__(self, store: EvidenceStore, state: Optional[MeterState] = None):
        self.store = store
        self.state = state or MeterState()
        self.live_flexprice = bool(os.environ.get("FLEXPRICE_API_KEY"))

    def emit_usage(
        self,
        run_id: str,
        event_name: str,
        quantity: int,
        *,
        security_decision: str = "ALLOW",
    ) -> EvidenceRef:
        if security_decision == "DENY":
            return self.store.append_receipt(
                "flexprice_usage",
                {
                    "run_id": run_id,
                    "event_name": event_name,
                    "quantity": quantity,
                    "observed_outcome": "DENIED",
                    "reason": "credits_never_override_security_deny",
                },
                provider="flexprice.local",
            )
        if not self.state.provider_up:
            return self.store.append_receipt(
                "flexprice_usage",
                {
                    "run_id": run_id,
                    "event_name": event_name,
                    "observed_outcome": "PENDING",
                    "reason": "delayed_or_down_provider",
                },
                provider="flexprice.local",
            )
        if run_id in self.state.events:
            existing = self.state.events[run_id]
            return self.store.append_receipt(
                "flexprice_usage",
                {
                    "run_id": run_id,
                    "event_name": event_name,
                    "quantity": existing["quantity"],
                    "observed_outcome": "DEDUPED",
                    "billable_effect": "ONCE",
                },
                provider="flexprice.local",
            )
        self.state.events[run_id] = {
            "event_name": event_name,
            "quantity": quantity,
            "observed_at": utc_now(),
        }
        if event_name == "skill_scan_completed":
            self.state.credits += quantity * self.state.price_per_scan
        return self.store.append_receipt(
            "flexprice_usage",
            {
                "run_id": run_id,
                "event_name": event_name,
                "quantity": quantity,
                "credits_after": self.state.credits,
                "live_flexprice": self.live_flexprice,
                "observed_outcome": "PASS" if self.live_flexprice else "LOCAL_CONTRACT_ONLY",
            },
            provider="flexprice.local",
        )

    def readback(self, run_id: str) -> dict[str, Any]:
        if not self.state.provider_up:
            return {"run_id": run_id, "observed_outcome": "PENDING"}
        event = self.state.events.get(run_id)
        if event is None:
            return {"run_id": run_id, "observed_outcome": "UNKNOWN"}
        return {"run_id": run_id, "observed_outcome": "PASS", **event}

    def can_start_paid_scan(self, available_credits: Optional[int] = None) -> dict[str, Any]:
        credits = self.state.credits if available_credits is None else available_credits
        # Free authorization/integrity verification remains available; paid scan gated.
        if credits < self.state.price_per_scan:
            return {
                "allowed": False,
                "reason": "insufficient_credits",
                "free_integrity_verification": True,
            }
        return {"allowed": True, "credits": credits}

    def availability(self) -> dict[str, Any]:
        return {
            "provider": "flexprice",
            "live_available": self.live_flexprice,
            "observed_outcome": "NOT_TESTED" if not self.live_flexprice else "READY",
            "credits": self.state.credits,
        }
