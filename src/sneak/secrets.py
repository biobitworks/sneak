"""Load operator secrets from outside the repository.

Never print, log, commit, or embed secret values into receipts.
Presence/permission checks only belong in evidence.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

DEFAULT_SECRET_FILE = Path.home() / ".secrets" / "sneak" / "providers.env"


def load_secret_file(path: Path | None = None) -> dict[str, str]:
    """Parse KEY=VALUE lines. Does not export into os.environ unless asked."""
    path = Path(path or os.environ.get("SNEAK_SECRETS_FILE", DEFAULT_SECRET_FILE))
    if not path.is_file():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def export_to_environ(path: Path | None = None) -> list[str]:
    """Export allowlisted keys into process env. Returns key names only."""
    allow = {
        "BAND_USER_API_KEY",
        "BAND_PLANNER_AGENT_ID",
        "BAND_PLANNER_API_KEY",
        "COGNEE_BASE_URL",
        "COGNEE_API_KEY",
        "FLEXPRICE_API_KEY",
        "LIQUID_API_KEY",
        "LIQUID_BASE_URL",
        "LIQUID_MODEL",
        "OPENJEV_API_KEY",
        "OPENJEV_BASE_URL",
        "OPENJEV_MODEL",
        "SNYK_TOKEN",
    }
    loaded = load_secret_file(path)
    names: list[str] = []
    for k, v in loaded.items():
        if k in allow and v and k not in os.environ:
            os.environ[k] = v
            names.append(k)
        elif k in allow and v and k in os.environ:
            names.append(k)
    return sorted(set(names))


def presence_receipt(path: Path | None = None) -> dict[str, Any]:
    """Safe receipt: paths, modes, which keys exist — never values."""
    path = Path(path or os.environ.get("SNEAK_SECRETS_FILE", DEFAULT_SECRET_FILE))
    parent = path.parent
    keys = list(load_secret_file(path).keys()) if path.is_file() else []
    return {
        "path_configured": str(path),
        "parent_exists": parent.is_dir(),
        "file_exists": path.is_file(),
        "parent_mode": oct(parent.stat().st_mode & 0o777) if parent.is_dir() else None,
        "file_mode": oct(path.stat().st_mode & 0o777) if path.is_file() else None,
        "keys_present": sorted(keys),
        "env_overrides_present": sorted(
            k
            for k in (
                "BAND_USER_API_KEY",
                "BAND_PLANNER_AGENT_ID",
                "BAND_PLANNER_API_KEY",
                "COGNEE_BASE_URL",
                "COGNEE_API_KEY",
                "FLEXPRICE_API_KEY",
                "LIQUID_API_KEY",
                "OPENJEV_API_KEY",
                "SNYK_TOKEN",
            )
            if os.environ.get(k)
        ),
        "value_inspected": False,
    }
