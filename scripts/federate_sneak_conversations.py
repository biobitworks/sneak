#!/usr/bin/env python3
"""Deterministic SNEAK conversation/model/question federation successor.

Reads frozen evidence, never replays inference, never claims missing transcripts.
Commits canonical model MMRs and observed source manifests to existing FCO ledger.
Exact predecessor required so reruns cannot duplicate or overwrite history.
"""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from sneak.fcg_registry import FCGRegistry
from sneak.merkle import canonical
from sneak.mmr_reference import MMR,mmr_verify,H
LEDGER=ROOT/"data/fcg/sneak-016-replay.jsonl"
PILOT=ROOT/"receipts/evaluations/LMEV2_20261020_PILOT.json"
QUESTIONS=Path("/tmp/sneak-lmev2-dataset/questions.jsonl")
REQ=ROOT/".planning/requirements.jsonl"
RECEIPT=ROOT/"receipts/evaluations/SNEAK_20261020_CONVERSATION_FEDERATION.json"
FROZEN_ROOT="5f7116cd7d568b61f2abeb67adf8b71f1780171e69c07836a9126f643fa20eec"
SOURCE_PATHS=(
 "receipts/connectors/SNEAK-015_LIVE_BAND_COGNEE.json",
 "receipts/connectors/SNEAK-017B_BAND_RELAY.json",
 "receipts/connectors/SNEAK-018_R15_LIVE_REVIEW.json",
 "receipts/connectors/SNEAK-019_BAND_READBACK.json",
 "docs/handoff/BAND_ROOM_STARTER_PLAN.md",
 "receipts/evaluations/LMEV2_20261020_PILOT.json",
 "receipts/evaluations/LMEV2_20261020_SECURITY_SUCCESSOR.json",
)
MISSING_CONVERSATION_SCOPES=(
 "ALL_BAND_ROOM_MESSAGES_AND_BOARD_HISTORY",
 "ALL_CHATGPT_PROJECT_CONVERSATION_EXACT_TRANSCRIPTS",
 "ALL_CLAUDE_AGENT_CONVERSATION_EXACT_TRANSCRIPTS",
 "BAND_PLANNER_ID_AND_LIVE_ACK",
)

def sha(raw:bytes)->str: return hashlib.sha256(raw).hexdigest()

def read_jsonl(p:Path):
 return [json.loads(s) for s in p.read_text(encoding="utf-8").splitlines() if s.strip()]

def commit_mmr(leaves:list[dict])->dict:
 """Leaves are already complete canonical records; verify and persist proofs."""
 mmr=MMR()
 bodies=[]
 for record in leaves:
  body=canonical(record);bodies.append(body);mmr.append(body)
 proof_ok=all(mmr_verify(body,mmr.proof(i),mmr.root()) for i,body in enumerate(bodies))
 # Negative test: a mutated single byte must fail inclusion against the same commitment.
 negative_ok=all(not mmr_verify(body+b"!",mmr.proof(i),mmr.root()) for i,body in enumerate(bodies))
 if not proof_ok or not negative_ok:
  raise ValueError("Merkle Mountain Range inclusion or negative-control failure")
 return {"algorithm":"sneak.mmr-reference.sha256-position-committed.v1",
  "leaf_count":len(leaves),"node_count":mmr.size,"root":mmr.root().hex(),
  "inclusion_verified":proof_ok,"tamper_rejected":negative_ok,
  "leaf_sha256":[sha(x) for x in bodies]}

def federate(*, registry:FCGRegistry, pilot:dict, questions:list[dict],
             requirements:list[dict], source_paths:list[str], missing_scopes:list[str],
             script_sha:str)->dict:
 parent=registry.verify()
 if parent["fco_count"]!=79 or parent["mmr_root"]!=FROZEN_ROOT:
  raise RuntimeError("Predecessor drift; refuse non-append-only replay")
 old=registry.rows()
 actor=old[58]["fco_id"]
 ctx={"project":"sneak","project_branch":"feature/conversation-federation-mmr-20261020",
      "predecessor_mmr_root":parent["mmr_root"],"model_method":"B0_no_retrieval",
      "data_source":"LongMemEval-V2 pinned two-question diagnostic",
      "full_conversation_corpus":"NOT_AVAILABLE"}
 def add(kind,payload,source_sha,state="OBSERVED",parent_fco=None,model_fco="NOT_APPLICABLE",edges=None):
  return registry.append(kind=kind,payload=payload,actor_fco=actor,
   model_fco=model_fco,parent_fco=parent_fco,edges=edges or [],state=state,
   source_sha256=source_sha,context=ctx)
 head=add("source",{"kind":"root_provenance","source_receipt":str(PILOT.relative_to(ROOT)),
  "parent_mmr":parent["mmr_root"],"all_project_conversations_complete":False},
  sha(PILOT.read_bytes()),parent_fco=old[-1]["fco_id"])
 coverage=[]
 for path in source_paths:
  file=ROOT/path
  if not file.is_file():raise FileNotFoundError(path)
  digest=sha(file.read_bytes())
  row=add("source",{"source_path":path,"byte_digest":digest,
    "coverage":"DOCUMENT_OR_RECEIPT_ONLY","not_a_complete_chat_transcript":True},
    digest,parent_fco=head["fco_id"])
  coverage.append({"source":path,"sha256":digest,"source_fco":row["fco_id"],
    "status":"OBSERVED_SOURCE_BYTES","conversation_completeness":"UNKNOWN"})
 for name in missing_scopes:
  row=add("classification",{"missing_scope":name,"coverage":"NOT_ESTABLISHED",
    "reason":"full original bytes and authoritative conversation listing unavailable"},
    "UNKNOWN",state="NOT_TESTED",parent_fco=head["fco_id"])
  coverage.append({"source":name,"source_fco":row["fco_id"],"sha256":None,
    "status":"NOT_TESTED","conversation_completeness":False})
 req_digest=sha(REQ.read_bytes())
 req_source=add("source",{"path":str(REQ.relative_to(ROOT)),"sha256":req_digest,
   "classification_count":len(requirements)},req_digest,parent_fco=head["fco_id"])
 classifications={}
 for req in requirements:
  rid=req.get("id")
  if not rid or rid in classifications:raise ValueError("Duplicate/missing requirement identifier")
  classified=add("classification",{"requirement_id":rid,"requirement_text":req.get("requirement"),
   "source_classification":req.get("classification",req.get("type","UNKNOWN")),
   "source_acceptance_state":req.get("acceptance_state","UNKNOWN"),
   "independently_satisfied":False,"evidence_scope":"source_manifest_only",
   "optional_or_bonus_retained":True},req_digest,parent_fco=req_source["fco_id"])
  classifications[rid]=classified["fco_id"]
 question_map={q["id"]:q for q in questions}
 qids={x["question_id"] for row in pilot["results"] for x in row["question_results"]}
 if set(question_map)!=qids:raise ValueError("question set mismatch")
 model_bundles={}
 project_federation=[]
 for model_record in pilot["results"]:
  name=model_record["model"]
  model_existing=next((x for x in old if x["identity"]["kind"]=="model" and x["identity"]["payload"].get("model")==name),None)
  agent_existing=next((x for x in old if x["identity"]["kind"]=="agent" and x["identity"]["payload"].get("model")==name),None)
  if not model_existing or not agent_existing:raise ValueError("Missing registered model/agent predecessor")
  model_id=model_existing["fco_id"]
  agent_id=agent_existing["fco_id"]
  leaves=[]
  traces=[]
  for row in model_record["question_results"]:
   question=question_map[row["question_id"]]
   question_bytes=question["question"].encode("utf-8")
   question_sha=sha(question_bytes)
   root_question_leaf=H(b"\\x00"+question_bytes).hex()
   question_fco=add("source",{
      "question_id":question["id"],"question_sha256":question_sha,
      "question_merkle_leaf_sha256":root_question_leaf,
      "question_domain":question["domain"],"hash_scheme":"SHA256(0x00 || exact UTF-8 question)",
      "not_a_hash_of_the_answer":True},question_sha,parent_fco=agent_id,
      model_fco=model_id)
   step_manifest={
    "script_sha256":script_sha,"source_benchmark":"LongMemEval-V2",
    "question_id":question["id"],"question_sha256":question_sha,
    "method":"B0_no_retrieval","temperature":0,"num_predict":128,"think":False,
    "gold_in_input":False,"model_name":name,
    "scorer":"official_evaluation_qa_eval_metrics.py",
   }
   step_sha=sha(canonical(step_manifest))
   step=add("transformation",{"deterministic_manifest_sha256":step_sha,
     "steps":["normalize pinned question bytes","Ollama generate with fixed options",
              "evaluate frozen answer using declared scorer"],
     "step_manifest":step_manifest},step_sha,parent_fco=question_fco["fco_id"],
     model_fco=model_id)
   candidate_output_sha=row["response_sha256"]
   match=next((x for x in old if x["identity"]["kind"]=="value"
    and x["identity"]["payload"].get("question_id")==question["id"]
    and x["identity"]["payload"].get("response_sha256")==candidate_output_sha
    and x["identity"]["model_fco"]==model_id),None)
   if not match or row.get("score_status")!="OBSERVED":raise ValueError("Unbound observed model output")
   result=add("value",{"question_id":question["id"],"input_sha256":question_sha,
    "output_response_sha256":candidate_output_sha,
    "prior_value_fco":match["fco_id"],
    "correct":row["correct"],"latency_ms":row["latency_ms"],
    "method":"B0_no_retrieval","response_bytes":"NOT_PERSISTED",
    "raw_ollama_response_digest_only":True},candidate_output_sha,
    parent_fco=step["fco_id"],model_fco=model_id,
    edges=[{"relation":"derived_from","to":match["fco_id"]}])
   same_question=[rr for run in pilot["results"] for rr in run["question_results"] if rr["question_id"]==question["id"]]
   reference=same_question[0]
   delta_accuracy=(int(bool(row["correct"]))-int(bool(reference["correct"])))
   delta_latency_ms=round(row["latency_ms"]-reference["latency_ms"],2)
   delta_record={"question_id":question["id"],"relative_to":"first_model_same_question",
     "baseline_model":pilot["results"][0]["model"],
     "correct_delta":delta_accuracy,"latency_ms_delta":delta_latency_ms,
     "delta_over_time":"NOT_COMPUTED","reason":"one evaluation timepoint per model",
     "hash_distance_is_not_a_performance_metric":True}
   delta_sha=sha(canonical(delta_record))
   delta=add("delta",delta_record,delta_sha,parent_fco=result["fco_id"],model_fco=model_id)
   leaves.extend([
    {"record":"root_question_anchor","model_fco":model_id,"question_id":question["id"],
     "input_sha256":question_sha,"question_fco":question_fco["fco_id"]},
    {"record":"deterministic_model_result","model_fco":model_id,"agent_fco":agent_id,
     "question_id":question["id"],"input_sha256":question_sha,
     "step_sha256":step_sha,"output_sha256":candidate_output_sha,
     "value_fco":result["fco_id"],"delta_fco":delta["fco_id"]}
   ])
   question_pair=commit_mmr(leaves[-2:])
   breakpoints=add("breakpoint",{
    "question_id":question["id"],"root_question_sha256":question_sha,
    "model_question_mmr_root":question_pair["root"],
    "model_question_mmr_nodes":question_pair["node_count"],
    "integrity_verified":question_pair["inclusion_verified"],
    "tamper_rejected":question_pair["tamper_rejected"],
    "acceptance":"PENDING","approval_required":True,
    "same_question_output_delta":delta_accuracy,
    "delta_over_time":"NOT_COMPUTED"},
    sha(canonical(question_pair)),parent_fco=delta["fco_id"],model_fco=model_id)
   traces.append({"question_id":question["id"],"question_root":root_question_leaf,
    "question_sha256":question_sha,"steps_hash":step_sha,
    "output_sha256":candidate_output_sha,
    "score_correct":bool(row["correct"]),"latency_ms":row["latency_ms"],
    "delta_correct_vs_baseline":delta_accuracy,
    "delta_ms_vs_baseline":delta_latency_ms,
    "model_question_mmr":question_pair,"breakpoint_fco":breakpoints["fco_id"],
    "acceptance":"PENDING"})
  model_mmr=commit_mmr(leaves)
  model_anchor=add("breakpoint",{
    "model":name,"model_fco":model_id,"agent_fco":agent_id,
    "model_mmr_root":model_mmr["root"],"model_mmr_nodes":model_mmr["node_count"],
    "model_mmr_leaves":model_mmr["leaf_count"],
    "integrity_verified":True,"acceptance":"PENDING",
    "temporal_accuracy_delta":"NOT_COMPUTED",
    "temporal_latency_delta":"NOT_COMPUTED",
    "missing_same_model_timepoints":True},
    sha(canonical(model_mmr)),parent_fco=traces[-1]["breakpoint_fco"],
    model_fco=model_id)
  model_bundles[name]={"model_fco":model_id,"agent_fco":agent_id,
    "model_mmr":model_mmr,"model_breakpoint_fco":model_anchor["fco_id"],"questions":traces}
  project_federation.append({"record":"model_mmr_snapshot","model":name,
    "root":model_mmr["root"],"model_fco":model_id,
    "model_breakpoint_fco":model_anchor["fco_id"],"integrity_verified":True,
    "acceptance":"PENDING"})
 # Source-backed conversation receipts are *not* the same as full conversation histories.
 for item in coverage:
  project_federation.append({"record":"conversation_source_manifest","source":item["source"],
   "sha256":item.get("sha256"),"source_fco":item["source_fco"],
   "status":item["status"],"conversation_completeness":item["conversation_completeness"]})
 federated=commit_mmr(project_federation)
 federation_fco=add("breakpoint",{
   "federation_mmr_root":federated["root"],"leaf_count":federated["leaf_count"],
   "mmr_size":federated["node_count"],"integrity_verified":True,
   "complete_conversation_corpus":False,"complete_project_capture":False,
   "acceptance":"PENDING","all_requirements_verified":False,
   "root_is_identity_not_scientific_truth":True},
   sha(canonical(federated)),parent_fco=head["fco_id"])
 successor=registry.verify()
 return {"schema":"sneak.conversation-model-federation.v1",
  "source":"pinned existing model-run receipts plus local source inventory",
  "parent":parent,"successor":successor,
  "source_coverage":coverage,"coverage_state":"PARTIAL",
  "full_band_planner_confirmation":"NOT_TESTED_AUTH_BLOCKED",
  "cognee_write_and_readback":"NOT_TESTED_BASE_URL_OR_AUTH_UNAVAILABLE",
  "models":model_bundles,"requirement_classification_fcos":classifications,
  "requirement_count":len(classifications),"requirements_accepted_count":0,
  "requirements_acceptance_status":"NOT_COMPLETELY_VERIFIED",
  "federation":federated,"federation_fco":federation_fco["fco_id"],
  "integrity_verified":True,"completeness_verified":False,"security_admission":"DENY"}

def main():
 questions_all=read_jsonl(QUESTIONS)
 pilot=json.loads(PILOT.read_text())
 selected={r["question_id"] for run in pilot["results"] for r in run["question_results"]}
 questions=[x for x in questions_all if x["id"] in selected]
 if len(questions)!=len(selected):raise ValueError("Missing exact questions")
 registry=FCGRegistry(LEDGER)
 result=federate(registry=registry,pilot=pilot,questions=questions,
 requirements=read_jsonl(REQ),source_paths=list(SOURCE_PATHS),
 missing_scopes=list(MISSING_CONVERSATION_SCOPES),
 script_sha=sha((ROOT/"scripts/run_lmev2_pilot.py").read_bytes()))
 RECEIPT.parent.mkdir(parents=True,exist_ok=True)
 RECEIPT.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=True)+"\\n")
 print(json.dumps({"parent":result["parent"],"successor":result["successor"],
 "federation_root":result["federation"]["root"],
 "coverage_state":result["coverage_state"],"requirements":result["requirement_count"],
 "models":{m:{"mmr_root":v["model_mmr"]["root"],
 "question_roots":[q["model_question_mmr"]["root"] for q in v["questions"]]}
 for m,v in result["models"].items()},
 "receipt_sha256":sha(RECEIPT.read_bytes())},sort_keys=True))

if __name__=="__main__":main()
