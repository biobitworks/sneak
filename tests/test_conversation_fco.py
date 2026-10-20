import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.conversation_fco import (
    ConversationEvalHarness,
    answer_match_quality,
    per_token_roi,
)
from sneak.evidence import EvidenceStore
from sneak.magicstudio import BASELINE_MODELS, RETIRED_MODELS
from sneak.model_clients import LiquidClient, OpenJevClient, estimate_tokens


class ConversationFcoTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = EvidenceStore(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_qwen_retired_from_baseline(self):
        self.assertTrue(any("lfm" in m or "openjev" in m for m in BASELINE_MODELS))
        self.assertTrue(any("qwen2.5" in m for m in RETIRED_MODELS))
        self.assertFalse(any(m.startswith("qwen") for m in BASELINE_MODELS))

    def test_answer_match_and_token_roi_deterministic(self):
        m1 = answer_match_quality("bike", "The bike")
        m2 = answer_match_quality("bike", "The bike")
        self.assertEqual(m1, m2)
        self.assertEqual(m1["observed_outcome"], "PARTIAL")
        r1 = per_token_roi(total_tokens=100, unit_cost_per_token="0.00000003", benefit_units="1.0")
        r2 = per_token_roi(total_tokens=100, unit_cost_per_token="0.00000003", benefit_units="1.0")
        self.assertEqual(r1, r2)
        self.assertEqual(r1["observed_outcome"], "COMPUTED")
        self.assertIsNotNone(r1["benefit_per_token"])

    def test_harness_emits_conversation_and_diff_fcos(self):
        liquid = LiquidClient(api_key=None)
        openjev = OpenJevClient(api_key=None, base_url="http://127.0.0.1:9")
        harness = ConversationEvalHarness(self.store, liquid=liquid, openjev=openjev)
        fixture = ROOT / "data/fixtures/longmemeval_oracle_sample.json"
        receipt = harness.run_fixture(fixture)
        items = json.loads(fixture.read_text())
        # 2 models × N scenarios
        self.assertEqual(len(harness.conversation_fcos), 2 * len(items))
        self.assertEqual(len(harness.diff_fcos), 2 * len(items))
        self.assertEqual(len(receipt["token_roi_rows"]), 2 * len(items))
        self.assertTrue(receipt["qwen25_retired"])
        self.assertEqual(receipt["mmr"], "NOT_COMMITTED")
        self.assertTrue(all(c["kind"] == "ConversationFCO" for c in harness.conversation_fcos))
        self.assertTrue(all(d["kind"] == "LongMemEvalDiffFCO" for d in harness.diff_fcos))
        # Missing Liquid key → NOT_TESTED conversations for liquid
        liquid_convs = [c for c in harness.conversation_fcos if c["model_provider"] == "liquid"]
        self.assertTrue(all(c["observed_outcome"] == "NOT_TESTED" for c in liquid_convs))

    def test_estimate_tokens_positive(self):
        self.assertGreater(estimate_tokens("hello world from liquid"), 0)

    def test_liquid_chat_without_key(self):
        r = LiquidClient(api_key=None).chat([{"role": "user", "content": "hi"}])
        self.assertEqual(r["observed_outcome"], "NOT_TESTED")
        self.assertFalse(r["ok"])


if __name__ == "__main__":
    unittest.main()
