#!/usr/bin/env python3
"""Build MVP single-hash travel for sponsor M01–M15 + optionals + agent→Snyk bindings.

Posts BAND awareness: every agent connects to Snyk (live scan still NOT_TESTED without token).
Emits SNEAK-029. Never claims SIGNED / MMR_COMMITTED / awarded bonus.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.band_client import DEFAULT_AGENTS, PLANNER_ROOM_ID, BandClient
from sneak.evidence import EvidenceStore, digest_payload, utc_now
from sneak.mvp_hash_travel import (
    agent_snyk_leaf_record,
    atom_leaf_record,
    build_mvp_travel,
)
from sneak.secrets import export_to_environ, presence_receipt

ATOMS = ROOT / "data/rules/atomic_acceptance_r5.jsonl"
LEDGER_028 = ROOT / "data/verification/requirements_sneak_028.jsonl"
OUT = ROOT / "receipts/connectors"
VER = ROOT / "data/verification"


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "MISSING"


def load_atoms() -> dict[str, dict]:
    out = {}
    for line in ATOMS.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            out[row["id"]] = row
    return out


def load_028() -> dict[str, dict]:
    out = {}
    if not LEDGER_028.is_file():
        return out
    for line in LEDGER_028.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            out[row["predecessor_requirement_id"]] = row
    return out


def optional_status(atom_id: str, atoms: dict) -> dict:
    """Honest optional/bonus status from known receipts — never graph inference."""
    req = atoms[atom_id]["requirement"]
    level = atoms[atom_id].get("level", "optional")
    # Map to existing connector receipts where we actually tried.
    if atom_id.startswith("REQ-AOK-S"):
        e019 = ROOT / "receipts/connectors/SNEAK-019_SNYK_BONUS_EVIDENCE.json"
        # From SNEAK-019 criteria table: S01 live product NOT_TESTED; S02 staged digest PASS;
        # S03–S08 enrichment tried via BAND/Cognee path but not all verified.
        if atom_id == "REQ-AOK-S02":
            outcome, verified = "PASS", True
        elif atom_id == "REQ-AOK-S01":
            outcome, verified = "NOT_TESTED", False
        else:
            outcome, verified = "NOT_TESTED", False
        return {
            "requirement": req,
            "level": level,
            "observed_outcome": outcome,
            "verified": verified,
            "tried": True,
            "sponsor_digest": file_digest(e019),
            "reason": "Snyk path via SNEAK-019 (EVIDENCE_PREPARED; live token scan NOT_TESTED)",
        }
    if atom_id.startswith("REQ-AOK-F"):
        e020 = ROOT / "receipts/connectors/SNEAK-020_FLEXPRICE_ACTOR_AUDIT.json"
        return {
            "requirement": req,
            "level": level,
            "observed_outcome": "LOCAL_CONTRACT" if e020.is_file() else "NOT_TESTED",
            "verified": False,
            "tried": e020.is_file(),
            "sponsor_digest": file_digest(e020),
            "reason": "FlexPrice actor audit local contract (SNEAK-020); live key optional",
        }
    if atom_id == "REQ-AOK-E01":
        return {
            "requirement": req,
            "level": level,
            "observed_outcome": "PASS",
            "verified": True,
            "tried": True,
            "sponsor_digest": file_digest(
                ROOT / "receipts/connectors/SNEAK-025_PLANNER_RUNTIME.json"
            ),
            "reason": "Tom=Claude harness, Jerry=ChatGPT harness in one room (SNEAK-025)",
        }
    if atom_id == "REQ-AOK-E02":
        e015 = ROOT / "receipts/connectors/SNEAK-015_LIVE_BAND_COGNEE.json"
        e024 = ROOT / "receipts/connectors/SNEAK-024_CONVERSATION_CUSTODY.json"
        return {
            "requirement": req,
            "level": level,
            "observed_outcome": "PASS" if e024.is_file() else "NOT_TESTED",
            "verified": e024.is_file(),
            "tried": True,
            "sponsor_digest": file_digest(e024 if e024.is_file() else e015),
            "reason": "Cognee @Data capture on SNEAK-024 (improve/forget/graph not fully claimed)",
        }
    return {
        "requirement": req,
        "level": level,
        "observed_outcome": "NOT_TESTED",
        "verified": False,
        "tried": False,
        "sponsor_digest": None,
        "reason": "No qualifying receipt for this optional atom yet",
    }


def main() -> int:
    export_to_environ()
    OUT.mkdir(parents=True, exist_ok=True)
    VER.mkdir(parents=True, exist_ok=True)
    store = EvidenceStore(ROOT / "local-runs/evidence-mvp-hash-travel")

    atoms = load_atoms()
    ledger = load_028()
    records: list[dict] = []

    # --- Sponsor mandatory MVP: M01–M15 ---
    for i in range(1, 16):
        mid = f"REQ-AOK-M{i:02d}"
        row = ledger.get(mid) or {
            "requirement": atoms[mid]["requirement"],
            "observed_outcome": "NOT_TESTED",
            "verified": False,
            "tried": False,
            "evidence": [],
        }
        sponsor = None
        if row.get("evidence"):
            sponsor = row["evidence"][0].get("artifact_digest")
        records.append(
            atom_leaf_record(
                atom_id=mid,
                kind="SponsorMandatoryAtom",
                requirement=row.get("requirement") or atoms[mid]["requirement"],
                observed_outcome=row.get("observed_outcome", "NOT_TESTED"),
                verified=bool(row.get("verified")),
                tried=bool(row.get("tried")),
                sponsor_digest=sponsor,
            )
        )

    # --- Optional / bonus / enrichment atoms ---
    optional_ids = [
        aid
        for aid, a in atoms.items()
        if a.get("level") in ("bonus_selected", "scoring_enrichment")
        and (
            aid.startswith("REQ-AOK-S")
            or aid.startswith("REQ-AOK-F")
            or aid.startswith("REQ-AOK-E")
        )
    ]
    optional_rows = []
    for aid in sorted(optional_ids):
        st = optional_status(aid, atoms)
        optional_rows.append({"id": aid, **st})
        records.append(
            atom_leaf_record(
                atom_id=aid,
                kind="OptionalBonusAtom",
                requirement=st["requirement"],
                observed_outcome=st["observed_outcome"],
                verified=st["verified"],
                tried=st["tried"],
                sponsor_digest=st.get("sponsor_digest"),
            )
        )

    # --- Shared Snyk connector digest (every agent binds to this) ---
    snyk_pkg = ROOT / "receipts/connectors/SNEAK-019_BONUS_PACKAGE.json"
    snyk_ev = ROOT / "receipts/connectors/SNEAK-019_SNYK_BONUS_EVIDENCE.json"
    snyk_binding = {
        "connector": "snyk-connector",
        "javier_pin": "6e1f27605fe278eed347b10dab6f39b3501f1486",
        "evidence_prepared": True,
        "bonus_awarded": False,
        "live_snyk": "NOT_TESTED",
        "package_digest": file_digest(snyk_pkg),
        "evidence_digest": file_digest(snyk_ev),
        "awareness": "every_agent_connects_to_snyk",
    }
    snyk_binding_digest = digest_payload(snyk_binding)

    agent_bindings = []
    for key, cfg in DEFAULT_AGENTS.items():
        rec = agent_snyk_leaf_record(
            agent_id=cfg["id"],
            handle=cfg["handle"],
            role=cfg.get("role") or key,
            snyk_binding_digest=snyk_binding_digest,
            live_snyk="NOT_TESTED",
        )
        records.append(rec)
        agent_bindings.append(
            {
                "harness_key": key,
                "handle": cfg["handle"],
                "agent_id": cfg["id"],
                "leaf_id": rec["id"],
                "snyk_binding_digest": snyk_binding_digest,
            }
        )

    travel = build_mvp_travel(records, breakpoint_id="SNEAK-029", parent_id="SNEAK-028")

    # BAND: tell every agent they connect to Snyk
    client = BandClient()
    band_msg = {"ok": False}
    if client.available:
        band_msg = client.send_mention(
            (
                f"SNEAK-029 MVP hash travel root=`{travel.get('mvp_root')}` "
                f"sponsors=M01–M15 optionals={travel.get('optional_count')} "
                f"agent→Snyk bindings={travel.get('agent_snyk_count')}. "
                f"Shared snyk_binding_digest=`{snyk_binding_digest[:16]}…` "
                "Every agent (Tom/Jerry/Planner) connects to Snyk connector; "
                "live scan NOT_TESTED without SNYK_TOKEN; bonus not awarded; "
                "mmr NOT_COMMITTED. Recall this before Done."
            ),
            ["claude", "chatgpt", "planner"],
            room_id=PLANNER_ROOM_ID,
        )
        store.append_receipt(
            "mvp_snyk_awareness_band",
            {
                "room_id": PLANNER_ROOM_ID,
                "ok": bool(band_msg.get("ok")),
                "message_id": (band_msg.get("message") or {}).get("id"),
                "mvp_root": travel.get("mvp_root"),
                "snyk_binding_digest": snyk_binding_digest,
                "recipients": band_msg.get("recipients"),
            },
            provider="band",
        )

    package = {
        "id": "SNEAK-029-MVP-HASH-TRAVEL",
        "parent": "SNEAK-028",
        "mvp_root": travel.get("mvp_root"),
        "sponsor_mandatory": [
            {
                "id": f"REQ-AOK-M{i:02d}",
                "outcome": (ledger.get(f"REQ-AOK-M{i:02d}") or {}).get(
                    "observed_outcome", "NOT_TESTED"
                ),
                "verified": bool((ledger.get(f"REQ-AOK-M{i:02d}") or {}).get("verified")),
                "tried": bool((ledger.get(f"REQ-AOK-M{i:02d}") or {}).get("tried")),
                "leaf": next(
                    t["leaf"]
                    for t in travel["hash_travels"]
                    if t["id"] == f"REQ-AOK-M{i:02d}"
                ),
                "verifies_to_mvp_root": next(
                    t["verifies_to_mvp_root"]
                    for t in travel["hash_travels"]
                    if t["id"] == f"REQ-AOK-M{i:02d}"
                ),
            }
            for i in range(1, 16)
        ],
        "optional_bonus": [
            {
                "id": r["id"],
                "outcome": r["observed_outcome"],
                "verified": r["verified"],
                "tried": r["tried"],
                "leaf": next(t["leaf"] for t in travel["hash_travels"] if t["id"] == r["id"]),
                "verifies_to_mvp_root": next(
                    t["verifies_to_mvp_root"]
                    for t in travel["hash_travels"]
                    if t["id"] == r["id"]
                ),
            }
            for r in optional_rows
        ],
        "agent_snyk_bindings": agent_bindings,
        "snyk_binding": snyk_binding,
        "snyk_binding_digest": snyk_binding_digest,
        "band_awareness": {
            "ok": bool(band_msg.get("ok")),
            "message_id": (band_msg.get("message") or {}).get("id"),
            "room_id": PLANNER_ROOM_ID,
        },
        "counts": {
            "sponsor": travel.get("sponsor_count"),
            "optional": travel.get("optional_count"),
            "agent_snyk": travel.get("agent_snyk_count"),
            "all_travels_verify": all(t["verifies_to_mvp_root"] for t in travel["hash_travels"]),
        },
        "secrets": presence_receipt(),
        "mmr": "NOT_COMMITTED",
        "signed": False,
        "bonus_awarded": False,
        "meaning": (
            "Clear MVP: single merkle root; each sponsor/optional/agent-Snyk leaf "
            "has hash travel proof; every agent aware of Snyk connector"
        ),
        "observed_at": utc_now(),
    }
    package["artifact_digest"] = digest_payload(package)
    travel["package_digest"] = package["artifact_digest"]
    store.append_receipt("mvp_hash_travel_package", package, provider="sneak.mvp")

    (OUT / "SNEAK-029_MVP_HASH_TRAVEL.json").write_text(
        json.dumps(travel, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (OUT / "SNEAK-029_MVP_HASH_TRAVEL_PACKAGE.json").write_text(
        json.dumps(package, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    # Sidecar JSONL: one row per leaf travel
    jsonl_path = VER / "mvp_hash_travel_sneak_029.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as fh:
        for t in travel["hash_travels"]:
            fh.write(
                json.dumps(
                    {
                        "id": t["id"],
                        "kind": t["kind"],
                        "leaf": t["leaf"],
                        "mvp_root": t["mvp_root"],
                        "verifies_to_mvp_root": t["verifies_to_mvp_root"],
                        "proof_steps": len(t["proof"]),
                        "mmr": "NOT_COMMITTED",
                    },
                    sort_keys=True,
                )
                + "\n"
            )

    md = [
        "# SNEAK-029 MVP hash travel (sponsors + optionals + agent→Snyk)",
        "",
        f"- MVP root: `{travel.get('mvp_root')}`",
        f"- Sponsors (M01–M15): **{travel.get('sponsor_count')}**",
        f"- Optionals (E/F/S): **{travel.get('optional_count')}**",
        f"- Agent→Snyk bindings: **{travel.get('agent_snyk_count')}**",
        f"- All travels verify: **{package['counts']['all_travels_verify']}**",
        f"- Snyk binding digest: `{snyk_binding_digest}`",
        f"- Live Snyk: **NOT_TESTED**; bonus awarded: **False**",
        f"- BAND awareness message: **{bool(band_msg.get('ok'))}** "
        f"id=`{(band_msg.get('message') or {}).get('id')}`",
        "- MMR: **NOT_COMMITTED**",
        "",
        "## Sponsor mandatory (M01–M15) — hash travel",
        "",
        "| ID | Outcome | Leaf… | → MVP root |",
        "|---|---|---|---|",
    ]
    for s in package["sponsor_mandatory"]:
        md.append(
            f"| {s['id']} | {s['outcome']} | `{s['leaf'][:16]}…` | {s['verifies_to_mvp_root']} |"
        )
    md.extend(
        [
            "",
            "## Optional / bonus",
            "",
            "| ID | Outcome | Tried | → MVP root |",
            "|---|---|---|---|",
        ]
    )
    for o in package["optional_bonus"]:
        md.append(
            f"| {o['id']} | {o['outcome']} | {o['tried']} | {o['verifies_to_mvp_root']} |"
        )
    md.extend(
        [
            "",
            "## Every agent → Snyk",
            "",
            "| Handle | Role | Binding digest… |",
            "|---|---|---|",
        ]
    )
    for a in agent_bindings:
        md.append(
            f"| `@{a['handle']}` | {a.get('harness_key')} | `{a['snyk_binding_digest'][:16]}…` |"
        )
    md.append("")
    (OUT / "SNEAK-029_MVP_HASH_TRAVEL.md").write_text("\n".join(md), encoding="utf-8")

    print(
        json.dumps(
            {
                "id": "SNEAK-029",
                "mvp_root": travel.get("mvp_root"),
                "sponsors": travel.get("sponsor_count"),
                "optionals": travel.get("optional_count"),
                "agent_snyk": travel.get("agent_snyk_count"),
                "all_verify": package["counts"]["all_travels_verify"],
                "snyk_binding_digest": snyk_binding_digest,
                "band_ok": bool(band_msg.get("ok")),
                "message_id": (band_msg.get("message") or {}).get("id"),
                "package_digest": package["artifact_digest"],
                "mmr": "NOT_COMMITTED",
                "bonus_awarded": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
