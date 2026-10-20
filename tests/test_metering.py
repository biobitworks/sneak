import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.evidence import EvidenceStore
from sneak.metering import MeteringAdapter


class MeteringTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = EvidenceStore(Path(self.tmp.name))
        self.meter = MeteringAdapter(self.store)

    def tearDown(self):
        self.tmp.cleanup()

    def test_duplicate_usage_one_effect(self):
        a = self.meter.emit_usage("run-1", "skill_scan_completed", 1)
        b = self.meter.emit_usage("run-1", "skill_scan_completed", 1)
        self.assertEqual(self.meter.state.credits, 1)
        self.assertIn("DEDUPED", Path(b.receipt_path).read_text())

    def test_credits_never_override_deny(self):
        self.meter.state.credits = 100
        r = self.meter.emit_usage("run-2", "skill_scan_completed", 1, security_decision="DENY")
        self.assertIn("DENIED", Path(r.receipt_path).read_text())
        self.assertEqual(self.meter.state.credits, 100)

    def test_insufficient_credits_gate(self):
        self.meter.state.credits = 0
        g = self.meter.can_start_paid_scan()
        self.assertFalse(g["allowed"])
        self.assertTrue(g["free_integrity_verification"])

    def test_delayed_readback_pending(self):
        self.meter.state.provider_up = False
        self.assertEqual(self.meter.readback("x")["observed_outcome"], "PENDING")


if __name__ == "__main__":
    unittest.main()
