"""Flexprice metering adapter with per-actor audit ROI.

Credits never override security DENY.
Duplicate usage events have one billable effect.
Each successful emit can bind an ActorEventFCO into the audit trail.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Optional

from .actor_audit import DEFAULT_UNIT_COST, ActorAuditTrail
from .contracts import EvidenceRef
from .evidence import EvidenceStore, utc_now
from .flexprice_client import FlexpriceClient


@dataclass
class MeterState:
    events: dict[str, dict[str, Any]] = field(default_factory=dict)
    credits: int = 0
    price_per_scan: int = 1
    provider_up: bool = True


class MeteringAdapter:
    def __init__(
        self,
        store: EvidenceStore,
        state: Optional[MeterState] = None,
        *,
        audit: Optional[ActorAuditTrail] = None,
        client: Optional[FlexpriceClient] = None,
    ):
        self.store = store
        self.state = state or MeterState()
        self.client = client or FlexpriceClient()
        self.live_flexprice = self.client.available
        self.audit = audit or ActorAuditTrail(store)

    def emit_usage(
        self,
        run_id: str,
        event_name: str,
        quantity: int,
        *,
        security_decision: str = "ALLOW",
        actor_id: Optional[str] = None,
        actor_role: str = "system",
        unit_cost: Any = DEFAULT_UNIT_COST,
        live_ingest: bool = True,
    ) -> EvidenceRef:
        if security_decision == "DENY":
            if actor_id:
                self.audit.record_action(
                    actor_id=actor_id,
                    actor_role=actor_role,
                    action=event_name,
                    quantity=quantity,
                    unit_cost=unit_cost,
                    outcome="DENIED",
                    meter_event_name=event_name,
                    properties={"run_id": run_id, "reason": "credits_never_override_security_deny"},
                )
            return self.store.append_receipt(
                "flexprice_usage",
                {
                    "run_id": run_id,
                    "event_name": event_name,
                    "quantity": quantity,
                    "actor_id": actor_id,
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
                    "actor_id": actor_id,
                    "observed_outcome": "PENDING",
                    "reason": "delayed_or_down_provider",
                },
                provider="flexprice.local",
            )
        if run_id in self.state.events:
            existing = self.state.events[run_id]
            if actor_id:
                self.audit.record_action(
                    actor_id=actor_id,
                    actor_role=actor_role,
                    action=event_name,
                    quantity=0,
                    unit_cost=unit_cost,
                    outcome="DEDUPED",
                    meter_event_name=event_name,
                    properties={"run_id": run_id, "billable_effect": "ONCE"},
                )
            return self.store.append_receipt(
                "flexprice_usage",
                {
                    "run_id": run_id,
                    "event_name": event_name,
                    "quantity": existing["quantity"],
                    "actor_id": actor_id,
                    "observed_outcome": "DEDUPED",
                    "billable_effect": "ONCE",
                },
                provider="flexprice.local",
            )
        self.state.events[run_id] = {
            "event_name": event_name,
            "quantity": quantity,
            "observed_at": utc_now(),
            "actor_id": actor_id,
        }
        if event_name == "skill_scan_completed":
            self.state.credits += quantity * self.state.price_per_scan

        live = {"observed_outcome": "NOT_TESTED", "ok": False}
        if live_ingest and self.live_flexprice and actor_id:
            live = self.client.ingest_event(
                event_name=event_name,
                external_customer_id=actor_id,
                event_id=run_id,
                properties={
                    "quantity": str(quantity),
                    "actor_role": actor_role,
                    "unit_cost": str(unit_cost),
                },
                source="sneak.actor-audit",
            )

        outcome = (
            live.get("observed_outcome")
            if live_ingest and self.live_flexprice
            else "LOCAL_CONTRACT_ONLY"
        )
        audit_row = None
        if actor_id:
            audit_row = self.audit.record_action(
                actor_id=actor_id,
                actor_role=actor_role,
                action=event_name,
                quantity=quantity,
                unit_cost=unit_cost,
                outcome=str(outcome),
                meter_event_name=event_name,
                properties={"run_id": run_id, "live_flexprice": self.live_flexprice},
            )

        return self.store.append_receipt(
            "flexprice_usage",
            {
                "run_id": run_id,
                "event_name": event_name,
                "quantity": quantity,
                "actor_id": actor_id,
                "credits_after": self.state.credits,
                "live_flexprice": self.live_flexprice,
                "live_ingest": live,
                "actor_fco_id": audit_row["id"] if audit_row else None,
                "actor_roi": audit_row["roi"] if audit_row else None,
                "observed_outcome": outcome if self.live_flexprice else "LOCAL_CONTRACT_ONLY",
            },
            provider="flexprice" if self.live_flexprice else "flexprice.local",
        )

    def readback(self, run_id: str) -> dict[str, Any]:
        if not self.state.provider_up:
            return {"run_id": run_id, "observed_outcome": "PENDING"}
        event = self.state.events.get(run_id)
        if event is None:
            return {"run_id": run_id, "observed_outcome": "UNKNOWN"}
        live = None
        if self.live_flexprice and event.get("actor_id"):
            live = self.client.get_event(run_id, external_customer_id=str(event["actor_id"]))
        return {"run_id": run_id, "observed_outcome": "PASS", "live_readback": live, **event}

    def can_start_paid_scan(self, available_credits: Optional[int] = None) -> dict[str, Any]:
        credits = self.state.credits if available_credits is None else available_credits
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
            "upstream": "https://github.com/flexprice/flexprice",
            "live_available": self.live_flexprice,
            "observed_outcome": "NOT_TESTED" if not self.live_flexprice else "READY",
            "credits": self.state.credits,
        }

    def actor_audit_receipt(self, breakpoint_id: str, parent_id: Optional[str] = None) -> dict[str, Any]:
        return self.audit.candidate_mmr_receipt(breakpoint_id=breakpoint_id, parent_id=parent_id)
