"""Deterministic, context-bound Archive-of-Knowledge (AoK) evidence bundle.

Schema sneak.aok.v1. A bundle is an ordered list of evidence records, each
binding (source bytes SHA-256, claim, context, status). A binary Merkle root is
computed over the ordered records with domain-separated hashing. MMR is NOT
implemented and is always reported as NOT_COMPUTED. Hash identity is integrity
only: it is not truth, authorization, a signature or acceptance.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re

from .sanitize import contains_secret

SCHEMA = "sneak.aok.v1"
DOMAIN_LEAF = b"sneak.aok.v1/leaf\x00"
DOMAIN_NODE = b"sneak.aok.v1/node\x00"
STATUSES = ("OBSERVED", "PROPOSED", "NOT_TESTED", "UNKNOWN")
KINDS = ("requirements_snapshot", "band_event_receipt", "verification_receipt",
         "custody_receipt", "scan_receipt", "memory_receipt", "human_decision", "planned_check")
RECORD_KEYS = {"id", "kind", "status", "claim", "context", "source", "supports_atoms"}
CLAIM_KEYS = {"text", "claim_ceiling"}
CONTEXT_KEYS = {"project", "actor", "parent", "observed_via"}
SOURCE_KEYS = {"path", "sha256", "size_bytes"}
ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9_\-]{1,63}$")
ATOM_RE = re.compile(r"^REQ-AOK-[A-Z][0-9]{2}$")
MAX_CLAIM = 600

CONSTRUCTION = {
    "hash": "SHA-256",
    "canonical": "UTF-8 JSON, recursively sorted keys, ensure_ascii=true, separators (',',':'), no newline",
    "ordering": "record id ascending (ASCII); duplicate ids rejected",
    "leaf": "SHA256('sneak.aok.v1/leaf' || 0x00 || canonical(record))",
    "internal": "SHA256('sneak.aok.v1/node' || 0x00 || left32 || right32)",
    "odd": "promote unchanged",
}


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"),
                      allow_nan=False).encode("ascii")


def leaf_hash(record: dict) -> bytes:
    return hashlib.sha256(DOMAIN_LEAF + canonical(record)).digest()


def node_hash(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(DOMAIN_NODE + left + right).digest()


def merkle_root(leaves: list) -> bytes:
    if not leaves:
        raise ValueError("empty evidence set")
    row = list(leaves)
    while len(row) > 1:
        row = [node_hash(row[i], row[i + 1]) if i + 1 < len(row) else row[i]
               for i in range(0, len(row), 2)]
    return row[0]


def _safe_rel(repo_root: pathlib.Path, rel: str) -> pathlib.Path:
    if not isinstance(rel, str) or not rel or rel.startswith("/") or "\\" in rel:
        raise ValueError(f"invalid source path: {rel!r}")
    if any(part in ("..", "") for part in rel.split("/")):
        raise ValueError(f"invalid source path: {rel!r}")
    p = (repo_root / rel).resolve()
    if repo_root.resolve() not in p.parents:
        raise ValueError(f"source path escapes repository: {rel!r}")
    if not p.is_file():
        raise ValueError(f"source file missing: {rel!r}")
    return p


def hash_source(repo_root: pathlib.Path, rel: str) -> dict:
    data = _safe_rel(repo_root, rel).read_bytes()
    return {"path": rel, "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)}


def validate_record(r: dict) -> None:
    """Explicit schema check. Raises ValueError on any violation."""
    if not isinstance(r, dict) or set(r) != RECORD_KEYS:
        raise ValueError(f"record keys must be exactly {sorted(RECORD_KEYS)}")
    if not isinstance(r["id"], str) or not ID_RE.match(r["id"]):
        raise ValueError(f"bad id {r.get('id')!r}")
    if r["kind"] not in KINDS:
        raise ValueError(f"{r['id']}: bad kind")
    if r["status"] not in STATUSES:
        raise ValueError(f"{r['id']}: bad status")
    c = r["claim"]
    if not isinstance(c, dict) or set(c) != CLAIM_KEYS or not all(isinstance(v, str) for v in c.values()):
        raise ValueError(f"{r['id']}: claim must be {sorted(CLAIM_KEYS)} strings")
    if len(c["text"]) > MAX_CLAIM:
        raise ValueError(f"{r['id']}: claim too long")
    x = r["context"]
    if not isinstance(x, dict) or set(x) != CONTEXT_KEYS:
        raise ValueError(f"{r['id']}: context must be {sorted(CONTEXT_KEYS)}")
    if x["parent"] is not None and not (isinstance(x["parent"], str) and ID_RE.match(x["parent"])):
        raise ValueError(f"{r['id']}: bad parent")
    if not all(isinstance(x[k], str) and x[k] for k in ("project", "actor", "observed_via")):
        raise ValueError(f"{r['id']}: incomplete context")
    if not isinstance(r["supports_atoms"], list) or not all(
            isinstance(a, str) and ATOM_RE.match(a) for a in r["supports_atoms"]):
        raise ValueError(f"{r['id']}: bad supports_atoms")
    s = r["source"]
    if s is None:
        if r["status"] == "OBSERVED":
            raise ValueError(f"{r['id']}: OBSERVED evidence requires source bytes")
    elif (not isinstance(s, dict) or set(s) != SOURCE_KEYS or
          not isinstance(s["path"], str) or not isinstance(s["size_bytes"], int) or s["size_bytes"] < 0 or
          not re.fullmatch(r"[0-9a-f]{64}", str(s["sha256"]))):
        raise ValueError(f"{r['id']}: bad source")
    if contains_secret(json.dumps(r)):
        raise ValueError(f"{r['id']}: secret-like content in record")


def build(spec: dict, repo_root: pathlib.Path) -> dict:
    """spec = {"bundle_context": {...}, "evidence": [record without source hashes]}."""
    if not isinstance(spec, dict) or not isinstance(spec.get("bundle_context"), dict) or not isinstance(spec.get("evidence"), list):
        raise ValueError("invalid AoK specification")
    records = []
    for item in spec["evidence"]:
        rec = dict(item)
        src = rec.pop("source_path", None)
        rec["source"] = hash_source(repo_root, src) if src else None
        validate_record(rec)
        records.append(rec)
    ids = [r["id"] for r in records]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate evidence id")
    known = set(ids)
    for r in records:
        if r["context"]["parent"] is not None and r["context"]["parent"] not in known:
            raise ValueError(f"{r['id']}: parent not in bundle")
    records.sort(key=lambda r: r["id"].encode("ascii"))
    leaves = [leaf_hash(r) for r in records]
    return {
        "schema": SCHEMA,
        "bundle_context": spec["bundle_context"],
        "construction": CONSTRUCTION,
        "leaf_count": len(leaves),
        "leaves": [{"record": r, "leaf": h.hex()} for r, h in zip(records, leaves)],
        "root": merkle_root(leaves).hex(),
        "mmr": "NOT_COMPUTED",
        "signed": False,
        "meaning": "Integrity of ordered evidence records and referenced source bytes only. "
                   "Not truth, acceptance, authorization, signature or canonical admission.",
    }


def verify(bundle: dict, repo_root: pathlib.Path) -> dict:
    """Independent recomputation. Fail closed: any anomaly -> pass False."""
    errors = []
    try:
        if bundle.get("schema") != SCHEMA:
            errors.append("schema mismatch")
        if not isinstance(bundle.get("bundle_context"), dict):
            errors.append("bundle context missing")
        if bundle.get("construction") != CONSTRUCTION:
            errors.append("construction mismatch")
        if bundle.get("mmr") != "NOT_COMPUTED":
            errors.append("unexpected MMR claim")
        if bundle.get("signed") is not False:
            errors.append("unexpected signing claim")
        leaves_in = bundle.get("leaves") or []
        recomputed, ids = [], []
        for i, entry in enumerate(leaves_in):
            rec = entry["record"]
            try:
                validate_record(rec)
            except ValueError as e:
                errors.append(f"leaf {i}: {e}")
                continue
            ids.append(rec["id"])
            h = leaf_hash(rec)
            recomputed.append(h)
            if entry.get("leaf") != h.hex():
                errors.append(f"leaf {i} ({rec['id']}): leaf hash mismatch")
            if rec["source"] is not None:
                try:
                    actual = hash_source(repo_root, rec["source"]["path"])
                    if actual != rec["source"]:
                        errors.append(f"{rec['id']}: source bytes changed")
                except ValueError as e:
                    errors.append(f"{rec['id']}: {e}")
        if ids != sorted(ids, key=lambda s: s.encode("ascii")) or len(set(ids)) != len(ids):
            errors.append("record ordering/duplicate violation")
        known = set(ids)
        for entry in leaves_in:
            parent = entry["record"]["context"]["parent"]
            if parent is not None and parent not in known:
                errors.append("parent not in bundle")
        if bundle.get("leaf_count") != len(leaves_in):
            errors.append("leaf_count mismatch")
        if not recomputed:
            errors.append("no valid leaves")
        elif merkle_root(recomputed).hex() != bundle.get("root"):
            errors.append("root mismatch")
    except (KeyError, TypeError, AttributeError) as e:
        errors.append(f"malformed bundle: {type(e).__name__}")
    return {"pass": not errors, "errors": errors}


def load_json(path: pathlib.Path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def dump_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=True, indent=1) + "\n"
