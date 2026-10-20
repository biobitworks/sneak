import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.score import (
    NON_LOW_CUTOFF,
    WEIGHTS,
    compute_score,
    is_clean_ten,
    score_with_coverage,
)


class ScoreTests(unittest.TestCase):
    def test_zero_findings_is_ten(self):
        z = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        self.assertEqual(compute_score(z, z), 10)

    def test_one_high_is_nine(self):
        sca = {"critical": 0, "high": 1, "medium": 0, "low": 0}
        sast = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        self.assertEqual(compute_score(sca, sast), 9)

    def test_eleven_medium_hard_zero(self):
        sca = {"critical": 0, "high": 0, "medium": NON_LOW_CUTOFF + 1, "low": 0}
        sast = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        weighted = max(0, 10 - WEIGHTS["medium"] * (NON_LOW_CUTOFF + 1))
        self.assertGreater(weighted, 0)
        self.assertEqual(compute_score(sca, sast), 0)

    def test_incomplete_coverage_rejects_application_score(self):
        z = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        r = score_with_coverage(
            sca_counts=z, sast_counts=z, sca_coverage=True, sast_coverage=False
        )
        self.assertEqual(r.raw_score, 10)
        self.assertIsNone(r.application_score)
        self.assertFalse(r.coverage_accepted)
        self.assertFalse(is_clean_ten(r))

    def test_complete_clean_is_ten(self):
        z = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        r = score_with_coverage(
            sca_counts=z, sast_counts=z, sca_coverage=True, sast_coverage=True
        )
        self.assertTrue(is_clean_ten(r))


if __name__ == "__main__":
    unittest.main()
