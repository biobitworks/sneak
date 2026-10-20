#!/usr/bin/env python3
"""Candidate intake Merkle construction, proofs and independent recomputation."""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
def digest(b): return hashlib.sha256(b).digest()
def canonical(x): return json.dumps(x,sort_keys=True,ensure_ascii=True,separators=(",",":")).encode("ascii")
def parent(a,b): return digest(b"\x01"+a+b)
def levels(leaves):
    result=[leaves]
    while len(result[-1])>1:
        xs=result[-1];result.append([parent(xs[i],xs[i+1]) if i+1<len(xs) else xs[i] for i in range(0,len(xs),2)])
    return result
def recursive_root(xs):
    if len(xs)==1:return xs[0]
    k=1<<(len(xs)-1).bit_length()-1
    return parent(recursive_root(xs[:k]),recursive_root(xs[k:]))
def proof_for(tree,index):
    proof=[]
    for level in tree[:-1]:
        if index%2: proof.append({"side":"left","hash":level[index-1].hex()})
        elif index+1<len(level):proof.append({"side":"right","hash":level[index+1].hex()})
        index//=2
    return proof
def verify(leaf,proof,root):
    try:
        value=leaf
        for step in proof:
            sibling=bytes.fromhex(step["hash"])
            if len(sibling)!=32 or step["side"] not in ("left","right"):return False
            value=parent(sibling,value) if step["side"]=="left" else parent(value,sibling)
        return value==root
    except (KeyError,ValueError,TypeError):return False
def inventory():
    ignored={".git",".secrets",".venv","__pycache__","local-runs","receipts"}
    records=[]
    for p in ROOT.rglob("*"):
        rel=p.relative_to(ROOT)
        if not p.is_file() or any(x in ignored for x in rel.parts) or rel.parts[:2]==("sources","app-security-score"):continue
        b=p.read_bytes();records.append({"path":rel.as_posix(),"size_bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()})
    return sorted(records,key=lambda r:r["path"].encode("utf-8"))
def compute():
    records=inventory()
    payloads=[canonical(x) for x in records]
    leaves=[digest(b"\x00"+x) for x in payloads]
    tree=levels(leaves);root=tree[-1][0]
    assert recursive_root(leaves)==root
    proofs=[proof_for(tree,i) for i in range(len(leaves))]
    checks={
      "iterative_equals_recursive":True,
      "all_inclusion_proofs_valid":all(verify(x,p,root) for x,p in zip(leaves,proofs)),
      "tampered_leaf_accepted":verify(digest(b"\x00"+payloads[0]+b"tamper"),proofs[0],root),
      "wrong_root_accepted":verify(leaves[0],proofs[0],bytes(32)),
      "leaf_removal_preserves_root":levels(leaves[1:])[-1][0]==root,
      "leaf_reorder_preserves_root":levels(list(reversed(leaves)))[-1][0]==root
    }
    assert checks["all_inclusion_proofs_valid"]
    assert not any(checks[k] for k in ("tampered_leaf_accepted","wrong_root_accepted","leaf_removal_preserves_root","leaf_reorder_preserves_root"))
    receipt={"schema":"skill-custody.intake-merkle.v1","breakpoint_id":"IP-20261020-006-MERKLE",
       "parent_turn":"IP-20261020-005","parent_root":"878ff2881af94b4b89d8fdc75cc09008b950901d72b407a0f6ee2b60fd21d4f2","project":"skill-custody-lab","scope":"CANDIDATE_INTAKE_ASSET_SNAPSHOT_NOT_CANONICAL",
       "construction":{"hash":"SHA-256","canonical_records":"ASCII JSON; sorted keys; ensure_ascii=True; separators comma/colon; no newline",
       "ordering":"UTF-8 path ascending","leaf":"SHA256(0x00 || canonical(asset-record))",
       "internal":"SHA256(0x01 || left-32-bytes || right-32-bytes)","odd":"promote unpaired node unchanged",
       "excludes":["receipts/**",".git/**",".secrets/**",".venv/**","__pycache__/**","local-runs/**","sources/app-security-score/**"]},
       "leaf_count":len(leaves),"root":root.hex(),"leaves":[{"record":r,"canonical_hex":p.hex(),"leaf":l.hex(),"proof":pr} for r,p,l,pr in zip(records,payloads,leaves,proofs)],
       "checks":checks,"project_mmr":"NOT_COMMITTED","signed":"NO","model_recomputation":"NOT_EXECUTED",
       "meaning":"Integrity of the declared asset snapshot; not truth, legal rights, causality, or application security."}
    target=ROOT/"receipts/INTAKE_MERKLE_R6.json";target.parent.mkdir(exist_ok=True)
    if target.exists():
        old=json.loads(target.read_text())
        if old["root"]!=receipt["root"]: raise RuntimeError("Existing breakpoint differs; create a successor, never overwrite.")
    target.write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps({"root":root.hex(),"leaves":len(leaves),"checks":checks}))
    return receipt
if __name__=="__main__":compute()
