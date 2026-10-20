#!/usr/bin/env python3
"""Audit Cognee capture over time, backfill gaps, finalize Planner on BAND.

SNEAK-030 successor: shows chain of custody (captured vs gap reasons).
Never prints secrets. Never claims SIGNED / MMR_COMMITTED / bonus awarded.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.band_client import DEFAULT_AGENTS, PLANNER_ROOM_ID, BandClient
from sneak.cognee_client import CogneeClient
from sneak.cognee_custody_chain import (
    CUSTODY_EPOCHS,
    chain_summary,
    custody_event_records,
    score_epoch,
)
from sneak.data_backend import DataBackend
from sneak.evidence import EvidenceStore, digest_payload, utc_now
from sneak.memory import ADMITTED, MemoryAdapter
from sneak.merkle import breakpoint_receipt, verify
from sneak.secrets import export_to_environ, presence_receipt

OUT = ROOT / "receipts/connectors"
VER = ROOT / "data/verification"


def _load_mvp_root() -> str:
    path = OUT / "SNEAK-029_MVP_HASH_TRAVEL_PACKAGE.json"
    if not path.is_file():
        return ""
    return str(json.loads(path.read_text(encoding="utf-8")).get("mvp_root") or "")


def _audit_epochs(client: CogneeClient, mvp_root: str) -> list[dict]:
    scored: list[dict] = []
    for epoch in CUSTODY_EPOCHS:
        result = client.search(
            epoch["query"],
            dataset=epoch["dataset"],
            search_type="CHUNKS",
            top_k=8,
        )
        scored.append(
            score_epoch(
                epoch,
                hits=result.get("hits") or [],
                search_ok=bool(result.get("ok")),
                mvp_root=mvp_root or None,
            )
        )
    return scored


def _backfill_029(
    memory: MemoryAdapter,
    data: DataBackend,
    mvp_root: str,
) -> dict:
    """Write missing SNEAK-029 markers into working memory + @Data."""
    finding = "sneak-029-mvp-hash-travel"
    text = (
        f"SNEAK-029 mvp_root={mvp_root} finding={finding} "
        "sponsors=M01-M15 optionals=E/F/S agent→Snyk bindings=3; "
        "all hash travels verify; live Snyk NOT_TESTED; bonus not awarded; "
        "mmr NOT_COMMITTED. Successor SNEAK-030 audits Cognee chain of custody."
    )
    mem_ref = memory.remember(
        {
            "dataset": ADMITTED,
            "writer": "sneak-cognee-custody-chain",
            "wait_seconds": 60,
            "content": {
                "finding": finding,
                "text": text,
                "mvp_root": mvp_root,
                "parent": "SNEAK-028",
            },
        }
    )
    data_ref = data.write_breakpoint(
        breakpoint_id="SNEAK-029",
        merkle_root=mvp_root or ("0" * 64),
        payload={
            "finding": finding,
            "mvp_root": mvp_root,
            "reason": "backfill after BAND-only awareness gap",
            "authority": "DATA_ONLY",
        },
        wait_seconds=60,
    )
    recalled = memory.recall(finding, ADMITTED)
    data_hits = data.recall(f"SNEAK-029 {mvp_root[:16]}" if mvp_root else "SNEAK-029")
    return {
        "memory_record_id": mem_ref.external_id,
        "data_record_id": data_ref.external_id,
        "working_memory_recall_hits": len(recalled),
        "at_data_recall_hits": len(data_hits),
        "working_memory_recall_ok": bool(recalled),
        "at_data_recall_ok": bool(data_hits),
    }


def main() -> int:
    export_to_environ()
    OUT.mkdir(parents=True, exist_ok=True)
    VER.mkdir(parents=True, exist_ok=True)
    store = EvidenceStore(ROOT / "local-runs/evidence-cognee-custody-chain")

    client = CogneeClient()
    health = client.health() if client.available else {"live": False, "http_status": None}
    mvp_root = _load_mvp_root()

    pre = _audit_epochs(client, mvp_root) if client.available else []
    pre_summary = chain_summary(pre) if pre else {
        "epoch_count": 0,
        "captured_count": 0,
        "gap_count": 0,
        "captured_ids": [],
        "gaps": [{"id": "*", "reason": "Cognee client unavailable", "dataset": None}],
        "continuous_chain": False,
        "authority": "DATA_ONLY",
        "mmr": "NOT_COMMITTED",
        "signed": False,
    }

    backfill = None
    post = pre
    post_summary = pre_summary
    if client.available and any(g["id"] == "SNEAK-029" for g in pre_summary.get("gaps") or []):
        memory = MemoryAdapter(store, live=True)
        data = DataBackend(store, live=True)
        backfill = _backfill_029(memory, data, mvp_root)
        post = _audit_epochs(client, mvp_root)
        post_summary = chain_summary(post)

    # Also write SNEAK-030 finalize marker into @Data for continuity.
    data_finalize = None
    if client.available:
        data = DataBackend(store, live=True)
        data_finalize = data.write_breakpoint(
            breakpoint_id="SNEAK-030",
            merkle_root=mvp_root or ("0" * 64),
            payload={
                "finding": "sneak-030-cognee-custody-chain",
                "pre_captured": pre_summary.get("captured_ids"),
                "pre_gaps": pre_summary.get("gaps"),
                "post_captured": post_summary.get("captured_ids"),
                "post_gaps": post_summary.get("gaps"),
                "backfill": bool(backfill),
                "authority": "DATA_ONLY",
                "mmr": "NOT_COMMITTED",
            },
            wait_seconds=45,
        )
        # re-score after 030 write does not change epoch list

    records = custody_event_records(post or pre)
    # Include pre/post summary leaf for the audit itself
    records.append(
        {
            "id": "CUSTODY-SNEAK-030-AUDIT",
            "kind": "cognee_custody_audit",
            "payload": {
                "pre_captured_count": pre_summary.get("captured_count"),
                "post_captured_count": post_summary.get("captured_count"),
                "pre_gap_count": pre_summary.get("gap_count"),
                "post_gap_count": post_summary.get("gap_count"),
                "backfill_029": bool(backfill),
                "mvp_root": mvp_root,
                "cognee_live": bool(health.get("live")),
            },
        }
    )
    bp = breakpoint_receipt(
        schema="sneak.cognee_custody_chain.v1",
        breakpoint_id="SNEAK-030",
        parent_id="SNEAK-029",
        records=records,
        meaning=(
            "Cognee-over-time chain of custody: which epochs remain recallable; "
            "why gaps exist; SNEAK-029 backfill when BAND-only awareness left memory empty"
        ),
    )
    # Independently recompute leaf→root for each travel
    travels_ok = all(
        verify(
            bytes.fromhex(leaf["leaf"]),
            leaf["proof"],
            bytes.fromhex(bp["root"]),
        )
        for leaf in bp["leaves"]
    )

    # Finalize planner update on BAND
    band_client = BandClient()
    planner_online = False
    band_msg: dict = {"ok": False}
    tasks_active = []
    if band_client.available:
        parts = band_client.list_participants(PLANNER_ROOM_ID)
        pid = DEFAULT_AGENTS["planner"]["id"]
        for p in parts.get("participants") or []:
            if p.get("id") == pid:
                planner_online = bool(p.get("online"))
                break
        tasks = band_client.list_tasks(PLANNER_ROOM_ID, state="active")
        tasks_active = [
            {"number": t.get("number"), "subject": (t.get("subject") or "")[:80]}
            for t in (tasks.get("tasks") or [])[:12]
            if isinstance(t, dict)
        ]
        gap_txt = (
            ", ".join(f"{g['id']}:{g['reason'][:60]}" for g in (pre_summary.get("gaps") or []))
            or "none"
        )
        post_gap_txt = (
            ", ".join(g["id"] for g in (post_summary.get("gaps") or [])) or "none"
        )
        band_msg = band_client.send_mention(
            (
                f"SNEAK-030 finalize: Cognee custody chain root=`{bp.get('root')}` "
                f"pre_captured={pre_summary.get('captured_ids')} pre_gaps=[{gap_txt[:180]}] "
                f"post_captured={post_summary.get('captured_ids')} post_gaps=[{post_gap_txt}] "
                f"backfill_029={bool(backfill)} mvp_root=`{(mvp_root or '')[:16]}…` "
                f"travels_ok={travels_ok} planner_online={planner_online}. "
                "Authority=DATA_ONLY; mmr NOT_COMMITTED; bonus not awarded; "
                "human #6/#7 still open. Do not mark Done."
            ),
            ["claude", "chatgpt", "planner"],
            room_id=PLANNER_ROOM_ID,
        )
        store.append_receipt(
            "cognee_custody_planner_finalize",
            {
                "room_id": PLANNER_ROOM_ID,
                "ok": bool(band_msg.get("ok")),
                "message_id": (band_msg.get("message") or {}).get("id"),
                "planner_online": planner_online,
                "custody_root": bp.get("root"),
            },
            provider="band",
        )

    package = {
        "id": "SNEAK-030-COGNEE-CUSTODY-CHAIN",
        "parent": "SNEAK-029",
        "cognee_health": {
            "available": client.available,
            "live": bool(health.get("live")),
            "http_status": health.get("http_status"),
        },
        "mvp_root": mvp_root,
        "pre_audit": pre_summary,
        "post_audit": post_summary,
        "epochs_pre": pre,
        "epochs_post": post,
        "backfill_029": backfill,
        "data_finalize_030": (
            {"record_id": data_finalize.external_id} if data_finalize else None
        ),
        "custody_breakpoint": {
            "id": bp.get("id"),
            "root": bp.get("root"),
            "leaf_count": bp.get("leaf_count"),
            "all_travels_verify": travels_ok,
            "mmr": bp.get("mmr"),
            "signed": bp.get("signed"),
        },
        "band_finalize": {
            "ok": bool(band_msg.get("ok")),
            "message_id": (band_msg.get("message") or {}).get("id"),
            "room_id": PLANNER_ROOM_ID,
            "planner_online": planner_online,
            "active_task_count": len(tasks_active),
            "active_tasks": tasks_active,
        },
        "why_not_showing_chain_before": {
            "SNEAK-029": (
                next(
                    (
                        g.get("reason")
                        for g in (pre_summary.get("gaps") or [])
                        if g.get("id") == "SNEAK-029"
                    ),
                    "already captured or unavailable",
                )
            ),
            "intermediate_SNEAK_020_028": (
                "Those successors wrote BAND/receipt lanes; only selected "
                "epochs (015/016/018/019/024) were designed to persist into Cognee. "
                "Absence of 020–028 in Cognee is expected, not a silent failure."
            ),
        },
        "secrets": presence_receipt(),
        "mmr": "NOT_COMMITTED",
        "signed": False,
        "bonus_awarded": False,
        "meaning": (
            "Double-check Cognee captured custody data over time; show chain "
            "with gap reasons; backfill SNEAK-029; finalize Planner on BAND"
        ),
        "observed_at": utc_now(),
    }
    package["artifact_digest"] = digest_payload(package)
    store.append_receipt("cognee_custody_chain_package", package, provider="sneak.custody")

    (OUT / "SNEAK-030_COGNEE_CUSTODY_CHAIN.json").write_text(
        json.dumps(bp, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (OUT / "SNEAK-030_COGNEE_CUSTODY_CHAIN_PACKAGE.json").write_text(
        json.dumps(package, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    md_lines = [
        "# SNEAK-030 Cognee custody chain (over time)",
        "",
        f"- Cognee live: **{bool(health.get('live'))}**",
        f"- Custody merkle root: `{bp.get('root')}`",
        f"- All leaf travels verify: **{travels_ok}**",
        f"- MVP root (SNEAK-029): `{mvp_root}`",
        f"- Pre-audit captured: **{pre_summary.get('captured_ids')}** gaps: **{pre_summary.get('gap_count')}**",
        f"- Post-audit captured: **{post_summary.get('captured_ids')}** gaps: **{post_summary.get('gap_count')}**",
        f"- Backfill SNEAK-029: **{bool(backfill)}**",
        f"- BAND finalize ok: **{bool(band_msg.get('ok'))}** planner_online: **{planner_online}**",
        f"- MMR: **NOT_COMMITTED**; signed: **False**; bonus awarded: **False**",
        "",
        "## Why the chain was incomplete",
        "",
    ]
    for g in pre_summary.get("gaps") or []:
        md_lines.append(f"- **{g.get('id')}** (`{g.get('dataset')}`): {g.get('reason')}")
    if not pre_summary.get("gaps"):
        md_lines.append("- No gaps at pre-audit.")
    md_lines.extend(
        [
            "",
            "- Intermediate SNEAK-020–028: expected receipt/BAND-only (not every successor writes Cognee).",
            "",
            "## Epoch recall (post-audit)",
            "",
            "| Epoch | Dataset | Captured | Hits | Missing markers |",
            "|---|---|---|---|---|",
        ]
    )
    for e in post or pre:
        missing = ",".join((e.get("missing") or [])[:4]) or "—"
        md_lines.append(
            f"| {e.get('id')} | `{e.get('dataset')}` | **{e.get('captured')}** | "
            f"{e.get('hit_count')} | `{missing}` |"
        )
    md_lines.extend(
        [
            "",
            "## Planner finalize",
            "",
            f"- Room: `{PLANNER_ROOM_ID}`",
            f"- Message id: `{(band_msg.get('message') or {}).get('id')}`",
            f"- Active tasks: **{len(tasks_active)}** (human #6/#7 remain open)",
            "",
        ]
    )
    (OUT / "SNEAK-030_COGNEE_CUSTODY_CHAIN.md").write_text(
        "\n".join(md_lines) + "\n", encoding="utf-8"
    )

    jsonl_path = VER / "cognee_custody_chain_sneak_030.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as fh:
        for e in post or pre:
            fh.write(
                json.dumps(
                    {
                        "id": f"REQ-CUSTODY-COGNEE-{e['id']}",
                        "kind": "custody_epoch",
                        "observed_outcome": "PASS" if e.get("captured") else "GAP",
                        "verified": bool(e.get("captured")),
                        "dataset": e.get("dataset"),
                        "gap_reason": e.get("gap_reason"),
                        "authority": "DATA_ONLY",
                    },
                    sort_keys=True,
                )
                + "\n"
            )
        fh.write(
            json.dumps(
                {
                    "id": "REQ-CUSTODY-COGNEE-CHAIN",
                    "kind": "custody_chain",
                    "observed_outcome": (
                        "PASS" if post_summary.get("continuous_chain") else "PARTIAL"
                    ),
                    "verified": bool(post_summary.get("continuous_chain")),
                    "custody_root": bp.get("root"),
                    "travels_ok": travels_ok,
                    "mmr": "NOT_COMMITTED",
                    "signed": False,
                },
                sort_keys=True,
            )
            + "\n"
        )

    print(
        json.dumps(
            {
                "id": package["id"],
                "custody_root": bp.get("root"),
                "travels_ok": travels_ok,
                "pre_gaps": pre_summary.get("gaps"),
                "post_captured": post_summary.get("captured_ids"),
                "post_gaps": post_summary.get("gaps"),
                "backfill_029": bool(backfill),
                "band_ok": bool(band_msg.get("ok")),
                "planner_online": planner_online,
                "mmr": "NOT_COMMITTED",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if travels_ok and bool(band_msg.get("ok") or not band_client.available) else 1


if __name__ == "__main__":
    raise SystemExit(main())
