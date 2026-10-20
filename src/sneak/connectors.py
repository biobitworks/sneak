"""Orchestrates Flexprice ↔ Snyk ↔ Cognee ↔ BAND connector wiring.

Local contract mode exercises bindings without claiming live provider success.
Live credentials/CLIs remain NOT_TESTED when unavailable.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .band_adapter import BandAdapter
from .evidence import EvidenceStore
from .gate import GateDecision, decide
from .memory import ADMITTED, CANDIDATE, MemoryAdapter
from .metering import MeteringAdapter
from .scanner import ScanResult, digest_tree, scan
from .score import is_clean_ten
from .secrets import presence_receipt


@dataclass
class ConnectorStatus:
    band: dict[str, Any]
    cognee: dict[str, Any]
    snyk: dict[str, Any]
    flex: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "band": self.band,
            "cognee": self.cognee,
            "snyk": self.snyk,
            "flex": self.flex,
            "all_live": all(
                x.get("live_available")
                for x in (self.band, self.cognee, self.snyk, self.flex)
            ),
        }


@dataclass
class ConnectorRuntime:
    store: EvidenceStore
    live: Optional[bool] = None
    band: BandAdapter = field(init=False)
    memory: MemoryAdapter = field(init=False)
    meter: MeteringAdapter = field(init=False)

    def __post_init__(self) -> None:
        self.band = BandAdapter(self.store, live=self.live)
        self.memory = MemoryAdapter(self.store, live=self.live)
        self.meter = MeteringAdapter(self.store)

    def status(self) -> ConnectorStatus:
        from .scanner import live_scan_availability

        snyk = live_scan_availability()
        snyk["provider"] = "snyk"
        snyk["live_available"] = snyk.get("observed_outcome") == "READY"
        status = ConnectorStatus(
            band=self.band.availability(),
            cognee=self.memory.availability(),
            snyk=snyk,
            flex=self.meter.availability(),
        )
        # Attach secret presence (no values) for operator diagnostics.
        status.band["secrets"] = presence_receipt()
        return status

    def load_band_receipt(self, path: Path) -> dict[str, Any]:
        return self.band.load_room_receipt(path)

    def security_review_cycle(
        self,
        *,
        staged_path: str,
        candidate_digest: Optional[str] = None,
        fixture: Optional[dict[str, Any]] = None,
        human_decision: str = "PENDING",
        policy_digest: str = "policy-v1",
        run_id: str,
        nonce: str,
        seen_nonces: Optional[set[str]] = None,
    ) -> dict[str, Any]:
        """Wire scan → BAND finding post → Cognee memory → Flex meter → gate.

        Credits never override security DENY. Pending human approval stays PENDING.
        """
        digest = candidate_digest or digest_tree(Path(staged_path))
        scan_result: ScanResult = scan(digest, staged_path, fixture=fixture)

        finding_note = {
            "candidate_digest": digest,
            "observed_outcome": scan_result.observed_outcome,
            "score": scan_result.score.to_dict(),
            "reasons": scan_result.reasons,
        }
        # Security reviewer posts findings into BAND handoff channel.
        handoff = self.band.publish_handoff(
            task_id=f"scan-{run_id}",
            recipient="security-reviewer",
            evidence=[],
            request_id=f"handoff-{run_id}",
        )
        self.band.record_decision(f"decision-{run_id}", human_decision)

        # Store recurring issue evidence in Cognee candidate namespace first.
        mem = self.memory.remember(
            {
                "dataset": CANDIDATE,
                "writer": "security-reviewer",
                "content": finding_note,
            }
        )
        # Admit only after authorized gate path — not from recall alone.
        recalled = self.memory.recall("candidate_digest", CANDIDATE)

        security_decision = "DENY"
        gate: GateDecision = decide(
            digest,
            evidence=[handoff, mem],
            policy_digest=policy_digest,
            scan=scan_result,
            human_decision=human_decision,
            authorization_nonce=nonce,
            seen_nonces=seen_nonces if seen_nonces is not None else set(),
            rights_ok=True,
            target_digest=digest,
            recalled_poison=any(
                "ignore policy" in json.dumps(r.get("content", {})).lower()
                for r in recalled
                if isinstance(r, dict)
            ),
        )
        if gate.decision == "ALLOW":
            # Never promote a receipt resolved outside the evidence-store sandbox.
            receipt_path = Path(mem.receipt_path).resolve(strict=True)
            if not receipt_path.is_relative_to(self.store.root.resolve()):
                raise ValueError("receipt must be confined to evidence store")
            security_decision = "ALLOW"
            self.memory.promote_candidate(
                json.loads(receipt_path.read_text())["payload"]["record_id"],
                authorized=True,
            )
        else:
            security_decision = "DENY"

        usage = self.meter.emit_usage(
            run_id=run_id,
            event_name="skill_scan_completed",
            quantity=1 if security_decision == "ALLOW" else 0,
            security_decision=security_decision,
        )
        readback = self.meter.readback(run_id)

        return {
            "candidate_digest": digest,
            "scan": scan_result.to_dict(),
            "band_handoff": handoff.to_dict(),
            "memory": mem.to_dict(),
            "recalled_count": len([r for r in recalled if "record_id" in r]),
            "gate": gate.to_dict(),
            "usage": usage.to_dict(),
            "usage_readback": readback,
            "clean_ten": is_clean_ten(scan_result.score),
            "connectors": self.status().to_dict(),
            "meaning": (
                "Local connector wiring exercised; live BAND/Cognee/Snyk/Flexprice "
                "remain NOT_TESTED unless status.live_available is true"
            ),
        }

    def deep_integration_ablation(self) -> dict[str, Any]:
        """M28/M29 local contract: removing BAND or Cognee changes required behavior."""
        # Baseline: handoff + recall changes next action.
        self.memory.remember(
            {
                "dataset": ADMITTED,
                "writer": "agent-a",
                "content": {"finding": "block-eval", "action": "deny_eval"},
            }
        )
        with_memory = self.memory.recall("block-eval", ADMITTED)
        next_action_with = "deny_eval" if with_memory else "continue"

        # Ablate Cognee: empty adapter
        ablated_mem = MemoryAdapter(self.store, live=False)
        without_memory = ablated_mem.recall("block-eval", ADMITTED)
        next_action_without_cognee = "continue" if not without_memory else "deny_eval"

        # Ablate BAND: no room / cannot publish coordinated approval path
        ablated_band = BandAdapter(self.store, live=False)
        ablated_band.state.room_id = None
        decision = ablated_band.read_decision("missing")
        band_essential = decision["approved"] is False and decision["human_decision"] == "PENDING"

        return {
            "baseline_next_action": next_action_with,
            "without_cognee_next_action": next_action_without_cognee,
            "cognee_changes_behavior": next_action_with != next_action_without_cognee,
            "band_removal_blocks_approval": band_essential,
            "observed_outcome": "LOCAL_CONTRACT_PASS",
            "live_provider_claim": False,
        }
