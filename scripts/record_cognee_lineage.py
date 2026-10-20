#!/usr/bin/env python3
"""Append source-bound FCOs for genuine Cognee OSS write and separate-process recall.

Reads observed local receipts only; never substitutes simulated data. Immutable
file identity plus ordered updated MMR link Cognee to the question history.
"""
from __future__ import annotations
import json, pathlib, hashlib, subprocess
from scripts import sneak_conversation_ledger as L
from scripts import mmr_reference as R

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"receipts/conversations/SNEAK_CONVERSATION_COGNEE_BP001_20261020.json"
W=ROOT/"local-runs/conversation_cognee_write.json"
Q=ROOT/"local-runs/conversation_cognee_read.json"
PUBLIC=ROOT/"deploy/vercel-preview/data/conversation-cognee-bridge.json"

def snapshot():
    wr=json.loads(W.read_text())
    rr=json.loads(Q.read_text())
    chain=L.compile_source()
    if wr.get("status")!="EXECUTED" or rr.get("status")!="EXECUTED":
        raise ValueError("Cognee connector has not actually executed both operations")
    if not rr.get("expected_root_found") or not rr.get("expected_session_marker_found"):
        raise ValueError("independent process did not recall the expected custody root and session")
    if wr.get("session")!=rr.get("session"):
        raise ValueError("different Cognee sessions")
    if rr.get("decisive_action")!="REQUEST_BAND_HANDOFF_AND_SNYK_PROOFS":
        raise ValueError("unexpected next action")
    pairs=(("COGNEE_WRITE",wr,W),("COGNEE_READ",rr,Q))
    predecessor=chain["events"][-1]["id"]
    transitions=[]
    source_prev=chain["question_mmr"]["root"]
    for seq,(label,rec,raw) in enumerate(pairs):
        body={"schema":"sneak.conversation-cognee-fco.v1",
              "kind":label,"parent_question_fco":chain["question"]["id"],
              "parent_event_fco":predecessor,"source_question_mmr":source_prev,
              "original_receipt_sha256":L.sha(raw.read_bytes()),
              "result_sha256":L.digest(rec),
              "operation":rec["op"],"status":rec["status"],
              "model_id":None,"model_version":None,
              "semantic_verdict":"UNKNOWN",
              "true_false_custody":True,
              "snyk_gate":"BLOCKED",
              "band_delivery":"NOT_SENT_AUTH_BLOCKED"}
        fid="FCO-"+label+"-"+R.H(b"\x00"+L.enc(body)).hex()[:24]
        fco={**body,"id":fid}
        transitions.append(fco)
        predecessor=fid
    records=[chain["question"]["question_record"],*chain["events"],*transitions]
    m=L.mmr_of(records)
    leafs=[R.H(b"\x00"+L.enc(r)) for r in records]
    tree=R.merkle_root(leafs).hex()
    return {
      "schema":"sneak.cognee-conversation-sync.v1",
      "id":"SNEAK-CONVERSATION-COGNEE-BP001",
      "parent_question_mmr_root":source_prev,
      "root_question_fco":chain["question"]["id"],
      "last_event_fco":transitions[-1]["id"],
      "fco_transitions":transitions,
      "updated_question_mmr":m,
      "updated_question_merkle_root":tree,
      "input_receipt_sha256":L.sha(W.read_bytes()),
      "output_receipt_sha256":L.sha(Q.read_bytes()),
      "write_status":"EXECUTED",
      "recall_status":"EXECUTED",
      "retrieved_entries":rr["retrieved_entries"],
      "root_found":True,
      "changed_action":rr["decisive_action"],
      "provider":"Cognee OSS",
      "session":"SNEAK-CONV-20261020-MMR",
      "scope":"only hashed three captured historic messages",
      "band_room_send":"NOT_SENT_AUTH_BLOCKED",
      "planner_consumed":"NOT_TESTED",
      "external_model_identity":"UNKNOWN",
      "live_model_mmr":"NOT_COMPUTED",
      "quality_delta":"NOT_COMPUTED",
      "signed":False,
    }

def main():
    record=snapshot()
    OUT.parent.mkdir(exist_ok=True,parents=True)
    if OUT.exists():
        if OUT.read_bytes()!=L.enc(record)+b"\n":
            raise ValueError("append-only receipt already exists with different bytes")
    else:OUT.write_bytes(L.enc(record)+b"\n")
    # Only allowlisted statuses + hashed references are sent to SSO-protected Vercel.
    public={k:record[k] for k in (
      "schema","id","parent_question_mmr_root","root_question_fco",
      "updated_question_mmr","updated_question_merkle_root","write_status",
      "recall_status","retrieved_entries","root_found","changed_action",
      "scope","band_room_send","planner_consumed","quality_delta","live_model_mmr"
    )}
    PUBLIC.parent.mkdir(parents=True,exist_ok=True)
    PUBLIC.write_bytes(L.enc(public)+b"\n")
    print(json.dumps({"receipt":str(OUT.relative_to(ROOT)),"bridge":str(PUBLIC.relative_to(ROOT)),
                      "root":record["updated_question_mmr"]["root"],
                      "fcos":len(record["fco_transitions"]),
                      "write":record["write_status"],"recall":record["recall_status"]},sort_keys=True))

if __name__=="__main__":main()
