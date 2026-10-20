#!/usr/bin/env python3
"""Append notebook and observed Snyk security status to the existing SNEAK MMR.

An independently executed post-pilot successor. Do not rewrite the pilot receipt.
"""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sneak.fcg_registry import FCGRegistry

LEDGER = ROOT / "data/fcg/sneak-016-replay.jsonl"
NOTEBOOK = ROOT / "notebooks/12_lmev2_agent_model_security_diagnostic.ipynb"
SAST = Path("/tmp/sneak-83c-snyk.DgLsml/sast.json")
SECURITY = ROOT / "receipts/evaluations/LMEV2_20261020_SECURITY.json"
SUCCESSOR = ROOT / "receipts/evaluations/LMEV2_20261020_SECURITY_SUCCESSOR.json"
CANDIDATE_COMMIT = "83c70a5407ba4ee65940073e28ab42c8c6e5e37c"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def main():
    registry = FCGRegistry(LEDGER)
    prior = registry.verify()
    if prior["fco_count"] != 74 or prior["mmr_root"] != "713334f89e48d44ea64b00651dfc1cf577e9aaab1e4b1d7be71d310f3e033f20":
        raise RuntimeError("Unexpected MMR parent; refuse overwrite or ambiguous successor")
    raw = json.loads(SAST.read_text())
    findings = []
    for run in raw.get("runs", []):
        for issue in run.get("results", []):
            loc = (issue.get("locations") or [{}])[0].get("physicalLocation") or {}
            findings.append({
                "rule": issue.get("ruleId"), "severity": issue.get("level"),
                "path": (loc.get("artifactLocation") or {}).get("uri"),
                "line": (loc.get("region") or {}).get("startLine"),
            })
    if len(findings) != 5 or any(f["severity"] != "note" for f in findings):
        raise RuntimeError("Live Snyk result diverges from five-low expected receipt")
    security = {
        "schema": "sneak.lmev2.security.v1",
        "target_git_commit": CANDIDATE_COMMIT,
        "snyk_code_version": "1.1307.2",
        "snyk_code_exit": 1,
        "snyk_code_report_sha256": sha(SAST.read_bytes()),
        "findings": findings,
        "snyk_sca_exit": 2,
        "snyk_sca_error": "Empty first-party runtime requirements manifest; dev SCA requires snyk auth",
        "sca_coverage_accepted": False,
        "sast_coverage_accepted": True,
        "raw_score_from_sast_only": 9.5,
        "accepted_application_score": None,
        "bonus": "NOT_OBSERVED",
        "security_gate": "DENY",
        "policy": "javiergarza-snyk/app-security-score@6e1f27605fe278eed347b10dab6f39b3501f1486",
    }
    SECURITY.parent.mkdir(parents=True, exist_ok=True)
    SECURITY.write_text(json.dumps(security, sort_keys=True, indent=2) + "\n")
    rows = registry.rows()
    actor = rows[58]["fco_id"]
    notebook_sha = sha(NOTEBOOK.read_bytes())
    artifact = registry.append(
        kind="artifact", actor_fco=actor, parent_fco=rows[-1]["fco_id"],
        source_sha256=notebook_sha, state="EXECUTED",
        payload={"name": NOTEBOOK.name, "sha256": notebook_sha, "notebook_executed_cells": 5},
        context={"parent_pilot_root": prior["mmr_root"], "classification": "pilot_not_leaderboard"},
    )
    scan = registry.append(
        kind="scan", actor_fco=actor, parent_fco=artifact["fco_id"],
        source_sha256=sha(SECURITY.read_bytes()), state="OBSERVED",
        payload={"findings": len(findings), "all_low": True, "sast_exit": 1, "sca_exit": 2,
                 "sast_report_sha256": security["snyk_code_report_sha256"]},
        context={"candidate_commit": CANDIDATE_COMMIT},
    )
    score = registry.append(
        kind="score", actor_fco=actor, parent_fco=scan["fco_id"],
        source_sha256=sha(SECURITY.read_bytes()), state="NULL",
        payload={"raw_sast_only_score": 9.5, "accepted_application_score": None,
                 "coverage_accepted": False, "security_admission": "DENY"},
        context={"scorer": security["policy"]},
    )
    new = registry.verify()
    successor = {
        "schema": "sneak.lmev2.security-successor.v1", "parent_mmr": prior,
        "successor_mmr": new, "artifact_fco": artifact["fco_id"],
        "scan_fco": scan["fco_id"], "score_fco": score["fco_id"],
        "security_receipt_sha256": sha(SECURITY.read_bytes()),
        "notebook_sha256": notebook_sha, "predecessor_preserved": True,
    }
    SUCCESSOR.write_text(json.dumps(successor, sort_keys=True, indent=2) + "\n")
    print(json.dumps(successor, sort_keys=True))


if __name__ == "__main__":
    main()
