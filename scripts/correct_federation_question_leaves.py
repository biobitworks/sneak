#!/usr/bin/env python3
"""Append a corrected, source-linked semantic successor (never rewrite v0).

V0 incorrectly used literal backslash-x characters for the question leaf tag.
The v0 MMR is byte-consistent; its source-scheme claim is FALSE.
This correction uses SHA256(0x00 || exact UTF-8 question) and cross-checks
all authoritative 56 PDF-derived requirement rows including optional/bonus.
"""
from __future__ import annotations
import hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from sneak.merkle import canonical
from sneak.fcg_registry import FCGRegistry
from sneak.mmr_reference import MMR,mmr_verify
from federate_sneak_conversations import commit_mmr,read_jsonl,sha
LEDGER=ROOT/"data/fcg/sneak-016-replay.jsonl"
V0=ROOT/"receipts/evaluations/SNEAK_20261020_CONVERSATION_FEDERATION.json"
V1=ROOT/"receipts/evaluations/SNEAK_20261020_CONVERSATION_FEDERATION_V1_CORRECTED.json"
Q=Path("/tmp/sneak-lmev2-dataset/questions.jsonl")
MD=ROOT/"docs/requirements/HACKATHON_REQUIREMENTS.md"
FROZEN="a24ecf8fcdde9ed0504bd2feb2f69cab811d4a18cc493ecd47bd187486aae9c2"
CATEGORIES={"EVENT","MANDATORY","BONUS","TRACK","JUDGING","EXTRA_CREDIT","PRIMER","SETUP","UNCONFIRMED","OPTIONAL"}

def parse_canonical_requirements(text):
 rows=[]
 for line in text.splitlines():
  if not line.startswith("|"):continue
  fields=[x.strip() for x in line.split("|")[1:-1]]
  if len(fields)<6 or fields[1] not in CATEGORIES:continue
  rows.append({"id":fields[0],"category":fields[1],"topic":fields[2],
  "source_page":fields[3],"acceptance_test":fields[4],"historical_status":fields[5]})
 if len(rows)!=56 or len({r["id"] for r in rows})!=56:
  raise ValueError("Source-derived requirement matrix incomplete")
 return rows

def main():
 rawv0=V0.read_bytes()
 # Deliberately preserve exact wrong suffix; never promote invalid json as a verified source.
 if not rawv0.endswith(bytes([92,110])):raise RuntimeError("Expected exact v0 malformed newline bytes")
 v0=json.loads(rawv0[:-2])
 oldroot=v0["successor"]["mmr_root"]
 reg=FCGRegistry(LEDGER);prior=reg.verify()
 if prior["fco_count"]!=174 or prior["mmr_root"]!=FROZEN or oldroot!=FROZEN:
  raise RuntimeError("Refuse correction without exact predecessor")
 actor=reg.rows()[58]["fco_id"]
 ctx={"purpose":"semantic_correction","v0_root":oldroot,
 "v0_receipt_sha256":sha(rawv0),"evidence_scope":"not_whole_chat_corpus"}
 def add(kind,payload,source,state="OBSERVED",parent=None,model="NOT_APPLICABLE"):
  return reg.append(kind=kind,payload=payload,actor_fco=actor,model_fco=model,
   parent_fco=parent,state=state,source_sha256=source,context=ctx)
 corrupt=add("classification",{
   "target":"v0_question_merkle_leaf_sha256_encoding",
   "declared":"SHA256(0x00 || UTF8(question))",
   "observed":"SHA256(ASCII(backslash-x00) || UTF8(question))",
   "scheme_valid":False,"old_mmr_arithmetic_valid":True,
   "v0_receipt_json_valid":False,"corrective_successor_required":True},
   sha(rawv0),state="NEGATIVE",parent=reg.rows()[-1]["fco_id"])
 questions={x["id"]:x for x in read_jsonl(Q)}
 pilot=json.loads((ROOT/"receipts/evaluations/LMEV2_20261020_PILOT.json").read_text())
 model_replacements={}
 federation=[]
 for name,oldbundle in sorted(v0["models"].items()):
  mid=oldbundle["model_fco"];agent=oldbundle["agent_fco"]
  leaves=[];corrected=[]
  for oldtrace in oldbundle["questions"]:
   qid=oldtrace["question_id"]
   qbytes=questions[qid]["question"].encode()
   qsha=sha(qbytes)
   if qsha!=oldtrace["question_sha256"]:raise ValueError("Question input hash inconsistent")
   correct_leaf=sha(bytes([0])+qbytes)
   old_leaf=oldtrace["question_root"]
   if correct_leaf==old_leaf:raise ValueError("Expected v0 question leaf defect absent")
   correction=add("source",{
     "question_id":qid,"question_sha256":qsha,
     "old_leaf_invalid":old_leaf,
     "correct_question_merkle_leaf_sha256":correct_leaf,
     "construction":"SHA256(0x00 || original UTF8 question bytes)",
     "correction_of_breakpoint_fco":oldtrace["breakpoint_fco"]},
      qsha,parent=oldtrace["breakpoint_fco"],model=mid)
   old_val=next((z for z in reg.rows()[:79] if z["identity"]["kind"]=="value" and
    z["identity"]["payload"].get("question_id")==qid and
    z["identity"]["payload"].get("response_sha256")==oldtrace["output_sha256"] and
    z["identity"]["model_fco"]==mid),None)
   if not old_val:raise ValueError("Cannot bind old output identity")
   qleaves=[
    {"record":"root_question_anchor_v1","model_fco":mid,"question_id":qid,
     "question_leaf_sha256":correct_leaf,"question_sha256":qsha,
     "corrected_source_fco":correction["fco_id"]},
    {"record":"model_output_v1","model_fco":mid,"agent_fco":agent,
     "question_id":qid,"question_leaf_sha256":correct_leaf,
     "source_output_fco":old_val["fco_id"],
     "output_sha256":oldtrace["output_sha256"],
     "steps_sha256":oldtrace["steps_hash"]}
   ]
   question_mmr=commit_mmr(qleaves)
   bp=add("breakpoint",{
     "question_id":qid,"root_question_leaf_sha256":correct_leaf,
     "per_question_mmr_root":question_mmr["root"],
     "mmr_size":question_mmr["node_count"],
     "integrity_verified":True,
     "construction_verified":True,"acceptance":"PENDING",
     "temporal_delta":"NOT_COMPUTED",
     "predecessor_v0_breakpoint_fco":oldtrace["breakpoint_fco"]},
    sha(canonical(question_mmr)),parent=correction["fco_id"],model=mid)
   corrected.append({"question_id":qid,"correct_question_leaf_sha256":correct_leaf,
      "rejected_v0_leaf_sha256":old_leaf,
      "per_question_mmr":question_mmr,"breakpoint_fco":bp["fco_id"],
      "delta_correct_vs_baseline":oldtrace["delta_correct_vs_baseline"],
      "delta_ms_vs_baseline":oldtrace["delta_ms_vs_baseline"]})
   leaves.extend(qleaves)
  model_mmr=commit_mmr(leaves)
  modelbp=add("breakpoint",{
   "model":name,"model_fco":mid,"agent_fco":agent,
   "corrected_model_mmr_root":model_mmr["root"],
   "old_v0_model_mmr_root":oldbundle["model_mmr"]["root"],
   "mmr_nodes":model_mmr["node_count"],"integrity_verified":True,
   "acceptance":"PENDING","temporal_delta":"NOT_COMPUTED",
   "predecessor_model_fco":oldbundle["model_breakpoint_fco"]},
   sha(canonical(model_mmr)),parent=corrected[-1]["breakpoint_fco"],model=mid)
  model_replacements[name]={"model_fco":mid,"agent_fco":agent,"model_mmr":model_mmr,
    "breakpoint_fco":modelbp["fco_id"],"questions":corrected}
  federation.append({"record":"corrected_model_mmr","model":name,
    "mmr_root":model_mmr["root"],"model_fco":mid,
    "breakpoint_fco":modelbp["fco_id"],"acceptance":"PENDING"})
 pdf_rows=parse_canonical_requirements(MD.read_text())
 source_sha=sha(MD.read_bytes())
 src=add("source",{"path":str(MD.relative_to(ROOT)),
  "record_count":len(pdf_rows),"document_sha256":source_sha,
  "source_classifications_preserved":True},
  source_sha,parent=corrupt["fco_id"])
 pdf_fcos={}
 from collections import Counter
 for req in pdf_rows:
  eid=req["id"]
  ev=add("classification",{
    "requirement_id":eid,"category":req["category"],"topic":req["topic"],
    "source_page":req["source_page"],
    "acceptance_test":req["acceptance_test"],
    "original_status":req["historical_status"],"accepted":False,
    "status":"NOT_TESTED",
    "classification_supported":True,"acceptance_supported":False},
    source_sha,parent=src["fco_id"])
  pdf_fcos[eid]=ev["fco_id"]
  federation.append({"record":"requirement_source_row","requirement_id":eid,
   "category":req["category"],"classification_fco":ev["fco_id"],
   "acceptance":"NOT_TESTED"})
 for s in v0["source_coverage"]:
  federation.append({"record":"conversation_source_coverage",
   "source":s["source"],"sha256":s.get("sha256"),
   "source_fco":s["source_fco"],
   "complete":bool(s["conversation_completeness"] is True)})
 fammr=commit_mmr(federation)
 fam=add("breakpoint",{
  "construction":"corrected_question_prefix_0x00_plus_original_requirements",
  "federation_mmr_root":fammr["root"],
  "federation_mmr_nodes":fammr["node_count"],
  "federation_mmr_leaves":fammr["leaf_count"],
  "integrity_verified":True,"previous_semantic_construction_valid":False,
  "complete_conversation_coverage":False,"all_requirements_accepted":False,
  "optional_and_bonus_requirements_preserved":True,"acceptance":"PENDING"},
  sha(canonical(fammr)),parent=src["fco_id"])
 result={"schema":"sneak.conversation-federation.corrected.v1",
  "parent":prior,"successor":reg.verify(),
  "failed_semantic_predecessor_receipt_sha256":sha(rawv0),
  "failed_semantic_predecessor_fco":corrupt["fco_id"],
  "source_matrix_sha256":source_sha,
  "official_source_requirement_count":len(pdf_rows),
  "official_source_classifications":dict(Counter(x["category"] for x in pdf_rows)),
  "manifest_only_requirement_count":v0["requirement_count"],
  "requirement_source_occurrences_in_both_manifests":len(pdf_rows)+v0["requirement_count"],
  "cross_manifest_identity_deduplication":"NOT_COMPUTED",
  "official_source_requirement_fcos":pdf_fcos,
  "model_roots":model_replacements,
  "federation":fammr,"federation_fco":fam["fco_id"],
  "all_conversations_captured":False,"live_band_planner":"NOT_TESTED_AUTH_BLOCKED",
  "live_cognee_update":"NOT_TESTED","coverage_state":"PARTIAL",
  "security_admission":"DENY"}
 V1.parent.mkdir(parents=True,exist_ok=True)
 V1.write_text(json.dumps(result,indent=2,sort_keys=True)+chr(10))
 print(json.dumps({"parent":prior,"successor":result["successor"],
  "models":{k:v["model_mmr"]["root"] for k,v in model_replacements.items()},
  "federation_root":fammr["root"],"pdf_requirement_count":len(pdf_rows),
  "classification_counts":result["official_source_classifications"],
  "output_sha256":sha(V1.read_bytes())},sort_keys=True))

if __name__=="__main__":main()
