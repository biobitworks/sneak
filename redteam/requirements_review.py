#!/usr/bin/env python3
"""Red-team requirements review: current state of all 46 R5 atoms against real receipts.

States are this reviewer's assessment as of the timestamp in the output; they are
proposals for the architect, not verdict successors. Receipt-level means the reviewer
recomputed or read the receipt but did not independently query the provider.
"""
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "redteam"
AS_OF = "2026-10-20T22:00Z"
REVIEWER = "claude-redteam (Claude Opus 5.5) on magicSTUDIObox / magicPRObox"

E = {  # evidence references
    "S013": "receipts/band/SNEAK-013_HANDOFF.json (root 29002d5e…, recomputed RT-22)",
    "H01": "SNEAK-H01 request in BAND room 20f1ee5f…, human_response=null",
    "PR5": "PR #5 (merged to main a67be28) scripts/run_lomo_snyk_breakpoints.py hard-codes APPROVE (RT-30)",
    "DESK": "band-desktop process observed on magicPRObox (pid 64146)",
    "INT1": "PR #3 receipts/integration/SNEAK-20261020-INTEGRATION-001.json (Cognee Cloud add/cognify/search 200)",
    "S015": "PR #5 receipts/connectors/SNEAK-015_LIVE_BAND_COGNEE.json (3 recall hits)",
    "SAST": "Snyk Code 1.1307.2 scans of main 979a4f7, PR#4 3d7c9f0, PR#8 edf9cbe: 4 low (PT) each (RT-29)",
    "SCA": "PR #3 INTEGRATION-001..003: SCA exit 3 / exit 2, no report",
    "FP": "RT-27: Flexprice v2.17 running, no meter/plan/event",
    "JER": "RT-33: Jerry process runs ClaudeSDKAdapter; 'ChatGPT→Jerry' authorship UNKNOWN",
}

# id -> (state, evidence keys, note)
OVERRIDES = {
    "M01": ("OBSERVED", ["DESK"], "Desktop app runs; agents connect through band-sdk, not shown as Desktop-coordinated"),
    "M03": ("OBSERVED", ["S013"], "CORRECTED from SUPPORTED: only the captured record's hash was recomputed; BAND was not queried and no verdict successor exists. receipt-level"),
    "M04": ("OBSERVED", ["S013"], "CORRECTED from SUPPORTED: only the captured record's hash was recomputed; BAND was not queried and no verdict successor exists. receipt-level"),
    "M10": ("OBSERVED", ["S013"], "CORRECTED from SUPPORTED: only the captured record's hash was recomputed; BAND was not queried and no verdict successor exists. receipt-level"),
    "M11": ("OBSERVED", ["S013"], "CORRECTED from SUPPORTED: only the captured record's hash was recomputed; BAND was not queried and no verdict successor exists. receipt-level"),
    "M12": ("OBSERVED", ["S013"], "CORRECTED from SUPPORTED: only the captured record's hash was recomputed; BAND was not queried and no verdict successor exists. receipt-level; handoff initiated by an agent via API"),
    "M13": ("NOT_TESTED", ["H01", "PR5"], "request exists; no human response; PR #5 APPROVE is hard-coded, rejected"),
    "M14": ("NOT_TESTED", ["H01", "PR5"], "as M13"),
    "M15": ("NOT_TESTED", ["PR5"], "the only 'approval' on record is hard-coded, which is what M15 forbids"),
    "M21": ("NOT_TESTED", ["INT1"], "only Cognee Cloud exercised; rule requires Cognee Open Source"),
    "M24": ("OBSERVED", ["INT1", "S015"], "receipt-level writes on Cognee Cloud"),
    "M25": ("OBSERVED", ["INT1", "S015"], "receipt-level recall on Cognee Cloud"),
    "M26": ("NOT_TESTED", ["INT1"], "cross_agent_changed_behavior NOT_TESTED"),
    "M27": ("NOT_TESTED", ["INT1"], "no restart or cross-agent behaviour diff"),
    "E01": ("UNKNOWN", ["JER"], "both live BAND agents run Claude SDK; other-harness authorship unverified"),
    "S01": ("EXECUTED", ["SAST", "SCA"], "real Snyk Code scans ran; SCA never completed"),
    "S02": ("EXECUTED", ["SAST"], "scanned repository commits; no agent-built app yet"),
    "F01": ("NOT_TESTED", ["FP"], "no usage event sent and read back"),
    "F02": ("NOT_TESTED", ["FP"], "no pricing model configured"),
}


def canon(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()


def main():
    atoms = [json.loads(l) for l in (ROOT / "data/rules/atomic_acceptance_r5.jsonl").read_text().splitlines() if l.strip()]
    rows = []
    for a in atoms:
        short = a["id"].replace("REQ-AOK-", "")
        state, ev, note = OVERRIDES.get(short, ("NOT_TESTED", [], "no receipt found"))
        rows.append({"id": a["id"], "level": a["level"], "requirement": a["requirement"],
                     "fco_candidate_sha256": a["fco_candidate_sha256"], "reviewed_state": state,
                     "evidence": [E[k] for k in ev], "note": note})
    counts = {}
    for r in rows:
        counts.setdefault(r["level"], {}).setdefault(r["reviewed_state"], 0)
        counts[r["level"]][r["reviewed_state"]] += 1
    mandatory_supported = sum(1 for r in rows if r["level"] == "mandatory" and r["reviewed_state"] == "SUPPORTED")
    summary = {"schema": "sneak.redteam-requirements-review.v1", "as_of": AS_OF, "reviewer": REVIEWER,
               "atoms": len(rows), "counts_by_level_and_state": counts,
               "mandatory_supported": mandatory_supported, "mandatory_total": sum(1 for r in rows if r["level"] == "mandatory"),
               "entry_gate": False, "security_app_score": "NOT_COMPUTED",
               "note": "Proposed review states; not verdict successors. entry_gate stays FALSE until every mandatory atom is independently SUPPORTED."}
    summary["rows_sha256"] = hashlib.sha256(b"".join(canon(r) + b"\n" for r in rows)).hexdigest()
    (OUT / "requirements_review.jsonl").write_text("".join(canon(r).decode() + "\n" for r in rows))
    (OUT / "requirements_review_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    md = [f"# Requirements review ({AS_OF})", "", f"Reviewer: {REVIEWER}. Proposed states, not verdicts. "
          f"Mandatory SUPPORTED: **{mandatory_supported}/{summary['mandatory_total']}**. Entry gate: **FALSE**. "
          "Security app score: **NOT_COMPUTED**.", "",
          "| Atom | Level | Requirement | Reviewed state | Evidence / note |", "|---|---|---|---|---|"]
    for r in rows:
        ev = "; ".join(r["evidence"]) or "—"
        md.append(f"| {r['id'].replace('REQ-AOK-', '')} | {r['level']} | {r['requirement']} | {r['reviewed_state']} | {r['note']}. {ev} |")
    (OUT / "REQUIREMENTS_REVIEW.md").write_text("\n".join(md) + "\n")
    print(json.dumps({k: summary[k] for k in ("counts_by_level_and_state", "mandatory_supported", "mandatory_total", "rows_sha256")}, indent=1))


if __name__ == "__main__":
    main()
