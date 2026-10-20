"""Prove each LOMO breakpoint is backed by contextual FCO/MMR successors."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from sneak.evidence import EvidenceStore
from sneak.fcg_registry import FCGRegistry
from sneak.lomo_score_pipeline import run_connector_lomo_with_scores

ROOT = Path(__file__).resolve().parents[1]
SOURCE = hashlib.sha256(b"synthetic-lomo-actor").hexdigest()


class LomoFcgHookTests(unittest.TestCase):
    def test_each_breakpoint_registers_score_classification_and_delta(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            store = EvidenceStore(base / "evidence")
            registry = FCGRegistry(base / "fcg.jsonl")
            actor = registry.append(kind="actor", payload={"name": "fixture-reviewer"},
                                    state="OBSERVED", source_sha256=SOURCE)["fco_id"]
            model = registry.append(kind="model", payload={"identity": "NOT_APPLICABLE_NO_INFERENCE"},
                                    actor_fco=actor, state="UNKNOWN")["fco_id"]
            out = run_connector_lomo_with_scores(
                store=store, staged_path=ROOT / "apps/security-demo",
                parent_breakpoint="LOMO-FCG-FIXTURE",
                live=False, notify_band=False,
                fcg=registry, actor_fco=actor, model_fco=model,
            )
            rows = registry.rows()
            self.assertEqual(len(out["scored"]), 8)
            self.assertEqual(len(rows), 2 + (8 * 4) + 4)
            self.assertEqual(len([x for x in rows if x["identity"]["kind"] == "delta"]), 4)
            self.assertEqual(len([x for x in rows if x["identity"]["kind"] == "classification"]), 8)
            self.assertTrue(all(x["post"]["fcg"]["last_inclusion_verified"] for x in out["scored"]))
            self.assertTrue(all(x["post"]["fcg_delta_fco_id"] for x in out["scored"]
                                if x["breakpoint_kind"] == "ablated_breakpoint"))
            self.assertTrue(all(x["post"]["scan"]["score"]["application_score"] is None
                                for x in out["scored"]))
            proof = registry.inclusion_proof(rows[-1]["fco_id"])
            self.assertTrue(proof["verified"])
            self.assertEqual(proof["mmr_root"], registry.verify()["mmr_root"])

    def test_missing_actor_denies_registry_hook(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "actor identity required"):
                run_connector_lomo_with_scores(
                    store=EvidenceStore(Path(tmp) / "ev"),
                    staged_path=ROOT / "apps/security-demo",
                    live=False, notify_band=False, fcg=FCGRegistry(Path(tmp) / "ledger"),
                )


if __name__ == "__main__":
    unittest.main()
