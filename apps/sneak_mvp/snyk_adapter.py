"""Snyk CLI adapter with a fail-closed completion gate.

    python3 -m apps.sneak_mvp.snyk_adapter scan [--target PATH] [--mode oss|code] [--persist]

- argv list (no shell), timeout, bounded output, sanitized logs in gitignored local-runs/.
- Binds target git commit, tree, dirty flag and snyk CLI version to the result.
- Exit 0 + well-formed JSON with zero issues  -> NO_ISSUES  (gate PASS only if target clean)
  Exit 1 + well-formed JSON with issues       -> FINDINGS   (gate BLOCKED)
  Exit >1, timeout, truncation, malformed JSON, inconsistent output, missing CLI,
  non-consented target                        -> ERROR/... (gate BLOCKED)
- Never fabricates findings or an empty success. Never reads credential values;
  authentication is whatever the installed CLI already has.
- `--mode code` uploads source to Snyk Code and therefore needs --allow-code-upload.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

from . import LOCAL_RUNS, REPO_ROOT
from .sanitize import contains_secret, redact

DEFAULT_TIMEOUT = 300
MAX_OUTPUT_BYTES = 20 * 1024 * 1024
PERSIST_DIR = REPO_ROOT / "receipts" / "sneak_mvp" / "scans"
SEVERITIES = ("critical", "high", "medium", "low")


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _git(target: pathlib.Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(target), *args], capture_output=True, check=True,
                          timeout=30).stdout.decode().strip()


def consented_targets() -> set:
    extra = os.environ.get("SNEAK_SCAN_CONSENTED", "")
    paths = {REPO_ROOT.resolve()}
    paths.update(pathlib.Path(p).resolve() for p in extra.split(os.pathsep) if p)
    return paths


def bind_target(target: pathlib.Path) -> dict:
    target = target.resolve()
    top = pathlib.Path(_git(target, "rev-parse", "--show-toplevel")).resolve()
    return {
        "path": str(top),
        "commit": _git(top, "rev-parse", "HEAD"),
        "tree": _git(top, "rev-parse", "HEAD^{tree}"),
        "dirty": bool(_git(top, "status", "--porcelain")),
    }


def _sarif_results(obj: dict) -> list:
    out = []
    for run in obj.get("runs") or []:
        for r in run.get("results") or []:
            loc = ((r.get("locations") or [{}])[0].get("physicalLocation") or {}).get("artifactLocation", {})
            level = r.get("level", "warning")
            out.append({"id": r.get("ruleId"), "severity": {"error": "high", "warning": "medium",
                        "note": "low"}.get(level, level), "where": loc.get("uri")})
    return out


def _oss_results(obj) -> list:
    projects = obj if isinstance(obj, list) else [obj]
    out = []
    for p in projects:
        if not isinstance(p, dict):
            raise ValueError("project entry not an object")
        if not isinstance(p.get("vulnerabilities"), list) or not isinstance(p.get("ok"), bool):
            raise ValueError("missing vulnerabilities or ok")
        for v in p.get("vulnerabilities") or []:
            out.append({"id": v.get("id"), "severity": v.get("severity"),
                        "where": f"{v.get('packageName')}@{v.get('version')}",
                        "title": v.get("title")})
    return out


def classify(exit_code, stdout: bytes, timed_out: bool = False, truncated: bool = False) -> dict:
    """Pure classification of a Snyk CLI run. Anything not clearly understood -> ERROR."""
    if timed_out:
        return {"outcome": "ERROR", "reason": "timeout", "findings": []}
    if truncated:
        return {"outcome": "ERROR", "reason": "output exceeded bound", "findings": []}
    if exit_code is None:
        return {"outcome": "ERROR", "reason": "no exit code", "findings": []}
    text = stdout.decode("utf-8", "replace").strip()
    if not text:
        return {"outcome": "ERROR", "reason": f"empty output (exit {exit_code})", "findings": []}
    try:
        obj = json.loads(text)
    except ValueError:
        return {"outcome": "ERROR", "reason": f"malformed JSON (exit {exit_code})", "findings": []}
    if exit_code >= 2 or exit_code < 0:
        msg = obj.get("error") if isinstance(obj, dict) else None
        return {"outcome": "ERROR", "reason": redact(f"snyk exit {exit_code}: {msg or 'error'}")[0][:400],
                "findings": []}
    try:
        if isinstance(obj, dict) and "runs" in obj:
            if not isinstance(obj["runs"], list) or not obj["runs"] or any(
                    not isinstance(run, dict) or not isinstance(run.get("results"), list) for run in obj["runs"]):
                raise ValueError("invalid SARIF runs")
            findings = _sarif_results(obj)
            ok_flag = None
        else:
            findings = _oss_results(obj)
            projects = obj if isinstance(obj, list) else [obj]
            ok_flag = all(p.get("ok") is True for p in projects) if projects else None
            if isinstance(obj, dict) and obj.get("error"):
                return {"outcome": "ERROR", "reason": "error field present", "findings": []}
    except (ValueError, AttributeError, TypeError, IndexError):
        return {"outcome": "ERROR", "reason": "unexpected JSON shape", "findings": []}
    if exit_code == 0:
        if findings or ok_flag is False:
            return {"outcome": "ERROR", "reason": "exit 0 but issues reported (inconsistent)", "findings": findings}
        if ok_flag is None and not (isinstance(obj, dict) and "runs" in obj):
            return {"outcome": "ERROR", "reason": "exit 0 without ok/runs evidence", "findings": []}
        return {"outcome": "NO_ISSUES", "reason": "snyk exit 0 with zero issues", "findings": []}
    # exit_code == 1
    if not findings:
        return {"outcome": "ERROR", "reason": "exit 1 but no findings parsed (inconsistent)", "findings": []}
    return {"outcome": "FINDINGS", "reason": f"{len(findings)} issue(s)", "findings": findings}


def gate(classification: dict, binding: dict | None) -> str:
    if classification.get("outcome") != "NO_ISSUES":
        return "BLOCKED"
    if not binding or binding.get("dirty") is not False or not binding.get("commit"):
        return "BLOCKED"
    return "PASS"


def _severity_counts(findings: list) -> dict:
    counts = {s: 0 for s in SEVERITIES}
    for f in findings:
        s = str(f.get("severity", "")).lower()
        counts[s] = counts.get(s, 0) + 1
    return counts


def run_scan(target: pathlib.Path, mode: str = "oss", timeout: int = DEFAULT_TIMEOUT,
             allow_code_upload: bool = False, snyk_bin: str | None = None) -> dict:
    receipt = {"schema": "sneak.snyk-receipt.v1", "started_at": _now(), "mode": mode,
               "target": None, "outcome": None, "gate": "BLOCKED"}
    target = pathlib.Path(target).resolve()
    if target not in consented_targets():
        receipt.update(outcome="NOT_CONSENTED", reason="target not in consented set")
        return receipt
    if mode == "code" and not allow_code_upload:
        receipt.update(outcome="NOT_CONSENTED", reason="snyk code uploads source; --allow-code-upload required")
        return receipt
    snyk = snyk_bin or shutil.which("snyk")
    if not snyk:
        receipt.update(outcome="NOT_AVAILABLE", reason="snyk CLI not found")
        return receipt
    try:
        binding = bind_target(target)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        receipt.update(outcome="ERROR", reason="target is not a readable git repository")
        return receipt
    receipt["target"] = {k: v for k, v in binding.items() if k != "path"}
    receipt["target"]["name"] = pathlib.Path(binding["path"]).name
    try:
        ver = subprocess.run([snyk, "--version"], capture_output=True, timeout=30).stdout.decode().strip()
    except (subprocess.TimeoutExpired, OSError):
        ver = "UNKNOWN"
    receipt["snyk_cli_version"] = redact(ver)[0][:64]
    argv = [snyk, "code", "test", "--json"] if mode == "code" else [snyk, "test", "--json"]
    receipt["argv"] = argv[1:]
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = LOCAL_RUNS / "snyk" / stamp
    run_dir.mkdir(parents=True, exist_ok=True)
    timed_out = truncated = False
    exit_code = None
    with tempfile.TemporaryFile(dir=run_dir) as out, tempfile.TemporaryFile(dir=run_dir) as err:
        try:
            p = subprocess.run(argv, stdout=out, stderr=err, timeout=timeout, cwd=binding["path"],
                               stdin=subprocess.DEVNULL)
            exit_code = p.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
        out.seek(0, 2)
        truncated = out.tell() > MAX_OUTPUT_BYTES
        out.seek(0)
        err.seek(0)
        stdout = out.read(MAX_OUTPUT_BYTES)
        stderr = err.read(256 * 1024)
    clean_out, n_out = redact(stdout.decode("utf-8", "replace"))
    clean_err, n_err = redact(stderr.decode("utf-8", "replace"))
    (run_dir / "stdout.json").write_text(clean_out)
    (run_dir / "stderr.txt").write_text(clean_err)
    c = classify(exit_code, stdout, timed_out, truncated)
    findings = [{k: redact(str(v))[0][:200] for k, v in f.items()} for f in c["findings"]]
    try:
        bound_after = bind_target(target)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        bound_after = None
    if not bound_after or any(bound_after[k] != binding[k] for k in ("commit", "tree", "dirty")):
        c = {"outcome": "ERROR", "reason": "target commit changed during scan", "findings": c["findings"]}
    receipt.update(
        finished_at=_now(), exit_code=exit_code, outcome=c["outcome"], reason=c["reason"],
        finding_count=len(findings), severity_counts=_severity_counts(findings), findings=findings[:50],
        stdout_sha256=hashlib.sha256(stdout).hexdigest(), stdout_bytes=len(stdout),
        redactions=n_out + n_err, local_run_dir=str(run_dir.relative_to(REPO_ROOT)),
    )
    receipt["gate"] = gate(c, binding)
    (run_dir / "receipt.json").write_text(json.dumps(receipt, indent=1, sort_keys=True))
    return receipt


def persist(receipt: dict) -> pathlib.Path:
    """Write a sanitized receipt to receipts/ only if it is provably free of secret patterns."""
    data = json.dumps(receipt, indent=1, sort_keys=True)
    if receipt.get("redactions") or contains_secret(data):
        raise ValueError("receipt not safe to persist (redactions or secret-like content)")
    PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    name = f"SNYK_{receipt['started_at'][:19].replace(':', '').replace('-', '')}.json"
    path = PERSIST_DIR / name
    if path.exists():
        raise ValueError("refusing to overwrite an existing receipt")
    path.write_text(data + "\n")
    return path


def latest_receipt() -> dict | None:
    """Latest persisted receipt, else latest local run, else None."""
    for base, pattern in ((PERSIST_DIR, "SNYK_*.json"), (LOCAL_RUNS / "snyk", "*/receipt.json")):
        files = sorted(base.glob(pattern)) if base.exists() else []
        if files:
            try:
                r = json.loads(files[-1].read_text())
                r["_source"] = "persisted" if base == PERSIST_DIR else "local-run"
                return r
            except ValueError:
                return {"outcome": "ERROR", "gate": "BLOCKED", "reason": "unreadable receipt"}
    return None


def _main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="snyk_adapter")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("--target", default=str(REPO_ROOT))
    s.add_argument("--mode", choices=("oss", "code"), default="oss")
    s.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    s.add_argument("--allow-code-upload", action="store_true")
    s.add_argument("--persist", action="store_true")
    a = ap.parse_args(argv)
    r = run_scan(pathlib.Path(a.target), a.mode, a.timeout, a.allow_code_upload)
    if a.persist:
        try:
            r["persisted_to"] = str(persist(r).relative_to(REPO_ROOT))
        except ValueError as e:
            r["persist_refused"] = str(e)
    print(json.dumps(r, indent=1, sort_keys=True))
    return 0 if r["gate"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(_main())
