"""Skill-review helper used by connector demos.

Intentionally boring: no dynamic eval, no credential handling.
"""

from __future__ import annotations

from typing import Any


ALLOWED_ACTIONS = frozenset({"summarize", "list_tools", "refuse"})


def review_skill_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    name = manifest.get("name")
    tools = manifest.get("tools")
    if not isinstance(name, str) or not name:
        return {"decision": "refuse", "reason": "missing_name"}
    if not isinstance(tools, list):
        return {"decision": "refuse", "reason": "missing_tools"}
    unsafe = [t for t in tools if not isinstance(t, str) or t.startswith("exec:")]
    if unsafe:
        return {"decision": "refuse", "reason": "unsafe_tools", "unsafe": unsafe}
    return {"decision": "summarize", "name": name, "tool_count": len(tools)}
