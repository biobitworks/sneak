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
