#!/usr/bin/env python3
"""One-shot, authenticated human relay. Never prints or persists API keys."""
from __future__ import annotations
import json,os,hashlib,pathlib,urllib.request,urllib.error,datetime

ROOT=pathlib.Path(__file__).resolve().parents[1]
DEST=ROOT/"receipts/integrations/SNEAK_20261020_JUDGE_ROI_BAND_COGNEE_HANDOFF.json"
BAND_BASE="https://api.band.ai/api/v1/me"
COGNEE_BASE="https://tenant-4ee605b3-4511-4496-bc8a-d9ee322fd30e.aws.cognee.ai"
ROOM="7e218ad7-4d4e-4a07-a3b2-d4db8a03b4c3"
AGENTS=["biobitworks/planner","biobitworks/tom","biobitworks/jerry"]
SOURCE_COMMIT="159134160d54288d9f8004f81c07244cb2d25296"
ROOT_QUESTION="Can agents preserve task context and verifiable custody while lowering complete cost per verified outcome?"
def canonical(x):return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
def h(x):return hashlib.sha256(canonical(x)).hexdigest()
def request(base,path,method="GET",payload=None,credential=None):
    headers={"Accept":"application/json"}
    if base==BAND_BASE:headers["X-API-Key"]=credential
    else:headers["X-Api-Key"]=credential
    raw=canonical(payload) if payload is not None else None
    if raw is not None:headers["Content-Type"]="application/json"
    req=urllib.request.Request(base+path,headers=headers,data=raw,method=method)
    try:
        with urllib.request.urlopen(req,timeout=22) as r:
            b=r.read()
            try:obj=json.loads(b) if b else {}
            except ValueError:obj={}
            return {"status":"HTTP_SUCCESS","http_code":r.status,"response_sha256":hashlib.sha256(b).hexdigest()},obj
    except urllib.error.HTTPError as e:
        return {"status":"HTTP_ERROR","http_code":e.code},{}
    except Exception as e:
        return {"status":"FAILED","error_type":type(e).__name__},{}
def main():
    if DEST.exists():raise RuntimeError("receipt exists; append successor under different path")
    cognee_key=os.getenv("COGNEE_API_KEY")
    band_key=os.getenv("BAND_API_KEY")
    if not cognee_key or not band_key:raise RuntimeError("requires both credentials in environment")
    evidence={"schema":"sneak.handoff.candidate.v1","root_question":ROOT_QUESTION,
              "root_question_sha256":hashlib.sha256(ROOT_QUESTION.encode()).hexdigest(),
              "repo":"biobitworks/sneak","source_commit":SOURCE_COMMIT,
              "roi_pr":17,"human_issue":18,"machine_mandatory_verified":0,
              "economics":"SIMULATED_NOT_OBSERVED","baseline_tokens_fixture":8000,
              "sneak_tokens_fixture":5000,"token_reduction_fixture_fraction":"0.375000",
              "flexprice_live":"NOT_TESTED","project_mmr":"NOT_COMPUTED"}
    bp="BP-"+h({"event_kind":"judge_roi_handoff","source":evidence,"room":ROOM})[:16]
    memory_text="SNEAK milestone address "+bp+"; source commit "+SOURCE_COMMIT+"; PR #17 simulated Flexprice events ONLY; judge human checklist issue #18; 0/30 machine verified mandatory; live Flexprice NOT_TESTED; Snyk gate BLOCKED; global project MMR NOT_COMPUTED. Ask planner to link next action to this address. Do not claim a success from mere delivery."
    record={"schema":"sneak.band-cognee.live-handoff-attempt.v1","created_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "identity":evidence,"candidate_bp_id":bp,"bp_status":"LOCAL_CONTENT_ADDRESS_ONLY",
            "actor":"HUMAN_API","band_room_id":ROOM,"target_handles":AGENTS,
            "cognee":{"add":"NOT_TESTED","cognify":"NOT_TESTED","search":"NOT_TESTED"},
            "band_send":"NOT_SENT","band_readback":"NOT_TESTED","agent_ack":"NOT_OBSERVED",
            "planner_execution":"NOT_OBSERVED","cross_agent_memory":"NOT_TESTED",
            "model_mmr":"NOT_COMPUTED","global_mmr":"NOT_COMPUTED",
            "signed":False}
    add,x=request(COGNEE_BASE,"/api/v1/add","POST",{"data":memory_text,"dataset_name":"sneak_judge_20261020"},cognee_key)
    record["cognee"]["add"]=add
    if add["status"]=="HTTP_SUCCESS":
        cognify,x=request(COGNEE_BASE,"/api/v1/cognify","POST",{"datasets":["sneak_judge_20261020"]},cognee_key)
        record["cognee"]["cognify"]=cognify
        if cognify["status"]=="HTTP_SUCCESS":
            sr,x=request(COGNEE_BASE,"/api/v1/search","POST",{"query":bp,"search_type":"CHUNKS"},cognee_key)
            record["cognee"]["search"]=sr
            record["cognee"]["independent_agent_readback"]="NOT_TESTED"
    ppl_resp,participants=request(BAND_BASE,"/chats/"+ROOM+"/participants",credential=band_key)
    record["band_preflight"]=ppl_resp
    ppl=participants.get("data",[]) if isinstance(participants,dict) else []
    ps={p.get("handle"):p for p in ppl if isinstance(p,dict)}
    if not all(x in ps for x in AGENTS):
        record["band_send"]="BLOCKED_MISSING_PARTICIPANTS"
    else:
        mentioned=[{"id":ps[name]["id"],"name":ps[name].get("name",name),"handle":name} for name in AGENTS]
        content=" ".join("@"+name for name in AGENTS)+" Please review SNEAK evidence address "+bp+". Repo biobitworks/sneak commit "+SOURCE_COMMIT+"; draft PR #17 simulated Flexprice attribution; human signoff issue #18. Baseline fixture 8000 vs SNEAK fixture 5000 tokens, 37.5% simulated reduction, NOT an observed product result. Cognee add="+str(record["cognee"]["add"].get("status"))+"; real cross-agent recall/board action NOT_OBSERVED; security DENY; machine acceptance 0/30. Planner: request separate agent-owned readback, task transitions and source-linked FCO/MMR; return receipt IDs, not claims of all-agent awareness."
        sent,x=request(BAND_BASE,"/chats/"+ROOM+"/messages","POST",{"message":{"content":content,"mentions":mentioned}},band_key)
        record["band_send"]=sent
        if sent["status"]=="HTTP_SUCCESS":
            ob=x.get("data",x) if isinstance(x,dict) else {}
            if isinstance(ob,dict):
                record["band_message_id"]=ob.get("id",ob.get("message_id"))
            rb,y=request(BAND_BASE,"/chats/"+ROOM+"/messages?message_type=text",credential=band_key)
            record["band_readback"]=rb
            blob=canonical(y)
            record["band_readback"]["body_digest_observed"]=bp.encode() in blob
    DEST.parent.mkdir(parents=True,exist_ok=True)
    record["receipt_sha256"]=h(record)
    DEST.write_bytes(canonical(record)+b"\n")
    print(json.dumps({"bp":bp,"cognee_add":record["cognee"]["add"],"cognee_cognify":record["cognee"]["cognify"],"cognee_search":record["cognee"]["search"],"band_send":record["band_send"],"band_readback":record["band_readback"],"agent_ack":record["agent_ack"],"receipt_sha256":record["receipt_sha256"]},sort_keys=True))
if __name__=="__main__":main()
