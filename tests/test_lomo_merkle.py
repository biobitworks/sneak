import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.lomo import matrix_connector_trials, run_one_component_trial
from sneak.merkle import leaf, proof, root, verify


class LomoMerkleTests(unittest.TestCase):
    def test_proofs_verify(self):
        xs = [leaf({"id": i}) for i in range(5)]
        r = root(xs)
        for i in range(5):
            self.assertTrue(verify(xs[i], proof(xs, i), r))

    def test_tamper_rejected(self):
        xs = [leaf({"id": i}) for i in range(3)]
        self.assertFalse(verify(leaf({"id": 9}), proof(xs, 0), root(xs)))

    def test_one_component_changes_root(self):
        full = {
            "source-atom": "a",
            "occurrence-context": "c",
            "rights-binding": "r",
            "policy-binding": "p",
            "scan-receipt": "s",
            "memory-reference": "m",
            "authorization-receipt": "auth",
            "parent-breakpoint": "SNEAK-013",
        }
        trial = run_one_component_trial(
            actor="gate",
            full_bindings=full,
            removed_component="authorization-receipt",
            parent_breakpoint="SNEAK-013",
            trial_id="LOMO-T01",
        )
        self.assertTrue(trial["roots_differ"])
        self.assertEqual(trial["authorization_effect"], "DENY")

    def test_connector_matrix_four_trials(self):
        trials = matrix_connector_trials()
        self.assertEqual(len(trials), 4)
        self.assertTrue(all(t["roots_differ"] for t in trials))


if __name__ == "__main__":
    unittest.main()
