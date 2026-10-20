#!/usr/bin/env python3
"""Exercise live Cognee storage + BAND Claude/ChatGPT messaging.

Secrets load from ~/.secrets/sneak/providers.env (never printed or committed).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.band_adapter import BandAdapter
from sneak.evidence import EvidenceStore
from sneak.memory import ADMITTED, MemoryAdapter
from sneak.merkle import breakpoint_receipt
from sneak.secrets import export_to_environ, presence_receipt


def main() -> int:
    export_to_environ()
    out_dir = ROOT / "receipts/connectors"
    out_dir.mkdir(parents=True, exist_ok=True)
    store = EvidenceStore(ROOT / "local-runs/evidence-live")

    band = BandAdapter(store, live=True)
    memory = MemoryAdapter(store, live=True)

    band_status = band.availability()
    cognee_status = memory.availability()

    # 1) Cognee as data storage: write + cognify + recall
    mem_ref = memory.remember(
        {
            "dataset": ADMITTED,
            "writer": "sneak-live-runner",
            "wait_seconds": 60,
            "content": {
                "finding": "live-block-eval-must-deny",
                "text": (
                    "SNEAK live: store security finding in Cognee. "
                    "Claude(Tom) and ChatGPT(Jerry) must recall block-eval-must-deny "
                    "before marking a BAND work item Done."
                ),
            },
        }
    )
    recalled = memory.recall("block-eval-must-deny", ADMITTED)

    # 2) BAND message to Claude + ChatGPT harness agents
    dual = band.message_claude_and_chatgpt(
        "SNEAK-015: Cognee now holds finding live-block-eval-must-deny. "
        "Claude (Tom): acknowledge and propose the next board task. "
        "ChatGPT (Jerry): confirm you will recall this finding before Done. "
        "Human decision remains PENDING until Byron replies in-band."
    )

    # Optional single handoffs
    to_claude = band.publish_handoff(
        "SNEAK-015-claude",
        "claude",
        [mem_ref],
        request_id="sneak-015-claude",
        message=(
            "Architect path: use Cognee recall of live-block-eval-must-deny "
            "before approving any eval-related skill admission."
        ),
    )
    to_chatgpt = band.publish_handoff(
        "SNEAK-015-chatgpt",
        "chatgpt",
        [mem_ref],
        request_id="sneak-015-chatgpt",
        message=(
            "Builder path: implement the security-demo fix only after recalling "
            "Cognee finding live-block-eval-must-deny."
        ),
    )

    events = [
        {
            "id": "SNEAK-015-SECRETS",
            "kind": "secret_presence",
            "payload": presence_receipt(),
        },
        {
            "id": "SNEAK-015-BAND-STATUS",
            "kind": "band_status",
            "payload": {
                k: band_status[k]
                for k in band_status
                if k != "secrets"
            },
        },
        {
            "id": "SNEAK-015-COGNEE-STATUS",
            "kind": "cognee_status",
            "payload": cognee_status,
        },
        {
            "id": "SNEAK-015-COGNEE-WRITE",
            "kind": "cognee_remember",
            "payload": {
                "receipt_id": mem_ref.external_id,
                "artifact_digest": mem_ref.artifact_digest,
                "recalled_count": len(recalled),
                "recalled_preview": [
                    {
                        "record_id": r.get("record_id"),
                        "provider": r.get("provider"),
                        "text_prefix": str((r.get("content") or {}).get("text", ""))[:160],
                    }
                    for r in recalled[:3]
                ],
                "observed_outcome": "PASS" if recalled else "FAIL",
            },
        },
        {
            "id": "SNEAK-015-BAND-DUAL",
            "kind": "band_claude_chatgpt_message",
            "payload": json.loads(Path(dual.receipt_path).read_text())["payload"],
        },
        {
            "id": "SNEAK-015-BAND-CLAUDE",
            "kind": "band_handoff_claude",
            "payload": {
                "receipt_id": to_claude.external_id,
                "digest": to_claude.artifact_digest,
            },
        },
        {
            "id": "SNEAK-015-BAND-CHATGPT",
            "kind": "band_handoff_chatgpt",
            "payload": {
                "receipt_id": to_chatgpt.external_id,
                "digest": to_chatgpt.artifact_digest,
            },
        },
    ]

    bp = breakpoint_receipt(
        schema="sneak.live-band-cognee.v1",
        breakpoint_id="SNEAK-015",
        parent_id="SNEAK-014",
        records=events,
        meaning=(
            "Live Cognee storage + BAND Claude/ChatGPT messaging integrity only; "
            "not Desktop UI proof, human approval, Snyk bonus, or entry_gate=true"
        ),
    )
    bp["human_decision"] = "PENDING"
    bp["signed"] = False
    bp["mmr"] = "NOT_COMMITTED"

    (out_dir / "SNEAK-015_LIVE_BAND_COGNEE.json").write_text(
        json.dumps(bp, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "SNEAK-015_LIVE_BAND_COGNEE.md").write_text(
        "\n".join(
            [
                "# SNEAK-015 live BAND + Cognee",
                "",
                f"- Merkle root: `{bp['root']}`",
                f"- BAND live: **{band_status.get('observed_outcome')}** room `{band_status.get('room_id')}`",
                f"- Harness map: Claude→{band_status.get('harness_map', {}).get('claude')}, "
                f"ChatGPT→{band_status.get('harness_map', {}).get('chatgpt')}",
                f"- Cognee live: **{cognee_status.get('observed_outcome')}** dataset `{cognee_status.get('dataset')}`",
                f"- Cognee recall hits: **{len(recalled)}**",
                f"- Dual-harness message outcome: "
                f"**{json.loads(Path(dual.receipt_path).read_text())['payload'].get('observed_outcome')}**",
                f"- Human decision: PENDING",
                "",
                "Secret values are not included. SNYK_TOKEN was not used in this step.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "id": "SNEAK-015",
                "root": bp["root"],
                "band": band_status.get("observed_outcome"),
                "cognee": cognee_status.get("observed_outcome"),
                "recalled": len(recalled),
                "dual_message": json.loads(Path(dual.receipt_path).read_text())["payload"].get(
                    "observed_outcome"
                ),
            },
            indent=2,
        )
    )
    return 0 if recalled and band_status.get("observed_outcome") == "READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
