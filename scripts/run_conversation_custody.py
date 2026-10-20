#!/usr/bin/env python3
"""Run conversation custody pipeline: hashed I/O, FCO steps, true/false breakpoints,
per-model MMR deltas vs root question; BAND ask/respond; Cognee @Data; planner check.

Emits SNEAK-024 receipts. Never claims SIGNED / MMR_COMMITTED / awarded bonus.
Secrets load from ~/.secrets/sneak/providers.env (never printed).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.band_adapter import BandAdapter
from sneak.band_client import DEFAULT_AGENTS, PLANNER_ROOM_ID, BandClient
from sneak.conversation_custody import (
    CUSTODY_REQUIREMENTS,
    ConversationCustodyLedger,
    verify_custody_requirements,
)
from sneak.evidence import EvidenceStore, digest_payload
from sneak.memory import ADMITTED, MemoryAdapter
from sneak.merkle import breakpoint_receipt
from sneak.secrets import export_to_environ, presence_receipt


ROOT_QUESTION_TEXT = (
    "Unique merkle tree breakpoints (pass true|false) per conversation; "
    "each model candidate MMR vs root question with delta over time; "
    "input hashed → deterministic script steps/FCO → output hashed; "
    "updates hashed via FCO tracking; BAND ask/respond; Cognee @Data; "
    "update all agents + planner; verify each requirement including optional."
)


def _read_payload(store: EvidenceStore, ref) -> dict:
    body = store.read(ref.receipt_path)
    return body.get("payload") or {}


def main() -> int:
    export_to_environ()
    for ln in Path.home().joinpath(".secrets/sneak/providers.env").read_text().splitlines():
        if ln.startswith("BAND_PLANNER_") and "=" in ln:
            k, v = ln.split("=", 1)
            os.environ.setdefault(k, v)

    out = ROOT / "receipts/connectors"
    out.mkdir(parents=True, exist_ok=True)
    ver_dir = ROOT / "data/verification"
    ver_dir.mkdir(parents=True, exist_ok=True)
    store = EvidenceStore(ROOT / "local-runs/evidence-conversation-custody")

    root_question = {
        "text": ROOT_QUESTION_TEXT,
        "requirements": [r["id"] for r in CUSTODY_REQUIREMENTS],
        "parent": "SNEAK-023",
    }
    ledger = ConversationCustodyLedger(store, root_question=root_question)

    turns = [
        {
            "conversation_id": "sneak024-liquid-tom-01",
            "model_id": "liquid-lfm",
            "agent_id": "tom",
            "input": {"role": "ask", "agent": "tom", "topic": "architecture-custody"},
            "steps": [
                {"name": "hash_input", "script": "digest_payload"},
                {"name": "emit_step_fco", "script": "fco_identity"},
                {"name": "hash_output", "script": "digest_payload"},
            ],
            "output": {"role": "respond", "agent": "tom", "pass": True, "note": "ACK custody BP"},
            "pass": True,
        },
        {
            "conversation_id": "sneak024-openjev-jerry-01",
            "model_id": "openjev",
            "agent_id": "jerry",
            "input": {"role": "ask", "agent": "jerry", "topic": "builder-custody"},
            "steps": [
                {"name": "hash_input", "script": "digest_payload"},
                {"name": "emit_step_fco", "script": "fco_identity"},
                {"name": "hash_output", "script": "digest_payload"},
            ],
            "output": {"role": "respond", "agent": "jerry", "pass": True, "note": "ACK implement"},
            "pass": True,
        },
        {
            "conversation_id": "sneak024-liquid-tom-02",
            "model_id": "liquid-lfm",
            "agent_id": "tom",
            "input": {"role": "ask", "agent": "tom", "topic": "delta-over-time"},
            "steps": [
                {"name": "hash_input", "script": "digest_payload"},
                {"name": "compare_mmr_delta", "script": "xor_distance"},
                {"name": "hash_output", "script": "digest_payload"},
            ],
            "output": {
                "role": "respond",
                "agent": "tom",
                "pass": False,
                "note": "intentional fail BP for true/false coverage",
            },
            "pass": False,
        },
        {
            "conversation_id": "sneak024-planner-01",
            "model_id": "planner-remote",
            "agent_id": "planner",
            "input": {"role": "ask", "agent": "planner", "topic": "plan-track-custody"},
            "steps": [
                {"name": "hash_input", "script": "digest_payload"},
                {"name": "file_checkoff", "script": "band_create_task"},
                {"name": "hash_output", "script": "digest_payload"},
            ],
            "output": {
                "role": "respond",
                "agent": "planner",
                "pass": True,
                "note": "planner custody turn recorded",
            },
            "pass": True,
        },
    ]

    parent = None
    for t in turns:

        def pred(inp, out, steps):
            # Gate outcome is the output pass flag (true|false breakpoint).
            return bool(out.get("pass"))

        receipt = ledger.run_turn(
            conversation_id=t["conversation_id"],
            model_id=t["model_id"],
            agent_id=t["agent_id"],
            input_payload=t["input"],
            steps=t["steps"],
            output_payload=t["output"],
            pass_predicate=pred,
            parent_breakpoint_id=parent,
        )
        parent = receipt["id"]
        ledger.track_update(
            update_id=f"UPD-{t['conversation_id']}",
            parent_fco_id=f"STEP-{t['conversation_id']}-0000",
            change={
                "kind": "agent_planner_notify",
                "agent_id": t["agent_id"],
                "model_id": t["model_id"],
                "breakpoint_id": receipt["id"],
                "pass": receipt["pass"],
                "model_mmr_delta_index": receipt["model_mmr_delta"]["index"],
            },
        )

    # --- Live BAND: ask/respond to Tom, Jerry, Planner in planner room ---
    band = BandAdapter(store, live=True)
    band.state.room_id = PLANNER_ROOM_ID
    client = BandClient()
    parts = client.list_participants(PLANNER_ROOM_ID) if client.available else {"ok": False}
    planner_cfg = DEFAULT_AGENTS["planner"]
    part_planner = next(
        (p for p in (parts.get("participants") or []) if p.get("id") == planner_cfg["id"]),
        None,
    )

    ask_content = (
        "SNEAK-024 conversation custody: unique merkle breakpoints (pass true|false); "
        "per-model candidate MMR deltas vs root question; hashed input→FCO→hashed output; "
        "update FCOs. Tom: ACK architecture. Jerry: ACK builder. "
        "Planner: confirm plan track stays open until evidence; do not mark Done."
    )
    band_ask: dict = {"ok": False, "observed_outcome": "NOT_TESTED"}
    if client.available:
        band_ask = client.send_mention(
            ask_content,
            ["claude", "chatgpt", "planner"],
            room_id=PLANNER_ROOM_ID,
        )
        store.append_receipt(
            "band_custody_ask",
            {
                "room_id": PLANNER_ROOM_ID,
                "http_status": band_ask.get("http_status"),
                "message_id": (band_ask.get("message") or {}).get("id"),
                "recipients": band_ask.get("recipients"),
                "observed_outcome": "PASS" if band_ask.get("ok") else "FAIL",
            },
            provider="band",
        )

    dual_ref = band.message_claude_and_chatgpt(
        "SNEAK-024: recall Cognee custody breakpoints before any Done mark. "
        "Planner room is source of plan track.",
        room_id=PLANNER_ROOM_ID,
    )
    dual_payload = _read_payload(store, dual_ref)

    to_planner_ref = band.publish_handoff(
        "SNEAK-024-planner",
        "planner",
        [],
        request_id="sneak-024-planner",
        message=(
            "SNEAK-024: custody ledger emits unique BPs + model MMR deltas. "
            "Keep CHECKOFFs open; overall Done remains false without human gates."
        ),
    )
    planner_handoff = _read_payload(store, to_planner_ref)

    task: dict = {"ok": False}
    if client.available:
        task = client.create_task(
            "SNEAK-024 conversation custody breakpoints + model MMR deltas",
            detail=(
                "Verify unique merkle BPs (true/false), hashed I/O FCO chain, "
                "per-model MMR vs root question, Cognee capture, agents+planner updated. "
                "Optional: live Liquid/OpenJev; MMR commit stays NOT_COMMITTED."
            ),
            room_id=PLANNER_ROOM_ID,
        )
        store.append_receipt(
            "band_custody_task",
            {
                "room_id": PLANNER_ROOM_ID,
                "http_status": task.get("http_status"),
                "task_id": (task.get("task") or {}).get("id"),
                "task_number": (task.get("task") or {}).get("number"),
                "observed_outcome": task.get("observed_outcome"),
            },
            provider="band",
        )

    planner_mentioned = any(
        (r or {}).get("name") == "Planner" for r in (band_ask.get("recipients") or [])
    )
    band_ok = bool(band_ask.get("ok")) and dual_payload.get("observed_outcome") == "PASS"
    agents_updated = bool(
        band_ask.get("ok")
        and planner_mentioned
        and dual_payload.get("observed_outcome") == "PASS"
        and planner_handoff.get("observed_outcome") in ("PASS", "LOCAL_CONTRACT_ONLY")
    )
    planner_checked = bool(part_planner) and bool(band_ask.get("ok")) and planner_mentioned

    # --- Cognee @Data capture of custody package ---
    memory = MemoryAdapter(store, live=True)
    project = ledger.project_connector_receipt(breakpoint_id="SNEAK-024")
    mem_ref = memory.remember(
        {
            "dataset": ADMITTED,
            "writer": "sneak-conversation-custody",
            "wait_seconds": 45,
            "content": {
                "finding": "sneak-024-conversation-custody",
                "text": (
                    f"SNEAK-024 custody root={project.get('root')} "
                    f"breakpoints={project.get('breakpoint_count')} "
                    f"pass={project.get('pass_count')} fail={project.get('fail_count')} "
                    f"models={list(project.get('model_trails') or {})} "
                    "mmr=NOT_COMMITTED"
                ),
                "root_question_leaf": ledger.root_question_leaf,
                "breakpoint_ids": [b["id"] for b in ledger.breakpoints],
            },
        }
    )
    mem_payload = _read_payload(store, mem_ref)
    live_mem = mem_payload.get("live") or {}
    recalled = memory.recall("sneak-024-conversation-custody", ADMITTED)
    recall_outcome = "HIT" if recalled else "MISS"

    if memory.live_cognee:
        cognee_ok = bool(live_mem.get("add_ok"))
    else:
        cognee_ok = False

    live_model_inference = False
    mmr_committed = False

    req_rows = verify_custody_requirements(
        ledger,
        band_ok=band_ok,
        cognee_ok=cognee_ok,
        planner_checked=planner_checked,
        agents_updated=agents_updated,
        live_model_inference=live_model_inference,
        mmr_committed=mmr_committed,
    )

    package = {
        "id": "SNEAK-024-CONVERSATION-CUSTODY",
        "parent": "SNEAK-023",
        "root_question": {
            "text": ROOT_QUESTION_TEXT,
            "fco_candidate_sha256": ledger.root_question_fco["fco_candidate_sha256"],
            "leaf": ledger.root_question_leaf,
        },
        "breakpoints": [
            {
                "id": b["id"],
                "root": b["root"],
                "pass": b["pass"],
                "model_id": b["model_id"],
                "agent_id": b["agent_id"],
                "input_hash": b["input_hash"],
                "output_hash": b["output_hash"],
                "model_mmr_delta": b.get("model_mmr_delta"),
            }
            for b in ledger.breakpoints
        ],
        "update_fco_count": len(ledger.update_fcos),
        "model_trails": project.get("model_trails"),
        "band": {
            "room_id": PLANNER_ROOM_ID,
            "ask_ok": bool(band_ask.get("ok")),
            "message_id": (band_ask.get("message") or {}).get("id"),
            "recipients": band_ask.get("recipients"),
            "dual_outcome": dual_payload.get("observed_outcome"),
            "planner_handoff": planner_handoff.get("observed_outcome"),
            "task_number": (task.get("task") or {}).get("number"),
            "planner_in_room": bool(part_planner),
            "planner_online": bool((part_planner or {}).get("online")),
        },
        "cognee": {
            "record_id": mem_ref.external_id,
            "observed_outcome": mem_payload.get("observed_outcome"),
            "live": live_mem,
            "recall_outcome": recall_outcome,
            "recall_hit_count": len(recalled) if isinstance(recalled, list) else 0,
        },
        "requirements": req_rows,
        "secrets": presence_receipt(),
        "mmr": "NOT_COMMITTED",
        "signed": False,
        "meaning": (
            "Conversation custody ledger with unique true/false merkle breakpoints, "
            "per-model candidate MMR deltas vs root question, BAND+Cognee+planner loop"
        ),
    }
    package["artifact_digest"] = digest_payload(package)
    store.append_receipt("conversation_custody_package", package, provider="sneak.custody")

    receipt = breakpoint_receipt(
        schema="sneak.conversation-custody.v1",
        breakpoint_id="SNEAK-024",
        parent_id="SNEAK-023",
        records=[
            {
                "id": "SNEAK-024-ROOT-Q",
                "kind": "RootQuestionFCO",
                "payload": {
                    "leaf": ledger.root_question_leaf,
                    "fco": ledger.root_question_fco["fco_candidate_sha256"],
                },
            },
            {
                "id": "SNEAK-024-BPS",
                "kind": "ConversationBreakpoints",
                "payload": {
                    "count": project["breakpoint_count"],
                    "pass_count": project["pass_count"],
                    "fail_count": project["fail_count"],
                    "ids": [b["id"] for b in ledger.breakpoints],
                },
            },
            {
                "id": "SNEAK-024-MODEL-MMR",
                "kind": "ModelMMRTrails",
                "payload": {
                    mid: {
                        "peak_count": t["peak_count"],
                        "latest_root": (t["roots"] or [None])[-1],
                        "mmr": "NOT_COMMITTED",
                    }
                    for mid, t in (project.get("model_trails") or {}).items()
                },
            },
            {
                "id": "SNEAK-024-BAND",
                "kind": "band_ask_respond",
                "payload": {
                    "ok": band_ok,
                    "room_id": PLANNER_ROOM_ID,
                    "message_id": (band_ask.get("message") or {}).get("id"),
                },
            },
            {
                "id": "SNEAK-024-COGNEE",
                "kind": "cognee_data",
                "payload": {
                    "ok": cognee_ok,
                    "outcome": mem_payload.get("observed_outcome"),
                },
            },
            {
                "id": "SNEAK-024-REQS",
                "kind": "custody_requirements",
                "payload": {
                    "mandatory_pass": sum(
                        1
                        for r in req_rows
                        if r["kind"] == "mandatory" and r["observed_outcome"] == "PASS"
                    ),
                    "mandatory_total": sum(1 for r in req_rows if r["kind"] == "mandatory"),
                    "optional": [
                        {
                            "id": r["id"],
                            "outcome": r["observed_outcome"],
                            "verified": r["verified"],
                        }
                        for r in req_rows
                        if r["kind"] == "optional"
                    ],
                },
            },
        ],
        meaning=package["meaning"],
    )
    receipt["mmr"] = "NOT_COMMITTED"
    receipt["package_digest"] = package["artifact_digest"]
    receipt["project_root"] = project.get("root")
    receipt["requirements"] = req_rows

    (out / "SNEAK-024_CONVERSATION_CUSTODY.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "SNEAK-024_CONVERSATION_CUSTODY_PACKAGE.json").write_text(
        json.dumps(package, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    jsonl_path = ver_dir / "requirements_sneak_024.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as fh:
        for r in req_rows:
            row = {
                "id": f"{r['id']}-SNEAK-024",
                "predecessor_requirement_id": r["id"],
                "kind": r["kind"],
                "statement": r["statement"],
                "observed_outcome": r["observed_outcome"],
                "verified": r["verified"],
                "required_for_entry": r["required_for_entry"],
                "evidence": [
                    {
                        "external_id": "SNEAK-024",
                        "provider": "sneak.custody",
                        "receipt_path": "receipts/connectors/SNEAK-024_CONVERSATION_CUSTODY.json",
                        "artifact_digest": package["artifact_digest"],
                    }
                ],
            }
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    md = [
        "# SNEAK-024 Conversation custody (merkle breakpoints + model MMR deltas)",
        "",
        "- Parent: SNEAK-023",
        f"- Root question leaf: `{ledger.root_question_leaf}`",
        f"- Project connector root: `{project.get('root')}`",
        f"- Breakpoints: **{project['breakpoint_count']}** "
        f"(pass={project['pass_count']}, fail={project['fail_count']})",
        f"- Update FCOs: **{len(ledger.update_fcos)}**",
        "- MMR: **NOT_COMMITTED** (never claimed)",
        "",
        "## Pipeline",
        "",
        "`input_hash` → deterministic step FCOs → `output_hash` → unique BP `pass: true|false`",
        "",
        "Per-model candidate MMR peaks vs root question (XOR distance deltas over time).",
        "",
        "## Model MMR trails",
        "",
        "| Model | Peaks | Latest bagged root | Latest vs root-Q XOR |",
        "|---|---:|---|---:|",
    ]
    for mid, trail in sorted((project.get("model_trails") or {}).items()):
        latest = (trail.get("deltas") or [{}])[-1]
        md.append(
            f"| `{mid}` | {trail.get('peak_count')} | "
            f"`{(trail.get('roots') or ['—'])[-1][:16]}…` | "
            f"{latest.get('vs_root_question_xor_distance', '—')} |"
        )
    md.extend(
        [
            "",
            "## BAND + Cognee + Planner",
            "",
            f"- Room: `{PLANNER_ROOM_ID}`",
            f"- Ask message ok: **{bool(band_ask.get('ok'))}** "
            f"id=`{(band_ask.get('message') or {}).get('id')}`",
            f"- Planner in room: **{bool(part_planner)}**; "
            f"online: **{(part_planner or {}).get('online')}**",
            f"- Board task #: **{(task.get('task') or {}).get('number')}**",
            f"- Cognee: outcome=`{mem_payload.get('observed_outcome')}` "
            f"add_ok={live_mem.get('add_ok')}",
            "",
            "## Requirements (mandatory + optional)",
            "",
            "| ID | Kind | Outcome | Verified | Statement |",
            "|---|---|---|---|---|",
        ]
    )
    for r in req_rows:
        stmt = r["statement"][:60]
        md.append(
            f"| {r['id']} | {r['kind']} | {r['observed_outcome']} | "
            f"{r['verified']} | {stmt}… |"
        )
    md.append("")
    (out / "SNEAK-024_CONVERSATION_CUSTODY.md").write_text("\n".join(md), encoding="utf-8")

    summary = {
        "id": "SNEAK-024",
        "parent": "SNEAK-023",
        "breakpoint_count": project["breakpoint_count"],
        "pass_count": project["pass_count"],
        "fail_count": project["fail_count"],
        "models": list((project.get("model_trails") or {}).keys()),
        "band_ok": band_ok,
        "cognee_ok": cognee_ok,
        "planner_checked": planner_checked,
        "agents_updated": agents_updated,
        "mandatory_pass": sum(
            1 for r in req_rows if r["kind"] == "mandatory" and r["observed_outcome"] == "PASS"
        ),
        "mandatory_total": sum(1 for r in req_rows if r["kind"] == "mandatory"),
        "optional": [
            {"id": r["id"], "outcome": r["observed_outcome"], "verified": r["verified"]}
            for r in req_rows
            if r["kind"] == "optional"
        ],
        "root": receipt.get("root"),
        "project_root": project.get("root"),
        "package_digest": package["artifact_digest"],
        "mmr": "NOT_COMMITTED",
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
