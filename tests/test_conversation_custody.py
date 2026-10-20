"""Unit tests for conversation custody ledger and requirement verification."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.conversation_custody import (
    CUSTODY_REQUIREMENTS,
    ConversationCustodyLedger,
    ModelMMRTrail,
    bag_peaks,
    verify_custody_requirements,
    xor_distance,
)
from sneak.evidence import EvidenceStore, digest_payload
from sneak.merkle import leaf, root


class ConversationCustodyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = EvidenceStore(Path(self.tmp.name))
        self.root_q = {
            "text": "Unique merkle breakpoints + model MMR deltas vs root question",
            "requirements": [r["id"] for r in CUSTODY_REQUIREMENTS],
        }

    def tearDown(self):
        self.tmp.cleanup()

    def test_xor_distance_and_bag_peaks_deterministic(self):
        a = digest_payload({"x": 1})
        b = digest_payload({"x": 2})
        d1 = xor_distance(a, b)
        d2 = xor_distance(a, b)
        self.assertEqual(d1, d2)
        self.assertEqual(xor_distance(a, a), 0)
        p1 = bytes.fromhex(a)
        p2 = bytes.fromhex(b)
        bag1 = bag_peaks([p1, p2])
        bag2 = bag_peaks([p1, p2])
        self.assertEqual(bag1, bag2)
        self.assertEqual(len(bag1), 32)

    def test_model_mmr_trail_deltas(self):
        rq = leaf({"id": "ROOT", "kind": "q", "payload": {"t": 1}}).hex()
        trail = ModelMMRTrail(model_id="liquid-lfm", root_question_leaf=rq)
        peak1 = leaf({"id": "p1", "kind": "peak", "payload": {"i": 1}}).hex()
        peak2 = leaf({"id": "p2", "kind": "peak", "payload": {"i": 2}}).hex()
        d1 = trail.append_peak(peak1)
        d2 = trail.append_peak(peak2)
        self.assertEqual(d1["index"], 0)
        self.assertIsNone(d1["vs_prev_model_root_xor_distance"])
        self.assertEqual(d2["index"], 1)
        self.assertIsNotNone(d2["vs_prev_model_root_xor_distance"])
        self.assertEqual(d1["mmr"], "NOT_COMMITTED")
        self.assertEqual(trail.to_dict()["peak_count"], 2)

    def test_run_turn_hashed_io_pass_flag_and_unique_breakpoints(self):
        ledger = ConversationCustodyLedger(self.store, root_question=self.root_q)
        parent = None
        receipts = []
        for i, (model, agent, ok) in enumerate(
            [
                ("liquid-lfm", "tom", True),
                ("openjev", "jerry", False),
                ("liquid-lfm", "tom", True),
            ]
        ):
            cid = f"conv-{i:03d}"

            def pred(inp, out, steps, expected=ok):
                return expected

            r = ledger.run_turn(
                conversation_id=cid,
                model_id=model,
                agent_id=agent,
                input_payload={"ask": f"q{i}", "root": self.root_q["text"]},
                steps=[
                    {"name": "parse_input", "script": "deterministic"},
                    {"name": "emit_fco", "script": "deterministic"},
                ],
                output_payload={"answer": f"a{i}", "ok": ok},
                pass_predicate=pred,
                parent_breakpoint_id=parent,
            )
            receipts.append(r)
            parent = r["id"]
            self.assertIn("pass", r)
            self.assertIs(r["pass"], ok)
            self.assertTrue(r["input_hash"])
            self.assertTrue(r["output_hash"])
            self.assertEqual(r["mmr"], "NOT_COMMITTED")
            self.assertIn("model_mmr_delta", r)
            # Independent leaf/root recompute
            leaves = [bytes.fromhex(x["leaf"]) for x in r["leaves"]]
            self.assertEqual(root(leaves).hex(), r["root"])

        ids = [r["id"] for r in receipts]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ledger.model_trails["liquid-lfm"].deltas), 2)
        self.assertEqual(len(ledger.model_trails["openjev"].deltas), 1)

    def test_update_fco_tracking_and_project_connector(self):
        ledger = ConversationCustodyLedger(self.store, root_question=self.root_q)
        ledger.run_turn(
            conversation_id="c-upd",
            model_id="liquid-lfm",
            agent_id="tom",
            input_payload={"ask": "u"},
            steps=[{"name": "step"}],
            output_payload={"answer": "v"},
            pass_predicate=lambda i, o, s: True,
        )
        upd = ledger.track_update(
            update_id="UPD-001",
            parent_fco_id="STEP-c-upd-0000",
            change={"field": "status", "to": "reviewed"},
        )
        self.assertEqual(upd["kind"], "UpdateTrackingFCO")
        self.assertTrue(upd["change_digest"])
        self.assertTrue(upd["fco_candidate_sha256"])
        project = ledger.project_connector_receipt(breakpoint_id="SNEAK-024")
        self.assertEqual(project["id"], "SNEAK-024")
        self.assertEqual(project["breakpoint_count"], 1)
        self.assertEqual(project["pass_count"], 1)
        self.assertEqual(project["mmr"], "NOT_COMMITTED")
        self.assertIn("liquid-lfm", project["model_trails"])

    def test_verify_custody_requirements_mandatory_and_optional(self):
        ledger = ConversationCustodyLedger(self.store, root_question=self.root_q)
        ledger.run_turn(
            conversation_id="c-v",
            model_id="m1",
            agent_id="a1",
            input_payload={"ask": "x"},
            steps=[{"name": "s"}],
            output_payload={"answer": "y"},
            pass_predicate=lambda i, o, s: True,
        )
        ledger.track_update(
            update_id="UPD-v",
            parent_fco_id="STEP-c-v-0000",
            change={"note": "agent+planner notified"},
        )
        rows = verify_custody_requirements(
            ledger,
            band_ok=True,
            cognee_ok=True,
            planner_checked=True,
            agents_updated=True,
            live_model_inference=False,
            mmr_committed=False,
        )
        by_id = {r["id"]: r for r in rows}
        self.assertEqual(len(rows), len(CUSTODY_REQUIREMENTS))
        for rid in (
            "REQ-CUSTODY-01",
            "REQ-CUSTODY-02",
            "REQ-CUSTODY-03",
            "REQ-CUSTODY-04",
            "REQ-CUSTODY-05",
            "REQ-CUSTODY-06",
            "REQ-CUSTODY-07",
            "REQ-CUSTODY-08",
            "REQ-CUSTODY-09",
        ):
            self.assertTrue(by_id[rid]["verified"], rid)
            self.assertEqual(by_id[rid]["observed_outcome"], "PASS")
            self.assertTrue(by_id[rid]["required_for_entry"])
        # Optional: live inference / MMR commit remain unverified without receipts
        self.assertFalse(by_id["REQ-CUSTODY-10"]["verified"])
        self.assertEqual(by_id["REQ-CUSTODY-10"]["observed_outcome"], "NOT_TESTED")
        self.assertFalse(by_id["REQ-CUSTODY-10"]["required_for_entry"])
        self.assertFalse(by_id["REQ-CUSTODY-11"]["verified"])
        self.assertEqual(by_id["REQ-CUSTODY-11"]["observed_outcome"], "NOT_TESTED")

    def test_never_claim_mmr_committed_without_flag(self):
        ledger = ConversationCustodyLedger(self.store, root_question=self.root_q)
        rows = verify_custody_requirements(
            ledger,
            band_ok=False,
            cognee_ok=False,
            planner_checked=False,
            agents_updated=False,
            mmr_committed=False,
        )
        mmr = next(r for r in rows if r["id"] == "REQ-CUSTODY-11")
        self.assertFalse(mmr["verified"])
        self.assertNotEqual(mmr["observed_outcome"], "PASS")


if __name__ == "__main__":
    unittest.main()
