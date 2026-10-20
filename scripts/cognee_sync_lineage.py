#!/usr/bin/env python3
"""Write and recall an allowlisted *hashed summary* of SNEAK history via genuine Cognee OSS.

This is a bounded local agent-memory test. It is NOT a full chat exporter, BAND send,
Cognee Cloud connection, or validation of unobserved agent identities.
"""
from __future__ import annotations
import argparse, asyncio, hashlib, json, pathlib

from apps.sneak_mvp.cognee_adapter import remember, recall
from scripts import sneak_conversation_ledger as L

ROOT=pathlib.Path(__file__).resolve().parents[1]
FILE=ROOT/"deploy/vercel-preview/data/conversation-lineage.json"
MEMORY_SESSION="SNEAK-CONV-20261020-MMR"
DATASET="sneak_conversation_lineage"

def payload():
    snap=L.compile_source()
    actors=sorted((x["actor"],x["mmr"]["root"],x["event_count"]) for x in snap["actor_mmr"].values())
    record={"schema":"sneak.cognee-memory-pointer.v1",
            "session":MEMORY_SESSION,
            "root_question_sha256":snap["question"]["question_sha256"],
            "root_question_mmr":snap["question_mmr"]["root"],
            "global_conversation_mmr":snap["global_mmr"]["root"],
            "captured_historical_messages":snap["source"]["message_count"],
            "actor_roots":actors,
            "model_mmr":"NOT_COMPUTED_MISSING_MODEL_VERSION",
            "quality_delta":"NOT_COMPUTED",
            "source_merkle":snap["source"]["event_merkle_root"],
            "candidate_instruction":"Never complete SNEAK work until BAND handoff and Snyk scan have exact receipts; compare root-question verdict UNKNOWN until corroborated."}
    return L.enc(record).decode("ascii")

async def write():
    text=payload()
    r=await remember(text,DATASET,MEMORY_SESSION,allow_llm=True)
    return {"op":"write","dataset":DATASET,"session":MEMORY_SESSION,"status":r["status"],
            "memory_payload_sha256":hashlib.sha256(text.encode()).hexdigest(),
            "cognee_result_type":r.get("result_type"),
            "error":r.get("error"),"cognee_result_receipt_sha256":L.digest(r)}

async def read():
    phrase="SNEAK-CONV-20261020-MMR root question MMR security gate scans and Cognee memory"
    r=await recall(phrase,DATASET,MEMORY_SESSION,allow_llm=True)
    strings=[str(s) for s in r.get("results",[])]
    marker=any("SNEAK-CONV-20261020-MMR" in s for s in strings)
    root=L.compile_source()["question_mmr"]["root"]
    root_found=any(root in s for s in strings)
    # No success inferred from a result count alone.
    return {"op":"read","dataset":DATASET,"session":MEMORY_SESSION,
            "status":r["status"],
            "recall_receipt_sha256":L.digest(r),
            "retrieved_entries":r.get("result_count",0),
            "expected_session_marker_found":marker,
            "expected_root_found":root_found,
            "decisive_action":"REQUEST_BAND_HANDOFF_AND_SNYK_PROOFS" if root_found else "ABSTAIN_MEMORY_PROOF",
            "cross_process_read":"EXECUTED" if r["status"]=="EXECUTED" else "ERROR",
            "error":r.get("error")}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("phase",choices=("write","read"))
    a=ap.parse_args()
    result=asyncio.run(write() if a.phase=="write" else read())
    print(json.dumps(result,sort_keys=True))
    raise SystemExit(0 if result["status"]=="EXECUTED" else 2)

if __name__=="__main__":main()
