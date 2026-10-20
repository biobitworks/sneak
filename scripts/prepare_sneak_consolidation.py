#!/usr/bin/env python3
"""Append-only SNEAK teammate import manifest: deterministic content identity, not claim truth."""
import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEST = ROOT / "receipts/sneak_mvp/TEAMMATE_IMPORT_20261020.json"
SOURCES = (
    "origin/cursor/connector-custody-review-0c2f",
    "origin/integration/cognee-flexprice-r14",
    "origin/integration/band-cognee-snyk-20261020",
    "origin/docs/merkle-mmr-knowledge-base",
    "origin/redteam/claude-20261020",
)
ASCII_PATH = re.compile(r"[\x20-\x7e]+")
HEX = re.compile(r"[0-9a-f]{40}")

def run(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], stderr=subprocess.DEVNULL)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def canon(record):
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")

def path_safe(value):
    if not isinstance(value, str) or not ASCII_PATH.fullmatch(value) or value.startswith("/") or "\\" in value:
        raise ValueError("unsafe path")
    if any(s in ("", ".", "..") for s in value.split("/")):
        raise ValueError("unsafe segment")
    p = ROOT.joinpath(*value.split("/"))
    if p.is_symlink() or not p.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("path escapes repo")
    return p

def graph_root(records):
    if not records: raise ValueError("empty manifest")
    layer = [hashlib.sha256(b"\x00" + canon(x)).digest() for x in records]
    while len(layer)>1:
        layer=[hashlib.sha256(b"\x01"+layer[i]+layer[i+1]).digest() if i+1<len(layer) else layer[i]
               for i in range(0,len(layer),2)]
    return layer[0].hex()

def source_shas():
    return {branch:run("rev-parse",branch).decode().strip() for branch in SOURCES}

def lookup_at(sha,path):
    if not HEX.fullmatch(sha):raise ValueError("invalid source commit")
    try: return run("show",sha+":"+path)
    except subprocess.CalledProcessError:return None

def build():
    candidates = set(run("ls-files", "--others", "--exclude-standard").decode().splitlines())
    candidates.update(run("diff", "--name-only", "HEAD", "--").decode().splitlines())
    candidates.discard(str(DEST.relative_to(ROOT)))
    sources = source_shas()
    records=[]
    for name in sorted(candidates):
        p=path_safe(name)
        if not p.is_file() or p.is_symlink():raise ValueError("not a regular file: "+name)
        data=p.read_bytes()
        candidates_for_path=[]
        for label,sha in sources.items():
            b=lookup_at(sha,name)
            if b is not None:
                candidates_for_path.append((label,sha,digest(b)))
        if not candidates_for_path:
            old=lookup_at(run("rev-parse","HEAD").decode().strip(),name)
            if old is not None:
                source="HEAD_PARENT";source_commit=run("rev-parse","HEAD").decode().strip()
                source_digest=digest(old)
                transformation="PATCHED_PREDECESSOR"
            else:
                source="CURRENT_BUILD";source_commit=None;source_digest=None
                transformation="NEW_IMPLEMENTATION"
        else:
            source,source_commit,source_digest=candidates_for_path[0]
            transformation="COPIED_EXACT" if source_digest==digest(data) else "COMPATIBILITY_SUCCESSOR"
        records.append({"path":name,"sha256":digest(data),"size_bytes":len(data),
                        "source_branch":source,"source_commit":source_commit,
                        "source_sha256":source_digest,"transformation":transformation})
    receipt={"schema":"sneak.teammate-import.v1","parent_commit":run("rev-parse","HEAD").decode().strip(),
             "sources":sources,"records":records,"leaf_count":len(records),
             "root":graph_root(records),"construction":"sha256 domain-separated 0x00 leaves, 0x01 internal, odd promote; canonical ASCII JSON sorted compact",
             "claim_ceiling":"file-byte identity and import lineage only; no live provider acceptance",
             "mmr":"NOT_COMPUTED","signed":False}
    if DEST.exists():raise FileExistsError("append-only manifest exists")
    DEST.parent.mkdir(parents=True,exist_ok=True)
    DEST.write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
    return receipt

def verify(receipt):
    errors=[]
    records=receipt.get("records",[])
    try:
        if receipt.get("root")!=graph_root(records):errors.append("root mismatch")
    except (TypeError,KeyError,ValueError):errors.append("invalid root")
    if receipt.get("leaf_count")!=len(records):errors.append("count mismatch")
    for r in records:
        try:
            p=path_safe(r["path"])
            if not p.is_file() or p.is_symlink():raise ValueError("file missing")
            data=p.read_bytes()
            if len(data)!=r["size_bytes"] or digest(data)!=r["sha256"]:errors.append("working bytes: "+r["path"])
            if r["source_commit"] is not None:
                b=lookup_at(r["source_commit"],r["path"])
                if b is None or digest(b)!=r["source_sha256"]:errors.append("source bytes: "+r["path"])
            if r["source_branch"]!="CURRENT_BUILD" and r["source_commit"] is None:errors.append("missing source commit: "+r["path"])
        except (ValueError,KeyError,OSError,TypeError):errors.append("invalid record: "+str(r.get("path")))
    return {"pass":not errors,"errors":errors[:20],"root":receipt.get("root"),
            "leaf_count":len(records)}

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("action",choices=["build","verify"])
    args=parser.parse_args()
    r=build() if args.action=="build" else json.loads(DEST.read_text())
    result=verify(r)
    print(json.dumps(result,sort_keys=True))
    sys.exit(0 if result["pass"] else 1)
