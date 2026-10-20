#!/usr/bin/env python3
"""Versioned Git snapshot integrity. Hash identity is not semantic truth."""
import argparse,hashlib,json,pathlib,subprocess,sys,re
def canonical(x):
    return json.dumps(x,sort_keys=True,ensure_ascii=True,separators=(",",":")).encode("ascii")
def h(x):return hashlib.sha256(x).digest()
def leaf(record):return h(b"\x00"+canonical(record))
def parent(a,b):return h(b"\x01"+a+b)
def layers(xs):
    if not xs:raise ValueError("empty tree")
    out=[list(xs)]
    while len(out[-1])>1:
        row=out[-1];out.append([parent(row[i],row[i+1]) if i+1<len(row) else row[i] for i in range(0,len(row),2)])
    return out
def root(xs):return layers(xs)[-1][0]
def proof(xs,index):
    if index<0 or index>=len(xs):raise ValueError("invalid leaf index")
    out=[]
    for row in layers(xs)[:-1]:
        if index%2:out.append({"side":"left","hash":row[index-1].hex()})
        elif index+1<len(row):out.append({"side":"right","hash":row[index+1].hex()})
        index//=2
    return out
def verify(value,steps,expected):
    try:
        if len(value)!=32 or len(expected)!=32:return False
        for step in steps:
            sibling=bytes.fromhex(step["hash"])
            if len(sibling)!=32 or step["side"] not in ("left","right"):return False
            value=parent(sibling,value) if step["side"]=="left" else parent(value,sibling)
        return value==expected
    except (ValueError,KeyError,TypeError):return False
def git(repo,*args):return subprocess.check_output(["git","-C",str(repo),*args])
def snapshot(repo,ref):
    commit=git(repo,"rev-parse",ref+"^{commit}").decode().strip()
    entries=git(repo,"ls-tree","-rz","--full-tree",commit).split(b"\0")
    records=[]
    for entry in entries:
        if not entry:continue
        meta,name=entry.split(b"\t",1);mode,kind,oid=meta.split()
        path=name.decode("ascii")
        if mode not in (b"100644",b"100755") or kind!=b"blob":raise ValueError("nonregular snapshot entry")
        data=git(repo,"cat-file","blob",oid.decode())
        records.append({"path":path,"size_bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()})
    records.sort(key=lambda x:x["path"].encode("utf-8"))
    xs=[leaf(x) for x in records]
    return {"schema":"sneak.git-snapshot.v1","snapshot_commit":commit,
      "scope":"ALL_REGULAR_TRACKED_FILES_AT_DECLARED_COMMIT","parent_breakpoint":"SNEAK-010",
      "construction":{"hash":"SHA-256","canonical":"ASCII JSON sorted keys ensure_ascii=true compact separators no newline",
      "ordering":"UTF-8 path ascending; ASCII paths required","leaf":"SHA256(0x00 || canonical(record))",
      "internal":"SHA256(0x01 || left || right)","odd":"promote unchanged"},
      "leaf_count":len(xs),"root":root(xs).hex(),
      "leaves":[{"record":r,"canonical_hex":canonical(r).hex(),"leaf":x.hex(),"proof":proof(xs,i)} for i,(r,x) in enumerate(zip(records,xs))],
      "exclusions":"Untracked/ignored assets and commits after snapshot_commit; this generated receipt is subsequent to its snapshot",
      "meaning":"Integrity only; not source truth, rights, security, signatures or canonical admission",
      "mmr":"NOT_COMMITTED","signed":False}
def check(repo,receipt):
    actual=snapshot(repo,receipt["snapshot_commit"])
    errors=[]
    for key in ("schema","snapshot_commit","construction","leaf_count","root","leaves"):
        if actual[key]!=receipt[key]:errors.append("snapshot mismatch: "+key)
    expected=bytes.fromhex(receipt["root"])
    for item in receipt["leaves"]:
        r=item["record"];candidate=repo/r["path"];p=candidate.resolve()
        if candidate.is_symlink():
            errors.append("symlink: "+r["path"]);continue
        if not p.is_relative_to(repo.resolve()):
            errors.append("traversal outside repository: "+r["path"]);continue
        if not verify(leaf(r),item["proof"],expected):errors.append("bad proof: "+r["path"])
        if not p.is_file() or p.is_symlink():errors.append("missing/nonregular: "+r["path"]);continue
        b=p.read_bytes()
        if len(b)!=r["size_bytes"] or hashlib.sha256(b).hexdigest()!=r["sha256"]:errors.append("working bytes differ: "+r["path"])
    return {"pass":not errors,"errors":errors,"root":receipt["root"],"leaf_count":receipt["leaf_count"],"snapshot_commit":receipt["snapshot_commit"]}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("action",choices=["create","verify"]);ap.add_argument("receipt");ap.add_argument("--ref",default="HEAD");args=ap.parse_args()
    repo=pathlib.Path(__file__).resolve().parents[1]
    if not re.fullmatch(r"receipts/(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_.-]+\.json",args.receipt):
        ap.error("receipt must be a JSON path under receipts/ without traversal")
    path=(repo/args.receipt).resolve()
    if not path.is_relative_to((repo/"receipts").resolve()):
        ap.error("receipt must resolve within receipts/")
    if args.action=="create":
        r=snapshot(repo,args.ref);path.parent.mkdir(parents=True,exist_ok=True)
        with path.open("x") as f:json.dump(r,f,indent=2);f.write("\n")
        print(json.dumps({"root":r["root"],"leaves":r["leaf_count"],"snapshot_commit":r["snapshot_commit"]}))
    else:
        result=check(repo,json.loads(path.read_text()));print(json.dumps(result));sys.exit(0 if result["pass"] else 1)
if __name__=="__main__":main()
