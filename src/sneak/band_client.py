"""Live BAND Human API client for coordinating Claude and ChatGPT agents."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Optional

from .secrets import export_to_environ

BAND_BASE = "https://app.band.ai/api/v1/me"

# Existing Sneak room agents (from SNEAK-012/013). Harness mapping is explicit.
DEFAULT_AGENTS = {
    "claude": {
        "id": "3926218d-8342-4667-9f07-5b556b50fb7f",
        "name": "Tom",
        "handle": "biobitworks/tom",
        "harness": "claude",
        "role": "architect",
    },
    "chatgpt": {
        "id": "8b51f295-c2e7-4aaa-99dd-5f2335dcab49",
        "name": "Jerry",
        "handle": "biobitworks/jerry",
        "harness": "chatgpt",
        "role": "builder",
    },
