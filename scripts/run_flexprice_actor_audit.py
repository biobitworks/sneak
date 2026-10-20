#!/usr/bin/env python3
"""FlexPrice actor audit trail with deterministic ROI over FCO/FCG (candidate MMR).

Upstream: https://github.com/flexprice/flexprice
Live ingest requires FLEXPRICE_API_KEY in ~/.secrets/sneak/providers.env.
Does NOT claim MMR_COMMITTED or awarded Flexprice bonus.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.actor_audit import ActorAuditTrail, deterministic_roi
from sneak.evidence import EvidenceStore, digest_payload
from sneak.metering import MeteringAdapter
from sneak.secrets import export_to_environ, presence_receipt


ACTORS = [
    {"actor_id": "tom", "actor_role": "claude-harness", "action": "band_security_review", "qty": 2, "outcome_hint": None},
    {"actor_id": "jerry", "actor_role": "chatgpt-harness", "action": "band_security_review", "qty": 1, "outcome_hint": None},
    {"actor_id": "scanner", "actor_role": "snyk-gate", "action": "skill_scan_completed", "qty": 1, "outcome_hint": None},
    {"actor_id": "cognee", "actor_role": "data-memory", "action": "data_breakpoint_write", "qty": 3, "outcome_hint": None},
    {"actor_id": "human", "actor_role": "operator", "action": "pending_decision", "qty": 1, "outcome_hint": "PENDING"},
]


def main() -> int:
    export_to_environ()
    out = ROOT / "receipts/connectors"
    out.mkdir(parents=True, exist_ok=True)
    store = EvidenceStore(ROOT / "local-runs/evidence-flexprice-audit")
    audit = ActorAuditTrail(store)
    meter = MeteringAdapter(store, audit=audit)

    emitted = []
    parent = None
    for i, spec in enumerate(ACTORS):
        run_id = f"sneak-actor-{spec['actor_id']}-{i:02d}"
        if spec.get("outcome_hint") == "PENDING":
            # Force delayed provider path for human pending decision.
            meter.state.provider_up = False
            ref = meter.emit_usage(
                run_id,
                spec["action"],
                spec["qty"],
                actor_id=spec["actor_id"],
                actor_role=spec["actor_role"],
            )
            meter.state.provider_up = True
            # Still record audit FCO for pending human with zero billable qty.
            row = audit.record_action(
                actor_id=spec["actor_id"],
                actor_role=spec["actor_role"],
                action=spec["action"],
                quantity=0,
                outcome="PENDING",
                parent_fco_id=parent,
                meter_event_name=spec["action"],
                properties={"run_id": run_id, "note": "human_decision_not_approved"},
            )
        else:
            ref = meter.emit_usage(
                run_id,
                spec["action"],
                spec["qty"],
                actor_id=spec["actor_id"],
                actor_role=spec["actor_role"],
            )
            row = audit.actors[spec["actor_id"]][-1]
            if parent:
                audit.edges.append(
                    {
                        "id": f"EDGE-{row['id']}-SEQ",
                        "kind": "FCGEdge",
                        "type": "PRECEDED_BY",
                        "from": row["id"],
                        "to": parent,
                    }
                )
        parent = row["id"]
        emitted.append(
            {
                "run_id": run_id,
                "actor_id": spec["actor_id"],
                "usage_receipt": ref.external_id,
                "fco_id": row["id"],
                "fco_candidate_sha256": row["fco_candidate_sha256"],
                "roi": row["roi"],
                "usage_outcome": json.loads(Path(ref.receipt_path).read_text())["payload"].get(
                    "observed_outcome"
                ),
            }
        )

    deny = meter.emit_usage(
        "sneak-actor-deny-00",
        "skill_scan_completed",
        1,
        security_decision="DENY",
        actor_id="scanner",
        actor_role="snyk-gate",
    )

    trail = meter.actor_audit_receipt("SNEAK-020", parent_id="SNEAK-019")
    fcg = audit.build_fcg()

    package = {
        "id": "SNEAK-020-FLEXPRICE-ACTOR-AUDIT",
        "parent": "SNEAK-019",
        "upstream": "https://github.com/flexprice/flexprice",
        "live_flexprice": meter.live_flexprice,
        "availability": meter.availability(),
        "emitted": emitted,
        "deny_receipt": deny.external_id,
        "actor_summaries": trail["actor_summaries"],
        "fcg_digest": trail["fcg_digest"],
        "candidate_mmr_root": trail["root"],
        "mmr": "NOT_COMMITTED",
        "signed": False,
        "roi_helper_check": deterministic_roi(cost_units="0.02", benefit_units="1.0"),
        "secrets": presence_receipt(),
        "meaning": (
            "Per-actor FlexPrice usage audit as FCO/FCG with deterministic ROI; "
            "candidate Merkle trail is not an Overwatch MMR commitment"
        ),
    }
    package["artifact_digest"] = digest_payload(package)

    (out / "SNEAK-020_FLEXPRICE_ACTOR_AUDIT.json").write_text(
        json.dumps(trail, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "SNEAK-020_FLEXPRICE_ACTOR_PACKAGE.json").write_text(
        json.dumps(package, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "SNEAK-020_ACTOR_FCG.json").write_text(
        json.dumps(fcg, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    md = [
        "# SNEAK-020 FlexPrice actor audit (FCO / FCG / candidate MMR)",
        "",
        f"- Upstream: https://github.com/flexprice/flexprice",
        f"- Candidate Merkle root: `{trail['root']}`",
        f"- FCG digest: `{trail['fcg_digest']}`",
        f"- Live FlexPrice: **{meter.availability()['observed_outcome']}**",
        f"- MMR: **NOT_COMMITTED**",
        f"- Actors: {', '.join(sorted(trail['actor_summaries']))}",
        "",
        "## Per-actor deterministic ROI",
        "",
        "| Actor | Events | Cost | Benefit | ROI |",
        "|---|---:|---:|---:|---:|",
    ]
    for actor_id, summary in sorted(trail["actor_summaries"].items()):
        agg = summary["aggregate_roi"]
        md.append(
            f"| {actor_id} | {summary['event_count']} | {agg['cost_units']} | "
            f"{agg['benefit_units']} | {agg['roi']} |"
        )
    md.extend(
        [
            "",
            "ROI = (benefit_units − cost_units) / cost_units with ROUND_HALF_EVEN to 6 dp.",
            "Benefit schedule is fixed in `src/sneak/actor_audit.py`; not an awarded bonus.",
            "",
        ]
    )
    (out / "SNEAK-020_FLEXPRICE_ACTOR_AUDIT.md").write_text("\n".join(md), encoding="utf-8")

    print(
        json.dumps(
            {
                "id": "SNEAK-020",
                "root": trail["root"],
                "fcg_digest": trail["fcg_digest"],
                "actors": list(trail["actor_summaries"]),
                "live_flexprice": meter.live_flexprice,
                "mmr": "NOT_COMMITTED",
                "package_digest": package["artifact_digest"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
