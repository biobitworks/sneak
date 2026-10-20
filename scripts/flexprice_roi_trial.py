#!/usr/bin/env python3
"""Deterministic simulated ROI + Flexprice-compatible events.

No backend delivery occurs unless --send is supplied. A local mock is not a
live Flexprice billing receipt. All source rows here are simulated.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/demo/roi_trial_fixture.json"
DEFAULT_OUT = ROOT / "receipts/flexprice/SNEAK_FLEXPRICE_ROI_SIMULATED_20261020.json"

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")

def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def measure(source):
    if source.get("evidence_class") != "SIMULATED_NOT_OBSERVED":
        raise ValueError("trial only accepts explicitly simulated input")
    rows = source["rows"]
    if not rows:
        raise ValueError("no rows")
    rate = Decimal(source["token_rate_usd_per_million_assumed"])
    human_rate = Decimal(source["human_rate_usd_per_hour_assumed"])
    by_scenario = {}
    events = []
    unique = set()
    tasks = {"baseline": set(), "sneak": set()}
    for row in rows:
        scenario = row["scenario"]
        if scenario not in ("baseline", "sneak"):
            raise ValueError("invalid scenario")
        if any(int(row[k]) < 0 for k in ("prompt_tokens", "completion_tokens")):
            raise ValueError("negative tokens")
        if Decimal(row["human_minutes"]) < 0:
            raise ValueError("negative human time")
        identity = {k: row[k] for k in ("scenario", "task_id", "agent_id", "model_id", "human_id")}
        if digest(identity) in unique:
            raise ValueError("duplicate source identity")
        unique.add(digest(identity))
        tasks[scenario].add(row["task_id"])
        tokens = int(row["prompt_tokens"]) + int(row["completion_tokens"])
        token_cost = Decimal(tokens) * rate / Decimal(1_000_000)
        human_cost = Decimal(row["human_minutes"]) * human_rate / Decimal(60)
        bucket = by_scenario.setdefault(scenario, {"tokens":0, "human_minutes":Decimal(0), "token_usd":Decimal(0), "human_usd":Decimal(0), "agents":{}, "models":{}, "humans":{}})
        bucket["tokens"] += tokens
        bucket["human_minutes"] += Decimal(row["human_minutes"])
        bucket["token_usd"] += token_cost
        bucket["human_usd"] += human_cost
        for dim, key in (("agents", "agent_id"), ("models", "model_id"), ("humans", "human_id")):
            entry = bucket[dim].setdefault(row[key], {"tokens":0,"human_minutes":Decimal(0),"estimated_total_usd":Decimal(0)})
            entry["tokens"] += tokens
            entry["human_minutes"] += Decimal(row["human_minutes"])
            entry["estimated_total_usd"] += token_cost + human_cost
        event_identity = {"schema":"sneak.flexprice.event.v1","source_identity":identity,"source_sha256":digest(row)}
        eid = digest(event_identity)
        events.append({
            "event_id": eid,
            "event_name":"sneak_agent_token_usage",
            "external_customer_id":"sneak-demo-not-a-real-customer",
            "source":"sneak-simulated-roi-trial",
            "properties":{
                "tokens":str(tokens),
                "prompt_tokens":str(row["prompt_tokens"]),
                "completion_tokens":str(row["completion_tokens"]),
                "agent_id":row["agent_id"],
                "model_id":row["model_id"],
                "human_id":row["human_id"],
                "task_id":row["task_id"],
                "scenario":scenario,
                "evidence_class":"SIMULATED_NOT_OBSERVED",
                "input_sha256":digest(row)
            }
        })
    if tasks["baseline"] != tasks["sneak"] or tasks["baseline"] != set(source["matched_task_ids"]):
        raise ValueError("noncomparable tasks between scenarios")
    def formatted(v):
        if isinstance(v, Decimal):
            return str(v.quantize(Decimal("0.000001")))
        if isinstance(v, dict):
            return {k: formatted(x) for k,x in v.items()}
        return v
    for b in by_scenario.values():
        b["total_usd"] = b["token_usd"] + b["human_usd"]
        b["cost_per_task_usd"] = b["total_usd"] / Decimal(len(tasks["baseline"]))
    base, improved = by_scenario["baseline"], by_scenario["sneak"]
    token_reduction = (Decimal(base["tokens"])-Decimal(improved["tokens"]))/Decimal(base["tokens"])
    cost_reduction = (base["total_usd"]-improved["total_usd"])/base["total_usd"]
    summary = {
        "schema":"sneak.flexprice.roi.trial.v1",
        "status":"SIMULATED_NOT_OBSERVED",
        "live_flexprice_metering":"NOT_TESTED",
        "billing_receipt":"NULL",
        "claim_not_supported":"REAL_WORLD_ROI",
        "fixture_sha256":hashlib.sha256(canonical(source)).hexdigest(),
        "task_count":len(tasks["baseline"]),
        "token_reduction_fraction":str(token_reduction.quantize(Decimal("0.000001"))),
        "estimated_cost_reduction_fraction":str(cost_reduction.quantize(Decimal("0.000001"))),
        "pricing":"ASSUMED_NOT_PROVIDER_PRICING",
        "metrics":formatted(by_scenario),
        "events":events,
        "global_merkle_root":"NOT_COMPUTED",
        "model_mmr_root":"NOT_COMPUTED",
        "anticube":"NOT_COMPUTED",
        "delta_g_star":"NOT_COMPUTED",
    }
    summary["receipt_sha256"] = digest(summary)
    return summary

def send_events(events, endpoint, api_key):
    parsed = urlsplit(endpoint)
    if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in ("localhost","127.0.0.1")):
        raise ValueError("endpoint must use HTTPS except for loopback tests")
    if not api_key:
        raise ValueError("FLEXPRICE_API_KEY is required for live send")
    result = []
    for event in events:
        request = Request(endpoint.rstrip("/") + "/events", data=canonical(event),
                          headers={"Content-Type":"application/json","x-api-key":api_key},
                          method="POST")
        with urlopen(request, timeout=12) as response:
            if response.status != 202:
                raise RuntimeError("expected Flexprice 202 accepted")
            result.append({"event_id":event["event_id"],"http_status":response.status})
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--send",action="store_true",help="explicitly send to Flexprice or local mock")
    parser.add_argument("--endpoint",default=os.environ.get("FLEXPRICE_API_HOST","https://us.api.flexprice.io/v1"))
    parser.add_argument("--out",type=Path,default=DEFAULT_OUT)
    args=parser.parse_args()
    source=json.loads(FIXTURE.read_text())
    report=measure(source)
    if args.send:
        if report["status"] == "SIMULATED_NOT_OBSERVED" and not urlsplit(args.endpoint).hostname in ("localhost","127.0.0.1"):
            raise ValueError("refuse billing simulated fixtures to a real Flexprice endpoint")
        report["local_mock_acknowledgments"] = send_events(report["events"], args.endpoint, os.getenv("FLEXPRICE_API_KEY", ""))
        report["live_flexprice_metering"] = "NOT_TESTED"
        report["receipt_sha256"] = digest({k:v for k,v in report.items() if k != "receipt_sha256"})
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes(canonical(report)+b"\n")
    print(json.dumps({"status":report["status"],"tokens_before":report["metrics"]["baseline"]["tokens"],"tokens_after":report["metrics"]["sneak"]["tokens"],"token_reduction_fraction":report["token_reduction_fraction"],"live_flexprice_metering":report["live_flexprice_metering"],"receipt_sha256":report["receipt_sha256"]},sort_keys=True))

if __name__ == "__main__":
    main()
