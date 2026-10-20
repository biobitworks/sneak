"""Offline independent recomputation of appended Cognee FCO transitions.

Does not pretend to verify external API execution without source process logs.
"""
import copy
import json
import unittest
from pathlib import Path
from scripts import sneak_conversation_ledger as C
from scripts import mmr_reference as R

RECEIPT=Path(__file__).resolve().parents[1]/"receipts/conversations/SNEAK_CONVERSATION_COGNEE_BP001_20261020.json"


class MemoryBridgeTests(unittest.TestCase):
    def test_two_real_recorded_operations_link_to_question(self):
        data=json.loads(RECEIPT.read_text())
        original=C.compile_source()
        self.assertEqual(data["parent_question_mmr_root"],original["question_mmr"]["root"])
        self.assertEqual(data["root_question_fco"],original["question"]["id"])
        self.assertEqual(data["write_status"],"EXECUTED")
        self.assertEqual(data["recall_status"],"EXECUTED")
        self.assertTrue(data["root_found"])
        self.assertEqual(data["planner_consumed"],"NOT_TESTED")
        self.assertEqual(data["band_room_send"],"NOT_SENT_AUTH_BLOCKED")
        transitions=data["fco_transitions"]
        self.assertEqual([x["kind"] for x in transitions],["COGNEE_WRITE","COGNEE_READ"])
        first=original["events"][-1]["id"]
        for event in transitions:
            raw={k:v for k,v in event.items() if k!="id"}
            expected="FCO-"+event["kind"]+"-"+R.H(b"\x00"+C.enc(raw)).hex()[:24]
            self.assertEqual(event["id"],expected)
            self.assertEqual(event["parent_event_fco"],first)
            first=event["id"]
        docs=[original["question"]["question_record"],*original["events"],*transitions]
        self.assertEqual(C.mmr_of(docs),data["updated_question_mmr"])
        self.assertEqual(R.merkle_root([R.H(b"\x00"+C.enc(x)) for x in docs]).hex(),
                         data["updated_question_merkle_root"])

    def test_tamper_changes_replay_root(self):
        data=json.loads(RECEIPT.read_text())
        original=C.compile_source()
        events=copy.deepcopy(data["fco_transitions"])
        events[1]["result_sha256"]="0"*64
        docs=[original["question"]["question_record"],*original["events"],*events]
        self.assertNotEqual(C.mmr_of(docs)["root"],data["updated_question_mmr"]["root"])
        self.assertEqual(data["live_model_mmr"],"NOT_COMPUTED")

if __name__=="__main__":unittest.main()
