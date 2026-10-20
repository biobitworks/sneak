"""Liquid AI + OpenJev clients (Qwen 2.5 retired from baseline probes).

Liquid: OpenAI-compatible chat (LIQUID_API_KEY / LIQUID_BASE_URL).
OpenJev: System One decisions API (OPENJEV_BASE_URL, optional OPENJEV_API_KEY).
Missing credentials → NOT_TESTED; never invents PASS inference.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Optional


LIQUID_DEFAULT_MODEL = "LFM2.5-1.2B-Instruct"
LIQUID_DEFAULT_BASE = "https://api.liquid.ai/v1"
OPENJEV_DEFAULT_MODEL = "openjev-latest"
OPENJEV_DEFAULT_BASE = "https://api.codiv.ai/v1"

# Deterministic $/token schedules for ROI (not live billing quotes).
TOKEN_UNIT_COST = {
    "liquid": "0.00000003",
    "openjev": "0.00000002",
    "band-tom": "0.00000005",
    "band-jerry": "0.00000005",
    "local-stub": "0.00000001",
}


def _post_json(url: str, payload: dict[str, Any], *, headers: dict[str, str], timeout: float = 60.0) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={**headers, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return {"ok": True, "http_status": getattr(resp, "status", 200), "body": body}
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "http_status": exc.code,
            "error_type": "HTTPError",
            "observed_outcome": "FAIL",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error_type": type(exc).__name__,
            "observed_outcome": "NOT_TESTED",
        }


def estimate_tokens(text: str) -> int:
    """Deterministic token estimate (whitespace + punctuation heuristic)."""
    if not text:
        return 0
    # ~4 chars/token baseline; floor at word count.
    by_chars = max(1, (len(text) + 3) // 4)
    by_words = max(1, len(text.split()))
    return max(by_chars, by_words)


class LiquidClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key if api_key is not None else os.environ.get("LIQUID_API_KEY")
        self.base_url = (base_url or os.environ.get("LIQUID_BASE_URL") or LIQUID_DEFAULT_BASE).rstrip("/")
        self.model = model or os.environ.get("LIQUID_MODEL") or LIQUID_DEFAULT_MODEL

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def chat(self, messages: list[dict[str, str]], *, max_tokens: int = 256) -> dict[str, Any]:
        if not self.available:
            return {
                "ok": False,
                "provider": "liquid",
                "model": self.model,
                "observed_outcome": "NOT_TESTED",
                "reason": "LIQUID_API_KEY missing",
                "prompt_tokens": sum(estimate_tokens(m.get("content", "")) for m in messages),
                "completion_tokens": 0,
                "total_tokens": sum(estimate_tokens(m.get("content", "")) for m in messages),
                "text": None,
            }
        result = _post_json(
            f"{self.base_url}/chat/completions",
            {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": max_tokens,
            },
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        if not result.get("ok"):
            return {
                "ok": False,
                "provider": "liquid",
                "model": self.model,
                "observed_outcome": result.get("observed_outcome") or "FAIL",
                "error_type": result.get("error_type"),
                "http_status": result.get("http_status"),
                "prompt_tokens": sum(estimate_tokens(m.get("content", "")) for m in messages),
                "completion_tokens": 0,
                "total_tokens": sum(estimate_tokens(m.get("content", "")) for m in messages),
                "text": None,
            }
        body = result["body"]
        choice = ((body.get("choices") or [{}])[0].get("message") or {})
        text = choice.get("content") or ""
        usage = body.get("usage") or {}
        prompt_tokens = int(usage.get("prompt_tokens") or sum(estimate_tokens(m.get("content", "")) for m in messages))
        completion_tokens = int(usage.get("completion_tokens") or estimate_tokens(text))
        return {
            "ok": True,
            "provider": "liquid",
            "model": self.model,
            "observed_outcome": "PASS",
            "text": text,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": int(usage.get("total_tokens") or (prompt_tokens + completion_tokens)),
        }


class OpenJevClient:
    """OpenJev System One decisions (typed choice / yes-no / score)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key if api_key is not None else os.environ.get("OPENJEV_API_KEY")
        self.base_url = (base_url or os.environ.get("OPENJEV_BASE_URL") or OPENJEV_DEFAULT_BASE).rstrip("/")
        self.model = model or os.environ.get("OPENJEV_MODEL") or OPENJEV_DEFAULT_MODEL

    @property
    def available(self) -> bool:
        # Hosted Codiv free tier may work without key; still require explicit base.
        return bool(self.base_url)

    def decide_match(
        self,
        *,
        question: str,
        gold_answer: str,
        candidate_answer: str,
        state: Optional[str] = None,
    ) -> dict[str, Any]:
        """Ask OpenJev whether candidate matches gold (choice A/B)."""
        prompt_state = state or (
            f"Question: {question}\nGold answer: {gold_answer}\nCandidate: {candidate_answer}"
        )
        payload = {
            "model": self.model,
            "state": prompt_state,
            "questions": [
                {
                    "id": "match",
                    "type": "choice",
                    "prompt": "Does the candidate answer the question correctly relative to the gold answer?",
                    "options": [
                        {"id": "A", "label": "yes_match"},
                        {"id": "B", "label": "no_mismatch"},
                    ],
                }
            ],
        }
        headers: dict[str, str] = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        # Try systemone then decisions.
        for path in ("/systemone", "/decisions"):
            result = _post_json(f"{self.base_url}{path}", payload, headers=headers, timeout=90.0)
            if result.get("ok"):
                body = result["body"]
                answers = body.get("answers") or body.get("data") or []
                usage = body.get("usage") or {}
                prompt_tokens = int(
                    usage.get("prompt_tokens")
                    or usage.get("input_tokens")
                    or estimate_tokens(prompt_state)
                )
                completion_tokens = int(usage.get("completion_tokens") or usage.get("output_tokens") or 1)
                return {
                    "ok": True,
                    "provider": "openjev",
                    "model": self.model,
                    "observed_outcome": "PASS",
                    "path": path,
                    "answers": answers,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                    "text": json.dumps(answers, sort_keys=True)[:500],
                }
        return {
            "ok": False,
            "provider": "openjev",
            "model": self.model,
            "observed_outcome": result.get("observed_outcome") or "NOT_TESTED",
            "error_type": result.get("error_type"),
            "http_status": result.get("http_status"),
            "prompt_tokens": estimate_tokens(prompt_state),
            "completion_tokens": 0,
            "total_tokens": estimate_tokens(prompt_state),
            "text": None,
        }
