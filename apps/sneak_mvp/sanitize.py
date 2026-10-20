"""Pattern-based credential redaction. Never reads environment secret values.

Detection is conservative and pattern-only: a clean result is NOT proof that
no secret is present, only that none of these patterns matched.
"""
from __future__ import annotations

import json
import re

REDACTED = "[REDACTED]"

_PATTERNS = [
    # KEY=value / KEY: value for credential-ish names (env dumps, CLI echoes)
    re.compile(r"(?i)\b([A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|PASSWD|API_?KEY|ACCESS_?KEY|PRIVATE_?KEY|AUTH)[A-Z0-9_]*)"
               r"(\s*[=:]\s*)(\"[^\"]*\"|'[^']*'|[^\s,;\"']+)"),
    # JSON "token": "..." style
    re.compile(r"(?i)(\"(?:[a-z0-9_\-]*(?:token|secret|password|api_?key|apikey|authorization)[a-z0-9_\-]*)\"\s*:\s*)"
               r"(\"[^\"]*\")"),
    re.compile(r"(?i)\b(bearer|token|basic)(\s+)([A-Za-z0-9\-._~+/]{16,}=*)"),
]
_STANDALONE = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_\-]{20,}"),       # Anthropic/OpenAI style
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"),                   # GitHub tokens
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),                           # AWS access key id
    re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}"),                # Slack
    re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}"),  # JWT
]


def redact(text: str) -> tuple[str, int]:
    """Return (redacted_text, number_of_redactions)."""
    count = 0

    def _kv(m: re.Match) -> str:
        nonlocal count
        value = m.group(m.lastindex)
        if value.strip("\"'") in ("", REDACTED):
            return m.group(0)
        count += 1
        return m.group(0)[: m.start(m.lastindex) - m.start(0)] + REDACTED

    for pat in _PATTERNS:
        text = pat.sub(_kv, text)
    for pat in _STANDALONE:
        text, n = pat.subn(REDACTED, text)
        count += n
    return text, count


def contains_secret(text: str) -> bool:
    return redact(text)[1] > 0


def assert_clean_json(obj) -> bytes:
    """Serialize obj; raise ValueError (fail closed) if any secret pattern matches."""
    data = json.dumps(obj, sort_keys=True, ensure_ascii=True, indent=1)
    if contains_secret(data):
        raise ValueError("secret-like content detected; refusing to emit")
    return data.encode("ascii")
