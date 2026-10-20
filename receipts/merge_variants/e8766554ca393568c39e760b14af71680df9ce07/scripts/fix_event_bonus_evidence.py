#!/usr/bin/env python3
"""Assemble Snyk/Javier event-bonus *evidence* via LOMO×merkle + BAND review.

Does NOT claim the event bonus is AWARDED (judges decide). Status is
EVIDENCE_PREPARED. Tool score scale remains 0–10 (10=clean); bonus is up to +10%.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.band_adapter import BandAdapter
from sneak.data_backend import DataBackend
from sneak.evidence import EvidenceStore, digest_payload, utc_now
from sneak.lomo import matrix_connector_trials
from sneak.lomo_score_pipeline import score_after_breakpoint
from sneak.merkle import breakpoint_receipt, leaf, root
from sneak.score import UPSTREAM_COMMIT, compute_score, score_with_coverage
from sneak.scanner import digest_tree, live_scan_availability
from sneak.secrets import export_to_environ, presence_receipt


BONUS_CRITERIA = [
    {
        "id": "J-007",
        "kind": "JUDGING_BONUS",
        "statement": "Snyk bonus up to +10%",
        "evidence_needed": "Real Snyk integration shown to judges; not auto-awarded by tool score",
    },
    {
        "id": "SNYK-001",
        "kind": "BONUS",
        "statement": "Snyk scan integrated in workflow with versioned receipt",
        "evidence_needed": "Scan bound to staged digest + Javier pin + LOMO breakpoint roots",
    },
    {
        "id": "SNYK-002",
        "kind": "BONUS",
        "statement": "Security reviewer blocks unsafe work and stores lessons in Cognee",
        "evidence_needed": "BAND security handoffs + @Data memory of findings/breakpoints",
    },
    {
        "id": "REQ-AOK-S01",
        "kind": "bonus_selected",
        "statement": "Use a real Snyk scanning product",
        "evidence_needed": "Live SCA/SAST when SNYK_TOKEN present; else NOT_TESTED",
    },
    {
        "id": "REQ-AOK-S02",
        "kind": "bonus_selected",
        "statement": "Scan the exact artifact built by the agents",
        "evidence_needed": "apps/security-demo digest bound into score receipts",
    },
]


def main() -> int:
    export_to_environ()
    out = ROOT / "receipts/connectors"
    out.mkdir(parents=True, exist_ok=True)
    store = EvidenceStore(ROOT / "local-runs/evidence-bonus")

    staged = ROOT / "apps/security-demo"
    demo_digest = digest_tree(staged)
    avail = live_scan_availability()
    parent = "SNEAK-018"

    # 1) LOMO trials → merkle breakpoints → Javier score bind + @Data + BAND
    data = DataBackend(store, live=True)
    band = BandAdapter(store, live=True)
    trials = matrix_connector_trials(parent_breakpoint=parent)
    scored_rows = []
    for trial in trials:
        for kind in ("baseline_breakpoint", "ablated_breakpoint"):
            bp = trial[kind]
            post = score_after_breakpoint(
                store=store,
                staged_path=staged,
                breakpoint_id=bp["id"],
                merkle_root=bp["root"],
                data=data,
                band=band,
                notify_band=band.live_available and kind == "ablated_breakpoint",
                wait_data_seconds=0.0,
            )
            scored_rows.append(
                {
                    "trial_id": trial["trial_id"],
                    "removed_component": trial["removed_component"],
                    "authorization_effect": trial["authorization_effect"],
                    "breakpoint_kind": kind,
                    "breakpoint_id": bp["id"],
                    "merkle_root": bp["root"],
                    "scan_outcome": post["scan"]["observed_outcome"],
                    "coverage_accepted": post["scan"]["score"]["coverage_accepted"],
                    "raw_score": post["scan"]["score"]["raw_score"],
                    "application_score": post["scan"]["score"]["application_score"],
                    "score_receipt_id": post["score_receipt_id"],
                    "data_outcome": post["data"].get("observed_outcome"),
                    "band_outcome": post["band"].get("observed_outcome"),
                }
            )

    # 2) Security-reviewer BAND role: post finding lesson to agents (bonus SNYK-002 path)
    z = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    helper = {
        "zero": compute_score(z, z),
        "incomplete_rejected": score_with_coverage(
            sca_counts=z, sast_counts=z, sca_coverage=True, sast_coverage=False
        ).to_dict(),
    }
    finding_lesson = {
        "role": "security-reviewer",
        "lesson": (
            "Incomplete SCA/SAST coverage must DENY admission; "
            "never treat missing coverage as zero findings. "
            "Bind every Javier score attempt to a LOMO merkle root."
        ),
        "javier_pin": UPSTREAM_COMMIT,
        "demo_digest": demo_digest,
    }
    data_lesson = data.write_breakpoint(
        breakpoint_id="SNEAK-019-LESSON",
        merkle_root=digest_payload(finding_lesson),
        payload=finding_lesson,
        wait_seconds=40.0,
    )

    # 3) Bonus evidence matrix (honest statuses)
    live_ready = avail.get("observed_outcome") == "READY"
    criteria_status = []
    for c in BONUS_CRITERIA:
        if c["id"] in ("J-007",):
            status = "EVIDENCE_PREPARED"
            observed = "WORKFLOW_INTEGRATED_PENDING_LIVE_SCAN" if not live_ready else "LIVE_SCAN_BOUND"
        elif c["id"] in ("SNYK-001", "REQ-AOK-S01"):
            status = "PARTIAL" if not live_ready else "PASS"
            observed = avail.get("observed_outcome")
        elif c["id"] in ("SNYK-002",):
            status = "PARTIAL"
            observed = "BAND_HANDOFFS_AND_COGNEE_LESSON_RECORDED"
        elif c["id"] in ("REQ-AOK-S02",):
            status = "PASS"
            observed = "STAGED_DIGEST_BOUND"
        else:
            status = "NOT_TESTED"
            observed = "NOT_TESTED"
        criteria_status.append({**c, "status": status, "observed_outcome": observed, "verified": False})

    bonus_package = {
        "id": "SNEAK-019-SNYK-BONUS-EVIDENCE",
        "parent": parent,
        "event_bonus_claim": "EVIDENCE_PREPARED",  # never AWARDED here
        "event_bonus_awarded": False,
        "max_event_bonus_percent": 10,
        "javier_pin": UPSTREAM_COMMIT,
        "tool_score_scale": "0-10",
        "tool_score_target": 10,
        "demo_digest": demo_digest,
        "live_snyk": avail.get("observed_outcome"),
        "breakpoint_score_count": len(scored_rows),
        "helper_checks": helper,
        "criteria": criteria_status,
        "scored_breakpoints": scored_rows,
        "lesson_data_receipt": data_lesson.external_id,
        "secrets": presence_receipt(),
        "observed_at": utc_now(),
        "meaning": (
            "Evidence package for judges regarding Snyk/+10% bonus path. "
            "Does not award the bonus. Live 10/10 still requires SNYK_TOKEN + full coverage."
        ),
    }
    package_digest = digest_payload(bonus_package)
    bonus_package["artifact_digest"] = package_digest

    data_pkg = data.write_breakpoint(
        breakpoint_id="SNEAK-019",
        merkle_root=package_digest,
        payload={
            "kind": "snyk_event_bonus_evidence",
            "event_bonus_claim": "EVIDENCE_PREPARED",
            "event_bonus_awarded": False,
            "artifact_digest": package_digest,
            "breakpoint_score_count": len(scored_rows),
            "live_snyk": avail.get("observed_outcome"),
        },
        wait_seconds=0.0,
    )

    # 4) Hashed BAND message for agent review
    msg = {
        "id": "SNEAK-019-BAND-BONUS-REVIEW",
        "kind": "bonus_evidence_review_request",
        "artifact_digest": package_digest,
        "javier_pin": UPSTREAM_COMMIT,
        "breakpoint_score_count": len(scored_rows),
        "event_bonus_claim": "EVIDENCE_PREPARED",
        "event_bonus_awarded": False,
        "live_snyk": avail.get("observed_outcome"),
        "data_receipt": data_pkg.external_id,
    }
    msg_leaf = leaf(msg).hex()
    msg_root = root([leaf(msg)]).hex()

    band_ref = None
    if band.live_available:
        band_ref = band.message_claude_and_chatgpt(
            "SNEAK-019 EVENT-BONUS EVIDENCE REVIEW (Claude/Tom + ChatGPT/Jerry).\n"
            f"Hashed message leaf={msg_leaf}\n"
            f"Hashed message root={msg_root}\n"
            f"Bonus evidence digest={package_digest}\n"
            f"Javier pin={UPSTREAM_COMMIT}; LOMO×merkle breakpoints scored={len(scored_rows)}\n"
            f"Staged app digest={demo_digest}\n"
            f"Live Snyk={avail.get('observed_outcome')}; application 10/10 not claimed.\n"
            "Claim status=EVIDENCE_PREPARED (NOT awarded). Judges may grant up to +10%.\n"
            "Please: (1) ACK leaf/root, (2) independently recompute leaf from the fields above if you can, "
            "(3) list any missing SNYK-001/002 evidence, (4) do not print secrets.\n"
            f"Cognee @Data receipts: lesson={data_lesson.external_id}, package={data_pkg.external_id}."
        )

    chain = breakpoint_receipt(
        schema="sneak.snyk-bonus-evidence.v1",
        breakpoint_id="SNEAK-019",
        parent_id=parent,
        records=[
            {
                "id": "SNEAK-019-SUMMARY",
                "kind": "bonus_summary",
                "payload": {
                    "event_bonus_claim": "EVIDENCE_PREPARED",
                    "event_bonus_awarded": False,
                    "breakpoints": len(scored_rows),
                    "live_snyk": avail.get("observed_outcome"),
                    "package_digest": package_digest,
                    "message_leaf": msg_leaf,
                    "message_root": msg_root,
                },
            },
            {
                "id": "SNEAK-019-CRITERIA",
                "kind": "bonus_criteria",
                "payload": {"criteria": criteria_status},
            },
            {
                "id": "SNEAK-019-LOMO",
                "kind": "lomo_score_rows",
                "payload": {
                    "rows": [
                        {
                            "breakpoint_id": r["breakpoint_id"],
                            "merkle_root": r["merkle_root"],
                            "scan_outcome": r["scan_outcome"],
                            "coverage_accepted": r["coverage_accepted"],
                            "application_score": r["application_score"],
                        }
                        for r in scored_rows
                    ]
                },
            },
            {
                "id": "SNEAK-019-BAND",
                "kind": "band_review",
                "payload": {
                    "message_leaf": msg_leaf,
                    "message_root": msg_root,
                    "band_receipt": band_ref.external_id if band_ref else None,
                    "band_outcome": (
                        json.loads(Path(band_ref.receipt_path).read_text())["payload"].get(
                            "observed_outcome"
                        )
                        if band_ref
                        else "SKIPPED"
                    ),
                },
            },
            {
                "id": "SNEAK-019-DATA",
                "kind": "cognee_data",
                "payload": {
                    "lesson_receipt": data_lesson.external_id,
                    "package_receipt": data_pkg.external_id,
                    "lesson_outcome": json.loads(Path(data_lesson.receipt_path).read_text())[
                        "payload"
                    ].get("observed_outcome"),
                },
            },
        ],
        meaning=(
            "Snyk event-bonus evidence chain via LOMO×merkle×Javier + BAND agent review; "
            "bonus not awarded by this receipt"
        ),
    )
    chain["event_bonus_claim"] = "EVIDENCE_PREPARED"
    chain["event_bonus_awarded"] = False
    chain["package_digest"] = package_digest
    chain["message_leaf"] = msg_leaf
    chain["message_root"] = msg_root
    chain["scored_breakpoints"] = scored_rows

    (out / "SNEAK-019_SNYK_BONUS_EVIDENCE.json").write_text(
        json.dumps(chain, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "SNEAK-019_BONUS_PACKAGE.json").write_text(
        json.dumps(bonus_package, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    by_id = {item["record"]["id"]: item["record"]["payload"] for item in chain["leaves"]}
    band_outcome = by_id.get("SNEAK-019-BAND", {}).get("band_outcome")
    lesson_outcome = by_id.get("SNEAK-019-DATA", {}).get("lesson_outcome")
    md = [
        "# SNEAK-019 Snyk event-bonus evidence (LOMO × merkle × Javier × BAND)",
        "",
        f"- Chain root: `{chain['root']}`",
        f"- Package digest: `{package_digest}`",
        f"- BAND message leaf/root: `{msg_leaf}`",
        f"- Event bonus claim: **EVIDENCE_PREPARED** (awarded=false)",
        f"- Javier pin: `{UPSTREAM_COMMIT}`",
        f"- LOMO breakpoints scored: **{len(scored_rows)}**",
        f"- Live Snyk: **{avail.get('observed_outcome')}**",
        f"- Staged digest: `{demo_digest}`",
        f"- BAND review: **{band_outcome}**",
        f"- Cognee lesson: **{lesson_outcome}**",
        "",
        "## Criteria",
        "",
        "| ID | Status | Observed |",
        "|---|---|---|",
    ]
    for c in criteria_status:
        md.append(f"| {c['id']} | {c['status']} | {c['observed_outcome']} |")
    md.extend(
        [
            "",
            "Judges decide any +10%. This package only prepares custody-bound evidence.",
            "Add `SNYK_TOKEN` to complete live SCA/SAST toward tool score 10/10.",
            "",
        ]
    )
    (out / "SNEAK-019_SNYK_BONUS_EVIDENCE.md").write_text("\n".join(md), encoding="utf-8")

    print(
        json.dumps(
            {
                "id": "SNEAK-019",
                "root": chain["root"],
                "package_digest": package_digest,
                "message_leaf": msg_leaf,
                "message_root": msg_root,
                "breakpoints": len(scored_rows),
                "event_bonus_claim": "EVIDENCE_PREPARED",
                "event_bonus_awarded": False,
                "band_outcome": band_outcome,
                "data_lesson": lesson_outcome,
                "live_snyk": avail.get("observed_outcome"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
