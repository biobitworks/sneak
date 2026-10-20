import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.evidence import EvidenceStore
from sneak.lomo_score_pipeline import run_connector_lomo_with_scores, score_after_breakpoint
from sneak.data_backend import DataBackend
from sneak.band_adapter import BandAdapter
from sneak.lomo import run_one_component_trial


class LomoScorePipelineTests(unittest.TestCase):
    def test_score_runs_after_each_breakpoint_offline(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = EvidenceStore(Path(tmp) / "ev")
            staged = ROOT / "apps/security-demo"
            result = run_connector_lomo_with_scores(
                store=store,
                staged_path=staged,
                parent_breakpoint="TEST-PARENT",
                live=False,
                notify_band=False,
            )
            # 4 trials × (baseline + ablated) = 8 scored breakpoints
            self.assertEqual(result["summary"]["breakpoint_score_count"], 8)
            self.assertEqual(result["chain"]["leaf_count"], 8)
            for row in result["summary"]["scored_breakpoints"]:
                self.assertIn(row["scan_outcome"], ("NOT_TESTED", "BLOCKED", "DENIED", "FAIL", "PASS"))
                # Without live Snyk, application_score must not pretend coverage
                self.assertFalse(row["coverage_accepted"])

    def test_single_breakpoint_binds_merkle_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = EvidenceStore(Path(tmp) / "ev")
            trial = run_one_component_trial(
                actor="t",
                full_bindings={
                    "source-atom": "a",
                    "occurrence-context": "c",
                    "rights-binding": "r",
                    "policy-binding": "p",
                    "scan-receipt": "s",
                    "memory-reference": "m",
                    "authorization-receipt": "auth",
                    "parent-breakpoint": "P",
                },
                removed_component="authorization-receipt",
                parent_breakpoint="P",
                trial_id="LOMO-T",
            )
            bp = trial["ablated_breakpoint"]
            post = score_after_breakpoint(
                store=store,
                staged_path=ROOT / "apps/security-demo",
                breakpoint_id=bp["id"],
                merkle_root=bp["root"],
                data=DataBackend(store, live=False),
                band=BandAdapter(store, live=False),
                notify_band=False,
                wait_data_seconds=0,
            )
            self.assertEqual(post["merkle_root"], bp["root"])
            self.assertFalse(post["gate_ready_for_allow"])


if __name__ == "__main__":
    unittest.main()
