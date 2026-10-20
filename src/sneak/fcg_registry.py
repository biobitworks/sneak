"""Append-only FCO/FCG event registry with position-committed MMR custody.

An FCO identifies one contextual occurrence, NOT scientific or security truth.
MMR size is node count (not number of leaves). Existing receipts remain immutable.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .merkle import canonical
from .mmr_reference import MMR, mmr_verify

SCHEMA = "sneak.fcg-occurrence.v1"
KINDS = frozenset({
    "actor", "agent", "agent_spawn", "model", "source", "value", "delta",
    "classification", "decision", "transformation", "tool", "scan",
    "score", "lomo", "breakpoint", "handoff", "memory", "artifact",
})
STATES = frozenset({
    "PROPOSED", "IMPLEMENTED", "EXECUTED", "OBSERVED", "SUPPORTED",
    "FAILED", "NULL", "NEGATIVE", "DEFERRED", "NOT_TESTED",
    "UNKNOWN", "NOT_COMPUTED",
})
RELATIONS = frozenset({
    "derived_from", "acted_by", "inferred_by", "classifies", "measures",
    "transforms", "ablates", "evaluates", "spawned_by", "precedes",
    "communicates", "scanned_by", "references",
})
SECRET_NAMES = ("api_key", "password", "private_key", "credential", "bearer", "auth_token")
HEX = set("0123456789abcdef")


def _validate_no_secrets(value: Any) -> None:
    if isinstance(value, dict):
        for k, v in value.items():
            if any(secret in str(k).lower() for secret in SECRET_NAMES):
                raise ValueError("credential-bearing metadata forbidden in FCO ledger")
            _validate_no_secrets(v)
    elif isinstance(value, list):
        for v in value:
            _validate_no_secrets(v)
    elif isinstance(value, str):
        if "-----BEGIN " in value and "PRIVATE KEY-----" in value:
            raise ValueError("private key forbidden in FCO ledger")


def _digest(source_sha256: str) -> bool:
    return len(source_sha256) == 64 and all(c in HEX for c in source_sha256)


def _refs(identity: dict[str, Any], seen: set[str]) -> None:
    kind = identity["kind"]
    actor = identity["actor_fco"]
    model = identity["model_fco"]
    precursor = identity["parent_fco"]
    if actor == "NOT_APPLICABLE" and kind != "actor":
        raise ValueError("non-actor FCO must reference registered actor FCO")
    if actor != "NOT_APPLICABLE" and actor not in seen:
        raise ValueError("actor FCO reference not registered")
    if kind == "agent_spawn" and model in ("NOT_APPLICABLE", "UNKNOWN"):
        raise ValueError("spawned agent must reference a registered model FCO")
    if model not in ("NOT_APPLICABLE", "UNKNOWN") and model not in seen:
        raise ValueError("model FCO reference not registered")
    if precursor is not None and precursor not in seen:
        raise ValueError("predecessor FCO is not registered")
    for edge in identity["edges"]:
        if not isinstance(edge, dict) or set(edge) != {"relation", "to"}:
            raise ValueError("invalid typed edge")
        if edge["relation"] not in RELATIONS or edge["to"] not in seen:
            raise ValueError("unregistered or unsupported edge")


def verify_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    mmr = MMR()
    seen: set[str] = set()
    prev_root = None
    for i, row in enumerate(rows):
        ident = row["identity"]
        if ident["schema"] != SCHEMA or ident["ordinal"] != i:
            raise ValueError(f"entry {i}: schema or occurrence order mismatch")
        if ident["kind"] not in KINDS or ident["state"] not in STATES:
            raise ValueError(f"entry {i}: unsupported kind or epistemic state")
        if ident["predecessor_mmr_root"] != prev_root:
            raise ValueError(f"entry {i}: predecessor MMR root mismatch")
        if not _digest(ident["source_sha256"]) and ident["source_sha256"] != "UNKNOWN":
            raise ValueError(f"entry {i}: invalid source digest")
        if ident["state"] in ("OBSERVED", "SUPPORTED", "EXECUTED") and not _digest(ident["source_sha256"]):
            raise ValueError(f"entry {i}: observed claim requires hashed evidence")
        _validate_no_secrets(ident)
        _refs(ident, seen)
        raw = canonical(ident)
        digest = hashlib.sha256(raw).hexdigest()
        fid = "FCO-" + digest
        if fid in seen or row["fco_id"] != fid or row["identity_sha256"] != digest:
            raise ValueError(f"entry {i}: duplicate or false FCO identity")
        leaf_pos = mmr.append(raw)
        prev_root = mmr.root().hex()
        if (row["leaf_position"] != leaf_pos or row["mmr_size"] != mmr.size
                or row["mmr_leaf_count"] != i + 1 or row["mmr_root"] != prev_root):
            raise ValueError(f"entry {i}: invalid MMR append or root")
        seen.add(fid)
    return {
        "verified": True, "fco_count": len(rows), "mmr_size": mmr.size,
        "mmr_root": prev_root, "fcg_edges": sum(len(r["identity"]["edges"]) + bool(r["identity"]["parent_fco"]) for r in rows),
    }


class FCGRegistry:
    def __init__(self, path: Path):
        self.path = Path(path)

    def rows(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text().splitlines() if line.strip()]

    def verify(self) -> dict[str, Any]:
        return verify_rows(self.rows())

    def append(
        self, *, kind: str, payload: dict[str, Any], actor_fco: str = "NOT_APPLICABLE",
        model_fco: str = "NOT_APPLICABLE", parent_fco: str | None = None,
        edges: list[dict[str, str]] | None = None, state: str = "PROPOSED",
        source_sha256: str = "UNKNOWN", context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if kind not in KINDS or state not in STATES:
            raise ValueError("invalid FCO kind or epistemic state")
        if not isinstance(payload, dict) or not isinstance(context or {}, dict):
            raise ValueError("payload and context must be objects")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Lock across processes; re-verify the full predecessor while locked.
        with self.path.open("a+", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                f.seek(0)
                rows = [json.loads(line) for line in f if line.strip()]
                previous = verify_rows(rows)
                known = {row["fco_id"] for row in rows}
                identity = {
                    "schema": SCHEMA, "ordinal": len(rows), "kind": kind,
                    "state": state, "payload": payload, "context": context or {},
                    "actor_fco": actor_fco, "model_fco": model_fco,
                    "parent_fco": parent_fco, "edges": edges or [],
                    "source_sha256": source_sha256,
                    "predecessor_mmr_root": previous["mmr_root"],
                }
                _validate_no_secrets(identity)
                _refs(identity, known)
                if state in ("OBSERVED", "SUPPORTED", "EXECUTED") and not _digest(source_sha256):
                    raise ValueError("executed/observed event must cite real hashed source bytes")
                if not _digest(source_sha256) and source_sha256 != "UNKNOWN":
                    raise ValueError("source_sha256 must be real SHA-256 or UNKNOWN")
                raw = canonical(identity)
                h = hashlib.sha256(raw).hexdigest()
                mmr = MMR()
                for row in rows:
                    mmr.append(canonical(row["identity"]))
                leaf_pos = mmr.append(raw)
                row = {
                    "identity": identity, "fco_id": "FCO-" + h, "identity_sha256": h,
                    "leaf_position": leaf_pos, "mmr_size": mmr.size,
                    "mmr_leaf_count": len(rows) + 1, "mmr_root": mmr.root().hex(),
                }
                f.write(canonical(row).decode("ascii") + "\n")
                f.flush()
                os.fsync(f.fileno())
                return row
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def inclusion_proof(self, fco_id: str) -> dict[str, Any]:
        rows = self.rows()
        verify_rows(rows)
        ids = [r["fco_id"] for r in rows]
        if fco_id not in ids:
            raise KeyError(fco_id)
        mmr = MMR()
        for r in rows:
            mmr.append(canonical(r["identity"]))
        index = ids.index(fco_id)
        proof = mmr.proof(index)
        source = canonical(rows[index]["identity"])
        assert mmr_verify(source, proof, mmr.root())
        return {
            "fco_id": fco_id, "leaf_index": index, "mmr_root": mmr.root().hex(),
            "mmr_size": mmr.size, "leaf_position": proof["leaf_pos"],
            "proof": {
                "size": proof["size"], "leaf_pos": proof["leaf_pos"],
                "path": [(side, pos, val.hex()) for side, pos, val in proof["path"]],
                "peak_pos": proof["peak_pos"],
                "peaks": [val.hex() for val in proof["peaks"]],
            },
            "verified": True,
        }
