"""Register each completed LOMO score attempt into the append-only FCG/MMR.

These records are a deterministic custody projection. Missing scanner coverage is
always represented as NOT_TESTED/NULL, never as a clean application score.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .fcg_registry import FCGRegistry


def register_breakpoint_result(
    registry: FCGRegistry, *, actor_fco: str, model_fco: str,
    breakpoint_id: str, merkle_root: str, score_receipt_path: Path,
    scan_outcome: str, application_score: float | None,
    coverage_accepted: bool, candidate_digest: str,
    parent_fco: str | None = None,
) -> dict[str, Any]:
    """Produce linked FCOs and an MMR proof after one specific Merkle root."""
    content = Path(score_receipt_path).read_bytes()
    source_digest = hashlib.sha256(content).hexdigest()
    context = {
        "source_receipt_sha256": source_digest,
        "source_receipt_kind": "breakpoint_snyk_score",
        "custody_type": "registered_breakpoint_attempt",
        "semantic_claim": "NOT_VALIDATED_BY_HASH",
    }

    def append(kind: str, payload: dict, *, parent: str | None = None,
               state: str = "EXECUTED", edges: list[dict] | None = None) -> str:
        return registry.append(
            kind=kind, payload=payload, state=state, source_sha256=source_digest,
            parent_fco=parent, actor_fco=actor_fco, model_fco=model_fco,
            edges=edges, context=context,
        )["fco_id"]

    bp = append("breakpoint", {
        "breakpoint_id": breakpoint_id,
        "merkle_root": merkle_root,
        "previous_fco": parent_fco,
        "stage": "post_lomo_score_attempt",
    }, parent=parent_fco)
    scan_state = (
        "NOT_TESTED" if scan_outcome in ("NOT_TESTED", "SKIPPED")
        else "FAILED" if scan_outcome in ("DENIED", "FAIL", "BLOCKED")
        else "OBSERVED" if scan_outcome == "PASS"
        else "UNKNOWN"
    )
    scan = append("scan", {
        "scan_outcome": scan_outcome, "candidate_digest": candidate_digest,
        "sca_sast_coverage_accepted": coverage_accepted,
        "upstream_scorer": "javiergarza-snyk/app-security-score",
    }, parent=bp, state=scan_state)
    val = append("value", {
        "metric": "application_security_score",
        "value": application_score, "unit": "score_out_of_10",
        "coverage_accepted": coverage_accepted,
    }, parent=scan, state="NULL" if application_score is None else "OBSERVED")
    cls = append("classification", {
        "gate": "DENY" if not coverage_accepted or application_score != 10.0 else "REVIEW",
        "clean_application_ten": bool(coverage_accepted and application_score == 10.0),
        "event_bonus": "NOT_AWARDED",
    }, parent=val)
    status = registry.verify()
    proof = registry.inclusion_proof(cls)
    return {
        "breakpoint_fco_id": bp, "scan_fco_id": scan,
        "score_value_fco_id": val, "classification_fco_id": cls,
        "mmr_root": status["mmr_root"], "mmr_size": status["mmr_size"],
        "leaf_count": status["fco_count"], "last_inclusion_verified": proof["verified"],
    }
