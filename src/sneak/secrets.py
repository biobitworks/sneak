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
