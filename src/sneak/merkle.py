"""RFC9162-style binary Merkle construction used for breakpoints and LOMO successors.

Matches scripts/custody_snapshot.py leaf/internal/odd rules so Python/Node
receipts can be independently recomputed.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable, Sequence


def canonical(obj: Any) -> bytes:
    return json.dumps(
        obj, sort_keys=True, ensure_ascii=True, separators=(",", ":")
    ).encode("ascii")


def _h(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def leaf(record: Any) -> bytes:
    return _h(b"\x00" + canonical(record))


def parent(left: bytes, right: bytes) -> bytes:
    return _h(b"\x01" + left + right)


def layers(leaves: Sequence[bytes]) -> list[list[bytes]]:
    if not leaves:
        raise ValueError("empty tree")
    out: list[list[bytes]] = [list(leaves)]
    while len(out[-1]) > 1:
        row = out[-1]
        nxt: list[bytes] = []
        for i in range(0, len(row), 2):
            if i + 1 < len(row):
                nxt.append(parent(row[i], row[i + 1]))
            else:
                nxt.append(row[i])  # odd: promote unchanged
        out.append(nxt)
    return out


def root(leaves: Sequence[bytes]) -> bytes:
    return layers(leaves)[-1][0]


def proof(leaves: Sequence[bytes], index: int) -> list[dict[str, str]]:
    if index < 0 or index >= len(leaves):
        raise ValueError("invalid leaf index")
    out: list[dict[str, str]] = []
    for row in layers(leaves)[:-1]:
        if index % 2:
            out.append({"side": "left", "hash": row[index - 1].hex()})
        elif index + 1 < len(row):
            out.append({"side": "right", "hash": row[index + 1].hex()})
        index //= 2
    return out


def verify(value: bytes, steps: Iterable[dict[str, str]], expected: bytes) -> bool:
    try:
        if len(value) != 32 or len(expected) != 32:
            return False
        cur = value
        for step in steps:
            sibling = bytes.fromhex(step["hash"])
            if len(sibling) != 32 or step["side"] not in ("left", "right"):
                return False
            cur = parent(sibling, cur) if step["side"] == "left" else parent(cur, sibling)
        return cur == expected
    except (ValueError, KeyError, TypeError):
        return False


def breakpoint_receipt(
    *,
    schema: str,
    breakpoint_id: str,
    parent_id: str | None,
    records: Sequence[dict[str, Any]],
    meaning: str,
) -> dict[str, Any]:
    """Build an ordered Merkle breakpoint over canonical event records."""
    ordered = sorted(records, key=lambda r: str(r.get("id", "")))
    xs = [leaf(r) for r in ordered]
    return {
        "schema": schema,
        "id": breakpoint_id,
        "parent": parent_id,
        "construction": {
            "hash": "SHA-256",
            "canonical": "ASCII JSON, recursively sorted keys, ensure_ascii=True, compact separators, no newline",
            "ordering": "event id ascending",
            "leaf": "SHA256(0x00 || canonical(event))",
            "internal": "SHA256(0x01 || left32 || right32)",
            "odd": "promote unchanged",
        },
        "root": root(xs).hex() if xs else None,
        "leaf_count": len(xs),
        "leaves": [
            {
                "record": r,
                "canonical_hex": canonical(r).hex(),
                "leaf": x.hex(),
                "proof": proof(xs, i),
            }
            for i, (r, x) in enumerate(zip(ordered, xs))
        ],
        "meaning": meaning,
        "mmr": "NOT_COMMITTED",
        "signed": False,
    }
