"""Deterministic admission gateway. Models and memory cannot grant authority."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .contracts import EvidenceRef
from .scanner import ScanResult


@dataclass
class GateDecision:
    decision: str  # ALLOW | DENY | PENDING
    reasons: list[str] = field(default_factory=list)
    candidate_digest: str = ""
    policy_digest: str = ""
    capability: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "reasons": self.reasons,
            "candidate_digest": self.candidate_digest,
            "policy_digest": self.policy_digest,
            "capability": self.capability,
        }


def decide(
    candidate_digest: str,
    evidence: list[EvidenceRef],
    policy_digest: str,
    *,
    scan: Optional[ScanResult] = None,
    human_decision: Optional[str] = None,
    authorization_nonce: Optional[str] = None,
    seen_nonces: Optional[set[str]] = None,
    rights_ok: bool = True,
    target_digest: Optional[str] = None,
    recalled_poison: bool = False,
) -> GateDecision:
    reasons: list[str] = []

    if not rights_ok:
        reasons.append("missing_rights")
    if not policy_digest:
        reasons.append("missing_policy")
    if human_decision is None:
        reasons.append("missing_approval")
    elif human_decision == "PENDING":
        return GateDecision(
            decision="PENDING",
            reasons=["human_decision_pending"],
            candidate_digest=candidate_digest,
            policy_digest=policy_digest,
        )
    elif human_decision not in ("APPROVE", "APPROVED"):
        reasons.append(f"human_decision_{human_decision}")

    if recalled_poison:
        reasons.append("recalled_poison_cannot_grant")

    if authorization_nonce and seen_nonces is not None and authorization_nonce in seen_nonces:
        reasons.append("authorization_replay")

    if target_digest is not None and target_digest != candidate_digest:
        reasons.append("target_substitution")

    if scan is None:
        reasons.append("missing_scan")
    else:
        if scan.candidate_digest != candidate_digest:
            reasons.append("stale_candidate_digest")
        if not scan.score.coverage_accepted:
            reasons.append("incomplete_scan_coverage")
        if scan.observed_outcome in ("DENIED", "NOT_TESTED", "BLOCKED"):
            reasons.append(f"scan_{scan.observed_outcome.lower()}")
        if scan.observed_outcome == "FAIL":
            reasons.append("scan_findings_present")
        if scan.sca.exit_code in (2, 3) or scan.sast.exit_code in (2, 3):
            reasons.append("scanner_error_exit")

    if not evidence:
        reasons.append("missing_evidence")

    if reasons:
        return GateDecision(
            decision="DENY",
            reasons=reasons,
            candidate_digest=candidate_digest,
            policy_digest=policy_digest,
        )

    return GateDecision(
        decision="ALLOW",
        reasons=["all_checks_passed"],
        candidate_digest=candidate_digest,
        policy_digest=policy_digest,
        capability={
            "action": "demo_store_write",
            "audience": "sneak.demo",
            "candidate_digest": candidate_digest,
            "nonce": authorization_nonce,
            "scope": "disposable_demo_truth_store_only",
        },
    )
