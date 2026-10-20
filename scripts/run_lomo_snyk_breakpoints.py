#!/usr/bin/env python3
"""Approved path: BAND communication + Cognee @Data backend + Snyk/score per LOMO breakpoint."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.band_adapter import BandAdapter
from sneak.data_backend import DataBackend
from sneak.evidence import EvidenceStore
from sneak.lomo_score_pipeline import run_connector_lomo_with_scores
from sneak.secrets import export_to_environ, presence_receipt


def main() -> int:
    export_to_environ()
    out = ROOT / "receipts/connectors"
    out.mkdir(parents=True, exist_ok=True)
    store = EvidenceStore(ROOT / "local-runs/evidence-lomo-score")

    # Record operator approval (this turn) for BAND + Cognee @Data usage.
    band = BandAdapter(store, live=True)
    approval = band.record_decision(
        "SNEAK-H-APPROVE-BAND-COGNEE-DATA",
        "APPROVE",
        "Operator approved BAND.ai for communication and Cognee as @Data backend; "
        "Snyk+score required after each LOMO merkle breakpoint.",
    )
    if band.live_available:
        band.message_claude_and_chatgpt(
            "Human APPROVED: use BAND for communication and Cognee as @Data backend. "
            "After every LOMO×merkle breakpoint, run Snyk and app-security-score before Done."
        )

    result = run_connector_lomo_with_scores(
        store=store,
        staged_path=ROOT / "apps/security-demo",
        parent_breakpoint="SNEAK-015",
        live=True,
        notify_band=True,
    )

    # Final @Data recall check
    data = DataBackend(store, live=True)
    recalled = data.recall("LOMO breakpoint merkle_root")

    chain = result["chain"]
    chain["human_decision"] = "APPROVE"
    chain["approval_receipt_id"] = approval.external_id
    chain["data_alias"] = "@Data"
    chain["data_recall_hits"] = len(recalled)
    chain["summary"] = {
        k: result["summary"][k]
        for k in (
            "trial_count",
            "breakpoint_score_count",
            "any_clean_ten",
            "live_snyk",
            "data_backend",
        )
    }
    # Strip secret key names only — presence receipt already safe
    chain["secret_presence"] = presence_receipt()
    chain["scored_breakpoints"] = result["summary"]["scored_breakpoints"]

    (out / "SNEAK-016_LOMO_SNYK_SCORE.json").write_text(
        json.dumps(chain, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    rows = result["summary"]["scored_breakpoints"]
    md = [
        "# SNEAK-016 LOMO × merkle × Snyk/score",
        "",
        f"- Parent: SNEAK-015",
        f"- Chain root: `{chain['root']}`",
        f"- Human decision: **APPROVE** (BAND + Cognee @Data)",
        f"- Breakpoints scored: **{len(rows)}**",
        f"- Live Snyk availability: **{result['summary']['live_snyk']}**",
        f"- Any clean 10/10 with full coverage: **{result['summary']['any_clean_ten']}**",
        f"- @Data recall hits (final): **{len(recalled)}**",
        "",
        "| Trial | Breakpoint | Merkle root (16) | Scan | Coverage | App score | @Data |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        md.append(
            f"| {r['trial_id']} | `{r['breakpoint_id']}` | `{r['merkle_root'][:16]}…` | "
            f"{r['scan_outcome']} | {r['coverage_accepted']} | {r['application_score']} | "
            f"{r['data_outcome']} |"
        )
    md.extend(
        [
            "",
            "Incomplete SCA/SAST coverage cannot yield application 10/10. "
            "Add `SNYK_TOKEN` to `~/.secrets/sneak/providers.env` for live scans.",
            "Secret values are not included in this receipt.",
            "",
        ]
    )
    (out / "SNEAK-016_LOMO_SNYK_SCORE.md").write_text("\n".join(md), encoding="utf-8")

    print(
        json.dumps(
            {
                "id": "SNEAK-016",
                "root": chain["root"],
                "breakpoints": len(rows),
                "live_snyk": result["summary"]["live_snyk"],
                "any_clean_ten": result["summary"]["any_clean_ten"],
                "data_ready": result["summary"]["data_backend"].get("observed_outcome"),
                "human_decision": "APPROVE",
            },
            indent=2,
        )
    )
    # Exit 0 even when Snyk NOT_TESTED — pipeline executed; token is operator gate.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
