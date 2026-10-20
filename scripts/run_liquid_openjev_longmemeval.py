#!/usr/bin/env python3
"""Liquid AI + OpenJev LongMemEval scenarios as Conversation/Diff FCOs with token ROI.

Qwen 2.5 is retired. Live calls need LIQUID_API_KEY / OPENJEV_*; otherwise
NOT_TESTED. Does not claim MMR_COMMITTED or validated detector performance.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.conversation_fco import ConversationEvalHarness
from sneak.evidence import EvidenceStore, digest_payload
from sneak.secrets import export_to_environ, presence_receipt


def main() -> int:
    export_to_environ()
    out = ROOT / "receipts/connectors"
    out.mkdir(parents=True, exist_ok=True)
    fixture = ROOT / "data/fixtures/longmemeval_oracle_sample.json"
    store = EvidenceStore(ROOT / "local-runs/evidence-liquid-openjev")
    harness = ConversationEvalHarness(store)
    receipt = harness.run_fixture(fixture)

    package = {
        "id": "SNEAK-021-LIQUID-OPENJEV-LONGMEMEVAL",
        "parent": "SNEAK-020",
        "qwen25_retired": True,
        "models_baseline": ["liquid", "openjev"],
        "fixture": str(fixture.relative_to(ROOT)),
        "scenario_count": len(receipt.get("scenarios") or []),
        "conversation_fco_count": len(harness.conversation_fcos),
        "diff_fco_count": len(harness.diff_fcos),
        "token_roi_rows": receipt.get("token_roi_rows"),
        "candidate_root": receipt.get("root"),
        "mmr": "NOT_COMMITTED",
        "signed": False,
        "liquid_available": harness.liquid.available,
        "openjev_base": harness.openjev.base_url,
        "secrets": presence_receipt(),
        "meaning": (
            "Each conversation is an FCO; each LongMemEval answer diff is an FCO; "
            "ROI shown per token for each model/agent/scenario"
        ),
    }
    package["artifact_digest"] = digest_payload(package)

    (out / "SNEAK-021_LIQUID_OPENJEV_LONGMEMEVAL.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "SNEAK-021_LIQUID_OPENJEV_PACKAGE.json").write_text(
        json.dumps(package, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    md = [
        "# SNEAK-021 Liquid AI + OpenJev × LongMemEval (FCO + token ROI)",
        "",
        "- Qwen 2.5: **retired**",
        "- Models: **Liquid AI LFM** + **OpenJev**",
        f"- Candidate Merkle root: `{receipt.get('root')}`",
        f"- Conversation FCOs: **{len(harness.conversation_fcos)}**",
        f"- LongMemEval diff FCOs: **{len(harness.diff_fcos)}**",
        f"- Live Liquid key: **{harness.liquid.available}**",
        "- MMR: **NOT_COMMITTED**",
        "",
        "## Per-token ROI by scenario / model / agent",
        "",
        "| Scenario | Model | Agent | Tokens | Cost | Benefit | ROI | Benefit/token |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in receipt.get("token_roi_rows") or []:
        tr = row["token_roi"]
        md.append(
            f"| {row['scenario_id']} | {row['model_provider']} | {row['agent_id']} | "
            f"{tr['total_tokens']} | {tr['cost_units']} | {tr['benefit_units']} | "
            f"{tr['roi']} | {tr['benefit_per_token']} |"
        )
    md.extend(
        [
            "",
            "Full LongMemEval corpus stays under `sources/` (gitignored) when downloaded;",
            "this run uses `data/fixtures/longmemeval_oracle_sample.json`.",
            "",
        ]
    )
    (out / "SNEAK-021_LIQUID_OPENJEV_LONGMEMEVAL.md").write_text("\n".join(md), encoding="utf-8")

    print(
        json.dumps(
            {
                "id": "SNEAK-021",
                "root": receipt.get("root"),
                "conversations": len(harness.conversation_fcos),
                "diffs": len(harness.diff_fcos),
                "token_roi_rows": len(receipt.get("token_roi_rows") or []),
                "qwen25_retired": True,
                "liquid_available": harness.liquid.available,
                "mmr": "NOT_COMMITTED",
                "package_digest": package["artifact_digest"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
