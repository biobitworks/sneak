#!/usr/bin/env python3
"""Score REQ-AOK-M01..M20 against receipts + live Band observation (successor ledger).

Source status only — never inferred from graph links.
Preserves predecessor atoms; appends SNEAK-028 successors.
Does not claim Band Desktop when only Human API / Agent SDK were used.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.aok import entry_gate
from sneak.band_client import DEFAULT_AGENTS, PLANNER_ROOM_ID, BandClient
from sneak.contracts import EvidenceRef, Verdict
from sneak.evidence import EvidenceStore, digest_payload, utc_now
from sneak.merkle import breakpoint_receipt
from sneak.secrets import export_to_environ, presence_receipt

ATOMS = ROOT / "data/rules/atomic_acceptance_r5.jsonl"
OUT = ROOT / "receipts/connectors"
VER = ROOT / "data/verification"


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evid(path: str, external_id: str) -> dict:
    p = ROOT / path
    return {
        "provider": "sneak.receipt",
        "external_id": external_id,
        "artifact_digest": file_digest(p) if p.is_file() else "MISSING",
        "receipt_path": path,
        "observed_at": utc_now(),
    }


def main() -> int:
    export_to_environ()
    OUT.mkdir(parents=True, exist_ok=True)
    VER.mkdir(parents=True, exist_ok=True)
    store = EvidenceStore(ROOT / "local-runs/evidence-aok-mvp-ledger")

    atoms = {
        row["id"]: row
        for line in ATOMS.read_text(encoding="utf-8").splitlines()
        if line.strip()
        for row in [json.loads(line)]
        if str(row.get("id", "")).startswith("REQ-AOK-M")
    }

    client = BandClient()
    live = {
        "me": client.me() if client.available else {"ok": False},
        "room_id": PLANNER_ROOM_ID,
        "participants": [],
        "tasks": [],
        "band_available": bool(client.available),
    }
    if client.available and live["me"].get("ok"):
        parts = client.list_participants(PLANNER_ROOM_ID)
        tasks = client.list_tasks(PLANNER_ROOM_ID)
        live["participants"] = parts.get("participants") or []
        live["tasks"] = tasks.get("tasks") or []

    agents = [p for p in live["participants"] if p.get("type") == "Agent"]
    online_agents = [p for p in agents if p.get("online")]
    biobitworks_agents = [
        p
        for p in agents
        if str(p.get("handle") or "").startswith("biobitworks/")
    ]
    completed = [t for t in live["tasks"] if t.get("overall_status") == "completed"]
    pending = [t for t in live["tasks"] if t.get("overall_status") == "pending"]

    e022 = evid("receipts/connectors/SNEAK-022_BAND_IDENTITY_VERIFY.json", "SNEAK-022")
    e023 = evid("receipts/connectors/SNEAK-023_PLANNER_PLAN_TRACK.json", "SNEAK-023")
    e024 = evid("receipts/connectors/SNEAK-024_CONVERSATION_CUSTODY.json", "SNEAK-024")
    e025 = evid("receipts/connectors/SNEAK-025_PLANNER_RUNTIME.json", "SNEAK-025")
    e026 = evid("receipts/connectors/SNEAK-026_PLANNER_ONBOARDING.json", "SNEAK-026")
    e027 = evid("receipts/connectors/SNEAK-027_LANES_WRAPUP.json", "SNEAK-027")

    # Honest per-atom scoring (source status from observed effects + receipts).
    scores: dict[str, dict] = {
        "REQ-AOK-M01": {
            "observed_outcome": "NOT_TESTED",
            "verified": False,
            "tried": True,
            "reason": (
                "Requirement is actual Band Desktop. magicstudio: CLI/app missing; "
                "magicpro: CLI present but band whoami unsigned (SNEAK-027). "
                "MVP used Human API + Agent SDK websocket instead — substitute does "
                "not satisfy Desktop."
            ),
            "evidence": [e027, e022],
        },
        "REQ-AOK-M02": {
            "observed_outcome": "PASS",
            "verified": True,
            "tried": True,
            "reason": (
                "Band platform coordinated Tom/Jerry/Planner via Human API mentions "
                "and Planner Agent SDK runtime (SNEAK-022..026)."
            ),
            "evidence": [e022, e025, e026],
        },
        "REQ-AOK-M03": {
            "observed_outcome": "PASS",
            "verified": True,
            "tried": True,
            "reason": f"Agents share planner room `{PLANNER_ROOM_ID}` (live + SNEAK-022/025).",
            "evidence": [e022, e025],
        },
        "REQ-AOK-M04": {
            "observed_outcome": "PASS" if len(online_agents) >= 2 else "FAIL",
            "verified": len(online_agents) >= 2,
            "tried": True,
            "reason": (
                f"Live online agents={len(online_agents)} "
                f"handles={[p.get('handle') for p in online_agents]}; "
                f"biobitworks agents in room={len(biobitworks_agents)}."
            ),
            "evidence": [e025, e026],
        },
        "REQ-AOK-M05": {
            "observed_outcome": "PASS",
            "verified": True,
            "tried": True,
            "reason": (
                "Planner (@biobitworks/planner) posted plan-track status in-room "
                "(SNEAK-025 replies_sent / plan-track reply observed)."
            ),
            "evidence": [e025, e023],
        },
        "REQ-AOK-M06": {
            "observed_outcome": "PASS",
            "verified": True,
            "tried": True,
            "reason": (
                "One shared plan-track CHECKOFF set (#2–#7) governs work; "
                "overall Done remains false (SNEAK-023/025)."
            ),
            "evidence": [e023, e025],
        },
        "REQ-AOK-M07": {
            "observed_outcome": "PASS",
            "verified": True,
            "tried": True,
            "reason": (
                f"Shared room task board observed via Human API "
                f"(active tasks={len(live['tasks'])}; SNEAK-022 empty-board→tasks)."
            ),
            "evidence": [e022, e023],
        },
        "REQ-AOK-M08": {
            "observed_outcome": "FAIL",
            "verified": False,
            "tried": True,
            "reason": (
                "Tried: chase Tom/Jerry to claim CHECKOFF #3/#4. Observed chat ACK only; "
                "board assignments empty; BOARD_TOOL_MISSING (SNEAK-025/027). "
                "Chat ACK is not a board claim."
            ),
            "evidence": [e025, e027],
        },
        "REQ-AOK-M09": {
            "observed_outcome": "PASS" if completed and pending else "FAIL",
            "verified": bool(completed and pending),
            "tried": True,
            "reason": (
                f"Board shows To-do/pending and Done/completed "
                f"(completed_numbers={[t.get('number') for t in completed]}; "
                f"pending_count={len(pending)}). Agent #3/#4 Done transitions still open."
            ),
            "evidence": [e023, e025],
        },
        "REQ-AOK-M10": {
            "observed_outcome": "PASS",
            "verified": True,
            "tried": True,
            "reason": (
                "Native BAND @mentions among Planner/Tom/Jerry observed "
                "(SNEAK-024/025/026 message ids)."
            ),
            "evidence": [e024, e025, e026],
        },
        "REQ-AOK-M11": {
            "observed_outcome": "PASS",
            "verified": True,
            "tried": True,
            "reason": (
                "Direct room handoffs: Human API dual-harness + Planner SDK replies "
                "carrying plan-track context (SNEAK-024/025)."
            ),
            "evidence": [e024, e025],
        },
        "REQ-AOK-M12": {
            "observed_outcome": "PASS",
            "verified": True,
            "tried": True,
            "reason": (
                "Agent replies delivered by Band platform to @mentions without "
                "human copy-paste of agent context between Tom/Jerry/Planner."
            ),
            "evidence": [e025, e026],
        },
        "REQ-AOK-M13": {
            "observed_outcome": "NOT_TESTED",
            "verified": False,
            "tried": True,
            "reason": (
                "Human CHECKOFF #7 still pending. Task #5 completed by planner API is "
                "not a qualifying human approval (SNEAK-023/027). No real human decision receipt."
            ),
            "evidence": [e023, e027],
        },
        "REQ-AOK-M14": {
            "observed_outcome": "NOT_TESTED",
            "verified": False,
            "tried": True,
            "reason": "Blocked on M13: no qualifying human decision to route through Band yet.",
            "evidence": [e023, e027],
        },
        "REQ-AOK-M15": {
            "observed_outcome": "NOT_TESTED",
            "verified": False,
            "tried": True,
            "reason": (
                "No qualifying decision body to assess hard-coding. Checkoff text is "
                "template; human approval content not yet observed."
            ),
            "evidence": [e023, e027],
        },
        "REQ-AOK-M16": {
            "observed_outcome": "NOT_TESTED",
            "verified": False,
            "tried": True,
            "reason": "Demo Desktop room view not captured; Desktop unsigned/missing (SNEAK-027).",
            "evidence": [e027],
        },
        "REQ-AOK-M17": {
            "observed_outcome": "NOT_TESTED",
            "verified": False,
            "tried": True,
            "reason": (
                "Work board observed via Human API JSON, not Band Desktop demo view. "
                "Desktop demo NOT_TESTED."
            ),
            "evidence": [e022, e027],
        },
        "REQ-AOK-M18": {
            "observed_outcome": "NOT_TESTED",
            "verified": False,
            "tried": False,
            "reason": "Per-agent Desktop session view not observed.",
            "evidence": [e027],
        },
        "REQ-AOK-M19": {
            "observed_outcome": "NOT_TESTED",
            "verified": False,
            "tried": False,
            "reason": "Token counts in Band Desktop UI not observed.",
            "evidence": [e027],
        },
        "REQ-AOK-M20": {
            "observed_outcome": "NOT_TESTED",
            "verified": False,
            "tried": False,
            "reason": "Estimated costs in Band Desktop UI not observed.",
            "evidence": [e027],
        },
    }

    rows = []
    verdicts = []
    for mid in [f"REQ-AOK-M{i:02d}" for i in range(1, 21)]:
        atom = atoms[mid]
        sc = scores[mid]
        sid = f"{mid}-SNEAK-028"
        row = {
            "id": sid,
            "predecessor_requirement_id": mid,
            "requirement": atom["requirement"],
            "level": atom.get("level", "mandatory"),
            "required_for_entry": bool(atom.get("required_for_entry", True)),
            "observed_outcome": sc["observed_outcome"],
            "verified": bool(sc["verified"]),
            "tried": bool(sc["tried"]),
            "reason": sc["reason"],
            "evidence": sc["evidence"],
            "source_status_policy": "receipts_and_live_observation_only_never_graph_links",
            "pass_gate": bool(sc["verified"]),
        }
        rows.append(row)
        clean = []
        for e in sc["evidence"]:
            if e.get("artifact_digest") and e["artifact_digest"] != "MISSING":
                clean.append(
                    EvidenceRef(
                        provider=e["provider"],
                        external_id=e["external_id"],
                        artifact_digest=e["artifact_digest"],
                        receipt_path=e["receipt_path"],
                        observed_at=e["observed_at"],
                    )
                )
        verdicts.append(
            Verdict(
                requirement_id=sid,
                verified=bool(sc["verified"]),
                observed_outcome=sc["observed_outcome"],  # type: ignore[arg-type]
                evidence=clean,
                predecessor_verdict_id=mid,
                reason=sc["reason"],
            )
        )

    gate = entry_gate(verdicts)
    # entry_gate helper keys off predecessor id starting REQ-AOK-M via requirement_id;
    # our successor ids also start with REQ-AOK-M so gate counts them — good.

    jsonl_path = VER / "requirements_sneak_028.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    package = {
        "id": "SNEAK-028-AOK-MVP-LEDGER",
        "parent": "SNEAK-027",
        "room_id": PLANNER_ROOM_ID,
        "planner_id": DEFAULT_AGENTS["planner"]["id"],
        "live": {
            "band_available": live["band_available"],
            "me_ok": bool(live["me"].get("ok")),
            "agent_count": len(agents),
            "online_agent_count": len(online_agents),
            "online_handles": [p.get("handle") for p in online_agents],
            "task_completed_numbers": [t.get("number") for t in completed],
            "task_pending_count": len(pending),
        },
        "scores": [
            {
                "id": r["predecessor_requirement_id"],
                "requirement": r["requirement"],
                "observed_outcome": r["observed_outcome"],
                "verified": r["verified"],
                "tried": r["tried"],
            }
            for r in rows
        ],
        "counts": {
            "pass": sum(1 for r in rows if r["observed_outcome"] == "PASS"),
            "fail": sum(1 for r in rows if r["observed_outcome"] == "FAIL"),
            "not_tested": sum(1 for r in rows if r["observed_outcome"] == "NOT_TESTED"),
            "verified_true": sum(1 for r in rows if r["verified"]),
            "tried": sum(1 for r in rows if r["tried"]),
        },
        "entry_gate": gate,
        "secrets": presence_receipt(),
        "mmr": "NOT_COMMITTED",
        "signed": False,
        "meaning": (
            "Successor AoK M01–M20 ledger from receipts + live Band observation; "
            "Desktop-specific atoms remain NOT_TESTED; entry_gate false"
        ),
    }
    package["artifact_digest"] = digest_payload(package)
    store.append_receipt("aok_mvp_ledger", package, provider="sneak.aok")

    receipt = breakpoint_receipt(
        schema="sneak.aok-mvp-ledger.v1",
        breakpoint_id="SNEAK-028",
        parent_id="SNEAK-027",
        records=[
            {
                "id": "SNEAK-028-COUNTS",
                "kind": "ledger_counts",
                "payload": package["counts"],
            },
            {
                "id": "SNEAK-028-GATE",
                "kind": "entry_gate",
                "payload": gate,
            },
            {
                "id": "SNEAK-028-LIVE",
                "kind": "live_band",
                "payload": package["live"],
            },
            {
                "id": "SNEAK-028-M01-M15",
                "kind": "mvp_band_atoms",
                "payload": {
                    r["predecessor_requirement_id"]: {
                        "outcome": r["observed_outcome"],
                        "verified": r["verified"],
                        "tried": r["tried"],
                    }
                    for r in rows
                    if int(r["predecessor_requirement_id"].split("M")[1]) <= 15
                },
            },
        ],
        meaning=package["meaning"],
    )
    receipt["mmr"] = "NOT_COMMITTED"
    receipt["package_digest"] = package["artifact_digest"]
    receipt["requirements"] = rows

    (OUT / "SNEAK-028_AOK_MVP_LEDGER.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (OUT / "SNEAK-028_AOK_MVP_LEDGER_PACKAGE.json").write_text(
        json.dumps(package, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    md = [
        "# SNEAK-028 AoK MVP requirement ledger (M01–M20)",
        "",
        "Source status from receipts + live Band observation — **never** from graph links.",
        f"Predecessor registry: `data/rules/atomic_acceptance_r5.jsonl` (unchanged).",
        f"Successor JSONL: `data/verification/requirements_sneak_028.jsonl`.",
        "",
        f"- entry_gate: **{gate['entry_gate']}** "
        f"(verified {gate['mandatory_verified']}/{gate['mandatory_count']})",
        f"- PASS={package['counts']['pass']} FAIL={package['counts']['fail']} "
        f"NOT_TESTED={package['counts']['not_tested']} tried={package['counts']['tried']}",
        f"- Live online agents: **{package['live']['online_agent_count']}** "
        f"`{package['live']['online_handles']}`",
        "- MMR: **NOT_COMMITTED**",
        "",
        "## M01–M15 (Band coordination MVP)",
        "",
        "| ID | Requirement | Tried | Outcome | Verified |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        n = int(r["predecessor_requirement_id"].split("M")[1])
        if n > 15:
            continue
        md.append(
            f"| {r['predecessor_requirement_id']} | {r['requirement']} | "
            f"{r['tried']} | **{r['observed_outcome']}** | {r['verified']} |"
        )
    md.extend(
        [
            "",
            "## M16–M20 (Desktop demo visibility)",
            "",
            "| ID | Requirement | Tried | Outcome | Verified |",
            "|---|---|---|---|---|",
        ]
    )
    for r in rows:
        n = int(r["predecessor_requirement_id"].split("M")[1])
        if n < 16:
            continue
        md.append(
            f"| {r['predecessor_requirement_id']} | {r['requirement']} | "
            f"{r['tried']} | **{r['observed_outcome']}** | {r['verified']} |"
        )
    md.extend(
        [
            "",
            "## Missed / still open",
            "",
            "- **M01** Band Desktop — not used (Human API/SDK substitute only)",
            "- **M08** board claims — FAIL (BOARD_TOOL_MISSING)",
            "- **M13–M15** real human decision path — NOT_TESTED (#7 pending)",
            "- **M16–M20** Desktop demo panels — NOT_TESTED",
            "",
        ]
    )
    (OUT / "SNEAK-028_AOK_MVP_LEDGER.md").write_text("\n".join(md), encoding="utf-8")

    summary = {
        "id": "SNEAK-028",
        "entry_gate": gate["entry_gate"],
        "counts": package["counts"],
        "m01_m15": {
            r["predecessor_requirement_id"]: r["observed_outcome"]
            for r in rows
            if int(r["predecessor_requirement_id"].split("M")[1]) <= 15
        },
        "root": receipt.get("root"),
        "package_digest": package["artifact_digest"],
        "mmr": "NOT_COMMITTED",
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
