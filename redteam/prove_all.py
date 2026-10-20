#!/usr/bin/env python3
"""Prove every claim in Claude's Sneak lanes from fresh GitHub clones.

Run this on a machine other than the one that produced the work. Each check records the
command, exit code, expected and observed result. Nothing is trusted from the local tree:
every lane is cloned fresh from github.com/biobitworks/sneak at its branch head.

  python3 redteam/prove_all.py --out redteam/PROOF_SNEAK-RT-CLAUDE-003.json
"""
import argparse, json, os, platform, socket, subprocess, sys, tempfile, time
from pathlib import Path

REPO = "https://github.com/biobitworks/sneak"
PY = sys.executable

LANES = {
    "PR#4 redteam/claude-20261020": ("redteam/claude-20261020", [
        ("custody snapshot, Python", [PY, "scripts/custody_snapshot.py", "verify", "receipts/repository_bootstrap/SNAPSHOT.json"], 0, "dcabcb5d"),
        ("custody merged snapshot, Python", [PY, "scripts/custody_snapshot.py", "verify", "receipts/repository_bootstrap/SNAPSHOT_MERGED.json"], 0, "6fcec1a8"),
        ("custody snapshot, Node", ["node", "scripts/verify_custody_snapshot.mjs", "receipts/repository_bootstrap/SNAPSHOT.json"], 0, "dcabcb5d"),
        ("unit tests", [PY, "-m", "unittest", "discover", "-s", "tests"], 0, None),
        ("hashed BAND message SNEAK-RT-CLAUDE-002 recomputes", [PY, "redteam/band_message.py", "verify"], 0, "770900454dad61c3"),
        ("SNEAK-013 BAND event root recomputes", [PY, "redteam/verify_band_events.py", "origin/main"], 0, "29002d5e05b18b58"),
        ("requirements review regenerates byte-identically", ["sh", "-c", f"{PY} redteam/requirements_review.py >/dev/null && git diff --exit-code -- redteam/"], 0, None),
        ("findings file parses with valid states", [PY, "-c",
            "import json;S={'PROPOSED','IMPLEMENTED','EXECUTED','OBSERVED','SUPPORTED','FAILED','NEGATIVE','NOT_TESTED','UNKNOWN','NOT_COMPUTED'};"
            "R=[json.loads(l) for l in open('redteam/findings_SNEAK-013.jsonl')];bad=[r['id'] for r in R if r['state'] not in S];"
            "print(len(R),'findings; bad states',bad);raise SystemExit(1 if bad else 0)"], 0, "36 findings"),
    ]),
    "PR#6 onboarding/teammate-fco-handoff": ("onboarding/teammate-fco-handoff", [
        ("FCO ledger verifies", [PY, "scripts/contribution_fco.py", "verify"], 0, "FCO-8b904d2cf8f265d9"),
        ("unit tests", [PY, "-m", "unittest", "discover", "-s", "tests"], 0, None),
    ]),
    "PR#8 docs/merkle-mmr-knowledge-base": ("docs/merkle-mmr-knowledge-base", [
        ("FCO ledger verifies", [PY, "scripts/contribution_fco.py", "verify"], 0, "FCO-cb3b6ef299f35553"),
        ("MMR/Merkle identity tests", [PY, "-m", "unittest", "tests.test_mmr_reference"], 0, None),
        ("reference MMR example", [PY, "scripts/mmr_reference.py"], 0, "[6, 9, 10]"),
    ]),
    "PR#14 feat/breakpoint-mmr-ledger": ("feat/breakpoint-mmr-ledger", [
        ("breakpoint ledger verifies", [PY, "scripts/breakpoint_ledger.py", "verify"], 0, "13f9023d76f9c827"),
        ("FCO ledger verifies", [PY, "scripts/contribution_fco.py", "verify"], 0, "FCO-4f0478a0b1982b9a"),
        ("requirement status regenerates byte-identically", ["sh", "-c", f"{PY} scripts/verify_breakpoint_requirements.py >/dev/null && git diff --exit-code -- data/breakpoints/REQUIREMENTS_STATUS.json"], 0, None),
        ("unit tests", [PY, "-m", "unittest", "discover", "-s", "tests"], 0, None),
    ]),
}


def run(cmd, cwd):
    t = time.time()
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=600)
    return p.returncode, (p.stdout + p.stderr)[-1500:], round(time.time() - t, 2)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); a = ap.parse_args()
    env = {"host": socket.gethostname(), "platform": platform.platform(), "python": platform.python_version(),
           "node": subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip(),
           "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    results = []
    with tempfile.TemporaryDirectory(prefix="sneak-proof-") as tmp:
        for lane, (branch, checks) in LANES.items():
            d = Path(tmp) / branch.replace("/", "_")
            subprocess.run(["git", "clone", "-q", REPO, str(d)], check=True)
            subprocess.run(["git", "-C", str(d), "checkout", "-q", branch], check=True)
            head = subprocess.run(["git", "-C", str(d), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
            for name, cmd, exp_rc, needle in checks:
                rc, out, secs = run(cmd, d)
                ok = rc == exp_rc and (needle is None or needle in out)
                results.append({"lane": lane, "branch": branch, "head": head, "check": name,
                                 "command": " ".join(cmd) if cmd[0] != "sh" else cmd[2], "exit_code": rc,
                                 "expected": f"exit {exp_rc}" + (f" and output contains {needle!r}" if needle else ""),
                                 "observed_tail": out.strip().splitlines()[-1][:300] if out.strip() else "",
                                 "seconds": secs, "state": "SUPPORTED" if ok else "FAILED"})
                print(f"{'PASS' if ok else 'FAIL'} {lane} :: {name} (rc={rc}, {secs}s)", flush=True)
    summary = {"schema": "sneak.proof-of-work.v1", "id": "SNEAK-RT-CLAUDE-003", "env": env,
               "checks": len(results), "supported": sum(r["state"] == "SUPPORTED" for r in results),
               "failed": [f"{r['lane']} :: {r['check']}" for r in results if r["state"] == "FAILED"],
               "meaning": "SUPPORTED here means re-executed from a fresh clone on this host with the expected result; "
                          "it does not upgrade any BAND/Cognee/Snyk/Flexprice requirement.",
               "results": results}
    Path(a.out).write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps({k: summary[k] for k in ("checks", "supported", "failed")}, indent=1))
    sys.exit(0 if not summary["failed"] else 1)


if __name__ == "__main__":
    main()
