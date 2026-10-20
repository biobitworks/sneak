"""Snyk scan normalization and staged-target binding.

Live scans require SNYK_TOKEN outside the repo and a working CLI/Docker path.
Without credentials or CLI, observed_outcome stays NOT_TESTED / BLOCKED.
Never place SNYK_TOKEN in prompts, logs, receipts, or candidate environments.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .score import ScoreResult, score_with_coverage

KNOWN_SCHEMAS = {"snyk.test.v1", "snyk.code.sarif.v1", "sneak.scan.normalized.v1"}


@dataclass
class ScanStage:
    name: str
    completed: bool
    exit_code: Optional[int]
    schema: Optional[str]
    counts: dict[str, int] = field(default_factory=lambda: {"critical": 0, "high": 0, "medium": 0, "low": 0})
    raw_ref: Optional[str] = None
    error: Optional[str] = None


@dataclass
class ScanResult:
    candidate_digest: str
    staged_path: str
    scanner_identity: str
    sca: ScanStage
    sast: ScanStage
    score: ScoreResult
    observed_outcome: str
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_digest": self.candidate_digest,
            "staged_path": self.staged_path,
            "scanner_identity": self.scanner_identity,
            "sca": self.sca.__dict__,
            "sast": self.sast.__dict__,
            "score": self.score.to_dict(),
            "observed_outcome": self.observed_outcome,
            "reasons": self.reasons,
        }


def digest_tree(path: Path) -> str:
    """Deterministic digest of regular files under a staged path."""
    root = Path(path)
    records: list[tuple[str, str]] = []
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.is_symlink():
            continue
        rel = p.relative_to(root).as_posix()
        if any(part.startswith(".") and part not in (".",) for part in p.parts):
            # Include hidden files that are part of the staged app; skip .git etc. only at root.
            pass
        if "/.git/" in ("/" + rel + "/") or rel.startswith(".git/"):
            continue
        records.append((rel, hashlib.sha256(p.read_bytes()).hexdigest()))
    payload = "|".join(f"{a}:{b}" for a, b in records)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def normalize_scan(
    *,
    candidate_digest: str,
    staged_path: str,
    sca: ScanStage,
    sast: ScanStage,
    scanner_identity: str = "snyk-cli+javier-score@6e1f276",
) -> ScanResult:
    reasons: list[str] = []

    for stage in (sca, sast):
        if stage.exit_code in (2, 3):
            reasons.append(f"{stage.name}_exit_{stage.exit_code}")
            stage.completed = False
            stage.error = stage.error or f"scanner_exit_{stage.exit_code}"
        if stage.completed and stage.schema and stage.schema not in KNOWN_SCHEMAS:
            reasons.append(f"{stage.name}_unknown_schema")
            stage.completed = False
        if stage.error:
            reasons.append(f"{stage.name}_error")
            stage.completed = False

    score = score_with_coverage(
        sca_counts=sca.counts if sca.completed else None,
        sast_counts=sast.counts if sast.completed else None,
        sca_coverage=sca.completed and sca.error is None,
        sast_coverage=sast.completed and sast.error is None,
    )
    if not score.coverage_accepted:
        reasons.append(score.reject_reason or "coverage_rejected")

    if reasons:
        outcome = "DENIED"
    elif score.raw_score == 10.0:
        outcome = "PASS"
    else:
        outcome = "FAIL"

    return ScanResult(
        candidate_digest=candidate_digest,
        staged_path=staged_path,
        scanner_identity=scanner_identity,
        sca=sca,
        sast=sast,
        score=score,
        observed_outcome=outcome,
        reasons=reasons,
    )


def token_present_outside_process_env_file(secret_path: Path) -> dict[str, Any]:
    """Presence/permission check only — never read or hash token values into receipts."""
    path = Path(secret_path)
    parent = path.parent
    result: dict[str, Any] = {
        "path_configured": str(path),
        "parent_exists": parent.is_dir(),
        "file_exists": path.is_file(),
        "parent_mode": oct(parent.stat().st_mode & 0o777) if parent.is_dir() else None,
        "file_mode": oct(path.stat().st_mode & 0o777) if path.is_file() else None,
        "env_token_exported": bool(os.environ.get("SNYK_TOKEN")),
        "snyk_cli": shutil.which("snyk"),
        "value_inspected": False,
    }
    return result


def resolve_snyk_cli() -> Optional[str]:
    """Locate snyk CLI without requiring a global install."""
    env_cli = os.environ.get("SNYK_CLI")
    if env_cli and Path(env_cli).is_file():
        return env_cli
    which = shutil.which("snyk")
    if which:
        return which
    for candidate in (
        Path("/tmp/snyk-cli/node_modules/.bin/snyk"),
        Path.home() / ".local/bin/snyk",
    ):
        if candidate.is_file():
            return str(candidate)
    return None


def live_scan_availability() -> dict[str, Any]:
    from .secrets import export_to_environ

    export_to_environ()
    cli = resolve_snyk_cli()
    token = bool(os.environ.get("SNYK_TOKEN"))
    return {
        "snyk_cli": cli,
        "docker": shutil.which("docker"),
        "token_in_env": token,
        "observed_outcome": "READY" if cli and token else "NOT_TESTED",
    }


def scan(
    candidate_digest: str,
    staged_path: str,
    *,
    fixture: Optional[dict[str, Any]] = None,
) -> ScanResult:
    """Scan interface.

    If fixture is provided (tests only), normalize that fixture against the digest.
    Otherwise report BLOCKED/NOT_TESTED without inventing clean findings.
    """
    path = Path(staged_path)
    actual = digest_tree(path) if path.exists() else ""
    if candidate_digest and actual and candidate_digest != actual:
        sca = ScanStage("sca", False, None, None, error="stale_or_mismatched_candidate_digest")
        sast = ScanStage("sast", False, None, None, error="stale_or_mismatched_candidate_digest")
        return normalize_scan(
            candidate_digest=candidate_digest,
            staged_path=staged_path,
            sca=sca,
            sast=sast,
        )

    if fixture is not None:
        sca_raw = fixture.get("sca", {})
        sast_raw = fixture.get("sast", {})
        sca = ScanStage(
            name="sca",
            completed=bool(sca_raw.get("completed", False)),
            exit_code=sca_raw.get("exit_code"),
            schema=sca_raw.get("schema", "snyk.test.v1"),
            counts=sca_raw.get("counts", dict(ZERO_COUNTS)),
            error=sca_raw.get("error"),
        )
        sast = ScanStage(
            name="sast",
            completed=bool(sast_raw.get("completed", False)),
            exit_code=sast_raw.get("exit_code"),
            schema=sast_raw.get("schema", "snyk.code.sarif.v1"),
            counts=sast_raw.get("counts", dict(ZERO_COUNTS)),
            error=sast_raw.get("error"),
        )
        return normalize_scan(
            candidate_digest=candidate_digest or actual,
            staged_path=staged_path,
            sca=sca,
            sast=sast,
        )

    avail = live_scan_availability()
    if avail["observed_outcome"] == "READY":
        return _run_live_snyk_scan(
            candidate_digest=candidate_digest or actual,
            staged_path=staged_path,
            snyk_cli=str(avail["snyk_cli"]),
        )

    sca = ScanStage("sca", False, None, None, error="live_scan_not_executed")
    sast = ScanStage("sast", False, None, None, error="live_scan_not_executed")
    result = normalize_scan(
        candidate_digest=candidate_digest or actual,
        staged_path=staged_path,
        sca=sca,
        sast=sast,
    )
    result.observed_outcome = "NOT_TESTED"
    result.reasons.append(f"live_availability:{avail['observed_outcome']}")
    if not avail.get("token_in_env"):
        result.reasons.append("SNYK_TOKEN_missing")
    if not avail.get("snyk_cli"):
        result.reasons.append("snyk_cli_missing")
    return result


def _run_live_snyk_scan(
    *,
    candidate_digest: str,
    staged_path: str,
    snyk_cli: str,
) -> ScanResult:
    """Execute SCA + SAST via Snyk CLI. Token stays in env for subprocess only."""
    import subprocess
    import tempfile

    path = Path(staged_path)
    env = os.environ.copy()
    # Never log token. Subprocess inherits SNYK_TOKEN from operator env.

    def run_json(args: list[str]) -> tuple[int, Any, Optional[str]]:
        try:
            proc = subprocess.run(
                [snyk_cli, *args],
                cwd=str(path),
                capture_output=True,
                text=True,
                timeout=300,
                env=env,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return 3, None, f"{type(exc).__name__}:{exc}"
        raw_txt = (proc.stdout or "").strip()
        if not raw_txt:
            return proc.returncode, None, (proc.stderr or "no_output")[:300]
        try:
            parsed = json.loads(raw_txt)
        except json.JSONDecodeError:
            return proc.returncode, None, "invalid_json"
        if isinstance(parsed, dict) and parsed.get("ok") is False and "vulnerabilities" not in parsed:
            return proc.returncode, None, str(parsed.get("error") or "ok:false")
        return proc.returncode, parsed, None

    from .score import ZERO as Z

    sca_code, sca_raw, sca_err = run_json(["test", "--json"])
    sast_code, sast_raw, sast_err = run_json(["code", "test", "--json"])

    sca_counts = dict(Z)
    sast_counts = dict(Z)
    if isinstance(sca_raw, dict):
        for v in sca_raw.get("vulnerabilities") or []:
            sev = str(v.get("severity", "low")).lower()
            if sev in sca_counts:
                sca_counts[sev] += 1
    elif isinstance(sca_raw, list):
        for proj in sca_raw:
            for v in (proj or {}).get("vulnerabilities") or []:
                sev = str(v.get("severity", "low")).lower()
                if sev in sca_counts:
                    sca_counts[sev] += 1

    # SARIF or code JSON
    if isinstance(sast_raw, dict) and "runs" in sast_raw:
        level_map = {"note": "low", "warning": "medium", "error": "high"}
        for run in sast_raw.get("runs") or []:
            for res in run.get("results") or []:
                sev = level_map.get(str(res.get("level", "note")).lower(), "low")
                sast_counts[sev] += 1

    # Persist raw reports outside git under local-runs/ (gitignored).
    runs = Path("local-runs")
    runs.mkdir(parents=True, exist_ok=True)
    raw_dir = Path(tempfile.mkdtemp(prefix="sneak-snyk-", dir=str(runs.resolve())))
    sca_ref = raw_dir / "sca.json"
    sast_ref = raw_dir / "sast.json"
    sca_ref.write_text(json.dumps(sca_raw, indent=2) if sca_raw is not None else json.dumps({"error": sca_err}))
    sast_ref.write_text(json.dumps(sast_raw, indent=2) if sast_raw is not None else json.dumps({"error": sast_err}))

    sca = ScanStage(
        name="sca",
        completed=sca_err is None and sca_code in (0, 1),
        exit_code=sca_code,
        schema="snyk.test.v1",
        counts=sca_counts,
        raw_ref=str(sca_ref),
        error=sca_err,
    )
    sast = ScanStage(
        name="sast",
        completed=sast_err is None and sast_code in (0, 1),
        exit_code=sast_code,
        schema="snyk.code.sarif.v1",
        counts=sast_counts,
        raw_ref=str(sast_ref),
        error=sast_err,
    )
    return normalize_scan(
        candidate_digest=candidate_digest,
        staged_path=staged_path,
        sca=sca,
        sast=sast,
        scanner_identity=f"snyk-cli+javier-score@6e1f276",
    )


ZERO_COUNTS = {"critical": 0, "high": 0, "medium": 0, "low": 0}
