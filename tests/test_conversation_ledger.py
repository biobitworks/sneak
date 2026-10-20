"""Conversation ledger: source custody, deterministic FCO, per-actor MMR, fail-closed import."""
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

from scripts import sneak_conversation_ledger as ledger
from scripts import mmr_reference as R


class ConversationLedgerTests(unittest.TestCase):
    def test_import_source_receipt_and_actor_mmr(self):
        d=ledger.compile_source()
        self.assertEqual(len(d["events"]),3)
        self.assertEqual(d["source"]["message_count"],3)
        self.assertEqual(d["source"]["event_count"],3)
        self.assertEqual({a["actor"] for a in d["actor_mmr"].values()},{"Tom","Jerry"})
        self.assertEqual(sorted(x["event_count"] for x in d["actor_mmr"].values()),[1,2])
        self.assertEqual(d["missing_model_identity"],3)
        self.assertEqual(d["model_mmr"],{})
        self.assertEqual(d["quality_delta"],"NOT_COMPUTED")
        self.assertFalse(d["all_conversations_imported"])
        self.assertEqual(d["live_band_sync"],"NOT_TESTED_AUTH_BLOCKED")
        self.assertTrue(all(x["claim_true"] is None for x in d["events"]))
        self.assertTrue(all(x["semantic_verdict"]=="UNKNOWN" for x in d["events"]))

    def test_fco_inputs_outputs_and_per_actor_predecessor(self):
        d=ledger.compile_source()
        prior="GENESIS"
        seen={}
        for i,event in enumerate(d["events"]):
            self.assertEqual(event["index"],i)
            self.assertEqual(event["parent_global_fco"],prior)
            self.assertEqual(event["parent_actor_fco"],seen.get(event["actor_identity_sha256"]))
            self.assertEqual(event["root_question_fco"],d["question"]["id"])
            self.assertEqual(event["source_receipt_sha256"],d["source"]["source_sha256"])
            self.assertEqual(len(event["input_sha256"]),64)
            self.assertEqual(len(event["output_sha256"]),64)
            self.assertEqual(len(event["steps"]),2)
            self.assertTrue(event["history_integrity"])
            prior=event["id"]
            seen[event["actor_identity_sha256"]]=event["id"]
        self.assertEqual(d["global_mmr"]["leaves"],3)
        self.assertEqual(d["question_mmr"]["leaves"],4)
        self.assertNotEqual(d["question_mmr"]["root"],d["global_mmr"]["root"])
        for actor,stream in d["actor_mmr"].items():
            xs=[x for x in d["events"] if x["actor_identity_sha256"]==actor]
            self.assertEqual(ledger.mmr_of(xs),stream["mmr"])
            m=R.MMR()
            for x in xs:m.append(ledger.enc(x))
            for j,x in enumerate(xs):
                self.assertTrue(R.mmr_verify(ledger.enc(x),m.proof(j),m.root()))

    def test_deterministic_repeat_and_fail_closed_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=pathlib.Path(tmp)/"snapshot.json"
            source=pathlib.Path(tmp)/"captured.json"
            source.write_bytes(ledger.DEFAULT_SOURCE.read_bytes())
            a=ledger.write_snapshot(source,out)
            original=out.read_bytes()
            b=ledger.write_snapshot(source,out)
            self.assertEqual(a,b)
            self.assertEqual(original,out.read_bytes())
            self.assertEqual(ledger.verify(source,out)["status"],"PASS")
            out.write_bytes(original.replace(b'"model_mmr":{}',b'"model_mmr":{"invented":"model"}'))
            with self.assertRaisesRegex(ValueError,"byte mismatch"):ledger.verify(source,out)
            src=json.loads(source.read_text())
            src["leaves"][0]["event"]["id"]="TAMPERED"
            source.write_text(json.dumps(src))
            with self.assertRaisesRegex(ValueError,"canonical event mismatch"):ledger.compile_source(source)

    def test_all_raw_chat_text_absent_from_output(self):
        d=ledger.compile_source()
        public=ledger.enc(d)
        input_obj=json.loads(ledger.DEFAULT_SOURCE.read_text())
        for leaf in input_obj["leaves"]:
            for m in leaf["event"].get("payload",{}).get("messages",[]):
                self.assertNotIn(m["content"].encode("utf-8"),public)
        self.assertNotIn(b'"content":',public)
        self.assertNotIn(b'"raw_message":',public)


if __name__=="__main__":unittest.main()
