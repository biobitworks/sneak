import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.connectors import ConnectorRuntime
from sneak.evidence import EvidenceStore


class DeepIntegrationTests(unittest.TestCase):
    def test_band_and_cognee_ablation_change_behavior(self):
        with tempfile.TemporaryDirectory() as tmp:
            rt = ConnectorRuntime(EvidenceStore(Path(tmp)), live=False)
            result = rt.deep_integration_ablation()
            self.assertTrue(result["cognee_changes_behavior"])
            self.assertTrue(result["band_removal_blocks_approval"])
            self.assertFalse(result["live_provider_claim"])

    def test_security_cycle_pending_human_denies_usage_authority(self):
        with tempfile.TemporaryDirectory() as tmp:
            rt = ConnectorRuntime(EvidenceStore(Path(tmp)), live=False)
            demo = ROOT / "apps/security-demo"
            out = rt.security_review_cycle(
                staged_path=str(demo),
                fixture={
                    "sca": {
                        "completed": True,
                        "exit_code": 0,
                        "schema": "snyk.test.v1",
                        "counts": {"critical": 0, "high": 0, "medium": 0, "low": 0},
                    },
                    "sast": {
                        "completed": True,
                        "exit_code": 0,
                        "schema": "snyk.code.sarif.v1",
                        "counts": {"critical": 0, "high": 0, "medium": 0, "low": 0},
                    },
                },
                human_decision="PENDING",
                run_id="t1",
                nonce="n1",
            )
            self.assertEqual(out["gate"]["decision"], "PENDING")
            # Pending is not ALLOW; metering must not invent security authority.
            self.assertIn(out["usage_readback"]["observed_outcome"], ("UNKNOWN", "PASS", "PENDING"))


if __name__ == "__main__":
    unittest.main()
