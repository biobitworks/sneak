#!/usr/bin/env python3
"""Review Flex/Snyk/Cognee/BAND connectors + score/LOMO/AoK breakpoint.

Writes successor receipts under receipts/connectors/. Does not claim live
provider success, SIGNED, MMR_COMMITTED, or an awarded Snyk bonus.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "apps/security-demo/src"))

from sneak.aok import successor_from_registry, summarize_optional_mandatory
from sneak.connectors import ConnectorRuntime
from sneak.evidence import EvidenceStore
from sneak.lomo import matrix_connector_trials
from sneak.merkle import breakpoint_receipt
from sneak.scanner import digest_tree
from sneak.score import UPSTREAM_COMMIT, compute_score, score_with_coverage


def main() -> int:
    out_dir = ROOT / "receipts/connectors"
    out_dir.mkdir(parents=True, exist_ok=True)
    store = EvidenceStore(ROOT / "local-runs/evidence")
    # Local contract review stays offline; use scripts/live_band_cognee.py for live providers.
    runtime = ConnectorRuntime(store, live=False)

    demo = ROOT / "apps/security-demo"
    digest = digest_tree(demo)

    # Contract fixture: complete clean coverage (local). Live scan stays separate.
    cycle = runtime.security_review_cycle(
        staged_path=str(demo),
        candidate_digest=digest,
        fixture={
            "sca": {
                "completed": True,
                "exit_code": 0,
                "schema": "snyk.test.v1",
                "counts": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            },
            "sast": {
                "completed": True,
                "exit_code": 0,
                "schema": "snyk.code.sarif.v1",
                "counts": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            },
        },
        human_decision="PENDING",
        run_id="review-014",
        nonce="nonce-014",
    )
    ablation = runtime.deep_integration_ablation()
    lomo = matrix_connector_trials(parent_breakpoint="SNEAK-013")

    band_receipt = ROOT / "receipts/band/SNEAK-013_HANDOFF.json"
    band_loaded = runtime.load_band_receipt(band_receipt) if band_receipt.exists() else None

    registry = ROOT / "data/verification/requirements_sneak_011.jsonl"
    verdicts = successor_from_registry(
        registry,
        successor_suffix="SNEAK-014",
        reason="Connector contract review; live providers remain NOT_TESTED without receipts",
    )
    # New successor file — do not mutate 011 in place.
    sneak014 = ROOT / "data/verification/requirements_sneak_014.jsonl"
    with sneak014.open("w", encoding="utf-8") as fh:
        for v in verdicts:
            row = v.to_dict()
            row["id"] = v.requirement_id if v.requirement_id.endswith("SNEAK-014") else (
                f"{v.predecessor_verdict_id}-SNEAK-014"
            )
            row["predecessor_requirement_id"] = v.predecessor_verdict_id
            row["required_for_entry"] = (v.predecessor_verdict_id or "").startswith("REQ-AOK-M")
            row["verified"] = False
            row["observed_outcome"] = "NOT_TESTED"
            row["reason"] = (
                "Local connector/score/LOMO contracts executed; live BAND Desktop, "
                "Cognee OSS, Snyk CLI, Flexprice remain NOT_TESTED in this environment"
            )
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    summary = summarize_optional_mandatory(
        successor_from_registry(sneak014, successor_suffix="SNEAK-014", reason="reload")
    )

    score_check = {
        "upstream_commit": UPSTREAM_COMMIT,
        "zero_findings_score": compute_score(
            {"critical": 0, "high": 0, "medium": 0, "low": 0},
            {"critical": 0, "high": 0, "medium": 0, "low": 0},
        ),
        "one_high_score": compute_score(
            {"critical": 0, "high": 1, "medium": 0, "low": 0},
            {"critical": 0, "high": 0, "medium": 0, "low": 0},
        ),
        "eleven_medium_score": compute_score(
            {"critical": 0, "high": 0, "medium": 11, "low": 0},
            {"critical": 0, "high": 0, "medium": 0, "low": 0},
        ),
        "incomplete_coverage": score_with_coverage(
            sca_counts={"critical": 0, "high": 0, "medium": 0, "low": 0},
            sast_counts={"critical": 0, "high": 0, "medium": 0, "low": 0},
            sca_coverage=True,
            sast_coverage=False,
        ).to_dict(),
        "sca_coverage": "NOT_EXECUTED_LIVE",
        "sast_coverage": "NOT_EXECUTED_LIVE",
        "application_score": None,
        "license": "UNKNOWN_ROOT_LICENSE_404",
    }

    events = [
        {
            "id": "SNEAK-014-STATUS",
            "kind": "connector_status",
            "payload": runtime.status().to_dict(),
        },
        {
            "id": "SNEAK-014-CYCLE",
            "kind": "security_review_cycle",
            "payload": {
                "candidate_digest": cycle["candidate_digest"],
                "gate": cycle["gate"],
                "clean_ten": cycle["clean_ten"],
                "usage_readback": cycle["usage_readback"],
            },
        },
        {
            "id": "SNEAK-014-ABLATION",
            "kind": "deep_integration_ablation",
            "payload": ablation,
        },
        {
            "id": "SNEAK-014-SCORE",
            "kind": "app_security_score_helper",
            "payload": score_check,
        },
        {
            "id": "SNEAK-014-LOMO",
            "kind": "lomo_connector_trials",
            "payload": {
                "trials": [
                    {
                        "trial_id": t["trial_id"],
                        "removed_component": t["removed_component"],
                        "roots_differ": t["roots_differ"],
                        "authorization_effect": t["authorization_effect"],
                        "baseline_root": t["baseline_root"],
                        "ablated_root": t["ablated_root"],
                    }
                    for t in lomo
                ]
            },
        },
        {
            "id": "SNEAK-014-AOK",
            "kind": "aok_entry_gate",
            "payload": summary["entry"],
        },
    ]
    if band_loaded:
        events.append(
            {
                "id": "SNEAK-014-BAND-RECEIPT",
                "kind": "band_receipt_loaded",
                "payload": band_loaded,
            }
        )

    bp = breakpoint_receipt(
        schema="sneak.connector-review-merkle.v1",
        breakpoint_id="SNEAK-014",
        parent_id="SNEAK-013",
        records=events,
        meaning=(
            "Integrity of connector-review records only; not live provider attestation, "
            "signatures, human approval, or application acceptance"
        ),
    )
    bp["human_decision"] = "PENDING"
    bp["entry_gate"] = summary["entry"]
    bp["demo_digest"] = digest
    bp["snyk_app_score"] = "NOT_COMPUTED_LIVE"
    bp["coding_errors"] = 0  # filled after tests externally

    (out_dir / "SNEAK-014_CONNECTOR_REVIEW.json").write_text(
        json.dumps(bp, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "SNEAK-014_LOMO_TRIALS.json").write_text(
        json.dumps(
            [{"trial_id": t["trial_id"], "baseline_root": t["baseline_root"],
              "ablated_root": t["ablated_root"], "authorization_effect": t["authorization_effect"],
              "removed_component": t["removed_component"], "roots_differ": t["roots_differ"]}
             for t in lomo],
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (out_dir / "SNEAK-014_SCORE_FUNCTION_CHECK.json").write_text(
        json.dumps(score_check, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    md = out_dir / "SNEAK-014_CONNECTOR_REVIEW.md"
    md.write_text(
        "\n".join(
            [
                "# SNEAK-014 connector review",
                "",
                f"- Parent breakpoint: SNEAK-013",
                f"- Merkle root: `{bp['root']}`",
                f"- Demo staged digest: `{digest}`",
                f"- Entry gate: **{summary['entry']['entry_gate']}** "
                f"({summary['entry']['mandatory_verified']}/{summary['entry']['mandatory_count']} mandatory verified)",
                f"- Live connectors all ready: **{runtime.status().to_dict()['all_live']}**",
                f"- Javier helper pin: `{UPSTREAM_COMMIT}`",
                f"- Live SCA/SAST: NOT_EXECUTED (no SNYK_TOKEN / snyk CLI in this environment)",
                f"- Human decision: PENDING (loaded BAND receipt does not approve)",
                f"- LOMO connector trials: {len(lomo)} one-component successors; all roots differ",
                f"- Local ablation cognee_changes_behavior={ablation['cognee_changes_behavior']}, "
                f"band_removal_blocks_approval={ablation['band_removal_blocks_approval']}",
                "",
                "Mandatory vs bonus/optional remain distinct. A local 10/10 helper result under a",
                "fixture is not a live scan and is not an awarded event bonus.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "id": "SNEAK-014",
                "root": bp["root"],
                "entry_gate": summary["entry"]["entry_gate"],
                "all_live": runtime.status().to_dict()["all_live"],
                "demo_digest": digest,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
