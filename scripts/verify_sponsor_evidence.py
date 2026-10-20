#!/usr/bin/env python3
"""Exact-byte sponsor traversal probe. All outputs are append-only; no secrets persisted."""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, subprocess, urllib.error, urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"receipts/integrations/SNEAK_SPONSOR_TRAVERSAL_V1_20261020.json"
BAND="https://api.band.ai/api/v1/me"
COGNEE="https://tenant-4ee605b3-4511-4496-bc8a-d9ee322fd30e.aws.cognee.ai"
ROOM="7e218ad7-4d4e-4a07-a3b2-d4db8a03b4c3"
DATASET="sneak_working_memory"
def enc(o): return json.dumps(o,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
def digest(b):return hashlib.sha256(b).hexdigest()
def identity(source_commit):
    rules=ROOT/"data/rules/atomic_acceptance_r5.jsonl"
    i={"schema":"sneak.sponsor-traversal.identity.v1","source_commit":source_commit,
       "requirements_sha256":digest(rules.read_bytes()),
       "root_question":"Can SNEAK agents carry traceable task knowledge between Band, Cognee, security and human decision with verified outcome economics?",
       "target_services":["band","cognee","snyk"],"context":"SNEAK judge readiness audit; not an accepted root"}
    return i,digest(enc(i))
def call(url,key,body=None,method="GET",band=False):
    if not key:return {"status":"BLOCKED_NO_CREDENTIAL"},None
    h={"Accept":"application/json",("X-API-Key" if band else "X-Api-Key"):key}
    if body is not None:h["Content-Type"]="application/json"
    q=urllib.request.Request(url,data=enc(body) if body is not None else None,headers=h,method=method)
    try:
        with urllib.request.urlopen(q,timeout=22) as r:
            b=r.read();o=json.loads(b) if b else {}
            return {"status":"HTTP_SUCCESS","http_code":r.status,"response_sha256":digest(b)},o
    except urllib.error.HTTPError as e:
        b=e.read()
        return {"status":"HTTP_ERROR","http_code":e.code,"response_sha256":digest(b)},None
    except Exception as e:return {"status":"FAILED","exception_type":type(e).__name__},None
def find_exact_hash(o,address):
    return address in enc(o).decode("utf-8") if o is not None else False
def merkle_root(leaves):
    if not leaves:return None
    level=[hashlib.sha256(b"\x00"+enc(x)).digest() for x in leaves]
    while len(level)>1:
        level=[hashlib.sha256(b"\x01"+level[i]+level[i+1]).digest() if i+1<len(level) else level[i] for i in range(0,len(level),2)]
    return level[0].hex()
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--live",action="store_true");args=ap.parse_args()
    if OUT.exists():raise SystemExit("receipt already exists; must append successor, not overwrite")
    sha=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    i,address=identity(sha)
    rec={"schema":"sneak.sponsor-traversal.receipt.v1","identity":i,"evidence_sha256":address,
         "band":{"status":"NOT_TESTED"},"cognee":{"status":"NOT_TESTED"},
         "snyk":{"status":"NOT_TESTED"},"human_approval":"NOT_OBSERVED",
         "agent_ack":"NOT_OBSERVED","provider_e2e_verdict":"NOT_TESTED",
         "model_mmr":"NOT_COMPUTED","global_project_mmr":"NOT_COMPUTED",
         "signature":"NOT_SIGNED","reason":"one hash through independent provider receipts required"}
    if args.live:
        bk=os.environ.get("BAND_API_KEY"); ck=os.environ.get("COGNEE_API_KEY")
        p,participants=call(BAND+"/chats/"+ROOM+"/participants",bk,band=True)
        mentions=[]
        arr=participants.get("data",[]) if isinstance(participants,dict) else []
        for a in arr:
            if a.get("handle") in ("biobitworks/planner","biobitworks/tom","biobitworks/jerry"):
                mentions.append({"id":a["id"],"name":a.get("name",a["handle"]),"handle":a["handle"]})
        content=("SNEAK deterministic custody probe sha256="+address+
          " source commit="+sha+" REQ-AOK-M01..M30. Human API sends, not agent-owned handoff. "+
          "Snyk and Cognee receipt status independent. Please report source-addressed independent ACK, board transition, "+
          "and human decision only if actually completed.")
        sent,obj=call(BAND+"/chats/"+ROOM+"/messages",bk,
                       {"message":{"content":content,"mentions":mentions}},"POST",True)
        rec["band"]={"preflight":p,"sent":sent,"mention_participants":len(mentions),
                     "actor":"HUMAN_API","agent_participation":"NOT_OBSERVED"}
        if sent.get("status")=="HTTP_SUCCESS":
            body=obj.get("data",obj) if isinstance(obj,dict) else {}
            rec["band"]["message_id"]=body.get("id",body.get("message_id")) if isinstance(body,dict) else None
            r,m=call(BAND+"/chats/"+ROOM+"/messages?message_type=text",bk,band=True)
            rec["band"]["readback"]=r
            rec["band"]["exact_hash_found"]=find_exact_hash(m,address)
        mem=("SNEAK source-bounded memory pointer sha256="+address+" source git "+sha+
             "; acceptance status remains UNVERIFIED until independent actor readback, real board transition and Snyk scan. "+
             "No savings claimed. Preserve this text verbatim for digest retrieval.")
        add,body=call(COGNEE+"/api/v1/add_text",ck,{"textData":[mem],"datasetName":DATASET},"POST")
        rec["cognee"]={"add_text":add,"dataset":DATASET,"independent_agent_recall":"NOT_TESTED"}
        if add.get("status")=="HTTP_SUCCESS":
            rec["cognee"]["add_response_has_hash"]=find_exact_hash(body,address)
            cogn,co=call(COGNEE+"/api/v1/cognify",ck,{"datasets":[DATASET],"runInBackground":True},"POST")
            rec["cognee"]["cognify"]=cogn
            if isinstance(co,dict):
                rec["cognee"]["pipeline_run_id"]=co.get("pipeline_run_id",co.get("run_id"))
            search,sr=call(COGNEE+"/api/v1/search",ck,{"query":address,"searchType":"CHUNKS","datasets":[DATASET]},"POST")
            rec["cognee"]["search"]=search
            rec["cognee"]["exact_hash_found"]=find_exact_hash(sr,address)
            rec["cognee"]["indexing_completion"]="UNKNOWN"
        # Run scan against current source; Snyk failure remains a failure, not a pass.
        try:
            s=subprocess.run(["snyk","code","test","--json"],cwd=ROOT,timeout=90,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            scan={"exit_code":s.returncode,"stdout_sha256":digest(s.stdout),"stderr_sha256":digest(s.stderr)}
            try:
                obj=json.loads(s.stdout)
                scan["response_ok"]=obj.get("ok") if isinstance(obj,dict) else None
                scan["auth_error"]=bool("auth" in str(obj.get("error","")).lower()) if isinstance(obj,dict) else False
            except Exception:scan["response_ok"]=None
            scan["verdict"]="EXECUTED_WITH_FINDINGS_OR_ERROR" if s.returncode else "SCAN_EXECUTED"
        except Exception as e:scan={"verdict":"FAILED","error_type":type(e).__name__}
        rec["snyk"]={"scan":scan,"source_commit":sha,"evidence_sha256_in_scan_target":"NOT_VERIFIED",
                      "same_hash_in_provider_receipt":"NOT_VERIFIED","full_coverage":"NOT_VERIFIED"}
        rec["provider_e2e_verdict"]=("SUPPORTED_BAND_COGNEE_HASH_ONLY" if
          rec["band"].get("exact_hash_found") and rec["cognee"].get("exact_hash_found")
          else "FAILED_OR_PARTIAL")
    leaves=[{"service":n,"result":rec[n],"evidence_sha256":address} for n in ("band","cognee","snyk")]
    rec["local_attempt_merkle"]={"algorithm":"sha256-domain-separated-leaf-0x00-node-0x01-promote-odd",
                                 "leaves":3,"root":merkle_root(leaves),
                                 "scope":"LOCAL_ATTEMPT_RECEIPTS_ONLY_NOT_CANONICAL_GLOBAL_MMR"}
    rec["receipt_sha256"]=digest(enc(rec))
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_bytes(enc(rec)+b"\n")
    print(json.dumps({"evidence_sha256":address,"band":rec["band"],"cognee":rec["cognee"],
       "snyk":rec["snyk"],"e2e":rec["provider_e2e_verdict"],"local_attempt_merkle":rec["local_attempt_merkle"],
       "receipt_sha256":rec["receipt_sha256"]},sort_keys=True))
if __name__=="__main__":main()
