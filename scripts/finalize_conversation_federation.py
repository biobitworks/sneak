#!/usr/bin/env python3
"""Seal verified Cognee recall and unsent BAND planner request as SNEAK FCOs."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from sneak.fcg_registry import FCGRegistry
from sneak.cognee_client import CogneeClient
from sneak.merkle import canonical

LEDGER=ROOT/"data/fcg/sneak-016-replay.jsonl"
PREV="2ff9f1a8d530278dc953bb14297d00314734e0d87a6b325995fbbdfb48c123e4"
FED=ROOT/"receipts/evaluations/SNEAK_20261020_CONVERSATION_FEDERATION_V1_CORRECTED.json"
PLAN=ROOT/"docs/handoff/BAND_PLANNER_FEDERATION_REQUEST.md"
NB=ROOT/"notebooks/13_conversation_federation_model_mmr.ipynb"
PACKET="5d732ab86d50b90f9513aa739c0232de0e672585cd5985874c90268b5aefa5d4"
RECEIPT=ROOT/"receipts/evaluations/SNEAK_20261020_PROVIDER_FEDERATION_SUCCESSOR.json"

def sha(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()

def main():
 reg=FCGRegistry(LEDGER);before=reg.verify()
 if before["fco_count"]!=243 or before["mmr_root"]!=PREV:
  raise RuntimeError("exact FCO predecessor required; successor must be append-only")
 fed=json.loads(FED.read_text())
 if fed["successor"]["mmr_root"]!=PREV:raise RuntimeError("Federation root mismatch")
 actor=reg.rows()[58]["fco_id"]
 ctx={"project":"sneak","source_federation_mmr_root":fed["federation"]["root"],
      "prior_fco_root":PREV,"conversation_scope":"partial"}
 def add(kind,payload,source,state,prior):
  return reg.append(kind=kind,payload=payload,actor_fco=actor,
    parent_fco=prior,state=state,source_sha256=source,context=ctx)
 notebook=add("artifact",{"path":str(NB.relative_to(ROOT)),
     "sha256":sha(NB.read_bytes()),"executed_code_cells":5,
     "full_benchmark":"NOT_TESTED"},
     sha(NB.read_bytes()),"EXECUTED",reg.rows()[-1]["fco_id"])
 packet=PLAN.read_bytes()
 handoff=add("handoff",{
    "destination":"historical BAND SNEAK room",
    "message_sha256":sha(packet),
    "message_path":str(PLAN.relative_to(ROOT)),
    "sent":False,"planner_identity":"UNKNOWN",
    "planner_approval":"NOT_OBSERVED","agent_ack":"NOT_OBSERVED",
    "band_account":"notConfigured"},
    "UNKNOWN","NOT_TESTED",notebook["fco_id"])
 status={"schema":"sneak.cognee-readback.v1","dataset":"Data",
  "request_packet_sha256":PACKET,"source_federation_root":fed["federation"]["root"],
  "write_prior_http":200,"cognify_prior_http":200,
  "exact_digest_recall":False,"agent_consumption":"NOT_OBSERVED",
  "agent_behavior_change":"NOT_TESTED","conversation_full_coverage":False}
 c=CogneeClient(base_url="https://tenant-4ee605b3-4511-4496-bc8a-d9ee322fd30e.aws.cognee.ai",dataset="Data")
 if c.available:
  try:
   response=c.search(PACKET,top_k=25)
   hits=response.get("hits") or []
   matching=[h for h in hits if PACKET in json.dumps(h,sort_keys=True)]
   status["search_http"]=response.get("http_status")
   status["hit_count"]=len(hits)
   status["exact_digest_recall"]=bool(matching)
   if matching:
    status["matching_hit_sha256"]=sha(canonical(matching[0]))
  except Exception as e:
   status["search_failure_kind"]=type(e).__name__
 else:
  status["search_failure_kind"]="CREDENTIALS_NOT_AVAILABLE"
 status["state"]="OBSERVED" if status["exact_digest_recall"] else "NOT_TESTED"
 read_path=ROOT/"receipts/evaluations/SNEAK_20261020_COGNEE_FEDERATION_READBACK.json"
 read_path.write_text(json.dumps(status,indent=2,sort_keys=True)+chr(10))
 memory=add("memory",{
    "dataset":"Data","packet_sha256":PACKET,
    "write_observed":True,"cognify_observed":True,
    "exact_digest_recall":status["exact_digest_recall"],
    "readback_receipt_sha256":sha(read_path.read_bytes()),
    "cross_agent_adoption":"NOT_OBSERVED"},
    sha(read_path.read_bytes()),"OBSERVED" if status["exact_digest_recall"] else "NOT_TESTED",
    handoff["fco_id"])
 decision=add("decision",{
   "integrity_verified":True,
   "source_federation_root":fed["federation"]["root"],
   "all_conversation_coverage":False,"planner_verified":False,
   "requirements_accepted":"NOT_ESTABLISHED",
   "model_temporal_delta":"NOT_COMPUTED",
   "security_admission":"DENY","decision":"PENDING"},
   sha(FED.read_bytes()),"EXECUTED",memory["fco_id"])
 after=reg.verify()
 result={"schema":"sneak.provider-federation-successor.v1",
  "parent":before,"successor":after,"federation_root":fed["federation"]["root"],
  "notebook_fco":notebook["fco_id"],"handoff_fco":handoff["fco_id"],
  "cognee_fco":memory["fco_id"],"decision_fco":decision["fco_id"],
  "notebook_sha256":sha(NB.read_bytes()),
  "planner_message_sha256":sha(packet),
  "planner_message_state":"NOT_SENT",
  "cognee_recall":status["state"],
  "cognee_packet_sha256":PACKET,
  "security_admission":"DENY",
  "complete_conversation_coverage":False}
 RECEIPT.write_text(json.dumps(result,indent=2,sort_keys=True)+chr(10))
 print(json.dumps({"state":status["state"],
 "packet_sha256":PACKET,"planner_message_state":"NOT_SENT",
 "successor":after,"receipt_sha256":sha(RECEIPT.read_bytes())},sort_keys=True))
if __name__=="__main__":main()
