#!/usr/bin/env python3
"""Deterministic structural LOMO tests and Merkle/MMR export custody.

The 80 actor×component trials test *only* schema-binding removal, not live agent
behavior or scientific performance. Real Snyk execution and acceptance remain separate.
"""
from __future__ import annotations
import hashlib, json, pathlib, sys
from scripts import mmr_reference as R

ROOT = pathlib.Path(__file__).resolve().parents[1]
MATRIX = ROOT/"data/lomo/actor_component_matrix.jsonl"
REPO_VIEW = ROOT/"deploy/vercel-preview"
HEATMAP_JSON = REPO_VIEW/"data/evidence-matrix.json"
CUSTODY_JSON = REPO_VIEW/"data/export-custody.json"
MANIFEST_JSON = REPO_VIEW/"EXPORT_MANIFEST.json"
COMPONENTS = ("source-atom","occurrence-context","rights-binding","policy-binding","scan-receipt","memory-reference","authorization-receipt","parent-breakpoint")
EXCLUSION = frozenset({"EXPORT_MANIFEST.json", "data/export-custody.json"})
SCHEMA = "sneak.evidence-grid.v1"

def canonical(obj) -> bytes:
    return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("ascii")

def sha(data:bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def merkle_leaf(data:bytes) -> bytes:
    return R.H(b"\x00"+data)

def run_matrix():
    rows = [json.loads(s) for s in MATRIX.read_text().splitlines() if s.strip()]
    if len(rows)!=80: raise ValueError(f"source matrix expected 80 entries, got {len(rows)}")
    actors = list(dict.fromkeys(x["actor"] for x in rows))
    if len(actors)!=10 or len(set(actors))!=10: raise ValueError("unexpected actor coverage")
    keyset={(x["actor"],x["removed_component"]) for x in rows}
    if keyset != {(a,c) for a in actors for c in COMPONENTS}: raise ValueError("matrix lacks full actor x component")
    results = []
    for i,source in enumerate(rows):
        actor,removed=source["actor"],source["removed_component"]
        if source["status"]!="NOT_TESTED": raise ValueError("source matrix outcome changed")
        bindings={c:{"source":"SNEAK-FIXTURE", "applicable":True, "binding":f"{actor}/{c}"} for c in COMPONENTS}
        before={"schema":"sneak.synthetic-binding.v1", "actor":actor, "bindings":bindings,"real_agent_observation":False}
        after={"schema":"sneak.synthetic-binding.v1","actor":actor,"bindings":{k:v for k,v in bindings.items() if k !=removed}, "real_agent_observation":False}
        bdata, adata=canonical(before),canonical(after)
        base_leaf, abl_leaf=merkle_leaf(bdata),merkle_leaf(adata)
        bm,am=R.MMR(),R.MMR()
        bm.append(bdata);am.append(adata)
        assert set(after["bindings"]) == set(COMPONENTS)-{removed}
        assert set(before["bindings"]) == set(COMPONENTS)
        assert base_leaf!=abl_leaf
        assert bm.root()!=am.root()
        missing=[c for c in COMPONENTS if c not in after["bindings"]]
        structural_gate="DENY_MISSING_REQUIRED_BINDING" if missing else "ALLOW"
        assert structural_gate=="DENY_MISSING_REQUIRED_BINDING"
        results.append({
          "index":i,"actor":actor,"component":removed,"trial_id":f"LOMO-STRUCT-{i+1:03d}",
          "parent":"SNEAK-016 / prior unexecuted source matrix",
          "source_row_status":"NOT_TESTED",
          "structural_execution":"PASS",
          "structural_gate":structural_gate,
          "baseline_merkle_root":base_leaf.hex(),"ablation_merkle_root":abl_leaf.hex(),
          "baseline_mmr_root":bm.root().hex(),"ablation_mmr_root":am.root().hex(),
          "mmr_nodes_each":bm.size, "remove_count":1,
          "agent_behavior":"NOT_TESTED","snyk_code_per_breakpoint":"NOT_TESTED",
          "snyk_oss_per_breakpoint":"NOT_TESTED","snyk_container_per_breakpoint":"NOT_TESTED",
          "external_app_score":"NOT_COMPUTED",
          "security_score":"NOT_COMPUTED",
          "root_semantics":"synthetic structural custody only"
        })
    return {"schema":SCHEMA,"actor_count":len(actors),"component_count":len(COMPONENTS),
        "trial_count":len(results),"actors":actors,"components":list(COMPONENTS),
        "source":{"path":"data/lomo/actor_component_matrix.jsonl","sha256":sha(MATRIX.read_bytes()),
                  "baseline_observed":"NOT_TESTED","origin_branch":"integration/sneak-consolidation-20261020"},
        "structural_tests":"EXECUTED_PASS","live_actor_trials":"NOT_TESTED",
        "snyk_per_trial":"NOT_TESTED","lomo_performance_delta":"NOT_COMPUTED",
        "rows":results}

def export_custody():
    files = sorted(p for p in REPO_VIEW.rglob("*") if p.is_file() and not p.is_symlink()
                   and ".vercel" not in p.parts and str(p.relative_to(REPO_VIEW)) not in EXCLUSION
                   and str(p.relative_to(REPO_VIEW)) != ".gitignore")
    if not files: raise ValueError("empty exported file set")
    records=[]
    for path in files:
        rel=path.relative_to(REPO_VIEW).as_posix()
        data=path.read_bytes()
        records.append({"path":rel,"sha256":sha(data),"size_bytes":len(data)})
    data=[canonical(r) for r in records]
    leaves=[merkle_leaf(x) for x in data]
    tree=R.merkle_root(leaves)
    mmr=R.MMR()
    for x in data: mmr.append(x)
    peaks = [{"position":p,"hash":h.hex()} for p,h in zip(R.peaks(mmr.size),mmr.peak_hashes())]
    return {"schema":"sneak.vercel-export-custody.v1",
        "canonical":"JSON sort_keys compact separators ensure_ascii=true NO trailing LF per record",
        "ordering":"UTF-8 relative path ascending",
        "tree":{"algorithm":"SHA-256","leaf":"SHA256(0x00 || canonical(record))",
            "node":"SHA256(0x01 || left || right)","odd":"promote unchanged",
            "root":tree.hex(),"leaves":len(leaves)},
        "mmr":{"algorithm":"SHA-256","leaf":"SHA256(0x00 || u64be(pos) || canonical(record))",
            "parent":"SHA256(0x01 || u64be(parent_pos) || left || right)",
            "root":"bag peaks from right using SHA256(0x02 || u64be(node_count) || left_peak || accumulated)",
            "size":mmr.size,"leaves":len(data),"peaks":peaks,"root_hash":mmr.root().hex()},
        "files":records,
        "excluded":["EXPORT_MANIFEST.json","data/export-custody.json",".gitignore",".vercel/*"],
        "status":"COMPUTED_AND_LOCALLY_VERIFIED",
        "scientific_or_security_truth":"NOT_ESTABLISHED",
        "signed":False
    }

def verify_custody(c):
    actual=export_custody()
    assert c==actual, "Merkle/MMR differs from exact current files"
    assert len(c["files"])==c["tree"]["leaves"]==c["mmr"]["leaves"]
    assert c["tree"]["root"] != c["mmr"]["root_hash"]
    return True

def main():
    REPO_VIEW.joinpath("data").mkdir(parents=True,exist_ok=True)
    matrix=run_matrix()
    HEATMAP_JSON.write_bytes(canonical(matrix)+b"\n")
    custody=export_custody()
    CUSTODY_JSON.write_bytes(canonical(custody)+b"\n")
    assert verify_custody(custody)
    old=json.loads(MANIFEST_JSON.read_text())
    old["outputs_sha256"] = {r["path"]:r["sha256"] for r in custody["files"]}
    old["export_merkle_root"]=custody["tree"]["root"]
    old["export_mmr_root"]=custody["mmr"]["root_hash"]
    old["export_leaf_count"]=custody["tree"]["leaves"]
    old["export_mmr_nodes"]=custody["mmr"]["size"]
    old["lomo_structural"]=matrix["trial_count"]
    old["lomo_real_agents"]="NOT_TESTED"
    old["mmr"]="COMPUTED_FOR_EXPORT_ONLY"
    old["export_root_semantics"]="deterministic immutable exported bytes only; excludes self-referential manifest and custody file"
    MANIFEST_JSON.write_bytes(canonical(old)+b"\n")
    print(json.dumps({"structural_lomo":len(matrix["rows"]), "merkle_export_root":custody["tree"]["root"],
          "mmr_export_root":custody["mmr"]["root_hash"],"files":len(custody["files"]),"mmr_nodes":custody["mmr"]["size"]},sort_keys=True))

if __name__=="__main__":main()
