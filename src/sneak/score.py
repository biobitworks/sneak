"""Pinned Javier app-security-score formula (local reimplementation).

Upstream pin: javiergarza-snyk/app-security-score@6e1f27605fe278eed347b10dab6f39b3501f1486
Local clone kept under sources/app-security-score/ (gitignored; license UNKNOWN).
This module recomputes the documented helper only; it is not a live scan.
Incomplete SCA/SAST coverage must reject application scoring (SNYK-01/02).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

UPSTREAM_COMMIT = "6e1f27605fe278eed347b10dab6f39b3501f1486"
UPSTREAM_REPO = "https://github.com/javiergarza-snyk/app-security-score"
WEIGHTS = {"critical": 3.0, "high": 1.0, "medium": 0.3, "low": 0.1}
NON_LOW_CUTOFF = 10
ZERO = {"critical": 0, "high": 0, "medium": 0, "low": 0}


@dataclass(frozen=True)
class ScoreResult:
    raw_score: Optional[float]
    application_score: Optional[float]
    sca_coverage: bool
    sast_coverage: bool
    coverage_accepted: bool
    reject_reason: Optional[str]
    upstream_commit: str = UPSTREAM_COMMIT

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_score": self.raw_score,
            "application_score": self.application_score,
            "sca_coverage": self.sca_coverage,
            "sast_coverage": self.sast_coverage,
            "coverage_accepted": self.coverage_accepted,
            "reject_reason": self.reject_reason,
            "upstream_commit": self.upstream_commit,
            "upstream_repo": UPSTREAM_REPO,
            "license": "UNKNOWN_ROOT_LICENSE_404",
            "meaning": "Tool score only; not an awarded event bonus or vulnerability-free claim",
        }


def _as_counts(counts: Optional[dict[str, int]]) -> dict[str, int]:
    base = dict(ZERO)
    if not counts:
        return base
    for k in base:
        base[k] = int(counts.get(k, 0))
    return base


def compute_score(
    sca_counts: Optional[dict[str, int]],
    sast_counts: Optional[dict[str, int]],
) -> float:
    """Pure helper matching upstream computeScore."""
    sca = _as_counts(sca_counts)
    sast = _as_counts(sast_counts)
    non_low = sum(sca[s] + sast[s] for s in ("critical", "high", "medium"))
    if non_low > NON_LOW_CUTOFF:
        return 0.0
    deduction = sum(WEIGHTS[s] * (sca[s] + sast[s]) for s in WEIGHTS)
    score = max(0.0, 10.0 - deduction)
    return round(score * 10) / 10


def score_with_coverage(
    *,
    sca_counts: Optional[dict[str, int]],
    sast_counts: Optional[dict[str, int]],
    sca_coverage: bool,
    sast_coverage: bool,
) -> ScoreResult:
    """Report 10/10 application score only when both stages completed with zero findings.

    Raw numeric score is preserved even when the wrapper rejects incomplete coverage.
    """
    raw = compute_score(sca_counts, sast_counts)
    if not sca_coverage or not sast_coverage:
        return ScoreResult(
            raw_score=raw,
            application_score=None,
            sca_coverage=sca_coverage,
            sast_coverage=sast_coverage,
            coverage_accepted=False,
            reject_reason="incomplete_sca_or_sast_coverage",
        )
    return ScoreResult(
        raw_score=raw,
        application_score=raw,
        sca_coverage=True,
        sast_coverage=True,
        coverage_accepted=True,
        reject_reason=None,
    )


def is_clean_ten(result: ScoreResult) -> bool:
    return (
        result.coverage_accepted
        and result.application_score == 10.0
        and result.raw_score == 10.0
    )
