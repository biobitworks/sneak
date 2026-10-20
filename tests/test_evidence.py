import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.contracts import cannot_verify_without_evidence
from sneak.evidence import EvidenceStore


class EvidenceTests(unittest.TestCase):
    def test_missing_evidence_cannot_verify(self):
        v = cannot_verify_without_evidence("REQ-AOK-M01")
        self.assertFalse(v.verified)
        self.assertEqual(v.observed_outcome, "NOT_TESTED")
        self.assertEqual(v.evidence, [])

    def test_successor_preserves_predecessor_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = EvidenceStore(Path(tmp))
            first = store.append_receipt("kind", {"n": 1}, parent_id=None)
            second = store.append_receipt("kind", {"n": 2}, parent_id=first.external_id)
            raw1 = Path(first.receipt_path).read_bytes()
            # append another and ensure first bytes unchanged
            store.append_receipt("kind", {"n": 3}, parent_id=second.external_id)
            self.assertEqual(Path(first.receipt_path).read_bytes(), raw1)
            body = json.loads(raw1)
            self.assertEqual(body["payload"]["n"], 1)

    def test_source_context_identities_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = EvidenceStore(Path(tmp))
            a = store.append_receipt(
                "atom",
                {"content_sha256": "aaa", "occurrence_sha256": "occ1", "context": {"page": 1}},
            )
            b = store.append_receipt(
                "atom",
                {"content_sha256": "aaa", "occurrence_sha256": "occ2", "context": {"page": 2}},
            )
            pa = json.loads(Path(a.receipt_path).read_text())["payload"]
            pb = json.loads(Path(b.receipt_path).read_text())["payload"]
            self.assertEqual(pa["content_sha256"], pb["content_sha256"])
            self.assertNotEqual(pa["occurrence_sha256"], pb["occurrence_sha256"])
            self.assertNotEqual(a.artifact_digest, b.artifact_digest)


if __name__ == "__main__":
    unittest.main()
