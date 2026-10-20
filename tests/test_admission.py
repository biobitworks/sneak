import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.contracts import EvidenceRef
from sneak.gate import decide
from sneak.scanner import ScanStage, normalize_scan


def _clean_scan(digest="dig"):
    z = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    return normalize_scan(
        candidate_digest=digest,
        staged_path="/tmp",
        sca=ScanStage("sca", True, 0, "snyk.test.v1", counts=z),
        sast=ScanStage("sast", True, 0, "snyk.code.sarif.v1", counts=z),
    )


def _ev():
    return EvidenceRef("t", "1", "d", "/r", "2026-10-20T00:00:00+00:00")


class AdmissionTests(unittest.TestCase):
    def test_pending_human_stays_pending(self):
        d = decide("dig", [_ev()], "pol", scan=_clean_scan(), human_decision="PENDING")
        self.assertEqual(d.decision, "PENDING")

    def test_replay_denied(self):
        d = decide(
            "dig",
            [_ev()],
            "pol",
            scan=_clean_scan(),
            human_decision="APPROVE",
            authorization_nonce="n1",
            seen_nonces={"n1"},
        )
        self.assertEqual(d.decision, "DENY")
        self.assertIn("authorization_replay", d.reasons)

    def test_poison_recall_denied(self):
        d = decide(
            "dig",
            [_ev()],
            "pol",
            scan=_clean_scan(),
            human_decision="APPROVE",
            recalled_poison=True,
        )
        self.assertEqual(d.decision, "DENY")

    def test_target_substitution_denied(self):
        d = decide(
            "dig",
            [_ev()],
            "pol",
            scan=_clean_scan(),
            human_decision="APPROVE",
            target_digest="other",
        )
        self.assertEqual(d.decision, "DENY")

    def test_valid_scoped_allow(self):
        d = decide(
            "dig",
            [_ev()],
            "pol",
            scan=_clean_scan(),
            human_decision="APPROVE",
            authorization_nonce="fresh",
            seen_nonces=set(),
            target_digest="dig",
        )
        self.assertEqual(d.decision, "ALLOW")
        self.assertEqual(d.capability["scope"], "disposable_demo_truth_store_only")


if __name__ == "__main__":
    unittest.main()
