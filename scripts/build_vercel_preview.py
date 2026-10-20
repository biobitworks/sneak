#!/usr/bin/env python3
"""Export a read-only, redacted Vercel preview from independently checked SNEAK evidence.

A projection is NOT a new Merkle root, MMR admission, LOMO observation, or a live Cognee integration.
Only explicitly allowlisted fields are exported. No project secrets, raw scan reports or local paths.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess

from apps.sneak_mvp import APP_DIR, REPO_ROOT
from apps.sneak_mvp.graph import build_graph, build_audit
from apps.sneak_mvp.sanitize import assert_clean_json

BUILD = REPO_ROOT / "deploy" / "vercel-preview"
WEB = APP_DIR / "web"
STATIC_ASSETS = ("index.html", "audit.html", "app.js", "audit.js", "style.css")


def canonical(obj):
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("ascii")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def current_commit():
    return subprocess.check_output(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"], text=True
    ).strip()


def snapshot():
    g = build_graph()
    a = build_audit()
    if not g.get("integrity", {}).get("pass"):
        raise ValueError("evidence verification failed; refusing preview")
    if len(a.get("atoms", [])) == 0:
        raise ValueError("missing acceptance atoms")
    allowed_node = ("id", "type", "label", "status", "ceiling", "leaf")
    allowed_edge = ("from", "to", "rel")
    allowed_action = ("action", "status", "source")  # no actor names, messages or details
    scan = g["scan"]
    scan_commit = (scan.get("target") or {}).get("commit")
    commit = current_commit()
    summary_scan = {
        "gate": "BLOCKED",  # preview cannot authorize release or deploy
        "outcome": scan.get("outcome", "NOT_RUN"),
        "reason": scan.get("reason", "missing evidence"),
        "finding_count": scan.get("finding_count"),
        "severity_counts": scan.get("severity_counts"),
        "scanned_commit": scan_commit,
        "scan_covers_export_source": scan_commit == commit,
    }
    projected = {
        "project": "SNEAK — So Now Every Agent Knows",
        "fco": g["fco"],
        "aok": g["aok"],
        "integrity": {"pass": True, "source_record_verification": "EXECUTED"},
        "nodes": [{k: n[k] for k in allowed_node if k in n} for n in g["nodes"]],
        "edges": [{k: e[k] for k in allowed_edge if k in e} for e in g["edges"]],
        "actions": [{k: x[k] for k in allowed_action if k in x} for x in g["actions"][-12:]],
        "scan": summary_scan,
        "deployment": {
            "kind": "STATIC_READ_ONLY_PROJECTION",
            "source_commit": commit,
            "api_live": False,
            "band_live": False,
            "cognee_live": False,
            "lomo": "NOT_COMPUTED",
            "mmr": g["aok"].get("mmr", "NOT_COMPUTED"),
            "anticube": "NOT_COMPUTED",
            "delta_g_star": "NOT_COMPUTED",
            "approval": "NOT_OBSERVED",
        },
    }
    public_audit = {
        "schema": a.get("schema"),
        "entry_gate": False,
        "mandatory_total": a["mandatory_total"],
        "mandatory_verified": a["mandatory_verified"],
        "atoms": [
            {k: x[k] for k in ("id", "requirement", "verified", "observed_outcome")
             if k in x} for x in a["atoms"]
        ],
        "scan": summary_scan,
        "note": "Static custody projection, not live BAND/Cognee. All status updates require evidence-bound successors.",
    }
    if a["entry_gate"] or a["mandatory_verified"]:
        raise ValueError("acceptance statuses changed; re-review before export")
    assert_clean_json(projected)
    assert_clean_json(public_audit)
    return projected, public_audit


def generate(out: pathlib.Path = BUILD) -> dict:
    projected, audit = snapshot()
    out.mkdir(parents=True, exist_ok=True)
    (out / "static").mkdir(exist_ok=True)
    (out / "data").mkdir(exist_ok=True)
    mapping = {
        "index.html": "index.html",
        "audit.html": "audit.html",
        "app.js": "static/app.js",
        "audit.js": "static/audit.js",
        "style.css": "static/style.css",
    }
    digest = {}
    for src, dest in mapping.items():
        target = out / dest
        source = WEB / src
        payload = source.read_bytes()
        if src == "index.html":
            if b"LOCAL PREVIEW" not in payload:
                raise ValueError("source preview marker unexpectedly changed")
            payload = payload.replace(b"LOCAL PREVIEW", b"PROTECTED VERCEL SNAPSHOT")
        target.write_bytes(payload)
        digest[dest] = sha256(payload)
    data_files = {"data/graph.json": projected, "data/audit.json": audit}
    for path, obj in data_files.items():
        payload = canonical(obj)
        (out / path).write_bytes(payload)
        digest[path] = sha256(payload)
    config = {
        "$schema": "https://openapi.vercel.sh/vercel.json",
        "cleanUrls": True,
        "rewrites": [
            {"source": "/api/graph", "destination": "/data/graph.json"},
            {"source": "/api/audit", "destination": "/data/audit.json"},
        ],
        "headers": [{"source": "/(.*)", "headers": [
            {"key": "X-Content-Type-Options", "value": "nosniff"},
            {"key": "Referrer-Policy", "value": "no-referrer"},
            {"key": "X-Robots-Tag", "value": "noindex, nofollow, noarchive"},
            {"key": "Content-Security-Policy",
             "value": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'"},
        ]}],
    }
    # /audit resolves to audit.html via cleanUrls
    for path, raw in {
        "vercel.json": canonical(config),
        "robots.txt": b"User-agent: *\nDisallow: /\n",
    }.items():
        (out / path).write_bytes(raw)
        digest[path] = sha256(raw)
    manifest = {
        "schema": "sneak.vercel-preview-snapshot.v1",
        "source_commit": projected["deployment"]["source_commit"],
        "aok_candidate_root": projected["aok"]["root"],
        "aok_root_semantics": "Identity/integrity, not claim truth or export root",
        "outputs_sha256": digest,
        "deployment": "NOT_EXECUTED",
        "snyk_gate": "BLOCKED",
        "lomo": "NOT_COMPUTED",
        "mmr": "NOT_COMPUTED",
        "export_merkle_root": "NOT_COMPUTED",
        "signed": False,
    }
    (out / "EXPORT_MANIFEST.json").write_bytes(canonical(manifest))
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=pathlib.Path, default=BUILD)
    args = ap.parse_args()
    result = generate(args.out)
    print(json.dumps({"result": "PASS", "source_commit": result["source_commit"],
                      "files": len(result["outputs_sha256"]),
                      "root": result["aok_candidate_root"],
                      "lomo": result["lomo"], "mmr": result["mmr"]}, sort_keys=True))


if __name__ == "__main__":
    main()
