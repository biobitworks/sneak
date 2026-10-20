#!/usr/bin/env python3
"""Versioned Git snapshot integrity. Hash identity is not semantic truth."""
import argparse,hashlib,json,pathlib,re,subprocess,sys
SAFE_REL=re.compile(r"[\x20-\x7e]+")
COMMIT=re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
# Historic snapshot parent labels are frozen and bound to their exact snapshot commit.
LEGACY_MERGE_COMMIT="48e72e9b1a62371fc25f79180196b7fb87ae8da1"
def parent_breakpoint(commit):
    return "SNEAK-011-MERGE" if commit==LEGACY_MERGE_COMMIT else "SNEAK-010"
def safe_relpath(rel):
    """Reject absolute, parent/empty/dot segments, backslash and non-printable-ASCII paths."""
    if not isinstance(rel,str) or not SAFE_REL.fullmatch(rel) or "\\" in rel or rel.startswith("/"):raise ValueError("unsafe path encoding")
    if any(part in ("",".","..") for part in rel.split("/")):raise ValueError("unsafe path segment")
    return rel
def contained(repo,rel,must_exist=True):
    """Resolve rel under repo with no symlink in any component and no escape from repo."""
    base=pathlib.Path(repo).resolve();cur=base
    for part in safe_relpath(rel).split("/"):
        cur=cur/part
        if cur.is_symlink():raise ValueError("symlink in path")
        if not cur.exists():
            if must_exist:raise ValueError("missing path")
            break
    target=(base/rel).resolve(strict=must_exist)
    if target!=base/rel or base not in target.parents:raise ValueError("path escapes repository")
    return target
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
    receipt={"schema":"sneak.git-snapshot.v1","snapshot_commit":commit,
      "scope":"ALL_REGULAR_TRACKED_FILES_AT_DECLARED_COMMIT","parent_breakpoint":parent_breakpoint(commit),
      "construction":{"hash":"SHA-256","canonical":"ASCII JSON sorted keys ensure_ascii=true compact separators no newline",
      "ordering":"UTF-8 path ascending; ASCII paths required","leaf":"SHA256(0x00 || canonical(record))",
      "internal":"SHA256(0x01 || left || right)","odd":"promote unchanged"},
      "leaf_count":len(xs),"root":root(xs).hex(),
      "leaves":[{"record":r,"canonical_hex":canonical(r).hex(),"leaf":x.hex(),"proof":proof(xs,i)} for i,(r,x) in enumerate(zip(records,xs))],
      "exclusions":"Untracked/ignored assets and commits after snapshot_commit; this generated receipt is subsequent to its snapshot",
      "meaning":"Integrity only; not source truth, rights, security, signatures or canonical admission",
      "mmr":"NOT_COMMITTED","signed":False}
    if commit==LEGACY_MERGE_COMMIT:
        receipt.update(parent_root="dcabcb5db384588b701b70014546d0afada1dd35e3a8b1b844c75c0bcf53e403",
                       parent_snapshot_receipt="receipts/repository_bootstrap/SNAPSHOT.json")
    return receipt
def check(repo,receipt):
    if not isinstance(receipt.get("snapshot_commit"),str) or not COMMIT.fullmatch(receipt["snapshot_commit"]):
        return {"pass":False,"errors":["invalid snapshot_commit"],"root":receipt.get("root"),"leaf_count":receipt.get("leaf_count"),"snapshot_commit":None}
    actual=snapshot(repo,receipt["snapshot_commit"])
    errors=[]
    for key in sorted(set(actual) | set(receipt)):
        if actual.get(key)!=receipt.get(key):errors.append("snapshot mismatch: "+key)
    expected=bytes.fromhex(receipt["root"])
    for item in receipt["leaves"]:
        r=item["record"]
        try:safe_relpath(r["path"])
        except ValueError:errors.append("unsafe path rejected");continue
        if not verify(leaf(r),item["proof"],expected):errors.append("bad proof: "+r["path"])
        try:p=contained(repo,r["path"])
        except (ValueError,OSError):errors.append("missing/nonregular: "+r["path"]);continue
        if not p.is_file():errors.append("missing/nonregular: "+r["path"]);continue
        b=p.read_bytes()
        if len(b)!=r["size_bytes"] or hashlib.sha256(b).hexdigest()!=r["sha256"]:errors.append("working bytes differ: "+r["path"])
    return {"pass":not errors,"errors":errors,"root":receipt["root"],"leaf_count":receipt["leaf_count"],"snapshot_commit":receipt["snapshot_commit"]}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("action",choices=["create","verify"]);ap.add_argument("receipt");ap.add_argument("--ref",default="HEAD");args=ap.parse_args()
    repo=pathlib.Path(__file__).resolve().parents[1]
    if not re.fullmatch(r"receipts/(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_.-]+\.json",args.receipt):
        ap.error("receipt must be a JSON path under receipts/ without traversal")
    if args.ref.startswith("-"):ap.error("invalid --ref")
    try:path=contained(repo,args.receipt,must_exist=args.action=="verify")
    except (ValueError,OSError) as e:ap.error("receipt path rejected: "+str(e))
    if args.action=="create":
        r=snapshot(repo,args.ref);path.parent.mkdir(parents=True,exist_ok=True)
        with path.open("x") as f:json.dump(r,f,indent=2);f.write("\n")
        print(json.dumps({"root":r["root"],"leaves":r["leaf_count"],"snapshot_commit":r["snapshot_commit"]}))
    else:
        result=check(repo,json.loads(path.read_text()));print(json.dumps(result));sys.exit(0 if result["pass"] else 1)
if __name__=="__main__":main()
