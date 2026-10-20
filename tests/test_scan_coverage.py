import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.scanner import ScanStage, digest_tree, normalize_scan, scan


class ScanCoverageTests(unittest.TestCase):
    def test_exit_2_cannot_allow(self):
        sca = ScanStage("sca", True, 2, "snyk.test.v1")
        sast = ScanStage("sast", True, 0, "snyk.code.sarif.v1")
        r = normalize_scan(candidate_digest="abc", staged_path="/x", sca=sca, sast=sast)
        self.assertEqual(r.observed_outcome, "DENIED")
        self.assertFalse(r.score.coverage_accepted)

    def test_unknown_schema_denied(self):
        sca = ScanStage("sca", True, 0, "totally.unknown")
        sast = ScanStage("sast", True, 0, "snyk.code.sarif.v1")
        r = normalize_scan(candidate_digest="abc", staged_path="/x", sca=sca, sast=sast)
        self.assertEqual(r.observed_outcome, "DENIED")
        self.assertIn("sca_unknown_schema", r.reasons)

    def test_missing_stage_denied(self):
        sca = ScanStage("sca", False, None, None, error="unsupported")
        sast = ScanStage("sast", True, 0, "snyk.code.sarif.v1")
        r = normalize_scan(candidate_digest="abc", staged_path="/x", sca=sca, sast=sast)
        self.assertFalse(r.score.coverage_accepted)

    def test_stale_digest_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "a.txt").write_text("hi")
            actual = digest_tree(p)
            r = scan("not-the-digest", str(p), fixture={
                "sca": {"completed": True, "exit_code": 0, "schema": "snyk.test.v1",
                        "counts": {"critical": 0, "high": 0, "medium": 0, "low": 0}},
                "sast": {"completed": True, "exit_code": 0, "schema": "snyk.code.sarif.v1",
                         "counts": {"critical": 0, "high": 0, "medium": 0, "low": 0}},
            })
            self.assertNotEqual(actual, "not-the-digest")
            self.assertEqual(r.observed_outcome, "DENIED")
            self.assertIn("stale_or_mismatched_candidate_digest", "".join(r.reasons) + (r.sca.error or ""))


if __name__ == "__main__":
    unittest.main()
