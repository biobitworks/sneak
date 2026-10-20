#!/usr/bin/env python3
"""Verify the breakpoint-pipeline requirements (BPR-*) stated by Byron on 2026-10-20.

Checks that can be computed from the ledger are computed; anything that needs a live provider
(BAND, Cognee, Flexprice, Snyk) is NOT_TESTED until a receipt exists. Writes
data/breakpoints/REQUIREMENTS_STATUS.{json,md}.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import breakpoint_ledger as B  # noqa: E402

D = ROOT / "data/breakpoints"


def lines(p):
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def main():
    v = B.verify()
    L = B.Ledger()
    rows = L.rows
    steps = [r for r in rows if r["identity"]["kind"] == "step"]
    roots = [r for r in rows if r["identity"]["kind"] == "root_question"]
    msgs = [r for r in rows if r["identity"]["kind"] == "message"]
    links = [r for r in rows if r["identity"]["kind"] == "link"]
    model_streams = sorted({r["stream"] for r in steps})
    bps = [r["identity"]["breakpoint"] for r in steps if r["identity"]["breakpoint"] is not None]
    deltas = {rq["bp_id"]: L.deltas(rq["bp_id"]) for rq in roots}
    turned = sorted({x["delta"] for d in deltas.values() for seq in d.values() for x in seq if "delta" in x})
    box = {k: lines(D / "outbox" / f"{k}.jsonl") for k in ("band", "cognee", "flexprice")}
    sent = {k: sum(1 for x in v_ if x.get("status") != "PENDING_SEND") for k, v_ in box.items()}
    # determinism: within-run replay (round 3 vs round 2) and cross-run evidence file
    rep = {}
    for r in steps:
        i = r["identity"]
        if i["step"] == "model_call" and i["round"] in (2, 3):
            rep.setdefault(r["stream"], {})[i["round"]] = i["output_sha256"]
    replay_ok = sum(1 for s in rep.values() if s.get(2) == s.get(3))
    xrun = json.loads((D / "runs/CROSS_RUN_DETERMINISM.json").read_text()) if (D / "runs/CROSS_RUN_DETERMINISM.json").exists() else None
    fco_links = [r for r in links if r["identity"]["target_type"] == "fco"]

    R = []
    def add(i, req, state, evidence, optional=False):
        R.append({"id": i, "requirement": req, "state": state, "evidence": evidence, "optional": optional})

    add("BPR-01", "Every conversation turn and step has a unique Merkle breakpoint",
        "EXECUTED" if v["pass"] else "FAILED",
        f"{v['entries']} entries, all ids unique and recomputed; this chat session recorded ({len(msgs)} messages). BAND conversations not yet captured")
    add("BPR-02", "A breakpoint can be TRUE or FALSE", "OBSERVED" if (True in bps and False in bps) else "NOT_TESTED",
        f"{bps.count(True)} TRUE, {bps.count(False)} FALSE step breakpoints")
    add("BPR-03", "Each model has its own MMR", "EXECUTED" if model_streams else "NOT_TESTED",
        "; ".join(f"{s} size {v['streams'][s]}" for s in model_streams))
    add("BPR-04", "Each model is compared to the root question",
        "EXECUTED" if steps and all(r["identity"]["root_bp"] in L.ids for r in steps) else "NOT_TESTED",
        f"{len(roots)} root question(s): " + ", ".join(r["bp_id"] for r in roots))
    add("BPR-05", "Delta over time for each model", "OBSERVED" if "TURNED_TRUE" in turned or "TURNED_FALSE" in turned else "EXECUTED",
        f"delta kinds seen: {turned}")
    add("BPR-06", "Input is hashed", "EXECUTED" if steps and all(B.HEX64.match(r["identity"]["input_sha256"]) for r in steps) else "NOT_TESTED",
        f"{len(steps)} steps with input_sha256")
    det_state = "SUPPORTED" if replay_ok == len(rep) and xrun and xrun["identical"] == xrun["total"] else ("FAILED" if xrun and xrun["identical"] < xrun["total"] else "EXECUTED")
    add("BPR-07", "Deterministic script steps", det_state,
        f"script_sha256 on every step; within-run replay {replay_ok}/{len(rep)} identical; cross-run "
        + (f"{xrun['identical']}/{xrun['total']} identical, differing: {xrun['differing']}" if xrun else "not recorded"))
    add("BPR-08", "Steps are FCO-style identities (hash of immutable fields)", "EXECUTED" if v["pass"] else "FAILED",
        "bp_sha256 = SHA256(canonical identity); verify recomputes all")
    add("BPR-09", "Output is hashed", "EXECUTED" if steps and all(B.HEX64.match(r["identity"]["output_sha256"]) for r in steps) else "NOT_TESTED",
        "output_sha256 on every step; breakpoint computed only when text matches hash")
    add("BPR-10", "Updates are hashed through FCO tracking", "EXECUTED" if fco_links else "IMPLEMENTED",
        f"{len(fco_links)} link(s) from breakpoints to contribution FCOs: " + ", ".join(r["identity"]["target_id"] for r in fco_links))
    add("BPR-11", "BAND is used to ask", "NOT_TESTED" if not sent["band"] else "EXECUTED",
        f"{len(box['band'])} question(s) queued, {sent['band']} sent (Claude not yet connected to BAND)")
    add("BPR-12", "BAND responses are recorded as breakpoints", "NOT_TESTED", "no BAND reply captured yet")
    add("BPR-13", "Cognee captures everything", "NOT_TESTED" if not sent["cognee"] else "EXECUTED",
        f"{len(box['cognee'])} memory item(s) queued, {sent['cognee']} sent (Cognee OSS not yet running)")
    add("BPR-14", "All agents are updated", "NOT_TESTED", "requires BAND delivery to every agent plus acknowledgements")
    add("BPR-15", "Planner is in the conversation and checked via BAND chat", "NOT_TESTED",
        "question to @planner queued as " + ", ".join(x["bp_id"] for x in box["band"]) if box["band"] else "no planner question queued")
    add("BPR-16", "Everything connects at the end (one project root)", "EXECUTED" if v["pass"] else "FAILED",
        f"global MMR root now {v['global_root']} over {v['entries']} entries; final project root NOT_COMPUTED until project end")
    add("BPR-17", "Each step is checked with Snyk", "NOT_TESTED", "branch-level Snyk Code scans exist (RT-29); per-step scanning not wired")
    add("BPR-18", "Flexprice analyses ROI per token", "NOT_TESTED",
        f"{len(box['flexprice'])} token event(s) queued, {sent['flexprice']} sent; ROI NOT_COMPUTED (value definition pending)")
    add("BPR-19", "Snyk API key set up from iPad and stored outside chat", "NOT_TESTED", "human action pending")
    add("BPR-20", "Claude, Cursor and the teammate each acknowledge in BAND by @mention", "NOT_TESTED",
        "Claude not connected; Cursor and teammate not seen in the room", optional=True)
    add("BPR-21", "Cognee OSS: raw upload vs SeedGraph LongMemEval comparison (30 questions)", "NOT_TESTED",
        "paused before setup; dataset sha256 d6f21ea9... verified", optional=True)

    summary = {"ledger_pass": v["pass"], "entries": v["entries"], "global_root": v["global_root"],
               "counts": {s: sum(1 for r in R if r["state"] == s) for s in sorted({r["state"] for r in R})}}
    (D / "REQUIREMENTS_STATUS.json").write_text(json.dumps({"summary": summary, "requirements": R}, indent=1) + "\n")
    md = ["# Breakpoint pipeline requirements status", "",
          f"Ledger verify: **{'PASS' if v['pass'] else 'FAIL'}**, {v['entries']} entries, global root `{v['global_root']}`.", "",
          "| ID | Requirement | State | Evidence |", "|---|---|---|---|"]
    md += [f"| {r['id']}{' (optional)' if r['optional'] else ''} | {r['requirement']} | {r['state']} | {r['evidence']} |" for r in R]
    (D / "REQUIREMENTS_STATUS.md").write_text("\n".join(md) + "\n")
    print(json.dumps(summary, indent=1))
    for r in R:
        print(f"{r['id']:7} {r['state']:11} {r['requirement']}")


if __name__ == "__main__":
    main()
