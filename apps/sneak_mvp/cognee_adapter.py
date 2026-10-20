"""Cognee OSS adapter. Imports the real `cognee` package; never substitutes a fake store.

Run with the project venv that has cognee installed, e.g.:
    .venv/bin/python -m apps.sneak_mvp.cognee_adapter status
    .venv/bin/python -m apps.sneak_mvp.cognee_adapter demo
    .venv/bin/python -m apps.sneak_mvp.cognee_adapter write  --session S --text "..."
    .venv/bin/python -m apps.sneak_mvp.cognee_adapter recall --session S --query "..."

Every command prints a JSON receipt. Status values are explicit:
  DEPENDENCY_MISSING, LLM_NOT_ENABLED_BY_OPERATOR, LLM_NOT_CONFIGURED, REFUSED,
  CLI_MISSING, ERROR, EXECUTED.
Without --allow-llm, LLM credential variables are removed from the process so
no payload can reach an external LLM/embedding provider.
EXECUTED means the call returned; it is not acceptance of any REQ-AOK atom.
LLM credential presence is checked by variable NAME only; values are never read.
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as _dt
import hashlib
import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys

from . import LOCAL_RUNS, REPO_ROOT
from .sanitize import contains_secret, redact

MAX_PAYLOAD_CHARS = 4000
MAX_RESULT_CHARS = 2000
COGNEE_HOME = LOCAL_RUNS / "cognee"
LLM_KEY_NAMES = ("LLM_API_KEY", "OPENAI_API_KEY", "EMBEDDING_API_KEY", "ANTHROPIC_API_KEY")
SECURITY_RULE_MARKER = "SNEAK-RULE-SEC-GATE"


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def local_env() -> dict:
    """Storage confined to the gitignored local-runs tree; telemetry off."""
    return {
        "DATA_ROOT_DIRECTORY": str(COGNEE_HOME / "data"),
        "SYSTEM_ROOT_DIRECTORY": str(COGNEE_HOME / "system"),
        "CACHE_ROOT_DIRECTORY": str(COGNEE_HOME / "cache"),
        "COGNEE_LOGS_DIR": str(COGNEE_HOME / "logs"),
        "TELEMETRY_DISABLED": "1",
        "NO_COLOR": "1",
    }


def apply_local_env() -> None:
    for k, v in local_env().items():
        os.environ.setdefault(k, v)
    for d in ("data", "system", "cache", "logs"):
        (COGNEE_HOME / d).mkdir(parents=True, exist_ok=True)


def cli_path() -> str | None:
    venv_cli = REPO_ROOT / ".venv" / "bin" / "cognee-cli"
    return str(venv_cli) if venv_cli.exists() else shutil.which("cognee-cli")


def status() -> dict:
    present = importlib.util.find_spec("cognee") is not None
    version = None
    if present:
        try:
            from importlib.metadata import version as _v
            version = _v("cognee")
        except Exception:  # noqa: BLE001
            version = "UNKNOWN"
    return {
        "component": "cognee",
        "checked_at": _now(),
        "python": sys.version.split()[0],
        "cognee_importable": present,
        "cognee_version": version,
        "cli": "PRESENT" if cli_path() else "CLI_MISSING",
        "llm_key_name_present": any(n in os.environ for n in LLM_KEY_NAMES),
        "status": "AVAILABLE" if present else "DEPENDENCY_MISSING",
        "note": "Presence check only; no memory write/recall executed by status.",
    }


def check_payload(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("empty memory payload")
    if len(text) > MAX_PAYLOAD_CHARS:
        raise ValueError(f"memory payload exceeds {MAX_PAYLOAD_CHARS} chars")
    if contains_secret(text):
        raise ValueError("memory payload contains secret-like content; refused")
    return text


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _bounded(obj) -> str:
    s = json.dumps(obj, default=str, ensure_ascii=True)
    s, _ = redact(s)
    return s[:MAX_RESULT_CHARS]


def disable_llm() -> None:
    """Remove LLM credential variables from this process (names only; values never read).

    Without --allow-llm no text may leave the machine via an LLM/embedding
    provider; a code path that needs one then fails closed instead.
    """
    for name in LLM_KEY_NAMES:
        os.environ.pop(name, None)


def _import_cognee(allow_llm: bool = False):
    if importlib.util.find_spec("cognee") is None:
        return None
    if not allow_llm:
        disable_llm()
    apply_local_env()
    import cognee  # noqa: WPS433 (real dependency, lazily imported)
    return cognee


async def remember(text: str, dataset: str, session_id: str | None, allow_llm: bool = False) -> dict:
    receipt = {"op": "remember", "at": _now(), "dataset": dataset, "session_id": session_id,
               "payload_sha256": None, "status": None}
    try:
        text = check_payload(text)
    except ValueError as e:
        receipt.update(status="REFUSED", error=str(e))
        return receipt
    receipt["payload_sha256"] = _sha(text)
    if session_id is None and not allow_llm:
        # Permanent memory runs add()+cognify(), which sends text to an LLM. Requires operator opt-in.
        receipt["status"] = "LLM_NOT_ENABLED_BY_OPERATOR"
        return receipt
    cognee = _import_cognee(allow_llm)
    if cognee is None:
        receipt["status"] = "DEPENDENCY_MISSING"
        return receipt
    if session_id is None and not any(n in os.environ for n in LLM_KEY_NAMES):
        receipt["status"] = "LLM_NOT_CONFIGURED"
        return receipt
    try:
        kwargs = {"dataset_name": dataset}
        if session_id is not None:
            kwargs.update(session_id=session_id, self_improvement=False)
        result = await cognee.remember(text, **kwargs)
        receipt.update(status="EXECUTED", result_type=type(result).__name__, result_excerpt=_bounded(result))
    except Exception as e:  # noqa: BLE001 - record and fail closed
        receipt.update(status="ERROR", error=redact(f"{type(e).__name__}: {e}")[0][:500])
    return receipt


async def recall(query: str, dataset: str, session_id: str | None, allow_llm: bool = False) -> dict:
    receipt = {"op": "recall", "at": _now(), "dataset": dataset, "session_id": session_id,
               "query_sha256": _sha(query), "status": None, "results": [],
               "graph_query_link": f"cognee://{dataset}?session={session_id or ''}&query_sha256={_sha(query)}"}
    if session_id is None and not allow_llm:
        receipt["status"] = "LLM_NOT_ENABLED_BY_OPERATOR"
        return receipt
    cognee = _import_cognee(allow_llm)
    if cognee is None:
        receipt["status"] = "DEPENDENCY_MISSING"
        return receipt
    try:
        kwargs = {"session_id": session_id} if session_id else {"datasets": [dataset]}
        results = await cognee.recall(query_text=query, **kwargs)
        out = []
        for r in list(results)[:10]:
            dump = r.model_dump() if hasattr(r, "model_dump") else r
            out.append(_bounded(dump))
        receipt.update(status="EXECUTED", result_count=len(results), results=out)
    except Exception as e:  # noqa: BLE001
        receipt.update(status="ERROR", error=redact(f"{type(e).__name__}: {e}")[0][:500])
    return receipt


def decide_next_action(recall_receipt: dict) -> dict:
    """Deterministic action selection from an actual recall receipt.

    If the recalled memory carries the security-gate rule marker, the agent must
    run the scan gate before marking Done; otherwise it may proceed. A recall
    that did not EXECUTE yields BLOCKED (fail closed), never a default success.
    """
    if recall_receipt.get("status") != "EXECUTED":
        return {"action": "BLOCKED", "reason": f"recall status {recall_receipt.get('status')}"}
    hit = any(SECURITY_RULE_MARKER in r for r in recall_receipt.get("results", []))
    return {"action": "RUN_SCAN_GATE_BEFORE_DONE" if hit else "REVIEW_MEMORY_CONTEXT",
            "reason": "recalled security rule marker" if hit else "no recalled security rule; completion remains gated",
            "recall_query_sha256": recall_receipt.get("query_sha256")}


def demo_smoke(timeout: int = 180) -> dict:
    """Runs `cognee-cli demo` (bundled graph, lexical search, no LLM)."""
    cli = cli_path()
    receipt = {"op": "cli_demo", "at": _now(), "status": None}
    if not cli:
        receipt["status"] = "CLI_MISSING"
        return receipt
    run_dir = COGNEE_HOME / "runs"
    run_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.update(local_env())
    apply_local_env()
    argv = [cli, "demo", "--dataset-name", "sneak_demo", "--query", "Where does Alice live?"]
    try:
        p = subprocess.run(argv, capture_output=True, timeout=timeout, env=env, cwd=str(REPO_ROOT))
    except subprocess.TimeoutExpired:
        receipt["status"] = "ERROR"
        receipt["error"] = f"timeout after {timeout}s"
        return receipt
    out = redact(p.stdout.decode("utf-8", "replace"))[0]
    err = redact(p.stderr.decode("utf-8", "replace"))[0]
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (run_dir / f"demo_{stamp}.stdout.txt").write_text(out)
    (run_dir / f"demo_{stamp}.stderr.txt").write_text(err)
    receipt.update(
        status="EXECUTED" if p.returncode == 0 else "ERROR",
        exit_code=p.returncode, argv=argv[1:],
        stdout_sha256=_sha(out), stdout_bytes=len(out),
        stdout_excerpt=out[-800:],
        local_log=str((run_dir / f"demo_{stamp}.stdout.txt").relative_to(REPO_ROOT)),
        meaning="Bundled demo graph restored and lexically searched; not SNEAK agent memory.",
    )
    return receipt


def _main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="cognee_adapter")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    sub.add_parser("demo")
    w = sub.add_parser("write")
    w.add_argument("--dataset", default="sneak_mvp")
    w.add_argument("--session")
    w.add_argument("--text", required=True)
    r = sub.add_parser("recall")
    r.add_argument("--dataset", default="sneak_mvp")
    r.add_argument("--session")
    r.add_argument("--query", required=True)
    for sp in (w, r):
        sp.add_argument("--allow-llm", action="store_true",
                        help="operator opt-in: permit text to reach the configured LLM/embedding provider")
    a = ap.parse_args(argv)
    if a.cmd == "status":
        out = status()
    elif a.cmd == "demo":
        out = demo_smoke()
    elif a.cmd == "write":
        out = asyncio.run(remember(a.text, a.dataset, a.session, a.allow_llm))
    else:
        out = asyncio.run(recall(a.query, a.dataset, a.session, a.allow_llm))
        out["decision"] = decide_next_action(out)
    print(json.dumps(out, indent=1, sort_keys=True, default=str))
    return 0 if out.get("status") in ("EXECUTED", "AVAILABLE") else 2


if __name__ == "__main__":
    sys.exit(_main())
