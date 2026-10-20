#!/usr/bin/env python3
"""Deterministic privacy-preserving SNEAK conversation lineage compiler.

Only imports explicitly allowlisted historical BAND receipts or an operator-supplied,
schema-validated event file. Hashes message bytes, never writes conversation text.
Input custody + deterministic script hash + FCO + output custody -> MMR streams.
Prior captured human/model identities must not be guessed from agent nicknames.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import sys
from collections import defaultdict

from scripts import mmr_reference as R

REPO=pathlib.Path(__file__).resolve().parents[1]
DEFAULT_SOURCE=REPO/"receipts/band/SNEAK-013_HANDOFF.json"
DEFAULT_OUT=REPO/"deploy/vercel-preview/data/conversation-lineage.json"
ROOT_QUESTION="Does every authorized SNEAK agent conversation produce evidence-bound FCO transitions with deterministic inputs and outputs, per-actor and per-model MMR histories, BAND handoffs, and verifiable Cognee recall?"
SCHEMA="sneak.conversation-lineage.v1"
SUPPORTED={"TRUE","FALSE","UNKNOWN"}
MAX_EVENTS=10000

def enc(o):
    return json.dumps(o,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("ascii")
def sha(b):
    return hashlib.sha256(b).hexdigest()
def digest(o):
    return sha(enc(o))
def mmr_of(items):
    if not items: return {"root":"NOT_COMPUTED","leaves":0,"nodes":0,"peaks":[]}
    m=R.MMR()
    for x in items: m.append(enc(x))
    return {"root":m.root().hex(),"leaves":len(items),"nodes":m.size,
            "peaks":[{"position":p,"sha256":h.hex()} for p,h in zip(R.peaks(m.size),m.peak_hashes())]}
def _receipt_events(path):
    """Validate recorded SNEAK-013 event Merkle root BEFORE ingesting its nested messages."""
    raw=path.read_bytes()
    source=json.loads(raw)
    if source.get("schema")!="sneak.band-event-merkle.v1":
        raise ValueError("source is not an explicitly recognized BAND receipt")
    leaves=source.get("leaves",[])
    if not 1<=len(leaves)<=MAX_EVENTS: raise ValueError("invalid source event count")
    verified=[]
    for leaf in leaves:
        e=leaf.get("event")
        if not isinstance(e,dict):raise ValueError("missing event")
        canonical=enc(e)
        if bytes.fromhex(leaf["canonical_hex"])!=canonical:
            raise ValueError("source canonical event mismatch")
        h=R.H(b"\x00"+canonical)
        if h.hex()!=leaf["leaf"]:raise ValueError("source leaf mismatch")
        verified.append(h)
    if R.merkle_root(verified).hex()!=source.get("root"):
        raise ValueError("source Merkle root mismatch")
    records={}
    for leaf in leaves:
        event=leaf["event"]; payload=event.get("payload",{})
        if not isinstance(payload,dict): continue
        by_id={p["id"]:p["name"] for p in payload.get("participants",[])
               if isinstance(p,dict) and isinstance(p.get("id"),str) and isinstance(p.get("name"),str)}
        room_id=payload.get("room_id")
        for msg in payload.get("messages",[]):
            if not isinstance(msg,dict):continue
            identifier=msg.get("id")
            text=msg.get("content")
            timestamp=msg.get("inserted_at")
            if not all(isinstance(s,str) and s.strip() for s in (identifier,text,timestamp)):
                raise ValueError("incomplete captured BAND message")
            data={"origin":"BAND_HISTORICAL_RECEIPT","source_event_id":event["id"],
                  "external_message_sha256":sha(identifier.encode()),
                  "room_sha256":sha(room_id.encode()) if isinstance(room_id,str) else "UNKNOWN",
                  "actor":by_id.get(msg.get("sender_id"),"UNKNOWN_ACTOR"),
                  "actor_identity_sha256":sha(msg["sender_id"].encode()) if isinstance(msg.get("sender_id"),str) else "UNKNOWN",
                  "model_id":None, "model_version":None,
                  "observed_at":timestamp,
                  "text_sha256":sha(text.encode("utf-8")),
                  "text_byte_count":len(text.encode("utf-8")),
                  "semantic_verdict":"UNKNOWN",
                  "task_status":"OBSERVED_CAPTURED",
                  "cognee_write":"NOT_TESTED",
                  "cognee_recall":"NOT_TESTED",
                  "band_delivery":"HISTORICAL_CAPTURED"}
            if identifier in records:
                if records[identifier]!=data:raise ValueError("conflicting duplicate BAND message")
                continue
            records[identifier]=data
    return {"source_sha256":sha(raw),"source_root":source["root"],
            "source_event_count":len(leaves),
            "messages":sorted(records.values(),key=lambda e:(e["observed_at"],e["external_message_sha256"]))}

def compile_source(source_path=DEFAULT_SOURCE):
    source_path=pathlib.Path(source_path).resolve()
    if not source_path.is_file():raise FileNotFoundError(source_path)
    result=_receipt_events(source_path)
    script_hash=sha(pathlib.Path(__file__).read_bytes())
    root_input={"schema":"sneak.root-question.v1","question_sha256":sha(ROOT_QUESTION.encode("utf-8")),
                "scope":"authorized_conversations_only","question_version":"1",
                "question_text_public":ROOT_QUESTION}
    root_id="FCO-QUESTION-"+digest(root_input)[:24]
    predecessor="GENESIS"; actor_prev={}; model_prev={}
    stream=[]; question_chain=[]
    root_fco={"id":root_id,"kind":"ROOT_QUESTION","payload_sha256":digest(root_input),
              "script_sha256":script_hash,"parent_fco_id":None,"verdict":"UNKNOWN",
              "observed_at":None}
    question_chain.append(root_fco)
    for index,item in enumerate(result["messages"]):
        # Explicit transformations are stable and bound to source+script identity.
        inp={"schema":"sneak.input.v1","message_sha256":item["text_sha256"],
             "source_receipt_sha256":result["source_sha256"],
             "origin_message_sha256":item["external_message_sha256"]}
        steps=[{"step":0,"operation":"validate_source_merkle",
                "script_sha256":script_hash,"input_sha256":digest(inp),
                "outcome":"PASS"},
               {"step":1,"operation":"hash_message_and_link_fco",
                "script_sha256":script_hash,"input_sha256":item["text_sha256"],
                "outcome":"PASS"}]
        actor_key=item["actor_identity_sha256"]
        model_key=(item["model_id"],item["model_version"]) if item["model_id"] and item["model_version"] else None
        body={"schema":"sneak.conversation-fco.v1","root_question_fco":root_id,
              "index":index,"actor":item["actor"],
              "actor_identity_sha256":actor_key,
              "model_id":item["model_id"],"model_version":item["model_version"],
              "source_message_sha256":item["external_message_sha256"],
              "observed_at":item["observed_at"],"input_sha256":digest(inp),
              "text_sha256":item["text_sha256"],"steps":steps,
              "parent_global_fco":predecessor,
              "parent_actor_fco":actor_prev.get(actor_key),
              "parent_model_fco":model_prev.get(model_key) if model_key else None,
              "semantic_verdict":item["semantic_verdict"],
              "captured_status":item["task_status"],
              "cognee_write":item["cognee_write"],"cognee_recall":item["cognee_recall"]}
        # H(0x00 || canonical body) identifies the FCO, not truth of its content.
        fco_id="FCO-MSG-"+R.H(b"\x00"+enc(body)).hex()[:24]
        output={"schema":"sneak.output.v1","fco_id":fco_id,
                "input_sha256":digest(inp),"transform_script_sha256":script_hash,
                "result":"CAPTURE_INTEGRITY_VERIFIED","verdict":"UNKNOWN"}
        fco={**body,"id":fco_id,"output_sha256":digest(output),
             "source_origin":item["origin"],"source_event_id":item["source_event_id"],
             "room_sha256":item["room_sha256"],
             "source_receipt_sha256":result["source_sha256"],
             "history_integrity":True, "claim_true":None}
        stream.append(fco)
        question_chain.append(fco)
        predecessor=fco_id
        actor_prev[actor_key]=fco_id
        if model_key: model_prev[model_key]=fco_id
    breakpoints=[]
    for step in range(1,len(stream)+1):
        prefix=stream[:step]
        question_prefix=[root_fco]+prefix
        current=prefix[-1]
        actor_prefix=[x for x in prefix if x["actor_identity_sha256"]==current["actor_identity_sha256"]]
        actor_key=current["actor_identity_sha256"]
        exact_model=(current["model_id"],current["model_version"])
        same_model=[x for x in prefix if x["model_id"] and x["model_version"]
                    and (x["model_id"],x["model_version"])==exact_model]
        leaves=[R.H(b"\x00"+enc(x)) for x in question_prefix]
        bp={
            "id":f"BP-CONVERSATION-{step:04d}-{current['id'][-12:]}",
            "parent_breakpoint":breakpoints[-1]["id"] if breakpoints else root_id,
            "event_fco_id":current["id"],
            "event_ordinal":step,
            "question_merkle_tree_root":R.merkle_root(leaves).hex(),
            "question_mmr":mmr_of(question_prefix),
            "global_mmr":mmr_of(prefix),
            "actor":current["actor"],
            "actor_identity_sha256":actor_key,
            "actor_mmr":mmr_of(actor_prefix),
            "model_id":current["model_id"],
            "model_version":current["model_version"],
            "model_mmr":mmr_of(same_model),
            "input_sha256":current["input_sha256"],
            "script_sha256":current["steps"][0]["script_sha256"],
            "output_sha256":current["output_sha256"],
            "source_merkle_verified":True,
            "custody_replay_bool":True,
            "root_question_true_false":None,
            "semantic_verdict":"UNKNOWN",
            "quality_delta":"NOT_COMPUTED",
            "cognee_write":"NOT_TESTED",
            "band_live_delivery":"NOT_TESTED_AUTH_BLOCKED",
        }
        breakpoints.append(bp)
    per_actor={}
    for a in sorted({x["actor_identity_sha256"] for x in stream}):
        vals=[x for x in stream if x["actor_identity_sha256"]==a]
        per_actor[a]={"actor":vals[0]["actor"],"mmr":mmr_of(vals),
                       "event_count":len(vals),"true_count":0,"false_count":0,
                       "unknown_count":len(vals),"quality_delta":"NOT_COMPUTED",
                       "claim_vs_question":"UNKNOWN"}
    per_model={}
    for key in sorted({(x["model_id"],x["model_version"]) for x in stream if x["model_id"] and x["model_version"]}):
        values=[x for x in stream if (x["model_id"],x["model_version"])==key]
        per_model[key[0]+"/"+key[1]]={"model_id":key[0],"model_version":key[1],
                                     "mmr":mmr_of(values),"verdict":"UNKNOWN",
                                     "evaluation_delta":"NOT_COMPUTED"}
    if not stream: raise ValueError("no authentic captured messages: do not invent history")
    return {"schema":SCHEMA,"question":{"id":root_id,
             "question_sha256":root_input["question_sha256"],"verdict":"UNKNOWN",
             "question_record":root_fco, "description":ROOT_QUESTION},
            "source":{"kind":"HISTORICAL_BAND_RECEIPT","source_sha256":result["source_sha256"],
                "event_merkle_root":result["source_root"],
                "event_count":result["source_event_count"],"message_count":len(stream),
                "scope":"one captured authorized room; not all BAND or ChatGPT conversations",
                "source_file":"receipts/band/SNEAK-013_HANDOFF.json"},
            "script_sha256":script_hash,
            "question_mmr":mmr_of(question_chain),
            "global_mmr":mmr_of(stream),
            "actor_mmr":per_actor,
            "model_mmr":per_model,
            "missing_model_identity":sum(1 for x in stream if x["model_id"] is None),
            "events":stream,
            "breakpoints":breakpoints,
            "breakpoint_count":len(breakpoints),
            "question_approval":"PROPOSED_USER_INTENT_NOT_FORMALLY_RATIFIED",
            "history_linkage":"VERIFIED",
            "quality_delta":"NOT_COMPUTED",
            "live_band_sync":"NOT_TESTED_AUTH_BLOCKED",
            "cognee_graph_commit":"NOT_EXECUTED",
            "web_export":"HASH_ONLY_NO_RAW_MESSAGES",
            "all_conversations_imported":False,
            "rights_scope":"AUTHORIZED_SOURCE_ONLY",
            "signed":False}

def write_snapshot(source=DEFAULT_SOURCE,out=DEFAULT_OUT):
    data=compile_source(source)
    out=pathlib.Path(out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_bytes(enc(data)+b"\n")
    return {"output_path":str(out),"output_sha256":sha(out.read_bytes()),
            "global_root":data["global_mmr"]["root"],
            "question_root":data["question_mmr"]["root"],
            "models":len(data["model_mmr"]),"agents":len(data["actor_mmr"]),
            "events":len(data["events"]),
            "live_band":data["live_band_sync"]}

def verify(source=DEFAULT_SOURCE,out=DEFAULT_OUT):
    expected=enc(compile_source(source))+b"\n"
    actual=pathlib.Path(out).read_bytes()
    if expected!=actual:raise ValueError("snapshot byte mismatch")
    return {"status":"PASS","snapshot_sha256":sha(actual),"bytes":len(actual)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("op",choices=("build","verify"))
    p.add_argument("--source",type=pathlib.Path,default=DEFAULT_SOURCE)
    p.add_argument("--out",type=pathlib.Path,default=DEFAULT_OUT)
    a=p.parse_args()
    obj=write_snapshot(a.source,a.out) if a.op=="build" else verify(a.source,a.out)
    print(json.dumps(obj,sort_keys=True))

if __name__=="__main__":main()
