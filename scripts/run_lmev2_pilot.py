#!/usr/bin/env python3
"""Bounded LongMemEval-V2 diagnostic; NOT an official leaderboard run.

Gold answers remain outside model context. Only test outcome/hashed response
metadata is committed. Cognee/BAND calls are attempted only with credentials.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sneak.fcg_registry import FCGRegistry
from sneak.band_client import BandClient
from sneak.cognee_client import CogneeClient
from sneak.secrets import export_to_environ

DATA = Path("/tmp/sneak-lmev2-dataset/questions.jsonl")
METRICS = Path("/tmp/LongMemEval-V2/evaluation/qa_eval_metrics.py")
LEDGER = ROOT / "data/fcg/sneak-016-replay.jsonl"
RECEIPT = ROOT / "receipts/evaluations/LMEV2_20261020_PILOT.json"
MODELS = (
    "qwen3:1.7b",
    "hf.co/LiquidAI/LFM2.5-1.2B-Instruct-GGUF:latest",
)
SCORABLE = ("norm_phrase_set_match|", "norm_phrase_set_match_ordered|", "mc_choice_match|")
BENCHMARK_REVISION = "2cc8c540bdb87fe6761629b585e727e1c4704520"
DATASET_REVISION = "f152293e235517d504809563c833d7190b8c713b"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else canonical(value)).hexdigest()


def cases_for_diagnostic(path):
    """Deterministically select one text-only, rule-evaluable item per domain."""
    questions = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    chosen = {}
    for row in sorted(questions, key=lambda q: q["id"]):
        domain = row.get("domain")
        if domain not in ("enterprise", "web") or domain in chosen:
            continue
        if row.get("image") not in (None, "None", ""):
            continue
        if not str(row.get("eval_function", "")).startswith(SCORABLE):
            continue
        chosen[domain] = row
    if set(chosen) != {"enterprise", "web"}:
        raise RuntimeError("Expected one rule-evaluable, text-only question per domain")
    return [chosen["enterprise"], chosen["web"]]


def metric_function(path):
    spec = importlib.util.spec_from_file_location("lmev2_original_qa_eval_metrics", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Official evaluator not importable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.eval_from_spec


def ollama_tags():
    with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=8) as r:
        return r.read()


def generate(model, prompt):
    payload = {
        "model": model, "prompt": prompt, "stream": False, "think": False,
        "options": {"temperature": 0, "num_predict": 128},
    }
    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate", data=canonical(payload),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    start = time.perf_counter()
    with urllib.request.urlopen(request, timeout=180) as response:
        raw = response.read()
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    result = json.loads(raw)
    if "error" in result:
        raise RuntimeError(str(result["error"])[:220])
    return result, duration_ms, digest(raw)


def main():
    if not DATA.is_file() or not METRICS.is_file():
        raise SystemExit("NOT_TESTED: pinned LongMemEval-V2 source files missing")
    questions_sha = digest(DATA.read_bytes())
    metric_sha = digest(METRICS.read_bytes())
    score = metric_function(METRICS)
    questions = cases_for_diagnostic(DATA)
    registry = FCGRegistry(LEDGER)
    predecessor = registry.verify()
    tags = ollama_tags()
    tag_digest = digest(tags)
    names = {m["name"] for m in json.loads(tags)["models"]}
    export_to_environ()
    band = BandClient()
    cognee = CogneeClient(dataset="sneak_lmev2_evaluations")
    context = {
        "benchmark": "LongMemEval-V2",
        "benchmark_code_revision": BENCHMARK_REVISION,
        "dataset_revision": DATASET_REVISION,
        "tier": "small_question_subset_NO_TRAJECTORIES",
        "procedure": "B0_NO_RETRIEVAL_FIXED_QUESTION_SET",
        "official_benchmark_score": "NOT_COMPUTED",
        "dataset_sha256": questions_sha,
    }
    actor = registry.append(
        kind="actor", state="OBSERVED", source_sha256=tag_digest,
        payload={"handle": "local-magicPRObox-evaluation-runner"},
        context=context,
    )
    source = registry.append(
        kind="source", actor_fco=actor["fco_id"], parent_fco=actor["fco_id"],
        state="OBSERVED", source_sha256=questions_sha,
        payload={"question_ids": [x["id"] for x in questions], "questions_sha256": questions_sha,
                 "eval_functions_sha256": metric_sha, "gold_excluded_from_prompt": True},
        context=context,
    )
    results = []
    for model in MODELS:
        model_event = registry.append(
            kind="model", actor_fco=actor["fco_id"], parent_fco=source["fco_id"],
            state="OBSERVED" if model in names else "NOT_TESTED",
            source_sha256=tag_digest if model in names else "UNKNOWN",
            payload={"model": model, "available_in_ollama": model in names}, context=context,
        )
        agent = registry.append(
            kind="agent", actor_fco=actor["fco_id"], model_fco=model_event["fco_id"],
            parent_fco=model_event["fco_id"], state="OBSERVED" if model in names else "NOT_TESTED",
            source_sha256=tag_digest if model in names else "UNKNOWN",
            payload={"handle": "sneak/local-ollama-runner", "model": model}, context=context,
        )
        model_rows = []
        for item in questions:
            row = {"question_id": item["id"], "domain": item["domain"],
                   "question_type": item.get("question_type"), "score_status": "NOT_COMPUTED",
                   "correct": None, "latency_ms": None, "response_sha256": None}
            if model in names:
                try:
                    response, latency, raw_sha = generate(model, item["question"])
                    answer = response.get("response", "")
                    row.update({"score_status": "OBSERVED",
                                "correct": bool(score(item["eval_function"], answer, item["answer"])),
                                "latency_ms": latency, "response_sha256": raw_sha,
                                "output_tokens": response.get("eval_count"),
                                "input_tokens": response.get("prompt_eval_count")})
                except Exception as exc:
                    row.update({"score_status": "FAILED", "error_type": type(exc).__name__})
            registry.append(
                kind="value", actor_fco=actor["fco_id"], model_fco=model_event["fco_id"],
                parent_fco=agent["fco_id"], state=row["score_status"],
                source_sha256=row["response_sha256"] or "UNKNOWN",
                payload=row, context=context,
            )
            model_rows.append(row)
        scored = [r for r in model_rows if r["score_status"] == "OBSERVED"]
        accuracy = sum(bool(r["correct"]) for r in scored) / len(scored) if len(scored) == len(questions) else None
        summary = {"model": model, "questions_attempted": len(questions),
                   "questions_scored": len(scored), "diagnostic_accuracy": accuracy,
                   "evaluation_type": "UNOFFICIAL_2_QUESTION_NO_RETRIEVAL",
                   "score_status": "OBSERVED" if accuracy is not None else "NULL"}
        score_event = registry.append(
            kind="score", actor_fco=actor["fco_id"], model_fco=model_event["fco_id"],
            parent_fco=agent["fco_id"], state=summary["score_status"],
            source_sha256=digest(model_rows) if scored else "UNKNOWN",
            payload=summary, context=context,
        )
        packet = {"schema": "sneak.lmev2.pilot-handoff.v1", "model": model,
                  "diagnostic_accuracy": accuracy, "questions_scored": len(scored),
                  "score_fco": score_event["fco_id"], "official_score": "NOT_COMPUTED"}
        packet_sha = digest(packet)
        if cognee.available:
            try:
                write = cognee.add_text([json.dumps({"packet_sha256": packet_sha, **packet}, sort_keys=True)])
                cognify = cognee.cognify() if write["ok"] else {"ok": False}
                cognee_result = "OBSERVED" if write["ok"] and cognify["ok"] else "FAILED"
            except Exception:
                cognee_result = "FAILED"
        else:
            cognee_result = "NOT_TESTED"
        registry.append(
            kind="memory", actor_fco=actor["fco_id"], parent_fco=score_event["fco_id"],
            state=cognee_result, source_sha256=packet_sha if cognee_result == "OBSERVED" else "UNKNOWN",
            payload={"dataset": cognee.dataset, "packet_sha256": packet_sha, "outcome": cognee_result},
            context=context,
        )
        if band.available:
            try:
                text = (f"SNEAK LongMemEval-V2 unofficial pilot | {model} | "
                        f"scored {len(scored)}/2 | result={accuracy} | packet_sha256={packet_sha}. "
                        "Tom and Jerry: independently review; benchmark tier score NOT_COMPUTED.")
                posted = band.send_mention(text, ["claude", "chatgpt"])
                band_result = "OBSERVED" if posted.get("ok") else "FAILED"
                band_id = (posted.get("message") or {}).get("id")
            except Exception:
                band_result, band_id = "FAILED", None
        else:
            band_result, band_id = "NOT_TESTED", None
        registry.append(
            kind="handoff", actor_fco=actor["fco_id"], parent_fco=score_event["fco_id"],
            state=band_result, source_sha256=packet_sha if band_result == "OBSERVED" else "UNKNOWN",
            payload={"packet_sha256": packet_sha, "band_message_id": band_id,
                     "outcome": band_result, "agents_acknowledged": "NOT_OBSERVED"},
            context=context,
        )
        results.append({**summary, "question_results": model_rows,
                        "packet_sha256": packet_sha, "cognee": cognee_result, "band": band_result})
    verified = registry.verify()
    receipt = {"schema": "sneak.lmev2.pilot-receipt.v1", "parent_mmr": predecessor,
               "successor_mmr": verified, "benchmark_revision": BENCHMARK_REVISION,
               "dataset_revision": DATASET_REVISION, "questions_sha256": questions_sha,
               "official_full_benchmark": "NOT_TESTED",
               "results": results, "security_admission": "DENY"}
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"parent": predecessor, "successor": verified,
                      "results": results, "receipt_sha256": digest(RECEIPT.read_bytes())}, sort_keys=True))


if __name__ == "__main__":
    main()
