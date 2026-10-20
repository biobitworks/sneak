#!/usr/bin/env python3
"""Create append-only evidence successors for the integrated SNEAK tree.

This reconciles identities of actual integrated bytes. It never rewrites a
predecessor receipt and makes no claim of agent execution or security success.
"""
from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import subprocess
from scripts import build_evidence_heatmap as export

ROOT = pathlib.Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "receipts/sneak_mvp/TEAMMATE_IMPORT_20261020_R4.json"
SUCCESSOR = ROOT / "receipts/sneak_mvp/TEAMMATE_IMPORT_20261020_R5.json"
PREDECESSOR_EXPORT = ROOT / "receipts/integrations/VERCEL_EXPORT_PRE_R5_20261020.json"
CURRENT_EXPORT = ROOT / "deploy/vercel-preview/data/export-custody.json"
REPORT = ROOT / "receipts/integrations/SNEAK_MAIN_MERGE_RECONCILIATION_R5_20261020.json"

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def canonical(x) -> bytes:
    return json.dumps(x, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("ascii")

def root_for(rows: list) -> str:
    if not rows:
        raise ValueError("empty manifest")
    layer = [hashlib.sha256(bytes([0]) + canonical(x)).digest() for x in rows]
    while len(layer) > 1:
        layer = [hashlib.sha256(bytes([1]) + layer[i] + layer[i + 1]).digest()
                 if i + 1 < len(layer) else layer[i] for i in range(0, len(layer), 2)]
    return layer[0].hex()

def write_new(path: pathlib.Path, content: bytes):
    if path.exists():
        if path.read_bytes() != content:
            raise RuntimeError("immutable predecessor/successor collision: " + str(path))
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

def main():
    origin_raw = ORIGINAL.read_bytes()
    old = json.loads(origin_raw)
    assert old["root"] == root_for(old["records"])
    successor = copy.deepcopy(old)
    changed = []
    for item in successor["records"]:
        rel = item["path"]
        if rel.startswith("/") or ".." in pathlib.PurePosixPath(rel).parts:
            raise ValueError("unsafe manifest path")
        p = (ROOT / rel)
        if not p.is_file() or p.is_symlink():
            raise ValueError("missing/nonregular: " + rel)
        raw = p.read_bytes()
        new_hash = digest(raw)
        if item["sha256"] != new_hash or item["size_bytes"] != len(raw):
            changed.append({"path": rel, "predecessor_sha256": item["sha256"],
                            "successor_sha256": new_hash,
                            "predecessor_size_bytes": item["size_bytes"],
                            "successor_size_bytes": len(raw)})
            item["predecessor_integrated_sha256"] = item["sha256"]
            item["predecessor_transformation"] = item["transformation"]
            item["transformation"] = "MERGE_RECONCILED_SUCCESSOR"
            item["sha256"] = new_hash
            item["size_bytes"] = len(raw)
    successor["schema"] = "sneak.teammate-import-merge-successor.v3"
    successor["parent_manifest"] = ORIGINAL.relative_to(ROOT).as_posix()
    successor["parent_manifest_sha256"] = digest(origin_raw)
    successor["parent_root"] = old["root"]
    successor["integration_parent_commit"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    successor["integration_changes"] = changed
    successor["claim_ceiling"] = ("Reconciled current working-tree file identities only; "
                                  "not proof of original import equivalence, live sponsor "
                                  "behavior, source rights, security, or accepted judging.")
    successor["root"] = root_for(successor["records"])
    successor["leaf_count"] = len(successor["records"])
    successor["mmr"] = "NOT_COMPUTED"
    successor["signed"] = False
    assert successor["root"] == root_for(successor["records"])
    write_new(SUCCESSOR, canonical(successor) + bytes([10]))

    old_export_bytes = CURRENT_EXPORT.read_bytes()
    old_export = json.loads(old_export_bytes)
    write_new(PREDECESSOR_EXPORT, old_export_bytes)
    export.main()
    new_export = json.loads(CURRENT_EXPORT.read_bytes())
    assert export.verify_custody(new_export)
    report = {
        "schema": "sneak.main-merge-reconciliation.v1",
        "parent_integration_head": successor["integration_parent_commit"],
        "import": {"predecessor_path": successor["parent_manifest"],
                   "predecessor_sha256": successor["parent_manifest_sha256"],
                   "predecessor_merkle_root": old["root"],
                   "successor_path": SUCCESSOR.relative_to(ROOT).as_posix(),
                   "successor_sha256": digest(SUCCESSOR.read_bytes()),
                   "successor_merkle_root": successor["root"],
                   "reconciled_files": changed,
                   "mmr": "NOT_COMPUTED"},
        "vercel": {"predecessor_sha256": digest(old_export_bytes),
                   "predecessor_export_merkle_root": old_export["tree"]["root"],
                   "predecessor_export_mmr_root": old_export["mmr"]["root_hash"],
                   "successor_export_merkle_root": new_export["tree"]["root"],
                   "successor_export_mmr_root": new_export["mmr"]["root_hash"],
                   "predecessor_receipt": PREDECESSOR_EXPORT.relative_to(ROOT).as_posix(),
                   "successor_projection": CURRENT_EXPORT.relative_to(ROOT).as_posix()},
        "snyk_gate": "BLOCKED_NOT_VERIFIED_FOR_INTEGRATED_HEAD",
        "band_agent_collaboration": "NOT_TESTED_END_TO_END",
        "cognee_agent_owned_recall": "NOT_TESTED_END_TO_END",
        "flexprice_live_roi": "NOT_TESTED",
        "mandatory_acceptance": "NOT_ESTABLISHED",
        "canonical_project_mmr": "NOT_COMPUTED",
        "meaning": "Integration byte identity only, not security or substantive correctness",
        "signed": False
    }
    write_new(REPORT, canonical(report) + bytes([10]))
    print(json.dumps({"reconciled_files": len(changed),
                      "import_root": successor["root"],
                      "vercel_export_root": new_export["tree"]["root"],
                      "vercel_mmr_root": new_export["mmr"]["root_hash"],
                      "report": REPORT.relative_to(ROOT).as_posix()}, sort_keys=True))

if __name__ == "__main__":
    main()
