#!/usr/bin/env python3
"""Mint and verify contribution FCOs (first-class objects) for Sneak.

A contribution FCO binds a teammate's committed work to a unique, recomputable ID.

Identity rule (fixes red-team RT-07): the ID hashes ONLY immutable fields:
schema, contributor, kind, title, requirement_ids, parent_fco_ids, source_commit
and the artifact records (path, size_bytes, sha256) read from Git at source_commit.
Timestamps, states and verdicts are NOT part of the identity. They live in separate
append-only status records keyed by fco_id, so recording a verdict never changes an ID.

  fco_sha256 = SHA256(canonical(identity))            canonical = ASCII JSON, sorted keys, compact
  fco_id     = "FCO-" + fco_sha256[:16]

Ledger: data/contributions/fco_ledger.jsonl (append-only, one JSON object per line).
Record kinds: {"record":"fco", ...} and {"record":"status", ...}.

Usage:
  python3 scripts/contribution_fco.py mint --contributor HANDLE --kind code \
      --title "..." --commit HEAD --path src/a.py --path tests/test_a.py \
      [--requirement REQ-AOK-M24] [--parent FCO-...]
  python3 scripts/contribution_fco.py status --fco FCO-... --state IMPLEMENTED \
      --actor HANDLE [--evidence receipts/x.json] [--note "..."]
  python3 scripts/contribution_fco.py verify
"""
import argparse, datetime, hashlib, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data/contributions/fco_ledger.jsonl"
SCHEMA = "sneak.contribution-fco.v1"
KINDS = {"code", "data", "doc", "test", "receipt", "finding", "notebook", "config"}
STATES = {"PROPOSED", "IMPLEMENTED", "EXECUTED", "OBSERVED", "SUPPORTED", "FAILED",
          "NEGATIVE", "NOT_TESTED", "UNKNOWN", "NOT_COMPUTED"}
HANDLE = re.compile(r"^[a-z0-9][a-z0-9-]{1,38}$")
SECRET = re.compile(r"(band_u_[A-Za-z0-9_]+|sk-ant-[A-Za-z0-9_-]+|sk_live_[A-Za-z0-9]+|ghp_[A-Za-z0-9]{20,}|"
                    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|SNYK_TOKEN\s*=\s*\S+)")


def canonical(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("ascii")


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def artifact(commit, path):
    if path.startswith("/") or ".." in Path(path).parts:
        raise SystemExit(f"artifact path must be repo-relative: {path}")
    try:
        data = git("show", f"{commit}:{path}")
    except subprocess.CalledProcessError:
        raise SystemExit(f"{path} is not committed at {commit}; commit it first")
    if SECRET.search(data.decode("utf-8", "ignore")):
        raise SystemExit(f"{path} looks like it contains a secret; refusing to mint")
    return {"path": path, "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def identity_of(rec):
    return {k: rec[k] for k in ("schema", "contributor", "kind", "title", "requirement_ids",
                                "parent_fco_ids", "source_commit", "artifacts")}


def fco_hash(identity):
    return hashlib.sha256(canonical(identity)).hexdigest()


def load():
    if not LEDGER.exists():
        return []
    return [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]


def append(rec):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a") as f:
        f.write(canonical(rec).decode() + "\n")


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def cmd_mint(a):
    if not HANDLE.match(a.contributor):
        raise SystemExit("contributor handle: lowercase letters, digits, hyphens (e.g. jane-doe)")
    if a.kind not in KINDS:
        raise SystemExit(f"kind must be one of {sorted(KINDS)}")
    commit = git("rev-parse", f"{a.commit}^{{commit}}").decode().strip()
    rows = load()
    known = {r["fco_id"] for r in rows if r["record"] == "fco"}
    for p in a.parent:
        if p not in known:
            raise SystemExit(f"parent {p} is not in the ledger")
    identity = {"schema": SCHEMA, "contributor": a.contributor, "kind": a.kind, "title": a.title.strip(),
                "requirement_ids": sorted(set(a.requirement)), "parent_fco_ids": sorted(set(a.parent)),
                "source_commit": commit,
                "artifacts": sorted((artifact(commit, p) for p in set(a.path)), key=lambda r: r["path"].encode())}
    if not identity["artifacts"]:
        raise SystemExit("at least one --path is required")
    h = fco_hash(identity)
    fid = "FCO-" + h[:16]
    if fid in known:
        raise SystemExit(f"{fid} already exists (identical contribution); nothing to mint")
    append({"record": "fco", "fco_id": fid, "fco_sha256": h, **identity, "minted_at": now()})
    append({"record": "status", "fco_id": fid, "state": "PROPOSED", "actor": a.contributor,
            "evidence": [], "note": "minted", "at": now()})
    print(json.dumps({"fco_id": fid, "fco_sha256": h, "artifacts": len(identity["artifacts"])}))


def cmd_status(a):
    if a.state not in STATES:
        raise SystemExit(f"state must be one of {sorted(STATES)}")
    if a.state == "SUPPORTED" and not a.evidence:
        raise SystemExit("SUPPORTED needs at least one --evidence path")
    if not HANDLE.match(a.actor):
        raise SystemExit("actor handle: lowercase letters, digits, hyphens")
    if a.fco not in {r["fco_id"] for r in load() if r["record"] == "fco"}:
        raise SystemExit(f"{a.fco} is not in the ledger")
    for e in a.evidence:
        if not (ROOT / e).is_file():
            raise SystemExit(f"evidence file not found: {e}")
    append({"record": "status", "fco_id": a.fco, "state": a.state, "actor": a.actor,
            "evidence": sorted(set(a.evidence)), "note": a.note or "", "at": now()})
    print(json.dumps({"fco_id": a.fco, "state": a.state}))


def cmd_verify(_):
    rows, errors, seen, latest = load(), [], set(), {}
    for n, r in enumerate(rows, 1):
        if r.get("record") == "fco":
            ident = identity_of(r)
            h = fco_hash(ident)
            if r["fco_sha256"] != h or r["fco_id"] != "FCO-" + h[:16]:
                errors.append(f"line {n}: {r['fco_id']} identity does not recompute")
            if r["fco_id"] in seen:
                errors.append(f"line {n}: duplicate {r['fco_id']}")
            for p in r["parent_fco_ids"]:
                if p not in seen:
                    errors.append(f"line {n}: parent {p} not defined earlier")
            for art in r["artifacts"]:
                try:
                    if artifact(r["source_commit"], art["path"]) != art:
                        errors.append(f"line {n}: {art['path']} bytes differ at {r['source_commit'][:12]}")
                except SystemExit as e:
                    errors.append(f"line {n}: {e}")
            seen.add(r["fco_id"])
        elif r.get("record") == "status":
            if r["fco_id"] not in seen:
                errors.append(f"line {n}: status for unknown {r['fco_id']}")
            if r["state"] not in STATES:
                errors.append(f"line {n}: bad state {r['state']}")
            if r["state"] == "SUPPORTED" and not r["evidence"]:
                errors.append(f"line {n}: SUPPORTED without evidence")
            latest[r["fco_id"]] = r["state"]
        else:
            errors.append(f"line {n}: unknown record type")
    print(json.dumps({"pass": not errors, "fco_count": len(seen), "latest_state": latest, "errors": errors}, indent=1))
    sys.exit(0 if not errors else 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("mint")
    m.add_argument("--contributor", required=True); m.add_argument("--kind", required=True)
    m.add_argument("--title", required=True); m.add_argument("--commit", default="HEAD")
    m.add_argument("--path", action="append", default=[]); m.add_argument("--requirement", action="append", default=[])
    m.add_argument("--parent", action="append", default=[])
    s = sub.add_parser("status")
    s.add_argument("--fco", required=True); s.add_argument("--state", required=True)
    s.add_argument("--actor", required=True); s.add_argument("--evidence", action="append", default=[])
    s.add_argument("--note")
    sub.add_parser("verify")
    a = ap.parse_args()
    {"mint": cmd_mint, "status": cmd_status, "verify": cmd_verify}[a.cmd](a)


if __name__ == "__main__":
    main()
