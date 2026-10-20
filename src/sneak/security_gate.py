"""Fail-closed interpretation of actual Snyk execution receipts, not a vendor score."""
from __future__ import annotations
import json

def summarize_sast(sarif):
    if not isinstance(sarif, dict) or not isinstance(sarif.get("runs"), list) or not sarif["runs"]:
        raise ValueError("Missing SARIF runs")
    findings = []
    for run in sarif["runs"]:
        if not isinstance(run.get("results"), list):
            raise ValueError("Incomplete SARIF results")
        for hit in run["results"]:
            location = (hit.get("locations") or [{}])[0].get("physicalLocation", {})
            findings.append({"rule_id":hit.get("ruleId", "UNKNOWN"),
                             "level":hit.get("level", "UNKNOWN"),
                             "path":location.get("artifactLocation", {}).get("uri", "UNKNOWN")})
    return {"finding_count":len(findings),"findings":findings}

def gate(sast_exit, sca_exit, sarif=None, coverage_required=("sast","sca")):
    if sast_exit not in (0,1) or sca_exit not in (0,1):
        return {"decision":"DENY","reason":"SCAN_ERROR_OR_UNSUPPORTED","score":"NOT_COMPUTED"}
    if "sast" in coverage_required and sarif is None:
        return {"decision":"DENY","reason":"SAST_REPORT_MISSING","score":"NOT_COMPUTED"}
    n = summarize_sast(sarif)["finding_count"] if sarif else 0
    if sast_exit == 1 or sca_exit == 1 or n:
        return {"decision":"DENY","reason":"UNRESOLVED_FINDINGS","score":"NOT_COMPUTED"}
    return {"decision":"PENDING","reason":"OTHER_GATES_NOT_VERIFIED","score":"NOT_COMPUTED"}

if __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("sarif"); parser.add_argument("--sast-exit",type=int,required=True)
    parser.add_argument("--sca-exit",type=int,required=True)
    a=parser.parse_args()
    sarif=json.load(open(a.sarif,encoding="utf-8"))
    print(json.dumps({"scan":summarize_sast(sarif),
                      "gate":gate(a.sast_exit,a.sca_exit,sarif)},indent=2))
