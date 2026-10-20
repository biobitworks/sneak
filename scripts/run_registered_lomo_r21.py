#!/usr/bin/env python3
"""Bind eight offline LOMO × Merkle security-score attempts into the real FCG/MMR.

This is a genuine local execution, not a successful Snyk SCA/SAST scan.
The registry and all evidence receipts are checked and committed as successors.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.evidence import EvidenceStore
from sneak.fcg_registry import FCGRegistry, verify_rows
from sneak.lomo_score_pipeline import run_connector_lomo_with_scores
from sneak.merkle import canonical, leaf, proof, root, verify

PINNED_HEAD = "97d1a7b3093dd0348a6bc8858604e8e1ab305c19"
PARENT_ROOT = "f0579f511bccecf09c588f1d564e33a12af3409502a56b7868c4b61eab87587a"
LEDGER = ROOT / "data/fcg/sneak-016-replay.jsonl"
OUTPUT = ROOT / "receipts/connectors/SNEAK-021_REGISTERED_LOMO.json"


def main() -> None:
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    if actual != PINNED_HEAD:
        raise SystemExit("source code commit changed; refuse unbound execution")
    if OUTPUT.exists() or (ROOT / "receipts/lomo-fcg-r21-evidence").exists():
        raise SystemExit("execution target exists; preserve prior receipts, do not rerun")
    registry = FCGRegistry(LEDGER)
    old_rows = registry.rows()
    before = registry.verify()
    assert len(old_rows) == 58 and before["mmr_root"] == PARENT_ROOT
    assert old_rows[0]["identity"]["kind"] == "actor"
    assert old_rows[2]["identity"]["kind"] == "model"
    store = EvidenceStore(ROOT / "receipts/lomo-fcg-r21-evidence")
    result = run_connector_lomo_with_scores(
        store=store,
        staged_path=ROOT / "apps/security-demo",
        parent_breakpoint="SNEAK-020",
        live=False,
        notify_band=False,
        fcg=registry,
        actor_fco=old_rows[0]["fco_id"],
        model_fco=old_rows[2]["fco_id"],
        chain_breakpoint_id="SNEAK-021",
    )
    after = registry.verify()
    assert verify_rows(registry.rows()[:58]) == before
    assert result["chain"]["leaf_count"] == 8
    assert len(result["scored"]) == 8
    assert len(registry.rows()) == 58 + 8 * 4 + 4
    assert after["fco_count"] == 94
    assert not result["summary"]["any_clean_ten"]
    chain = result["chain"]
    event_hashes = [leaf(x["record"]) for x in chain["leaves"]]
    assert root(event_hashes).hex() == chain["root"]
    assert all(verify(h, e["proof"], bytes.fromhex(chain["root"]))
               for h, e in zip(event_hashes, chain["leaves"]))
    compact = [
        {
            "trial": x["trial_id"],
            "kind": x["breakpoint_kind"],
            "breakpoint_id": x["post"]["breakpoint_id"],
            "merkle_root": x["post"]["merkle_root"],
            "scan_outcome": x["post"]["scan"]["observed_outcome"],
            "application_score": x["post"]["scan"]["score"]["application_score"],
            "coverage_accepted": x["post"]["scan"]["score"]["coverage_accepted"],
            "registry_mmr_root": x["post"]["fcg"]["mmr_root"],
            "registry_mmr_size": x["post"]["fcg"]["mmr_size"],
            "breakpoint_fco_id": x["post"]["fcg"]["breakpoint_fco_id"],
            "scan_fco_id": x["post"]["fcg"]["scan_fco_id"],
            "value_fco_id": x["post"]["fcg"]["score_value_fco_id"],
            "classification_fco_id": x["post"]["fcg"]["classification_fco_id"],
            "delta_fco_id": x["post"].get("fcg_delta_fco_id"),
        }
        for x in result["scored"]
    ]
    assert all(x["scan_outcome"] == "NOT_TESTED" for x in compact)
    assert all(x["application_score"] is None for x in compact)
    receipt = {
        "schema": "sneak.registered-lomo-mmr.v1",
        "id": "SNEAK-021",
        "source_commit": PINNED_HEAD,
        "parent_mmr_root": PARENT_ROOT,
        "source_merkle_id": "SNEAK-016",
        "local_mode": True,
        "live_snyk": "NOT_TESTED",
        "live_cognee_per_event": "NOT_TESTED",
        "live_band_per_event": "NOT_TESTED",
        "security_admission": "DENY",
        "tool_application_score": None,
        "status": "EXECUTED_LOCAL",
        "checkpoint_merkle_root": chain["root"],
        "checkpoint_leaf_count": chain["leaf_count"],
        "checkpoint_chain": chain,
        "scored_breakpoints": compact,
        "fcg": after,
        "last_inclusion_verified": registry.inclusion_proof(registry.rows()[-1]["fco_id"])["verified"],
    }
    OUTPUT.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
    print(json.dumps({
        "chain_id": receipt["id"], "merkle_root": receipt["checkpoint_merkle_root"],
        "breakpoint_count": len(compact), "new_fcos": after["fco_count"] - before["fco_count"],
        "added_deltas": 4, "fcg": after, "score": None,
        "scan_state": "NOT_TESTED",
    }, indent=2))


if __name__ == "__main__":
    main()
