"""MagicStudio / Ollama probe helpers.

Desktop Commander on magicSTUDIObox.local is the intended transport.
This module never invents inference success: unreachable hosts stay NOT_TESTED.
"""

from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from typing import Any, Optional

# From SNEAK-009 inventory
MAGICSTUDIO_DEVICE_ID = "00925fd7-ab95-4c88-89a5-963739392fc2"
MAGICSTUDIO_HOSTNAME = "magicSTUDIObox.local"
BASELINE_MODELS = ("qwen2.5:0.5b", "qwen2.5:1.5b")


def ollama_tags(base_url: str = "http://127.0.0.1:11434", timeout: float = 5.0) -> dict[str, Any]:
    try:
        req = urllib.request.Request(base_url.rstrip("/") + "/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode())
        models = []
        for m in body.get("models") or []:
            models.append(
                {
                    "name": m.get("name"),
                    "digest": m.get("digest"),
                    "size": m.get("size"),
                    "modified_at": m.get("modified_at"),
                }
            )
        return {"ok": True, "models": models, "base_url": base_url}
    except Exception as exc:  # noqa: BLE001 — probe must capture all failure modes
        return {
            "ok": False,
            "models": [],
            "base_url": base_url,
            "error": f"{type(exc).__name__}:{exc}",
            "observed_outcome": "NOT_TESTED",
        }


def ollama_generate(
    model: str,
    prompt: str = "Reply with exactly: OLLAMA_OK",
    *,
    base_url: str = "http://127.0.0.1:11434",
    timeout: float = 60.0,
) -> dict[str, Any]:
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(
        base_url.rstrip("/") + "/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode())
        text = str(body.get("response") or "")
        return {
            "ok": "OLLAMA_OK" in text,
            "model": model,
            "response_prefix": text[:120],
            "observed_outcome": "PASS" if "OLLAMA_OK" in text else "FAIL",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "model": model,
            "error": f"{type(exc).__name__}:{exc}",
            "observed_outcome": "NOT_TESTED",
        }


def local_hostname() -> str:
    try:
        return subprocess.check_output(["hostname"], text=True, timeout=5).strip()
    except Exception:  # noqa: BLE001
        return "UNKNOWN"


def probe_local_ollama(base_url: Optional[str] = None) -> dict[str, Any]:
    """Run on the machine that hosts Ollama (MagicStudio via Desktop Commander)."""
    url = base_url or os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
    host = local_hostname()
    tags = ollama_tags(url)
    tests = []
    if tags.get("ok"):
        names = {m.get("name") for m in tags.get("models") or []}
        for wanted in BASELINE_MODELS:
            # allow tag variants
            match = next((n for n in names if n == wanted or n.startswith(wanted.split(":")[0])), None)
            if match is None:
                tests.append(
                    {
                        "wanted": wanted,
                        "model": None,
                        "ok": False,
                        "observed_outcome": "NOT_TESTED",
                        "reason": "model_not_installed",
                    }
                )
                continue
            tests.append(ollama_generate(match, base_url=url))
    return {
        "schema": "sneak.magicstudio-ollama-probe.v1",
        "hostname": host,
        "is_magicstudio": host.lower().startswith("magicstudio") or host == MAGICSTUDIO_HOSTNAME,
        "expected_device_id": MAGICSTUDIO_DEVICE_ID,
        "expected_hostname": MAGICSTUDIO_HOSTNAME,
        "ollama": tags,
        "inference_tests": tests,
        "desktop_commander": {
            "transport": "REQUIRED_FOR_REMOTE_CLOUD_AGENT",
            "observed_in_this_process": False,
        },
        "observed_outcome": (
            "PASS"
            if tags.get("ok") and any(t.get("ok") for t in tests)
            else ("PARTIAL" if tags.get("ok") else "NOT_TESTED")
        ),
        "meaning": "Local Ollama probe only; not application acceptance or BAND Desktop proof",
    }


SHELL_PROBE_SCRIPT = r'''#!/bin/zsh
set -euo pipefail
echo "HOSTNAME=$(hostname)"
echo "UNAME=$(uname -a)"
command -v ollama >/dev/null && ollama list || echo "OLLAMA_CLI=MISSING"
curl -fsS --max-time 5 http://127.0.0.1:11434/api/tags | head -c 4000 || echo "OLLAMA_HTTP=DOWN"
for m in qwen2.5:0.5b qwen2.5:1.5b; do
  if ollama list 2>/dev/null | awk '{print $1}' | grep -qx "$m"; then
    out=$(ollama run "$m" "Reply with exactly: OLLAMA_OK" 2>/dev/null | tr -d '\n' | head -c 200 || true)
    echo "INFER_$m=$out"
  else
    echo "INFER_$m=NOT_INSTALLED"
  fi
done
command -v claude >/dev/null && echo "CLAUDE_CLI=$(command -v claude)" || echo "CLAUDE_CLI=MISSING"
command -v codex >/dev/null && echo "CODEX_CLI=$(command -v codex)" || echo "CODEX_CLI=MISSING"
'''
