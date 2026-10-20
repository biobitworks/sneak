"""Evidence-backed SNEAK integration view. Receipts are not live acceptance."""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
from collections import Counter

from . import REPO_ROOT
from .sanitize import redact

MANIFEST = REPO_ROOT / "receipts/sneak_mvp/TEAMMATE_IMPORT_20261020_R5.json"
BAND_RECEIPT = REPO_ROOT / "receipts/band/SNEAK-013_INDEPENDENT_VERIFY.json"
COGNEE_RECEIPT = REPO_ROOT / "receipts/sneak_mvp/COGNEE_RECALL_SUCCESSOR_20261020.json"
FLEX_RECEIPT = REPO_ROOT / "receipts/integrations/SNEAK-014_TURN_BREAKPOINT.json"
PATH = re.compile(r"[\x20-\x7e]+")

def read(path: pathlib.Path):
    try: return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError): return None

def canonical(row):
    return json.dumps(row, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("ascii")

def root_for(records):
    if not isinstance(records, list) or not records:raise ValueError("empty manifest")
    layer=[hashlib.sha256(b"\x00"+canonical(row)).digest() for row in records]
    while len(layer)>1:
        layer=[hashlib.sha256(b"\x01"+layer[i]+layer[i+1]).digest() if i+1<len(layer) else layer[i]
               for i in range(0,len(layer),2)]
    return layer[0].hex()

def imported_files():
    manifest=read(MANIFEST)
    if not isinstance(manifest,dict):
        return {"status":"MISSING","verified":False,"file_count":0,"source_counts":{}}
    rows=manifest.get("records",[])
    errors=[]
    if not isinstance(rows,list):rows=[];errors.append("invalid rows")
    try:
        if root_for(rows)!=manifest.get("root"):errors.append("root mismatch")
    except (ValueError,TypeError,KeyError):errors.append("invalid candidate root")
    if manifest.get("leaf_count")!=len(rows):errors.append("count mismatch")
    for row in rows:
        try:
            name=row["path"]
            if not PATH.fullmatch(name) or name.startswith("/") or "\\" in name or any(
                    part in ("",".","..") for part in name.split("/")):
                raise ValueError("unsafe path")
            p=REPO_ROOT.joinpath(*name.split("/"))
            if p.is_symlink() or not p.resolve().is_relative_to(REPO_ROOT.resolve()):
                raise ValueError("unsafe file")
            b=p.read_bytes()
            if len(b)!=row["size_bytes"] or hashlib.sha256(b).hexdigest()!=row["sha256"]:
                raise ValueError("file mismatch")
        except (KeyError,ValueError,OSError,TypeError):
            errors.append("file mismatch or unsafe path")
    return {
        "status":"LOCAL_BYTES_VERIFIED" if not errors else "FAILED",
        "verified":not errors,
        "file_count":len(rows),
        "candidate_root":manifest.get("root"),
        "source_counts":dict(Counter(row.get("source_branch","UNKNOWN") for row in rows)),
        "transformation_counts":dict(Counter(row.get("transformation","UNKNOWN") for row in rows)),
        "errors":errors[:5],
        "source_commit_validation":"ORIGINAL_IMPORT_VERIFIER_PASSED_NOT_REEXECUTED",
        "mmr":manifest.get("mmr","NOT_COMPUTED"),
    }

def stack():
    import_state=imported_files()
    b=read(BAND_RECEIPT) or {}
    c=read(COGNEE_RECEIPT) or {}
    f=read(FLEX_RECEIPT) or {}
    from . import snyk_adapter
    snyk=snyk_adapter.latest_receipt() or {}
    commit=None; dirty=None
    try:
        commit=subprocess.check_output(["git","-C",str(REPO_ROOT),"rev-parse","HEAD"],timeout=5).decode().strip()
        dirty=bool(subprocess.check_output(["git","-C",str(REPO_ROOT),"status","--porcelain"],timeout=5))
    except (OSError,subprocess.SubprocessError):pass
    match=snyk.get("target",{}).get("commit")==commit and dirty is False
    return {
        "schema":"sneak.integration-evidence.v1","claims_ceiling":"local evidence and candidate integration, not judge acceptance",
        "source_import":import_state,
        "band":{"status":"RECEIPT_ONLY" if b.get("root") else "NOT_TESTED",
                "event_root":b.get("root"),"human_decision":b.get("human_decision","UNKNOWN"),
                "live_desktop":"NOT_VERIFIED"},
        "cognee":{"status":"OBSERVED_LOCAL_OSS_RECALL" if c.get("read",{}).get("executed") and c.get("write",{}).get("executed") else "NOT_TESTED",
                  "next_action":c.get("decision_successor",{}).get("selected_action"),
                  "band_action_dispatch":"NOT_EXECUTED"},
        "snyk":{"status":snyk.get("outcome","NOT_RUN"),"gate":"BLOCKED" if not match or snyk.get("gate")!="PASS" else "PASS",
                "scanned_commit":snyk.get("target",{}).get("commit"),
                "current_commit":commit,"target_current_and_clean":match,
                "finding_count":snyk.get("finding_count"),"source_receipt":"receipts/sneak_mvp/scans/"},
        "flexprice":{"status":"IMPORTED_RECEIPT_ONLY" if f else "NOT_TESTED",
                     "metered_product_events":"NOT_VERIFIED"},
        "release_gate":"BLOCKED",
    }

def graph_items(fco):
    statuses=stack()
    roles=(
        ("IMPORT-TEAM","teammate_import","Teammate contributions indexed","source_import"),
        ("BAND-ROOM","agent_coordination","BAND collaboration evidence","band"),
        ("COGNEE-MEM","knowledge_memory","Cognee memory recall","cognee"),
        ("SNYK-SCAN","scanner","Snyk secure ship gate","snyk"),
        ("FLEX-METER","billing","Flexprice integration candidate","flexprice"),
    )
    nodes=[]; edges=[]
    for node_id,kind,title,key in roles:
        detail=statuses[key]
        nodes.append({"id":node_id,"type":kind,"label":title,"status":detail.get("status"),
                      "actor":"evidence_gateway","source":None,
                      "ceiling":"Provider receipt only; not mandatory acceptance"})
        edges.append({"from":fco,"to":node_id,"rel":"integration_candidate"})
    edges.append({"from":"COGNEE-MEM","to":"SNYK-SCAN","rel":"policy_recall"})
    edges.append({"from":"SNYK-SCAN","to":"BAND-ROOM","rel":"approval_pending"})
    return nodes,edges

def live_check():
    result=stack()
    try:
        p=subprocess.run(["band","whoami"],capture_output=True,timeout=8,check=False)
        result["band"]["runtime_account"]="AUTHENTICATED" if p.returncode==0 else "NOT_AUTHENTICATED"
    except (OSError,subprocess.TimeoutExpired):
        result["band"]["runtime_account"]="UNKNOWN"
    return result
