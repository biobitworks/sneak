"""MVP hash travel: one leaf per sponsor/optional atom → single merkle root + proofs.

Source status is supplied by callers (receipts/live). Never inferred from graph links.
Project MMR remains NOT_COMMITTED.
"""

from __future__ import annotations

from typing import Any, Sequence

from .merkle import breakpoint_receipt, leaf, proof, root, verify


def atom_leaf_record(
    *,
    atom_id: str,
    kind: str,
    requirement: str,
    observed_outcome: str,
    verified: bool,
    tried: bool,
    sponsor_digest: str | None = None,
) -> dict[str, Any]:
    """Canonical event record for one MVP atom leaf."""
    return {
        "id": atom_id,
        "kind": kind,
        "payload": {
            "requirement": requirement,
            "observed_outcome": observed_outcome,
            "verified": bool(verified),
            "tried": bool(tried),
            "sponsor_digest": sponsor_digest,
            "mmr": "NOT_COMMITTED",
        },
    }


def agent_snyk_leaf_record(
    *,
    agent_id: str,
    handle: str,
    role: str,
    snyk_binding_digest: str,
    live_snyk: str,
) -> dict[str, Any]:
    """Every agent binds to the shared Snyk connector hash (awareness leaf)."""
    return {
        "id": f"AGENT-SNYK-{handle.replace('/', '-')}",
        "kind": "AgentSnykBinding",
        "payload": {
            "agent_id": agent_id,
            "handle": handle,
            "role": role,
            "snyk_connector": "snyk-connector",
            "snyk_binding_digest": snyk_binding_digest,
            "live_snyk": live_snyk,
            "awareness": "every_agent_connects_to_snyk",
            "mmr": "NOT_COMMITTED",
        },
    }


def build_mvp_travel(
    records: Sequence[dict[str, Any]],
    *,
    breakpoint_id: str = "SNEAK-029",
    parent_id: str = "SNEAK-028",
) -> dict[str, Any]:
    """Build ordered merkle over atom/agent leaves with per-leaf hash travel proofs."""
    ordered = sorted(records, key=lambda r: str(r.get("id", "")))
    leaves = [leaf(r) for r in ordered]
    mvp_root = root(leaves).hex() if leaves else None
    travels = []
    for i, (rec, lf) in enumerate(zip(ordered, leaves)):
        steps = proof(leaves, i)
        ok = verify(lf, steps, bytes.fromhex(mvp_root)) if mvp_root else False
        travels.append(
            {
                "id": rec["id"],
                "kind": rec.get("kind"),
                "leaf": lf.hex(),
                "proof": steps,
                "verifies_to_mvp_root": bool(ok),
                "mvp_root": mvp_root,
            }
        )
    receipt = breakpoint_receipt(
        schema="sneak.mvp-hash-travel.v1",
        breakpoint_id=breakpoint_id,
        parent_id=parent_id,
        records=list(ordered),
        meaning=(
            "Single MVP merkle root over sponsor mandatory atoms, optional/bonus atoms, "
            "and per-agent Snyk bindings; hash travel = leaf + proof → mvp_root; "
            "mmr NOT_COMMITTED"
        ),
    )
    receipt["mvp_root"] = mvp_root
    receipt["hash_travels"] = travels
    receipt["mmr"] = "NOT_COMMITTED"
    receipt["sponsor_count"] = sum(1 for r in ordered if r.get("kind") == "SponsorMandatoryAtom")
    receipt["optional_count"] = sum(1 for r in ordered if r.get("kind") == "OptionalBonusAtom")
    receipt["agent_snyk_count"] = sum(1 for r in ordered if r.get("kind") == "AgentSnykBinding")
    return receipt
