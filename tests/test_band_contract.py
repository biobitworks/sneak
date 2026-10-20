import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.band_adapter import BandAdapter
from sneak.contracts import EvidenceRef
from sneak.evidence import EvidenceStore


class BandContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = EvidenceStore(Path(self.tmp.name))
        self.band = BandAdapter(self.store, live=False)

    def tearDown(self):
        self.tmp.cleanup()

    def test_pending_not_approved(self):
        d = self.band.read_decision("req-1")
        self.assertFalse(d["approved"])
        self.assertEqual(d["human_decision"], "PENDING")

    def test_reconnect_preserves_request_identity(self):
        self.band.record_decision("req-1", "APPROVE", "A")
        d = self.band.read_decision("req-1")
        self.assertTrue(d["approved"])
        self.assertTrue(d["reconnect_preserved"])
        self.assertEqual(d["request_id"], "req-1")

    def test_duplicate_handoff_deduped(self):
        ev = EvidenceRef("p", "e1", "d", "/r", "t")
        a = self.band.publish_handoff("t1", "jerry", [ev], request_id="r1")
        b = self.band.publish_handoff("t1", "jerry", [ev], request_id="r1")
        self.assertIn("duplicate", Path(b.receipt_path).read_text())


if __name__ == "__main__":
    unittest.main()
