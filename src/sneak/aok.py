"""Atomic acceptance (AoK) registry and entry gate.

verified=false means no qualifying evidence; NOT_TESTED is not an observed failure.
Only mandatory atoms gate entry. Bonus/optional remain distinct.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .contracts import EvidenceRef, Verdict


def load_atoms(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    text = Path(path).read_text(encoding="utf-8")
    if path.suffix != ".jsonl":
        raise ValueError("expected jsonl atom registry")
    for line in text.splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def entry_gate(verdicts: list[Verdict], *, mandatory_ids: set[str] | None = None) -> dict[str, Any]:
    if mandatory_ids is None:
        mandatory = [
            v
            for v in verdicts
            if (v.predecessor_verdict_id or v.requirement_id).startswith("REQ-AOK-M")
        ]
    else:
        mandatory = [
            v
            for v in verdicts
            if (v.predecessor_verdict_id or v.requirement_id) in mandatory_ids
        ]
    ok = bool(mandatory) and all(v.verified for v in mandatory)
    return {
        "entry_gate": ok,
        "mandatory_count": len(mandatory),
        "mandatory_verified": sum(1 for v in mandatory if v.verified),
        "mandatory_unverified": sum(1 for v in mandatory if not v.verified),
        "meaning": "entry_gate = all(mandatory_atom.verified is True)",
    }


def successor_from_registry(
    registry_path: Path,
    *,
    successor_suffix: str,
    reason: str,
) -> list[Verdict]:
    """Append successor verdicts without rewriting predecessor atoms."""
    verdicts: list[Verdict] = []
    for row in load_atoms(registry_path):
        pred_id = row.get("predecessor_requirement_id") or row.get("id")
        req_id = row.get("id")
        if req_id is None:
            req_id = f"{pred_id}-{successor_suffix}"
        evidence_raw = row.get("evidence") or []
        clean: list[EvidenceRef] = []
        for e in evidence_raw:
            if isinstance(e, dict) and {"provider", "external_id", "artifact_digest", "receipt_path", "observed_at"} <= set(e):
                clean.append(EvidenceRef(**{k: e[k] for k in (
                    "provider", "external_id", "artifact_digest", "receipt_path", "observed_at"
                )}))
        verdicts.append(
            Verdict(
                requirement_id=str(req_id),
                verified=bool(row.get("verified", False)),
                observed_outcome=row.get("observed_outcome", "NOT_TESTED"),
                evidence=clean,
                predecessor_verdict_id=str(pred_id),
                reason=row.get("reason", reason),
            )
        )
    return verdicts


def classify_requirement_kind(atom_id: str) -> str:
    base = atom_id
    if "-SNEAK-" in atom_id:
        base = atom_id.split("-SNEAK-")[0]
    if base.startswith("REQ-AOK-M"):
        return "mandatory"
    if base.startswith("REQ-AOK-F01") or base.startswith("REQ-AOK-F02"):
        return "bonus_selected"
    if base.startswith("REQ-AOK-S01") or base.startswith("REQ-AOK-S02"):
        return "bonus_selected"
    if base.startswith("REQ-AOK-F") or base.startswith("REQ-AOK-S") or base.startswith("REQ-AOK-E"):
        return "scoring_enrichment"
    return "other"


def summarize_optional_mandatory(verdicts: list[Verdict]) -> dict[str, Any]:
    buckets: dict[str, list[dict[str, Any]]] = {
        "mandatory": [],
        "bonus_selected": [],
        "scoring_enrichment": [],
        "other": [],
    }
    for v in verdicts:
        kind = classify_requirement_kind(v.predecessor_verdict_id or v.requirement_id)
        buckets.setdefault(kind, [])
        buckets[kind].append(
            {
                "id": v.requirement_id,
                "verified": v.verified,
                "observed_outcome": v.observed_outcome,
            }
        )
    return {
        "counts": {k: len(v) for k, v in buckets.items()},
        "entry": entry_gate(verdicts),
        "buckets": buckets,
    }
