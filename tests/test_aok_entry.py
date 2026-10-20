import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.aok import entry_gate, summarize_optional_mandatory, successor_from_registry
from sneak.contracts import Verdict


class AokEntryTests(unittest.TestCase):
    def test_entry_gate_false_when_unverified(self):
        verdicts = [
            Verdict("REQ-AOK-M01-X", False, "NOT_TESTED", predecessor_verdict_id="REQ-AOK-M01"),
            Verdict("REQ-AOK-F01-X", False, "NOT_TESTED", predecessor_verdict_id="REQ-AOK-F01"),
        ]
        g = entry_gate(verdicts)
        self.assertFalse(g["entry_gate"])
        self.assertEqual(g["mandatory_count"], 1)

    def test_bonus_does_not_gate_entry(self):
        verdicts = [
            Verdict("REQ-AOK-M01-X", True, "PASS", predecessor_verdict_id="REQ-AOK-M01"),
            Verdict("REQ-AOK-S01-X", False, "NOT_TESTED", predecessor_verdict_id="REQ-AOK-S01"),
        ]
        self.assertTrue(entry_gate(verdicts)["entry_gate"])

    def test_registry_successor_loads(self):
        path = ROOT / "data/verification/requirements_sneak_011.jsonl"
        verdicts = successor_from_registry(path, successor_suffix="SNEAK-014", reason="test")
        summary = summarize_optional_mandatory(verdicts)
        self.assertGreaterEqual(summary["counts"]["mandatory"], 30)
        self.assertFalse(summary["entry"]["entry_gate"])


if __name__ == "__main__":
    unittest.main()
