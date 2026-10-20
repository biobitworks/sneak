"""Independent behavioural gates for contextual FCO/FCG × MMR."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from sneak.fcg_registry import FCGRegistry
from sneak.merkle import canonical
from sneak.mmr_reference import MMR, mmr_verify

SOURCE = hashlib.sha256(b"observed-fixture-bytes").hexdigest()


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "fcg.jsonl"
        self.registry = FCGRegistry(self.path)
        self.actor = self.registry.append(kind="actor", payload={"handle": "operator"},
                                          state="OBSERVED", source_sha256=SOURCE)["fco_id"]

    def test_every_type_and_inclusion(self):
        model = self.registry.append(
            kind="model", payload={"digest": "sha256:" + SOURCE},
            actor_fco=self.actor, state="OBSERVED", source_sha256=SOURCE)["fco_id"]
        agent = self.registry.append(
            kind="agent_spawn", payload={"role": "security-reviewer"},
            actor_fco=self.actor, model_fco=model, state="EXECUTED",
            source_sha256=SOURCE,
            edges=[{"relation": "spawned_by", "to": self.actor}])["fco_id"]
        value = self.registry.append(
            kind="value", payload={"metric": "findings", "value": 4, "unit": "count"},
            actor_fco=self.actor, model_fco=model, parent_fco=agent,
            source_sha256=SOURCE, state="OBSERVED")["fco_id"]
        delta = self.registry.append(
            kind="delta", payload={"baseline": 4, "successor": 2, "delta": -2},
            actor_fco=self.actor, model_fco=model, parent_fco=value,
            source_sha256=SOURCE, state="NOT_TESTED")["fco_id"]
        self.registry.append(
            kind="classification", payload={"epistemic_state": "UNKNOWN", "action": "ABSTAIN"},
            actor_fco=self.actor, model_fco=model, parent_fco=delta, state="PROPOSED")
        info = self.registry.verify()
        self.assertEqual(info["fco_count"], 6)
        self.assertEqual(info["mmr_size"], 10)
        proof = self.registry.inclusion_proof(value)
        self.assertTrue(proof["verified"])
        self.assertEqual(proof["mmr_root"], info["mmr_root"])
        p = proof["proof"]
        self.assertTrue(mmr_verify(
            canonical(self.registry.rows()[3]["identity"]),
            {"size": p["size"], "leaf_pos": p["leaf_pos"],
             "path": [(s, pos, bytes.fromhex(h)) for s, pos, h in p["path"]],
             "peak_pos": p["peak_pos"], "peaks": [bytes.fromhex(x) for x in p["peaks"]]},
            bytes.fromhex(proof["mmr_root"]),
        ))

    def test_occurrences_are_not_deduplicated(self):
        kwargs = dict(kind="value", payload={"value": 7}, actor_fco=self.actor,
                      state="OBSERVED", source_sha256=SOURCE)
        a, b = self.registry.append(**kwargs), self.registry.append(**kwargs)
        self.assertNotEqual(a["fco_id"], b["fco_id"])
        self.assertNotEqual(a["mmr_root"], b["mmr_root"])
        self.assertEqual(self.registry.verify()["fco_count"], 3)

    def test_orphan_model_and_agent_rejected(self):
        with self.assertRaisesRegex(ValueError, "model FCO"):
            self.registry.append(kind="agent_spawn", actor_fco=self.actor,
                                 model_fco="FCO-nonexistent", payload={"role": "agent"})
        with self.assertRaisesRegex(ValueError, "registered model"):
            self.registry.append(kind="agent_spawn", actor_fco=self.actor,
                                 payload={"role": "agent"})
        with self.assertRaisesRegex(ValueError, "actor FCO"):
            self.registry.append(kind="delta", payload={"delta": 5})
        self.assertEqual(self.registry.verify()["fco_count"], 1)

    def test_failed_source_cannot_claim_observed(self):
        with self.assertRaisesRegex(ValueError, "real hashed source"):
            self.registry.append(kind="scan", payload={"result": "PASS"},
                                 actor_fco=self.actor, state="OBSERVED")
        self.assertEqual(self.registry.verify()["fco_count"], 1)

    def test_secret_and_tamper_rejected(self):
        with self.assertRaisesRegex(ValueError, "credential"):
            self.registry.append(kind="value", payload={"api_key": "secret"},
                                 actor_fco=self.actor)
        rows = self.registry.rows()
        rows[0]["identity"]["payload"]["handle"] = "attacker"
        self.path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        with self.assertRaises(ValueError):
            self.registry.verify()
        with self.assertRaises(ValueError):
            self.registry.append(kind="delta", payload={"delta": 1},
                                 actor_fco=self.actor)

    def test_parent_root_replay_rejected(self):
        self.registry.append(kind="value", payload={"value": 1},
                             actor_fco=self.actor, state="NOT_TESTED")
        rows = self.registry.rows()
        rows[1]["identity"]["predecessor_mmr_root"] = "0" * 64
        self.path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        with self.assertRaisesRegex(ValueError, "predecessor"):
            self.registry.verify()


if __name__ == "__main__":
    unittest.main()
