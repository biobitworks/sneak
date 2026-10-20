#!/usr/bin/env python3
"""Independent check of receipts/band/SNEAK-013_HANDOFF.json (event Merkle) from git, no project imports."""
import hashlib, json, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ref = sys.argv[1] if len(sys.argv) > 1 else "origin/main"
rc = json.loads(subprocess.check_output(["git", "-C", str(REPO), "show", f"{ref}:receipts/band/SNEAK-013_HANDOFF.json"]))


def canon(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("ascii")


def H(b):
    return hashlib.sha256(b).digest()


events = [l["event"] for l in rc["leaves"]]
order_ok = [e["id"] for e in events] == sorted(e["id"] for e in events)
leaves = [H(b"\x00" + canon(e)) for e in events]
canon_ok = all(canon(e).hex() == l["canonical_hex"] for e, l in zip(events, rc["leaves"]))
leaf_ok = all(x.hex() == l["leaf"] for x, l in zip(leaves, rc["leaves"]))
lvl = leaves
while len(lvl) > 1:
    lvl = [H(b"\x01" + lvl[i] + lvl[i + 1]) if i + 1 < len(lvl) else lvl[i] for i in range(0, len(lvl), 2)]
root_ok = lvl[0].hex() == rc["root"]


def walk(v, steps):
    for s in steps:
        sib = bytes.fromhex(s["hash"])
        v = H(b"\x01" + sib + v) if s["side"] == "left" else H(b"\x01" + v + sib)
    return v


proof_ok = all(walk(x, l["proof"]).hex() == rc["root"] for x, l in zip(leaves, rc["leaves"]))
hr = next(e for e in events if e["kind"] == "human_request")["payload"]
print(json.dumps({"ref": ref, "root": rc["root"], "leaf_count": len(leaves), "ordering_ok": order_ok,
                  "canonical_ok": canon_ok, "leaves_ok": leaf_ok, "proofs_ok": proof_ok, "root_ok": root_ok,
                  "human_request_id": hr["id"], "human_response": hr["human_response"],
                  "human_decision": hr["human_decision"], "instruction_origin": hr["instruction_origin"],
                  "state": "SUPPORTED" if all([order_ok, canon_ok, leaf_ok, proof_ok, root_ok]) else "FAILED"}, indent=1))
