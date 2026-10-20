"""Per-actor audit trail as FCO nodes + FCG edges with deterministic ROI.

Uses the project Merkle construction over ordered ActorEventFCOs as a
*candidate* MMR-shaped append-only trail. Project MMR remains NOT_COMMITTED
unless a separate Overwatch receipt says otherwise.

ROI is derived only from canonical FCO fields (cost_units, benefit_units)
so independent recomputation is deterministic.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any, Optional

from .evidence import EvidenceStore, digest_payload, utc_now
from .merkle import breakpoint_receipt, canonical, leaf, root


# Fixed benefit schedule — outcomes map to rational benefit units.
BENEFIT_UNITS = {
    "PASS": Decimal("1.0"),
    "ALLOW": Decimal("1.0"),
    "PARTIAL": Decimal("0.5"),
    "DEDUPED": Decimal("0.0"),
    "DENIED": Decimal("0.0"),
    "DENY": Decimal("0.0"),
    "FAIL": Decimal("0.0"),
    "PENDING": Decimal("0.0"),
    "NOT_TESTED": Decimal("0.0"),
    "UNKNOWN": Decimal("0.0"),
    "LOCAL_CONTRACT_ONLY": Decimal("0.25"),
    "READY": Decimal("0.25"),
    "ACK_RECEIVED": Decimal("0.5"),
}

# Default micro-cost per usage quantity unit (credits). Override per event.
DEFAULT_UNIT_COST = Decimal("0.01")


def _d(value: Any) -> Decimal:
    return Decimal(str(value))


def deterministic_roi(*, cost_units: Any, benefit_units: Any) -> dict[str, Any]:
    """Banker's-rounded ROI = (benefit - cost) / cost; null when cost is 0."""
    cost = _d(cost_units)
    benefit = _d(benefit_units)
    if cost == 0:
        return {
            "cost_units": str(cost),
            "benefit_units": str(benefit),
            "roi": None,
            "roi_basis": "(benefit_units - cost_units) / cost_units",
            "rounding": "ROUND_HALF_EVEN_to_6dp",
            "observed_outcome": "UNDEFINED_ZERO_COST",
        }
    raw = (benefit - cost) / cost
    rounded = raw.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
    return {
        "cost_units": str(cost),
        "benefit_units": str(benefit),
        "roi": str(rounded),
        "roi_basis": "(benefit_units - cost_units) / cost_units",
        "rounding": "ROUND_HALF_EVEN_to_6dp",
        "observed_outcome": "COMPUTED",
    }


def fco_identity(payload: dict[str, Any]) -> str:
    """SHA-256 of canonical payload excluding the identity field itself."""
    body = {k: v for k, v in payload.items() if k != "fco_candidate_sha256"}
    return hashlib.sha256(canonical(body)).hexdigest()


@dataclass
class ActorAuditTrail:
    """Append-only actor audit: each action is an FCO; edges form an FCG."""

    store: EvidenceStore
    actors: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    edges: list[dict[str, Any]] = field(default_factory=list)
    fcos: list[dict[str, Any]] = field(default_factory=list)

    def record_action(
        self,
        *,
        actor_id: str,
        actor_role: str,
        action: str,
        quantity: int = 1,
        unit_cost: Any = DEFAULT_UNIT_COST,
        outcome: str = "LOCAL_CONTRACT_ONLY",
        properties: Optional[dict[str, Any]] = None,
        parent_fco_id: Optional[str] = None,
        meter_event_name: str = "actor_action",
    ) -> dict[str, Any]:
        cost = _d(unit_cost) * _d(quantity)
        benefit = BENEFIT_UNITS.get(outcome, Decimal("0.0"))
        roi = deterministic_roi(cost_units=cost, benefit_units=benefit)
        event_id = f"ACTOR-{actor_id}-{len(self.actors.get(actor_id, [])):04d}"
        fco_body = {
            "id": event_id,
            "kind": "ActorEventFCO",
            "actor_id": actor_id,
            "actor_role": actor_role,
            "action": action,
            "meter_event_name": meter_event_name,
            "quantity": int(quantity),
            "unit_cost": str(_d(unit_cost)),
            "outcome": outcome,
            "cost_units": roi["cost_units"],
            "benefit_units": roi["benefit_units"],
            "roi": roi,
            "properties": properties or {},
            "observed_at": utc_now(),
            "verified": False,
        }
        fco_body["fco_candidate_sha256"] = fco_identity(fco_body)
        self.fcos.append(fco_body)
        self.actors.setdefault(actor_id, []).append(fco_body)

        if parent_fco_id:
            self.edges.append(
                {
                    "id": f"EDGE-{event_id}-PRECEDED",
                    "kind": "FCGEdge",
                    "type": "PRECEDED_BY",
                    "from": event_id,
                    "to": parent_fco_id,
                }
            )
        self.edges.append(
            {
                "id": f"EDGE-{event_id}-ACTOR",
                "kind": "FCGEdge",
                "type": "EMITTED_BY",
                "from": event_id,
                "to": f"ACTOR-NODE-{actor_id}",
            }
        )
        self.edges.append(
            {
                "id": f"EDGE-{event_id}-ROI",
                "kind": "FCGEdge",
                "type": "ROI_DERIVED_FROM",
                "from": f"{event_id}-ROI",
                "to": event_id,
                "roi": roi["roi"],
            }
        )

        receipt = self.store.append_receipt(
            "actor_event_fco",
            fco_body,
            parent_id=parent_fco_id,
            provider="sneak.actor-audit",
        )
        return {**fco_body, "receipt_id": receipt.external_id, "receipt_digest": receipt.artifact_digest}

    def actor_roi_summary(self, actor_id: str) -> dict[str, Any]:
        rows = self.actors.get(actor_id, [])
        cost = sum((_d(r["cost_units"]) for r in rows), Decimal("0"))
        benefit = sum((_d(r["benefit_units"]) for r in rows), Decimal("0"))
        roi = deterministic_roi(cost_units=cost, benefit_units=benefit)
        return {
            "actor_id": actor_id,
            "event_count": len(rows),
            "fco_ids": [r["id"] for r in rows],
            "aggregate_roi": roi,
            "events": [
                {
                    "id": r["id"],
                    "action": r["action"],
                    "outcome": r["outcome"],
                    "roi": r["roi"]["roi"],
                    "fco_candidate_sha256": r["fco_candidate_sha256"],
                }
                for r in rows
            ],
        }

    def build_fcg(self) -> dict[str, Any]:
        actor_nodes = [
            {
                "id": f"ACTOR-NODE-{actor_id}",
                "kind": "ActorFCO",
                "actor_id": actor_id,
                "identity": digest_payload({"actor_id": actor_id, "events": [e["id"] for e in rows]}),
                "verified": False,
            }
            for actor_id, rows in sorted(self.actors.items())
        ]
        return {
            "schema": "sneak.actor-audit-fcg.v1",
            "scope": "CANDIDATE_NOT_CANONICAL",
            "nodes": [
                {
                    "id": f["id"],
                    "identity": f["fco_candidate_sha256"],
                    "kind": f["kind"],
                    "verified": False,
                }
                for f in self.fcos
            ]
            + actor_nodes,
            "edges": list(self.edges),
            "mmr": "NOT_COMMITTED",
            "signed": False,
        }

    def candidate_mmr_receipt(
        self,
        *,
        breakpoint_id: str,
        parent_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Merkle over ActorEventFCOs + ROI summaries (candidate MMR; not committed)."""
        records: list[dict[str, Any]] = []
        for fco in self.fcos:
            records.append(
                {
                    "id": fco["id"],
                    "kind": "ActorEventFCO",
                    "payload": {
                        "fco_candidate_sha256": fco["fco_candidate_sha256"],
                        "actor_id": fco["actor_id"],
                        "action": fco["action"],
                        "outcome": fco["outcome"],
                        "roi": fco["roi"],
                    },
                }
            )
        for actor_id in sorted(self.actors):
            summary = self.actor_roi_summary(actor_id)
            records.append(
                {
                    "id": f"ROI-{actor_id}",
                    "kind": "ActorROIAggregate",
                    "payload": summary,
                }
            )
        fcg = self.build_fcg()
        records.append(
            {
                "id": "FCG-SNAPSHOT",
                "kind": "ActorAuditFCG",
                "payload": {
                    "node_count": len(fcg["nodes"]),
                    "edge_count": len(fcg["edges"]),
                    "fcg_digest": digest_payload(fcg),
                },
            }
        )
        receipt = breakpoint_receipt(
            schema="sneak.actor-audit-mmr-candidate.v1",
            breakpoint_id=breakpoint_id,
            parent_id=parent_id,
            records=records,
            meaning=(
                "Candidate MMR-shaped Merkle over actor FCOs/FCG with deterministic ROI; "
                "not an Overwatch MMR commitment"
            ),
        )
        # Explicit peaks list (MMR-shaped bagging of leaves in append order).
        leaf_hexes = [leaf(r).hex() for r in sorted(records, key=lambda x: str(x.get("id", "")))]
        receipt["mmr_peaks_candidate"] = leaf_hexes  # leaves as peaks until bagged externally
        receipt["mmr"] = "NOT_COMMITTED"
        receipt["root_recompute"] = root(
            [bytes.fromhex(h) for h in leaf_hexes]
        ).hex() if leaf_hexes else None
        receipt["fcg_digest"] = digest_payload(fcg)
        receipt["actor_summaries"] = {
            actor_id: self.actor_roi_summary(actor_id) for actor_id in sorted(self.actors)
        }
        return receipt
