#!/usr/bin/env python3
"""Generate judge-safe question -> answer -> agent/model/token story.

Historical BAND events contain NO measured model tokens. Do not manufacture them.
Simulated Flexprice costs are separate, visibly classified synthetic evidence.
Only hashed/message metadata and editorial summaries reach static output.
"""
from __future__ import annotations
import hashlib,json,pathlib
from scripts.sneak_conversation_ledger import compile_source,sha,digest,enc
from scripts.flexprice_roi_trial import measure,canonical as roi_canonical

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"deploy/vercel-preview/data/token-journeys.json"
FIXTURE=ROOT/"data/demo/roi_trial_fixture.json"
RECEIPT=ROOT/"receipts/flexprice/SNEAK_FLEXPRICE_ROI_SIMULATED_20261020.json"
SOURCE=ROOT/"receipts/band/SNEAK-013_HANDOFF.json"
LINKS={
 "website_production":"https://sneak-evidence-preview.vercel.app",
 "website_judge":"https://sneak-evidence-preview.vercel.app/judge",
 "website_tokens":"https://sneak-evidence-preview.vercel.app/tokens",
 "website_conversations":"https://sneak-evidence-preview.vercel.app/conversations",
 "website_heatmap":"https://sneak-evidence-preview.vercel.app/heatmap",
 "github_repo":"https://github.com/biobitworks/sneak-judges",
 "github_private_development_repo":"https://github.com/biobitworks/sneak",
 "github_pr":"https://github.com/biobitworks/sneak/pull/11",
 "github_final_handoff":"https://github.com/biobitworks/sneak/blob/deploy/sneak-vercel-preview-20261020/docs/SNEAK_FINAL_PLANNER_HANDOFF_20261020.md",
}
def build():
    source=compile_source()
    a=source["events"]
    if len(a)!=3 or a[0]["actor"]!="Tom" or a[1]["actor"]!="Jerry":
        raise ValueError("historical message identity/order changed; reject editorial projection")
    raw=json.loads(SOURCE.read_text())
    by_id={}
    for e in raw["leaves"]:
        for m in e["event"].get("payload",{}).get("messages",[]):
            by_id[sha(m["id"].encode())]=m.get("content","")
    expected=("Project handoff token:","Acknowledged:","Decision SNEAK-H01:")
    for e,marker in zip(a,expected):
        content=by_id.get(e["source_message_sha256"] or "",None) if "source_message_sha256" in e else by_id.get(e["source_message_sha256"],None)
        if content is None:
            content=by_id.get(e["source_message_sha256"],None)
        if content is None or marker not in content:
            raise ValueError("source content mismatches declared editorial summaries")
        if sha(content.encode("utf-8"))!=e["text_sha256"]:
            raise ValueError("source message checksum differs")
    def meta(e):
        return {"fco_id":e["id"],"observed_at":e["observed_at"],
                "actor":e["actor"],"actor_identity_sha256":e["actor_identity_sha256"],
                "message_sha256":e["text_sha256"],
                "input_sha256":e["input_sha256"],"output_sha256":e["output_sha256"],
                "model_id":None,"model_version":None,
                "prompt_tokens":None,"completion_tokens":None,
                "total_tokens":None,"token_status":"NOT_MEASURED",
                "model_status":"NOT_ATTESTED"}
    observed=[
        {"id":"BAND-QA-001","evidence_class":"HISTORICALLY_OBSERVED_MESSAGE_IDS_WITH_EDITORIAL_SUMMARIES",
         "question":"Please acknowledge the shared project handoff in this BAND room.",
         "answer":"Handoff acknowledged. BAND, Cognee, Snyk and Flexprice remain requirements, not automatically completed work.",
         "question_source":meta(a[0]),"answer_source":meta(a[1]),
         "result":"ACKNOWLEDGMENT_CAPTURED","scored_quality":"NOT_COMPUTED",
         "next_action":"Independent verification of sponsor requirements and human review."},
        {"id":"BAND-QA-002","evidence_class":"HISTORICALLY_OBSERVED_QUESTION_WITHOUT_CONFIRMED_ANSWER",
         "question":"Which skill-review input should SNEAK implement first: MCP-delivered or CLI-delivered?",
         "answer":None,"question_source":meta(a[2]),"answer_source":None,
         "result":"AWAITING_EVIDENCE_BOUND_HUMAN_ANSWER","scored_quality":"NOT_COMPUTED",
         "next_action":"Obtain actual human decision and its BAND message ID."}
    ]
    fixture=json.loads(FIXTURE.read_text())
    roi=measure(fixture)
    if roi["status"]!="SIMULATED_NOT_OBSERVED" or roi["live_flexprice_metering"]!="NOT_TESTED":
        raise ValueError("cannot publish ROI as live")
    if RECEIPT.exists():
        existing=json.loads(RECEIPT.read_text())
        if existing!=roi: raise ValueError("simulated ROI receipt differs from calculation")
    rows=[]
    for item in roi["events"]:
        p=item["properties"]
        rows.append({
          "question":"Illustrative matched task "+p["task_id"]+" (not a recorded prompt)",
          "answer":"Synthetic "+p["scenario"]+" step (not a recorded model response)",
          "task_id":p["task_id"],"scenario":p["scenario"],
          "agent":p["agent_id"],"model":p["model_id"],"human":p["human_id"],
          "prompt_tokens":int(p["prompt_tokens"]),
          "answer_tokens":int(p["completion_tokens"]),
          "total_tokens":int(p["tokens"]),
          "outcome":"SIMULATED_ONLY_NOT_A_PRODUCTION_SUCCESS",
          "event_id":item["event_id"],
          "input_sha256":p["input_sha256"],
          "classification":"SIMULATED_NOT_OBSERVED"
        })
    projection={"schema":"sneak.judge-token-journeys.v1",
      "public_safe":True,"source_scope":"ONE_CAPTURED_BAND_ROOM_ONLY",
      "headline":"Question → answer → agent → model → outcome → tokens",
      "links":LINKS,
      "observed_question_answer":observed,
      "observed_model_token_coverage":"NOT_MEASURED",
      "observed_token_cost":"NOT_COMPUTED",
      "simulated":{"classification":"SIMULATED_NOT_OBSERVED",
        "human_rates":"ASSUMED_NOT_OBSERVED",
        "provider_prices":"ASSUMED_NOT_PROVIDER_PRICING",
        "tokens_baseline":roi["metrics"]["baseline"]["tokens"],
        "tokens_sneak":roi["metrics"]["sneak"]["tokens"],
        "token_reduction_fraction":roi["token_reduction_fraction"],
        "cost_reduction_fraction":roi["estimated_cost_reduction_fraction"],
        "real_roi":"NOT_COMPUTED",
        "rows":rows,"fixture_sha256":sha(roi_canonical(fixture)),
        "receipt_sha256":roi["receipt_sha256"]},
      "security_score":"NOT_COMPUTED",
      "snyk_code":"ERROR_AUTHENTICATION",
      "snyk_oss":"ERROR_DEPENDENCY_RESOLUTION",
      "snyk_container":"NOT_TESTED_NO_IDENTIFIED_IMAGE",
      "teammate_score":"PENDING_HUMAN_REVIEW",
      "band_planner_live":"NOT_VERIFIED",
      "judge_acceptance":"NOT_OBSERVED",
      "release_claim":"EVIDENCE_DEMO_NOT_FULL_HACKATHON_ACCEPTANCE",
      "source_receipt_sha256":sha(SOURCE.read_bytes())}
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_bytes(enc(projection)+b"\n")
    return projection
if __name__=="__main__":
    p=build()
    print(json.dumps({"observed_qa":len(p["observed_question_answer"]),"simulated_rows":len(p["simulated"]["rows"]),"result":"PASS","observed_tokens":p["observed_model_token_coverage"]},sort_keys=True))
