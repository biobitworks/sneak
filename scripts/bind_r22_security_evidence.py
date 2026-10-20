#!/usr/bin/env python3
"""Freeze the actual Snyk post-hardening result as an append-only FCO successor."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sneak.fcg_registry import FCGRegistry
from sneak.merkle import canonical

PINNED = "97d1a7b3093dd0348a6bc8858604e8e1ab305c19"
PREDECESSOR = "e214642bb3e8153c8a2a16a0b63444e6534afb95cc0c5853e808948df9903e78"
LEDGER = ROOT / "data/fcg/sneak-016-replay.jsonl"
OUTPUT = ROOT / "receipts/connectors/SNEAK-022_SECURITY_REVIEW.json"


def load_scan(name: str):
    p = ROOT / "local-runs" / name / "sast.json"
    content = p.read_bytes()
    report = json.loads(content)
    findings = [
        {"level": row.get("level", "unknown"), "rule": row.get("ruleId")}
        for run in report.get("runs", [])
        for row in run.get("results", [])
    ]
    return findings, hashlib.sha256(content).hexdigest()


def main():
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    assert actual == PINNED
    assert not OUTPUT.exists()
    registry = FCGRegistry(LEDGER)
    previous = registry.verify()
    assert previous["mmr_root"] == PREDECESSOR and previous["fco_count"] == 94

    baseline, baseline_sha = load_scan("security-r16")
    successor, successor_sha = load_scan("security-r20")
    sca_bytes = (ROOT / "local-runs/security-r20/sca.json").read_bytes()
    sca_sha = hashlib.sha256(sca_bytes).hexdigest()
    sca_report = json.loads(sca_bytes)
    assert len(baseline) == 7 and len(successor) == 5
    assert all(x["level"] == "note" for x in successor)
    assert sca_report.get("ok") is False and sca_report.get("error")
    assert sca_sha == "4e840e75217fe925534c93c6097f1ec22ac713db47701548ab036a7c4fd2df16"

    statement = {
        "schema": "sneak.security-rescan-evidence.v1",
        "code_commit": PINNED,
        "baseline_code_commit": "5660be64d2cd94fd1488b0961bc6685a0fb8b2cf",
        "scanner": "Snyk CLI 1.1307.2",
        "sast": {"status": "EXECUTED_FINDINGS", "exit_code": 1, "count": len(successor),
                 "severity_levels": {"note": len(successor), "warning": 0},
                 "raw_report_sha256": successor_sha,
                 "reported_findings": successor},
        "baseline_sast": {"count": len(baseline), "raw_report_sha256": baseline_sha},
        "delta": {"metric": "SAST finding count", "from": len(baseline),
                  "to": len(successor), "delta": len(successor) - len(baseline),
                  "meaning": "scan outputs; not independently confirmed risk reduction"},
        "sca": {"status": "FAILED", "exit_code": 2,
                "raw_report_sha256": sca_sha,
                "error_class": "unable_to_resolve_empty_manifest"},
        "javier": {"source": "javiergarza-snyk/app-security-score",
                   "formula_pin": "6e1f27605fe278eed347b10dab6f39b3501f1486",
                   "application_score": None, "reason": "SCA incomplete; SAST findings"},
        "classification": {"gate": "DENY", "bonus_awarded": "NOT_VERIFIED"},
    }
    blob = canonical(statement)
    digest = hashlib.sha256(blob).hexdigest()
    actor = registry.rows()[0]["fco_id"]
    model = registry.rows()[2]["fco_id"]
    predecessor = registry.rows()[-1]["fco_id"]

    def append(kind, payload, parent, state, edges=None):
        row = registry.append(
            kind=kind, actor_fco=actor, model_fco=model, parent_fco=parent,
            payload=payload, state=state, source_sha256=digest,
            edges=edges or [],
            context={"schema": "sneak.security-rescan-evidence.v1", "evidence_sha256": digest,
                     "source_commit": PINNED, "source_report_bytes": "local-runs/security-r20"},
        )
        return row["fco_id"]

    artifact = append("artifact", {"code_commit": PINNED}, predecessor, "OBSERVED")
    sast = append("scan", statement["sast"], artifact, "OBSERVED")
    value = append("value", {"metric": "SAST finding count", "value": 5, "unit": "findings"}, sast, "OBSERVED")
    delta = append("delta", statement["delta"], value, "OBSERVED")
    sca = append("scan", statement["sca"], delta, "FAILED")
    score = append("score", statement["javier"], sca, "NULL")
    classification = append("classification", statement["classification"], score, "EXECUTED")
    result = {
        "statement": statement, "statement_sha256": digest,
        "parent_mmr": previous, "successor_mmr": registry.verify(),
        "classification_fco": classification,
        "last_inclusion_verified": registry.inclusion_proof(classification)["verified"],
        "notes": ["Raw Snyk reports are retained locally; Git contains their report digests and bounded findings only.",
                  "A reported path traversal is not independently validated exploitability.",
                  "No application security score is accepted because SCA coverage failed."],
    }
    OUTPUT.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"id": "SNEAK-022", "sast_findings": 5, "sca": "FAILED",
                      "application_score": None, "source_sha256": digest,
                      "mmr": result["successor_mmr"]}, indent=2))


if __name__ == "__main__":
    main()
