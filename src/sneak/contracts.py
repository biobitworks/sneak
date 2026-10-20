"""Shared evidence and verdict contracts (local; not provider API claims)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Optional


ObservedOutcome = Literal[
    "PASS",
    "FAIL",
    "NOT_TESTED",
    "UNKNOWN",
    "PENDING",
    "BLOCKED",
    "DENIED",
    "REQUEST_OBSERVED",
]


@dataclass(frozen=True)
class EvidenceRef:
    provider: str
    external_id: str
    artifact_digest: str
    receipt_path: str
    observed_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Verdict:
    requirement_id: str
    verified: bool
    observed_outcome: ObservedOutcome
    evidence: list[EvidenceRef] = field(default_factory=list)
    predecessor_verdict_id: Optional[str] = None
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "verified": self.verified,
            "observed_outcome": self.observed_outcome,
            "evidence": [e.to_dict() for e in self.evidence],
            "predecessor_verdict_id": self.predecessor_verdict_id,
            "reason": self.reason,
        }


def cannot_verify_without_evidence(
    requirement_id: str,
    observed_outcome: ObservedOutcome = "NOT_TESTED",
    reason: str = "missing qualifying evidence",
    predecessor_verdict_id: Optional[str] = None,
) -> Verdict:
    """Missing evidence never yields verified=True."""
    return Verdict(
        requirement_id=requirement_id,
        verified=False,
        observed_outcome=observed_outcome,
        evidence=[],
        predecessor_verdict_id=predecessor_verdict_id,
        reason=reason,
    )
