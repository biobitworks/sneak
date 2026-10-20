"""Builds the product graph and audit views from committed receipts and local runs.

Nothing here invents observations: every node status comes from an AoK record,
the atom-status receipt, or an actual adapter receipt on disk. Missing inputs
surface as NOT_RUN / MISSING, never as success.
"""
from __future__ import annotations

import json
import pathlib

from . import LOCAL_RUNS, REPO_ROOT
from . import aok, snyk_adapter

RECEIPT_DIR = REPO_ROOT / "receipts" / "sneak_mvp"
AOK_PATH = RECEIPT_DIR / "AOK_MVP_20261020.json"
ATOM_STATUS_PATH = RECEIPT_DIR / "ATOM_STATUS_20261020.json"
COMPONENT_PATH = RECEIPT_DIR / "COMPONENT_SMOKE_20261020.json"


def _load(path: pathlib.Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def scan_summary() -> dict:
    r = snyk_adapter.latest_receipt()
    if r is None:
        return {"gate": "BLOCKED", "outcome": "NOT_RUN", "reason": "no scan receipt"}
    keys = ("gate", "outcome", "reason", "exit_code", "finding_count", "severity_counts",
            "snyk_cli_version", "mode", "started_at", "target", "_source")
    out = {k: r.get(k) for k in keys if k in r}
    out["gate"] = "PASS" if r.get("gate") == "PASS" else "BLOCKED"
    return out


def _cognee_actions() -> list:
    base = LOCAL_RUNS / "cognee"
    acts = []
    for name in ("demo_receipt.json", "probe_write.json", "probe_recall.json", "probe_control.json"):
        r = _load(base / name)
        if not isinstance(r, dict):
            continue
        acts.append({"at": r.get("at"), "actor": "cognee_adapter", "source": "local-run",
                     "action": f"cognee {r.get('op')}", "status": r.get("status"),
                     "detail": (r.get("decision") or {}).get("action") or r.get("payload_sha256")
                     or r.get("query_sha256") or r.get("exit_code")})
    return acts


def build_graph() -> dict:
    bundle = _load(AOK_PATH)
    atoms = _load(ATOM_STATUS_PATH) or {}
    atom_index = {a["id"]: a for a in atoms.get("atoms", [])}
    if bundle is None:
        return {"error": "AOK bundle missing", "integrity": {"pass": False, "errors": ["missing"]},
                "nodes": [], "edges": [], "scan": scan_summary(), "actions": []}
    integrity = aok.verify(bundle, REPO_ROOT)
    if not integrity["pass"]:
        return {"error": "AoK integrity failed", "integrity": integrity, "nodes": [], "edges": [],
                "scan": scan_summary(), "actions": []}
    ctx = bundle["bundle_context"]
    fco = ctx["fco"]
    nodes = [{"id": fco, "type": "fco", "label": "SNEAK project FCO", "status": "CONTEXT"}]
    edges = []
    actions = []
    for entry in bundle["leaves"]:
        r = entry["record"]
        src = r["source"]
        nodes.append({"id": r["id"], "type": r["kind"], "label": r["claim"]["text"], "status": r["status"],
                      "ceiling": r["claim"]["claim_ceiling"], "actor": r["context"]["actor"],
                      "source": {"path": src["path"], "sha256": src["sha256"]} if src else None,
                      "leaf": entry["leaf"]})
        edges.append({"from": fco, "to": r["id"], "rel": "contains"})
        if r["context"]["parent"]:
            edges.append({"from": r["context"]["parent"], "to": r["id"], "rel": "lineage"})
        for a in r["supports_atoms"]:
            if not any(n["id"] == a for n in nodes):
                st = atom_index.get(a, {}).get("observed_outcome", "NOT_TESTED")
                nodes.append({"id": a, "type": "atom", "label": atom_index.get(a, {}).get("requirement", a),
                              "status": st})
            edges.append({"from": r["id"], "to": a, "rel": "candidate_evidence_for"})
        actions.append({"at": None, "actor": r["context"]["actor"], "source": "aok",
                        "action": r["id"], "status": r["status"], "detail": r["claim"]["text"]})
    scan = scan_summary()
    nodes.append({"id": "SCAN-GATE", "type": "scan_gate", "label": f"Snyk gate: {scan['gate']}",
                  "status": scan["outcome"]})
    edges.append({"from": fco, "to": "SCAN-GATE", "rel": "gated_by"})
    if scan["outcome"] != "NOT_RUN":
        actions.append({"at": scan.get("started_at"), "actor": "snyk_adapter", "source": scan.get("_source"),
                        "action": "snyk scan", "status": scan["outcome"], "detail": scan.get("reason")})
    actions.extend(_cognee_actions())
    return {
        "project": ctx["project"], "fco": fco, "bundle_context": ctx,
        "aok": {"root": bundle["root"], "leaf_count": bundle["leaf_count"], "mmr": bundle["mmr"],
                "signed": bundle["signed"]},
        "integrity": integrity, "nodes": nodes, "edges": edges, "scan": scan, "actions": actions,
    }


def build_audit() -> dict:
    atoms = _load(ATOM_STATUS_PATH)
    comp = _load(COMPONENT_PATH)
    if atoms is None:
        return {"error": "atom status receipt missing", "entry_gate": False}
    mandatory = [a for a in atoms["atoms"] if a["level"] == "mandatory"]
    entry_gate = bool(mandatory) and all(a["verified"] is True for a in mandatory)
    return {
        "schema": atoms.get("schema"),
        "entry_gate": entry_gate,
        "mandatory_total": len(mandatory),
        "mandatory_verified": sum(1 for a in mandatory if a["verified"] is True),
        "atoms": atoms["atoms"],
        "integrations": atoms.get("integrations"),
        "component_smoke": comp,
        "scan": scan_summary(),
        "note": "Atoms only change through appended evidence-bound verdict successors.",
    }
