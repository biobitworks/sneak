#!/usr/bin/env python3
"""Replay a source-bound SNEAK Merkle receipt into a new FCO/FCG/MMR lineage.

Does not mutate source Merkle receipts and does not claim live service scans.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.fcg_registry import FCGRegistry
from sneak.merkle import canonical, leaf, proof, root, verify

INPUT = ROOT / "receipts/connectors/SNEAK-016_LOMO_SNYK_SCORE.json"
OUTPUT = ROOT / "data/fcg/sneak-016-replay.jsonl"


def verify_source(receipt: dict) -> None:
    leaves = receipt.get("leaves") or []
    if len(leaves) != receipt.get("leaf_count") or not leaves:
        raise ValueError("source leaf count mismatch")
    records = [e["record"] for e in leaves]
    if records != sorted(records, key=lambda r: str(r.get("id", ""))):
        raise ValueError("source leaf ordering mismatch")
    hashes = [leaf(r) for r in records]
    if root(hashes).hex() != receipt["root"]:
        raise ValueError("source root mismatch")
    for i, row in enumerate(leaves):
        if row["leaf"] != hashes[i].hex():
            raise ValueError("source leaf hash mismatch")
        if row["canonical_hex"] != canonical(records[i]).hex():
            raise ValueError("source canonical bytes mismatch")
        if row["proof"] != proof(hashes, i):
            raise ValueError("source proof representation mismatch")
        if not verify(hashes[i], row["proof"], bytes.fromhex(receipt["root"])):
            raise ValueError("source inclusion proof mismatch")


def replay(receipt_path: Path = INPUT, output_path: Path = OUTPUT) -> dict:
    raw = receipt_path.read_bytes()
    source_hash = hashlib.sha256(raw).hexdigest()
    receipt = json.loads(raw)
    verify_source(receipt)
    if output_path.exists():
        raise FileExistsError("append-only target already exists; verify existing lineage, do not overwrite")
    reg = FCGRegistry(output_path)
    context = {
        "source_receipt": str(receipt_path.relative_to(ROOT)),
        "source_merkle_id": receipt["id"],
        "source_merkle_root": receipt["root"],
        "source_parent_id": receipt.get("parent"),
        "source_mmr_state": receipt.get("mmr", "UNKNOWN"),
        "provenance": "replay_of_existing_receipt_not_new_live_scan",
        "rights": "private_repo_hold",
    }

    def add(kind, payload, actor=None, model="NOT_APPLICABLE", parent=None,
            state="OBSERVED", edges=None):
        return reg.append(
            kind=kind, payload=payload, actor_fco=actor or "NOT_APPLICABLE",
            model_fco=model, parent_fco=parent, edges=edges,
            state=state, source_sha256=source_hash, context=context,
        )["fco_id"]

    actor = add("actor", {"handle": "connector-runtime", "identity": "declared_in_LOMO_source"})
    source = add("source", {"receipt_sha256": source_hash, "merkle_root": receipt["root"],
                            "leaf_count": len(receipt["leaves"])},
                 actor=actor, state="OBSERVED")
    # A model must never be fabricated for runs that did not execute model inference.
    # This FCO records the actual epistemic state of the model identification.
    model_unknown = add("model", {"model_identity": "UNKNOWN", "reason": "LOMO receipt contains no model-run digest"},
                        actor=actor, state="UNKNOWN")
    base_by_trial: dict[str, tuple[str, str]] = {}
    counts = {"breakpoints": 0, "scans_not_tested": 0, "null_scores": 0, "deltas": 0}

    for row in receipt["scored_breakpoints"]:
        trial_id = row["trial_id"]
        kind = "baseline" if row["breakpoint_id"].endswith("-BASE") else "ablated"
        bp = add(
            "breakpoint", {"trial_id": trial_id, "kind": kind, "id": row["breakpoint_id"],
                           "merkle_root": row["merkle_root"]},
            actor=actor, parent=source, state="OBSERVED",
            edges=[{"relation": "references", "to": model_unknown}],
        )
        counts["breakpoints"] += 1
        scan_state = "NOT_TESTED" if row["scan_outcome"] == "NOT_TESTED" else (
            "FAILED" if row["scan_outcome"] in ("DENIED", "FAIL") else "OBSERVED"
        )
        scan = add("scan", {
            "scanner": "snyk", "result": row["scan_outcome"],
            "sca_sast_coverage_accepted": row["coverage_accepted"],
            "live_execution_in_this_replay": False,
        }, actor=actor, parent=bp, state=scan_state)
        if scan_state == "NOT_TESTED":
            counts["scans_not_tested"] += 1
        score_value = row["application_score"]
        score = add(
            "score", {
                "scorer": "javiergarza-snyk/app-security-score",
                "application_score": score_value,
                "unit": "score_out_of_10",
                "coverage_accepted": row["coverage_accepted"],
                "not_an_awarded_bonus": True,
            }, actor=actor, parent=scan,
            state="NULL" if score_value is None else "OBSERVED",
        )
        if score_value is None:
            counts["null_scores"] += 1
        add("classification", {
            "security_admission": "DENY" if not row["coverage_accepted"] else "REVIEW",
            "epistemic_state": "UNKNOWN" if scan_state == "NOT_TESTED" else "RESOLVED",
            "reason": "incomplete_sca_sast_coverage" if not row["coverage_accepted"] else "check_scan_results",
        }, actor=actor, parent=score, state="EXECUTED")
        for external, etype in (("data_outcome", "memory"), ("band_outcome", "handoff")):
            state = "OBSERVED" if row[external] == "PASS" else (
                "NOT_TESTED" if row[external] in ("SKIPPED", "NOT_TESTED") else "UNKNOWN"
            )
            add(etype, {"source_field": external, "reported_outcome": row[external],
                        "live_retested_in_this_replay": False},
                actor=actor, parent=bp, state=state)
        if kind == "baseline":
            base_by_trial[trial_id] = (bp, row["merkle_root"])
        else:
            if trial_id not in base_by_trial:
                raise ValueError("ablation without baseline")
            base_id, base_root = base_by_trial[trial_id]
            add("delta", {
                "metric": "ordered_merkle_root_identity",
                "baseline_root": base_root,
                "successor_root": row["merkle_root"],
                "changed": base_root != row["merkle_root"],
                "numeric_delta": "NOT_COMPUTED",
            }, actor=actor, parent=bp, state="EXECUTED",
                edges=[{"relation": "ablates", "to": base_id}])
            counts["deltas"] += 1

    verified = reg.verify()
    last = reg.rows()[-1]
    included = reg.inclusion_proof(last["fco_id"])
    if not included["verified"]:
        raise ValueError("MMR proof failed")
    return {"source_sha256": source_hash, "source_merkle_root": receipt["root"],
            "source_mmr": receipt.get("mmr"), "fcg": verified,
            "last_fco": last["fco_id"], "last_inclusion_verified": True,
            "counts": counts, "output": str(output_path)}


if __name__ == "__main__":
    print(json.dumps(replay(), indent=2, sort_keys=True))
