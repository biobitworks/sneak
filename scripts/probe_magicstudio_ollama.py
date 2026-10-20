#!/usr/bin/env python3
"""Probe Ollama on the current host (run via Desktop Commander on MagicStudio).

From this cloud agent, MagicStudio is not LAN-reachable; Tom/Jerry on BAND
may relay host probes. This script is the deterministic local probe.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.band_adapter import BandAdapter
from sneak.evidence import EvidenceStore
from sneak.magicstudio import MAGICSTUDIO_DEVICE_ID, MAGICSTUDIO_HOSTNAME, SHELL_PROBE_SCRIPT, probe_local_ollama
from sneak.merkle import breakpoint_receipt
from sneak.secrets import export_to_environ


def main() -> int:
    export_to_environ()
    out_dir = ROOT / "receipts/connectors"
    out_dir.mkdir(parents=True, exist_ok=True)
    store = EvidenceStore(ROOT / "local-runs/evidence-magicstudio")

    local = probe_local_ollama()
    # Cloud agent context: record that Desktop Commander is required.
    desktop_commander = {
        "mcp_available_in_cloud_agent": False,
        "prior_device_id": MAGICSTUDIO_DEVICE_ID,
        "prior_hostname": MAGICSTUDIO_HOSTNAME,
        "self_hosted_workers_seen": "MacBook Pro workers listed; MagicStudio hostname not in worker display names",
        "lan_reachable_from_cloud_vm": False,
        "shell_probe_script_bytes": len(SHELL_PROBE_SCRIPT.encode()),
    }

    band = BandAdapter(store, live=True)
    band_msg = None
    if band.live_available:
        band_msg = band.message_claude_and_chatgpt(
            "SNEAK-017: Cloud agent cannot reach magicSTUDIObox.local or Desktop Commander MCP. "
            "Please run on MagicStudio (or report output): "
            "`ollama list` and `ollama run lfm2.5:1.2b-instruct 'Reply with exactly: OLLAMA_OK'` "
            "plus same for openjev:latest. Qwen 2.5 is retired. Also confirm hostname. "
            "We will bind results into @Data + LOMO score chain. "
            "Do not print secrets."
        )

    events = [
        {
            "id": "SNEAK-017-LOCAL-PROBE",
            "kind": "ollama_local_probe",
            "payload": {
                "hostname": local.get("hostname"),
                "is_magicstudio": local.get("is_magicstudio"),
                "observed_outcome": local.get("observed_outcome"),
                "ollama_ok": (local.get("ollama") or {}).get("ok"),
                "model_count": len((local.get("ollama") or {}).get("models") or []),
                "inference_ok_count": sum(1 for t in local.get("inference_tests") or [] if t.get("ok")),
            },
        },
        {
            "id": "SNEAK-017-DESKTOP-COMMANDER",
            "kind": "desktop_commander_status",
            "payload": desktop_commander,
        },
        {
            "id": "SNEAK-017-BAND-RELAY",
            "kind": "band_probe_request",
            "payload": (
                json.loads(Path(band_msg.receipt_path).read_text())["payload"]
                if band_msg
                else {"observed_outcome": "SKIPPED"}
            ),
        },
    ]
    bp = breakpoint_receipt(
        schema="sneak.magicstudio-probe.v1",
        breakpoint_id="SNEAK-017",
        parent_id="SNEAK-016",
        records=events,
        meaning=(
            "MagicStudio/Ollama/Desktop Commander reachability probe; "
            "NOT_TESTED until Desktop Commander executes on magicSTUDIObox.local"
        ),
    )
    bp["human_decision"] = "APPROVE_TO_USE_WHEN_REACHABLE"
    bp["observed_outcome"] = "NOT_TESTED"
    bp["shell_probe_script"] = SHELL_PROBE_SCRIPT

    (out_dir / "SNEAK-017_MAGICSTUDIO_OLLAMA.json").write_text(
        json.dumps(bp, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "SNEAK-017_MAGICSTUDIO_OLLAMA.md").write_text(
        "\n".join(
            [
                "# SNEAK-017 MagicStudio / Ollama / Desktop Commander",
                "",
                f"- Chain root: `{bp['root']}`",
                f"- Cloud local hostname: `{local.get('hostname')}` (is_magicstudio={local.get('is_magicstudio')})",
                f"- Ollama on cloud VM: **{(local.get('ollama') or {}).get('ok')}**",
                f"- Desktop Commander MCP in this cloud agent: **False**",
                f"- Expected MagicStudio device: `{MAGICSTUDIO_DEVICE_ID}` / `{MAGICSTUDIO_HOSTNAME}`",
                f"- BAND Claude/ChatGPT probe relay: "
                f"**{(events[2]['payload'] or {}).get('observed_outcome')}**",
                "",
                "## Operator / Desktop Commander next step",
                "",
                "On MagicStudio via Desktop Commander, run:",
                "",
                "```zsh",
                SHELL_PROBE_SCRIPT.strip(),
                "```",
                "",
                "Or: `python3 scripts/probe_magicstudio_ollama.py` on that host.",
                "Paste non-secret stdout back into BAND; we will append a successor receipt.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "id": "SNEAK-017",
                "root": bp["root"],
                "observed_outcome": "NOT_TESTED",
                "desktop_commander_mcp": False,
                "band_relay": (events[2]["payload"] or {}).get("observed_outcome"),
                "local_ollama": (local.get("ollama") or {}).get("ok"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
