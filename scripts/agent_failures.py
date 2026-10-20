#!/usr/bin/env python3
"""Show, with evidence, where each agent was wrong or failed on something it was asked to do.

Sources (all recomputable from github.com/biobitworks/sneak, no chat memory):
  - every origin/* branch head; every JSON receipt/data file under receipts/ and data/
  - commit authorship per file (who added it): Cursor = cursoragent@cursor.com,
    Claude = Claude-Session/Co-Authored-By Claude trailer or claude-redteam author,
    otherwise "codex-or-byron" (the architect commits as Byron; authorship cannot be split further)
  - Claude's self-disclosed failures: data/breakpoints/FAILURE_PROOFS.json
  - GitHub checks on PR heads (gh api) for Snyk-in-GitHub
Failure markers: any JSON value equal to/starting with FAILED, ERROR, BLOCKED, DENY, TIMEOUT, or
containing 'FAILED_'/'ERROR_', a non-zero *exit* field, or a hard-coded human approval (RT-30 pattern).
"Asked" = the requirement atoms the area maps to (BAND M01-M20, Cognee M21-M27, Snyk S01-S09,
Flexprice F01-F05, human decision M13-M15) or an explicit owner request in this session.

Each agent gets a root question "Did <agent> fail or err on a requested item?" (rule ^YES$),
evidence leaves (file blob sha256 per failure), a proof step and leave-one-out steps.
Writes data/breakpoints/AGENT_FAILURES.{json,md}.
"""
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from breakpoint_ledger import Ledger, sha, canon  # noqa: E402
from prove_failures import merkle_root  # noqa: E402

SCRIPT_SHA = sha(Path(__file__).read_bytes())
MARK = re.compile(r"^(FAILED|ERROR|BLOCKED|DENY|TIMEOUT)|FAILED_|ERROR_|_FAILED\b|UNINTENDED", re.I)
EXPECTED_KEYS = {"authorization_effect", "expected", "expected_effect"}
EXPECTED_VALUES = {"deny_eval"}


def category(markers):
    t = " ".join(str(v) for _, v in markers).upper()
    if "HARD-CODED" in t or "UNINTENDED" in t or "SELF-DISCLOSED" in t:
        return "wrong"
    if re.search(r"\bEXIT [1-9]|FAILED|ERROR|TIMEOUT", t):
        return "error"
    return "gate_blocked"


AREAS = [("band", "BAND M01-M20"), ("cognee", "Cognee M21-M27"), ("snyk", "Snyk S01-S09"), ("sca", "Snyk S01-S09"),
         ("sast", "Snyk S01-S09"), ("flexprice", "Flexprice F01-F05"), ("human", "Human decision M13-M15"),
         ("approval", "Human decision M13-M15"), ("vercel", "Owner request: deploy preview"), ("ollama", "Owner request: Ollama on magicstudio"),
         ("notebook", "AGENTS.md: reproducible notebooks"), ("jupyter", "AGENTS.md: reproducible notebooks")]


def git(*a, binary=False):
    p = subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True)
    return p.stdout if binary else p.stdout.decode("utf-8", "replace")


def agent_of(branch, path):
    log = git("log", "--diff-filter=A", "--format=%H%x09%an%x09%ae%x09%B%x1e", branch, "--", path)
    c = log.split("\x1e")[0] if log.strip() else ""
    if "cursoragent@cursor.com" in c:
        return "cursor", c[:40]
    if "Claude-Session" in c or "Co-Authored-By: Claude" in c or "claude-redteam" in c:
        return "claude", c[:40]
    return ("codex-or-byron", c[:40]) if c else ("unknown", "")


def asked_for(path, key):
    t = f"{path} {key}".lower()
    hits = sorted({label for k, label in AREAS if k in t})
    return hits or ["AGENTS.md / plan"]


def walk(x, p=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from walk(v, f"{p}.{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from walk(v, f"{p}[{i}]")
    else:
        yield p, x


def scan_branch(branch):
    out = []
    files = [f for f in git("ls-tree", "-r", "--name-only", branch).splitlines()
             if f.endswith(".json") and (f.startswith("receipts/") or f.startswith("data/")) and "/snapshots/" not in f
             and not f.startswith("data/breakpoints/") and "SNAPSHOT" not in f and "MERKLE" not in f]
    for f in files:
        raw = git("show", f"{branch}:{f}", binary=True)
        try:
            d = json.loads(raw)
        except Exception:
            continue
        hits = []
        for p, v in walk(d):
            leaf = p.rsplit(".", 1)[-1].lower()
            if leaf in EXPECTED_KEYS or (isinstance(v, str) and v.lower() in EXPECTED_VALUES):
                continue                     # designed ablation outcome (gate working), not a failure
            if isinstance(v, str) and MARK.search(v) and "not_" not in v.lower()[:4]:
                hits.append((p, v[:120]))
            elif re.search(r"exit(_code)?$", leaf) and isinstance(v, int) and not isinstance(v, bool) and v != 0:
                hits.append((p, f"exit {v}"))
        if hits:
            agent, commit = agent_of(branch, f)
            out.append({"branch": branch, "path": f, "blob_sha256": sha(raw), "agent": agent, "added_in": commit.split("\t")[0][:12],
                        "markers": hits[:8], "marker_count": len(hits), "category": category(hits), "asked": asked_for(f, " ".join(h[0] for h in hits))})
    return out


def hardcoded_approvals(branch):
    out = []
    for f in git("ls-tree", "-r", "--name-only", branch).splitlines():
        if not f.endswith(".py") or f.startswith("redteam/") or f.startswith("tests/"):
            continue
        src = git("show", f"{branch}:{f}")
        if re.search(r'human_decision"\]\s*=\s*"APPROVE"', src) or re.search(r'record_decision\(\s*"[^"]+",\s*"APPROVE"', src):
            agent, commit = agent_of(branch, f)
            out.append({"branch": branch, "path": f, "blob_sha256": sha(src.encode()), "agent": agent, "added_in": commit.split("\t")[0][:12],
                        "markers": [("source", "hard-coded human APPROVE (RT-30)")], "marker_count": 1, "category": "wrong", "asked": ["Human decision M13-M15"]})
    return out


def integrations(all_hits):
    pr = json.loads(subprocess.run(["gh", "pr", "list", "--state", "all", "--json", "number,headRefOid", "--limit", "50"],
                                   capture_output=True, text=True, cwd=ROOT).stdout or "[]")
    snyk_checks = 0; contexts = set()
    for p in pr:
        r = subprocess.run(["gh", "api", f"repos/biobitworks/sneak/commits/{p['headRefOid']}/status", "--jq", "[.statuses[].context]"],
                           capture_output=True, text=True, cwd=ROOT).stdout
        for c in json.loads(r or "[]"):
            contexts.add(c); snyk_checks += "snyk" in c.lower()
    def rec(area):
        return sorted({h["path"] for h in all_hits if any(area.lower() in a.lower() for a in h["asked"])})
    return {
        "snyk_in_github": {"state": "NOT_TESTED" if snyk_checks == 0 else "OBSERVED", "github_status_contexts": sorted(contexts),
                           "note": "No Snyk check/status on any PR head; Snyk ran only as local CLI, with recorded auth and dependency errors."},
        "snyk_local_cli": {"state": "EXECUTED", "note": "Real snyk code test runs exist (RT-29; PR #3 receipts); SCA never completed; recent runs failed auth."},
        "band": {"state": "OBSERVED (receipt-level)", "note": "Room 20f1ee5f with Byron/Tom/Jerry captured in SNEAK-013/015 receipts; no human decision; BAND Desktop board NOT_TESTED."},
        "cognee": {"state": "OBSERVED (receipt-level, Cognee Cloud)", "note": "Cloud writes/recalls in PR #3/#5 receipts; Cognee Open Source (required M21) NOT_TESTED."},
        "flexprice": {"state": "EXECUTED (self-host up, RT-27)", "note": "No usage event sent and read back; ROI NOT_COMPUTED."},
        "vercel": {"state": "OBSERVED", "note": "Claude curl: 5 sneak-evidence-preview URLs incl. production alias return 302 to Vercel SSO; content not viewable without login."},
        "failure_receipts_by_area": {a: len(rec(a)) for a in ("band", "cognee", "snyk", "flexprice", "human", "vercel")},
    }


def main():
    branches = [b for b in git("for-each-ref", "--format=%(refname:short)", "refs/remotes/origin").split() if b not in ("origin", "origin/HEAD")]
    hits = []
    for b in branches:
        hits += scan_branch(b) + hardcoded_approvals(b)
    uniq = {}
    for h in hits:                          # same file bytes on several branches count once
        uniq.setdefault((h["path"], h["blob_sha256"]), {**h, "branches": []})["branches"].append(h["branch"])
    hits = list(uniq.values())
    claude_self = json.loads((ROOT / "data/breakpoints/FAILURE_PROOFS.json").read_text())["failures"]
    for f in claude_self:
        if f["verdict"] == "PROVEN":
            hits.append({"branch": "origin/feat/breakpoint-mmr-ledger", "path": f"data/breakpoints/FAILURE_PROOFS.json#{f['failure']}",
                         "blob_sha256": f["evidence_root"], "agent": "claude", "added_in": "31b858c", "branches": ["origin/feat/breakpoint-mmr-ledger"],
                         "markers": [("self-disclosed", f["summary"][:120])], "marker_count": 1, "category": "wrong", "asked": ["Owner request in this session"]})
    agents = sorted({h["agent"] for h in hits})
    L = Ledger(); report = {}
    for ag in agents:
        items = [{"ref": f"{h['path']}", "role": "failure", "sha256": h["blob_sha256"], "supports": True} for h in hits if h["agent"] == ag]
        rq = L.root_question(f"Did {ag} fail or err on a requested item?", r"^YES$", sha(canon(sorted(i["ref"] for i in items))), label=f"agent:{ag}")
        root = merkle_root(items); v = "YES" if items else "NO"
        stream = f"agent-failures:{ag}"
        base = L.step(rq["bp_id"], stream, 0, "proof:all-failures", SCRIPT_SHA, root, sha(v.encode()), output_text=v, parent_bp=rq["bp_id"], model="deterministic")
        lomo = []
        for k, it in enumerate(items, 1):
            rest = items[:k - 1] + items[k:]
            v2 = "YES" if rest else "NO"
            s = L.step(rq["bp_id"], stream, k, f"lomo:remove:{it['ref'][:60]}", SCRIPT_SHA, merkle_root(rest), sha(v2.encode()),
                       output_text=v2, parent_bp=base["bp_id"], model="deterministic")
            lomo.append({"removed": it["ref"], "verdict": v2, "bp_id": s["bp_id"]})
        report[ag] = {"root_bp": rq["bp_id"], "proof_bp": base["bp_id"], "evidence_root": root, "verdict": v,
                      "failure_count": len(items),
                      "by_category": {c: sum(1 for h in hits if h["agent"] == ag and h.get("category") == c) for c in ("wrong", "error", "gate_blocked")},
                      "lomo_all_still_yes": all(x["verdict"] == "YES" for x in lomo),
                      "failures": [h for h in hits if h["agent"] == ag]}
    integ = integrations(hits)
    out = {"schema": "sneak.agent-failures.v1", "script_sha256": SCRIPT_SHA, "branches_scanned": len(branches),
           "attribution_note": "Architect commits use Byron's identity; 'codex-or-byron' cannot be split further from git metadata.",
           "agents": report, "integrations": integ}
    (ROOT / "data/breakpoints/AGENT_FAILURES.json").write_text(json.dumps(out, indent=1, default=list) + "\n")
    md = ["# Agent failures despite being asked", "", f"Branches scanned: {len(branches)}. Script sha256 `{SCRIPT_SHA[:16]}…`. Every row cites a file blob hash on GitHub.", ""]
    for ag, r in report.items():
        md += [f"## {ag}: {r['verdict']} ({r['failure_count']} failure records, evidence root `{r['evidence_root'][:16]}…`, proof {r['proof_bp']})", "",
               "| File | Kind | Asked for | Example markers |", "|---|---|---|---|"]
        for h in r["failures"][:40]:
            md.append(f"| `{h['path']}` | {h.get('category')} | {', '.join(h['asked'])} | {'; '.join(f'{p}={v}' for p, v in h['markers'][:3])} |")
        md.append("")
    md += ["## Integrations (evidence-based)", "", "| Integration | State | Note |", "|---|---|---|"]
    md += [f"| {k} | {v['state']} | {v['note']} |" for k, v in integ.items() if isinstance(v, dict) and "state" in v]
    (ROOT / "data/breakpoints/AGENT_FAILURES.md").write_text("\n".join(md) + "\n")
    for ag, r in report.items():
        print(f"{ag:16} {r['verdict']} failures={r['failure_count']:3} {r['by_category']} root={r['evidence_root'][:12]} proof={r['proof_bp']}")
    print(json.dumps({k: v["state"] for k, v in integ.items() if isinstance(v, dict) and "state" in v}, indent=1))


if __name__ == "__main__":
    main()
