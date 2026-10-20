"""One-component LOMO successors with Merkle breakpoints.

Each applicable assignment removes exactly one binding/component, recomputes
custody, and separately records task/security outcomes. Actors cannot self-award.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from .merkle import breakpoint_receipt, leaf, root


COMPONENTS = (
    "source-atom",
    "occurrence-context",
    "rights-binding",
    "policy-binding",
    "scan-receipt",
    "memory-reference",
    "authorization-receipt",
    "parent-breakpoint",
    "band-connector",
    "cognee-connector",
    "snyk-connector",
    "flex-connector",
)


def load_matrix(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def ablate_binding(full: dict[str, Any], removed_component: str) -> dict[str, Any]:
    """Return a successor binding with exactly one component removed."""
    if removed_component not in full:
        # Allow connector-style keys that may be nested under connectors.
        connectors = dict(full.get("connectors", {}))
        key = removed_component.replace("-connector", "")
        if key in connectors:
            connectors = {k: v for k, v in connectors.items() if k != key}
            out = dict(full)
            out["connectors"] = connectors
            out["removed_component"] = removed_component
            return out
        raise KeyError(removed_component)
    out = {k: v for k, v in full.items() if k != removed_component}
    out["removed_component"] = removed_component
    return out


def authorization_effect(bindings: dict[str, Any]) -> str:
    """Missing authorization context causes abstention/denial, never implicit permission."""
    if bindings.get("removed_component") == "authorization-receipt":
        return "DENY"
    if bindings.get("removed_component") == "rights-binding":
        return "DENY"
    if bindings.get("removed_component") == "policy-binding":
        return "DENY"
    if "authorization-receipt" not in bindings and "removed_component" not in bindings:
        return "DENY"
    if bindings.get("removed_component") == "band-connector":
        return "FAIL_CLOSED_NO_COORDINATION"
    if bindings.get("removed_component") == "cognee-connector":
        return "FAIL_CLOSED_NO_MEMORY_CONTINUATION"
    if bindings.get("removed_component") == "snyk-connector":
        return "DENY"
    if bindings.get("removed_component") == "flex-connector":
        return "METERING_UNAVAILABLE_SECURITY_UNCHANGED"
    return "ALLOW_SCOPED"


def run_one_component_trial(
    *,
    actor: str,
    full_bindings: dict[str, Any],
    removed_component: str,
    parent_breakpoint: str,
    trial_id: str,
) -> dict[str, Any]:
    baseline_records = [
        {"id": f"{trial_id}-baseline", "actor": actor, "bindings": full_bindings}
    ]
    ablated = ablate_binding(full_bindings, removed_component)
    ablated_records = [
        {"id": f"{trial_id}-ablated", "actor": actor, "bindings": ablated}
    ]
    baseline_bp = breakpoint_receipt(
        schema="sneak.lomo-breakpoint.v1",
        breakpoint_id=f"{trial_id}-BASE",
        parent_id=parent_breakpoint,
        records=baseline_records,
        meaning="LOMO baseline custody; not application acceptance",
    )
    ablated_bp = breakpoint_receipt(
        schema="sneak.lomo-breakpoint.v1",
        breakpoint_id=f"{trial_id}-ABLATE",
        parent_id=baseline_bp["id"],
        records=ablated_records,
        meaning="One-component LOMO successor; integrity only",
    )
    baseline_root = baseline_bp["root"]
    ablated_root = ablated_bp["root"]
    return {
        "trial_id": trial_id,
        "actor": actor,
        "removed_component": removed_component,
        "baseline_root": baseline_root,
        "ablated_root": ablated_root,
        "roots_differ": baseline_root != ablated_root,
        "authorization_effect": authorization_effect(ablated),
        "task_outcome": "NOT_SELF_AWARDED",
        "baseline_breakpoint": baseline_bp,
        "ablated_breakpoint": ablated_bp,
        "status": "EXECUTED_LOCAL",
    }


def matrix_connector_trials(
    parent_breakpoint: str = "SNEAK-013",
) -> list[dict[str, Any]]:
    """Execute local LOMO trials for the four web-app connectors."""
    full = {
        "source-atom": "aok-core",
        "occurrence-context": "ctx-1",
        "rights-binding": "private-hold",
        "policy-binding": "gate-v1",
        "scan-receipt": "scan-pending",
        "memory-reference": "mem-pending",
        "authorization-receipt": "auth-pending",
        "parent-breakpoint": parent_breakpoint,
        "connectors": {
            "band": True,
            "cognee": True,
            "snyk": True,
            "flex": True,
        },
    }
    trials = []
    for i, component in enumerate(
        ("band-connector", "cognee-connector", "snyk-connector", "flex-connector")
    ):
        trials.append(
            run_one_component_trial(
                actor="connector-runtime",
                full_bindings=full,
                removed_component=component,
                parent_breakpoint=parent_breakpoint,
                trial_id=f"LOMO-CONN-{i+1:02d}",
            )
        )
    return trials
