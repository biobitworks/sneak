import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.actor_audit import ActorAuditTrail, deterministic_roi, fco_identity
from sneak.evidence import EvidenceStore
from sneak.merkle import root, leaf
from sneak.metering import MeteringAdapter


class ActorAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = EvidenceStore(Path(self.tmp.name))
        self.audit = ActorAuditTrail(self.store)

    def tearDown(self):
        self.tmp.cleanup()

    def test_deterministic_roi_bankers_rounding(self):
        a = deterministic_roi(cost_units="0.03", benefit_units="1.0")
        b = deterministic_roi(cost_units="0.03", benefit_units="1.0")
        self.assertEqual(a, b)
        self.assertEqual(a["roi"], str(Decimal("32.333333")))
        self.assertIsNone(deterministic_roi(cost_units="0", benefit_units="1")["roi"])

    def test_fco_identity_stable(self):
        payload = {
            "id": "ACTOR-tom-0000",
            "kind": "ActorEventFCO",
            "actor_id": "tom",
            "action": "review",
            "quantity": 1,
            "unit_cost": "0.01",
            "outcome": "PASS",
            "cost_units": "0.01",
            "benefit_units": "1.0",
        }
        h1 = fco_identity(payload)
        payload2 = {**payload, "fco_candidate_sha256": h1}
        self.assertEqual(h1, fco_identity(payload2))

    def test_per_actor_audit_and_fcg(self):
        a = self.audit.record_action(
            actor_id="tom", actor_role="claude", action="band_review", outcome="PASS", quantity=2
        )
        b = self.audit.record_action(
            actor_id="jerry",
            actor_role="chatgpt",
            action="band_review",
            outcome="PARTIAL",
            quantity=1,
            parent_fco_id=a["id"],
        )
        self.assertTrue(a["fco_candidate_sha256"])
        self.assertEqual(b["roi"]["observed_outcome"], "COMPUTED")
        fcg = self.audit.build_fcg()
        self.assertGreaterEqual(len(fcg["nodes"]), 2)
        self.assertTrue(any(e["type"] == "PRECEDED_BY" for e in fcg["edges"]))
        self.assertEqual(fcg["mmr"], "NOT_COMMITTED")

        receipt = self.audit.candidate_mmr_receipt(breakpoint_id="SNEAK-TEST-AUDIT")
        self.assertEqual(receipt["mmr"], "NOT_COMMITTED")
        self.assertEqual(receipt["root"], receipt["root_recompute"])
        # Independent recompute of leaf root
        ordered = sorted(
            ({"id": x["record"]["id"], "kind": x["record"]["kind"], "payload": x["record"]["payload"]} for x in receipt["leaves"]),
            key=lambda r: r["id"],
        )
        # leaves in receipt already include records; recompute from receipt leaf hashes
        xs = [bytes.fromhex(item["leaf"]) for item in sorted(receipt["leaves"], key=lambda i: i["record"]["id"])]
        self.assertEqual(root(xs).hex(), receipt["root"])

        tom = self.audit.actor_roi_summary("tom")
        self.assertEqual(tom["event_count"], 1)
        self.assertIsNotNone(tom["aggregate_roi"]["roi"])

    def test_metering_binds_actor_fco(self):
        meter = MeteringAdapter(self.store, audit=self.audit)
        r = meter.emit_usage(
            "run-actor-1",
            "skill_scan_completed",
            1,
            actor_id="scanner",
            actor_role="snyk-gate",
            live_ingest=False,
        )
        self.assertIn("LOCAL_CONTRACT_ONLY", Path(r.receipt_path).read_text())
        self.assertEqual(len(self.audit.actors["scanner"]), 1)
        trail = meter.actor_audit_receipt("SNEAK-TEST-METER")
        self.assertIn("scanner", trail["actor_summaries"])


if __name__ == "__main__":
    unittest.main()
