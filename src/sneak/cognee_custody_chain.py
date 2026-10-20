"""Cognee-over-time custody chain: expected epochs, marker match, gap reasons.

Recalled Cognee content is DATA_ONLY and never becomes authorization.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional, Sequence


# Expected live Cognee epochs (receipt-backed). Dataset is where the write targeted.
CUSTODY_EPOCHS: list[dict[str, Any]] = [
    {
        "id": "SNEAK-015",
        "dataset": "sneak_working_memory",
        "query": "live-block-eval-must-deny",
        "markers": ["live-block-eval-must-deny", "SNEAK-015", "block-eval"],
        "receipt": "receipts/connectors/SNEAK-015_LIVE_BAND_COGNEE.json",
        "role": "admitted_working_memory",
    },
    {
        "id": "SNEAK-016",
        "dataset": "Data",
        "query": "LOMO-CONN-01-ABLATE",
        "markers": ["LOMO-CONN-01-ABLATE", "@Data", "merkle_root"],
        "receipt": "receipts/connectors/SNEAK-016_LOMO_SNYK_SCORE.json",
        "role": "at_data_breakpoint",
    },
    {
        "id": "SNEAK-018",
        "dataset": "Data",
        "query": "SNEAK-018",
        "markers": ["SNEAK-018", "@Data"],
        "receipt": "receipts/connectors/SNEAK-018_SCORE_SETUP_REVIEW.json",
        "role": "at_data_breakpoint",
    },
    {
        "id": "SNEAK-019",
        "dataset": "Data",
        "query": "SNEAK-019-LESSON",
        "markers": ["SNEAK-019", "@Data"],
        "receipt": "receipts/connectors/SNEAK-019_SNYK_BONUS_EVIDENCE.json",
        "role": "at_data_breakpoint",
    },
    {
        "id": "SNEAK-024",
        "dataset": "sneak_working_memory",
        "query": "sneak-024-conversation-custody",
        "markers": ["sneak-024-conversation-custody", "BP-sneak024", "NOT_COMMITTED"],
        "receipt": "receipts/connectors/SNEAK-024_CONVERSATION_CUSTODY.json",
        "role": "admitted_working_memory",
    },
    {
        "id": "SNEAK-029",
        "dataset": "sneak_working_memory",
        "query": "sneak-029-mvp-hash-travel",
        "markers": ["sneak-029-mvp-hash-travel", "SNEAK-029", "mvp_root"],
        "receipt": "receipts/connectors/SNEAK-029_MVP_HASH_TRAVEL_PACKAGE.json",
        "role": "admitted_working_memory",
        # Known gap until SNEAK-030 backfill: MVP travel notified BAND only.
        "expected_gap_reason": (
            "run_mvp_hash_travel.py posted BAND awareness but never called "
            "MemoryAdapter/DataBackend; mvp_root stayed receipt-local only"
        ),
    },
]


def blob_from_hits(hits: Sequence[dict[str, Any]]) -> str:
    parts: list[str] = []
    for h in hits:
        if not isinstance(h, dict):
            continue
        parts.append(str(h.get("text") or h.get("content") or ""))
        content = h.get("content")
        if isinstance(content, dict):
            parts.append(str(content.get("text") or ""))
    return " ".join(parts)


def match_markers(blob: str, markers: Iterable[str]) -> dict[str, Any]:
    markers_list = list(markers)
    lower = blob.lower()
    found = [m for m in markers_list if m.lower() in lower]
    missing = [m for m in markers_list if m.lower() not in lower]
    # Majority of markers (min 1) so partial semantic hits still score.
    need = max(1, (len(markers_list) + 1) // 2)
    captured = len(found) >= need
    return {
        "found": found,
        "missing": missing,
        "need": need,
        "captured": captured,
        "hit_text_chars": len(blob),
    }


def score_epoch(
    epoch: dict[str, Any],
    *,
    hits: Sequence[dict[str, Any]],
    search_ok: bool,
    mvp_root: Optional[str] = None,
) -> dict[str, Any]:
    markers = list(epoch.get("markers") or [])
    if mvp_root and epoch.get("id") == "SNEAK-029":
        markers = markers + [mvp_root[:16]]
    match = match_markers(blob_from_hits(hits), markers)
    captured = bool(search_ok and match["captured"])
    gap_reason = None
    if not captured:
        gap_reason = epoch.get("expected_gap_reason") or (
            "markers not recalled from Cognee dataset "
            f"`{epoch.get('dataset')}` for query `{epoch.get('query')}`"
        )
    return {
        "id": epoch["id"],
        "dataset": epoch["dataset"],
        "query": epoch["query"],
        "role": epoch.get("role"),
        "receipt": epoch.get("receipt"),
        "search_ok": search_ok,
        "hit_count": len(hits),
        "markers": markers,
        "found": match["found"],
        "missing": match["missing"],
        "captured": captured,
        "gap_reason": gap_reason,
        "authority": "DATA_ONLY",
    }


def chain_summary(epochs_scored: Sequence[dict[str, Any]]) -> dict[str, Any]:
    captured = [e["id"] for e in epochs_scored if e.get("captured")]
    gaps = [
        {"id": e["id"], "reason": e.get("gap_reason"), "dataset": e.get("dataset")}
        for e in epochs_scored
        if not e.get("captured")
    ]
    continuous = len(gaps) == 0
    return {
        "epoch_count": len(epochs_scored),
        "captured_count": len(captured),
        "gap_count": len(gaps),
        "captured_ids": captured,
        "gaps": gaps,
        "continuous_chain": continuous,
        "authority": "DATA_ONLY",
        "mmr": "NOT_COMMITTED",
        "signed": False,
    }


def custody_event_records(epochs_scored: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """One canonical event per epoch for merkle breakpoint leaves."""
    records = []
    for e in epochs_scored:
        records.append(
            {
                "id": f"CUSTODY-{e['id']}",
                "kind": "cognee_custody_epoch",
                "payload": {
                    "epoch_id": e["id"],
                    "dataset": e["dataset"],
                    "captured": bool(e.get("captured")),
                    "hit_count": int(e.get("hit_count") or 0),
                    "found_markers": list(e.get("found") or []),
                    "gap_reason": e.get("gap_reason"),
                },
            }
        )
    return records
