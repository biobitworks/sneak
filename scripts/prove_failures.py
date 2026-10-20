#!/usr/bin/env python3
"""Prove (or fail to prove) each failure Claude disclosed on 2026-10-20, as LOMO x Merkle breakpoints.

For every failure F:
  1. root_question  "Is failure F proven by evidence?"  answer rule ^PROVEN$
  2. evidence items, each hashed from a primary source (git object, GitHub API record, local file)
     and each with a role; the evidence set is a Merkle tree (Sneak custody construction)
  3. step 'proof'   input = evidence root, output = PROVEN / NOT_PROVEN (all roles present and supporting)
  4. LOMO steps     remove one evidence item at a time -> new root, new verdict (TRUE/FALSE breakpoint)
  5. links          failure -> the session request it happened under (graph traversal) and to findings/commits
A failure with no machine evidence is recorded as NOT_PROVEN, never asserted.

Local-only evidence (files on magicSTUDIObox) is committed as hashes only, never contents.
"""
import hashlib, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from breakpoint_ledger import Ledger, sha, canon  # noqa: E402

SCRIPT_SHA = sha(Path(__file__).read_bytes())
CONV = "claude-session-01XKcMH77EYJTVYe5TzHa8M5"
MY_BRANCHES = ["origin/redteam/claude-20261020", "origin/onboarding/teammate-fco-handoff",
               "origin/docs/merkle-mmr-knowledge-base", "origin/feat/breakpoint-mmr-ledger"]
MY_COMMENTS = [6302626402, 6302626823, 6302627424, 6302628146, 6302628620]


def git(*a):
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True).stdout


def item(ref, role, data: bytes, supports: bool, detail: str):
    return {"ref": ref, "role": role, "sha256": sha(data), "supports": bool(supports), "detail": detail}


def blob(rev, path):
    return subprocess.run(["git", "-C", str(ROOT), "show", f"{rev}:{path}"], capture_output=True).stdout


def local(path):
    p = Path(path)
    return p.read_bytes() if p.exists() else b""


def merkle_root(items):
    lvl = [hashlib.sha256(b"\x00" + canon({k: i[k] for k in ("ref", "role", "sha256", "supports")})).digest() for i in items]
    if not lvl:
        return "0" * 64
    while len(lvl) > 1:
        lvl = [hashlib.sha256(b"\x01" + lvl[i] + lvl[i + 1]).digest() if i + 1 < len(lvl) else lvl[i] for i in range(0, len(lvl), 2)]
    return lvl[0].hex()


# ---------------- evidence collectors (each returns items, required roles, parent request id) ----------------
def f1():
    return [], {"blocked-action-trace"}, "req-01", "Second Tom & Jerry registration attempt re-implemented a blocked action. Blocked actions leave no machine trace."


def f2():
    files = ["/tmp/rt/cognee_openapi.json", "/tmp/rt/cognee_health.json", "/tmp/rt/cognee__api_v1_datasets_.json"]
    its = [item(f"magicSTUDIObox:{f}", "cognee-response-on-disk", local(f), bool(local(f)), "file exists" if local(f) else "missing") for f in files]
    return its, {"cognee-response-on-disk"}, "req-02", "Cognee tenant API called with the pasted key from magicstudio before the owner confirmed key use."


def f3():
    old = blob("97f09049fcc1ccf5fccef45a5dfd6c2af5724abb", "redteam/requirements_review_summary.json")
    new = blob("origin/redteam/claude-20261020", "redteam/requirements_review_summary.json")
    msg = blob("origin/redteam/claude-20261020", "redteam/BAND_MESSAGE_SNEAK-RT-CLAUDE-002.txt")
    o = json.loads(old or b"{}").get("mandatory_supported"); n = json.loads(new or b"{}").get("mandatory_supported")
    return [item("97f0904:redteam/requirements_review_summary.json", "overstated-claim", old, o == 5, f"mandatory_supported={o}"),
            item("redteam/BAND_MESSAGE_SNEAK-RT-CLAUDE-002.txt", "claim-published", msg, b"SUPPORTED 5/30" in msg, "hashed message says SUPPORTED 5/30"),
            item("origin/redteam/claude-20261020:redteam/requirements_review_summary.json", "correction", new, n == 0, f"mandatory_supported={n}")], \
        {"overstated-claim", "claim-published", "correction"}, "req-06", "Marked M03/M04/M10-M12 SUPPORTED from a receipt-hash check only."


def f4():
    its = []
    for b in MY_BRANCHES:
        log = git("log", "--format=%H%x09%an%x09%ae%x09%G?%x09%B%x1e", f"origin/main..{b}")
        mine = [c for c in log.split("\x1e") if "Claude-Session: https://claude.ai/code/session_01XKcMH77EYJTVYe5TzHa8M5" in c or "Co-Authored-By: Claude" in c]
        as_byron = [c for c in mine if "\tByron P. Lee\tbyron@biobitworks.com\t" in c]
        unsigned = [c for c in mine if c.strip().split("\t")[3:4] == ["N"]]
        its.append(item(f"{b} commits", "authored-as-byron", "\n".join(c.split("\t")[0] for c in as_byron).encode(),
                        len(as_byron) > 0, f"{len(as_byron)}/{len(mine)} Claude commits authored as Byron; {len(unsigned)} unsigned"))
    return its, {"authored-as-byron"}, "req-02", "Claude's commits carry Byron's name and email, unsigned."


def f5():
    its = []
    for cid in MY_COMMENTS:
        raw = subprocess.run(["gh", "api", f"repos/biobitworks/sneak/issues/comments/{cid}"], capture_output=True).stdout
        try:
            d = json.loads(raw); login = d["user"]["login"]; footer = "Generated with [Claude Code]" in d["body"]
        except Exception:
            login, footer = None, False
        its.append(item(f"github:issuecomment-{cid}", "posted-from-user-account",
                        canon({"id": cid, "login": login, "claude_footer": footer}), login == "biobitworks" and footer,
                        f"author={login}; claude_footer={footer}"))
    return its, {"posted-from-user-account"}, "req-06", "Claude's GitHub comments were posted from the owner's account."


def f6():
    proof = blob("origin/redteam/claude-20261020", "redteam/PROOF_SNEAK-RT-CLAUDE-003.json")
    d = json.loads(proof or b"{}")
    script_log = git("log", "--format=%B", "-1", "origin/redteam/claude-20261020", "--", "redteam/prove_all.py")
    return [item("redteam/PROOF_SNEAK-RT-CLAUDE-003.json", "labelled-supported", proof, d.get("supported") == d.get("checks") == 17, f"{d.get('supported')}/{d.get('checks')} labelled SUPPORTED"),
            item("redteam/prove_all.py authoring commit", "same-author-wrote-checker", script_log.encode(), "Claude-Session" in script_log, "checker written in the same Claude session")], \
        {"labelled-supported", "same-author-wrote-checker"}, "req-06", "Proof-of-work labelled SUPPORTED though checker and checked work share one author."


def f7():
    return [], {"pre-commit-diff"}, "req-05", "Knowledge-base claim about proof sides encoding the index was wrong; fixed before the first commit, so no committed trace."


def f8():
    xr = blob("origin/feat/breakpoint-mmr-ledger", "data/breakpoints/runs/CROSS_RUN_DETERMINISM.json")
    x = json.loads(xr or b"{}")
    pre = blob("99b6195", "tests/test_contribution_fco.py")
    fp = local("/tmp/rt/fp_setup_attempt1_main-4bc124e.log")
    led = blob("origin/feat/breakpoint-mmr-ledger", "scripts/breakpoint_ledger.py")
    return [item("CROSS_RUN_DETERMINISM.json", "nondeterminism", xr, x.get("identical", 0) < x.get("total", 0), f"{x.get('identical')}/{x.get('total')} identical; {x.get('differing')}"),
            item("99b6195:tests/test_contribution_fco.py", "secret-check-hit-own-test", pre, bool(re.search(rb"band_u_\d", pre)), "literal fake key in committed test"),
            item("magicSTUDIObox:/tmp/rt/fp_setup_attempt1_main-4bc124e.log", "flexprice-attempt1-failed", fp, b"setup_rc=2" in fp, "setup_rc=2" if fp else "log missing"),
            item("scripts/breakpoint_ledger.py (fixed)", "ledger-bugs-fixed", led,
                 b'"stream": stream}   # stream is part of identity' in led and b"compare like with like" in led, "stream-in-identity and per-step delta fixes present")], \
        {"nondeterminism", "secret-check-hit-own-test", "flexprice-attempt1-failed", "ledger-bugs-fixed"}, "req-08", \
        "Engineering failures: cross-run nondeterminism, secret check hit own test, Flexprice attempt 1 failed, two ledger bugs."


def f9():
    other = git("ls-tree", "-r", "--name-only", "origin/main").splitlines()
    theirs = [p for p in other if "SNEAK-016" in p]
    mine = blob("origin/redteam/claude-20261020", "redteam/findings_SNEAK-013.jsonl")
    return [item("origin/main SNEAK-016 receipts", "other-agent-uses-id", "\n".join(theirs).encode(), bool(theirs), f"{len(theirs)} file(s)"),
            item("redteam/findings_SNEAK-013.jsonl", "claude-used-same-id", mine, b'"successor_id":"SNEAK-016-REDTEAM"' in mine, "SNEAK-016-REDTEAM used")], \
        {"other-agent-uses-id", "claude-used-same-id"}, "req-02", "Successor IDs collided with the architect's numbering twice."


FAILURES = [("F1", f1), ("F2", f2), ("F3", f3), ("F4", f4), ("F5", f5), ("F6", f6), ("F7", f7), ("F8", f8), ("F9", f9)]


def verdict(items, roles):
    present = {i["role"] for i in items if i["supports"]}
    return "PROVEN" if roles and roles <= present else "NOT_PROVEN"


def main():
    L = Ledger()
    req = {r["identity"]["source_id"]: r["bp_id"] for r in L.rows
           if r["identity"]["kind"] == "message" and r["identity"].get("conversation") == CONV}
    report = []
    for fid, fn in FAILURES:
        items, roles, req_id, summary = fn()
        parent = req.get(req_id)
        rq = L.root_question(f"Is failure {fid} proven by evidence? {summary}", r"^PROVEN$",
                             sha(canon(sorted(roles))), parent, label=f"failure:{fid}")
        stream = f"failure:{fid}"
        root = merkle_root(items)
        v = verdict(items, roles)
        base = L.step(rq["bp_id"], stream, 0, "proof:all-evidence", SCRIPT_SHA, root, sha(v.encode()),
                      output_text=v, parent_bp=rq["bp_id"], model="deterministic")
        lomo = []
        for k, removed in enumerate(items, 1):
            rest = items[:k - 1] + items[k:]
            r2, v2 = merkle_root(rest), verdict(rest, roles)
            s = L.step(rq["bp_id"], stream, k, f"lomo:remove:{removed['role']}:{removed['ref'][:48]}", SCRIPT_SHA, r2,
                       sha(v2.encode()), output_text=v2, parent_bp=base["bp_id"], model="deterministic")
            lomo.append({"removed": removed["ref"], "role": removed["role"], "root": r2[:16],
                         "verdict": v2, "breakpoint": s["identity"]["breakpoint"], "bp_id": s["bp_id"]})
        report.append({"failure": fid, "summary": summary, "root_bp": rq["bp_id"], "parent_request_bp": parent,
                       "evidence_root": root, "verdict": v, "proof_bp": base["bp_id"],
                       "evidence": items, "lomo": lomo,
                       "path_to_conversation": [base["bp_id"], rq["bp_id"]] + ([parent] if parent else [])})
    out = ROOT / "data/breakpoints/FAILURE_PROOFS.json"
    out.write_text(json.dumps({"schema": "sneak.failure-proofs.v1", "script_sha256": SCRIPT_SHA, "failures": report}, indent=1) + "\n")
    for r in report:
        dep = [f"{x['role']}->{x['verdict']}" for x in r["lomo"]]
        print(f"{r['failure']} {r['verdict']:10} root={r['evidence_root'][:12]} bp={r['proof_bp']} lomo={dep}")


if __name__ == "__main__":
    main()
