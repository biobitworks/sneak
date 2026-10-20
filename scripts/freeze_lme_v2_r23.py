#!/usr/bin/env python3
"""Freeze an LME-V2 text-only six-question pilot selection BEFORE model inference.

The official LME-V2 leaderboard is larger; this manifest is a smoke subset.
Data remains local-runs (uncommitted) and no reference answers enter prompts.
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "local-runs/LongMemEval-V2/data/longmemeval-v2"
OUT = ROOT / "data/evaluations/lme_v2_r23_frozen.json"
SEED = "SNEAK-LME-V2-FROZEN-R23-20261020"
CATEGORIES = ("static-environment", "dynamic-environment", "procedure")
ALLOWED = {"norm_phrase_set_match", "norm_phrase_set_match_ordered", "mc_choice_match"}
SOURCE_COMMIT = "2cc8c540bdb87fe6761629b585e727e1c4704520"
DATA_REVISION = "f152293e235517d504809563c833d7190b8c713b"

def main():
    questions = [json.loads(s) for s in (DATA / "questions.jsonl").read_text().splitlines() if s]
    h = json.loads((DATA / "haystacks/lme_v2_small.json").read_text())
    ids = []
    for domain in ("enterprise", "web"):
        for category in CATEGORIES:
            eligible = [q for q in questions if q["domain"] == domain
                        and q["question_type"] == category and q["image"] is None
                        and q["eval_function"].split("|",1)[0] in ALLOWED
                        and q["id"] in h]
            ordered = sorted(eligible, key=lambda q: hashlib.sha256((SEED + ":" + q["id"]).encode()).hexdigest())
            if not ordered:
                raise ValueError("empty frozen stratum")
            ids.append(ordered[0]["id"])
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    frozen = {
        "schema": "sneak.longmemeval-v2.text-pilot.freeze.v1",
        "state": "FROZEN_BEFORE_INFERENCE",
        "seed": SEED, "selection": "minimum SHA256(seed + ':' + question_id) per domain x question_type",
        "question_ids": ids,
        "count": len(ids),
        "source_repo": "https://github.com/xiaowu0162/LongMemEval-V2",
        "source_repo_commit": SOURCE_COMMIT,
        "dataset": "xiaowu0162/longmemeval-v2", "dataset_revision": DATA_REVISION,
        "data_sha256": {
            "questions.jsonl": digest(DATA/"questions.jsonl"),
            "haystacks/lme_v2_small.json": digest(DATA/"haystacks/lme_v2_small.json"),
            "trajectories.jsonl": digest(DATA/"trajectories.jsonl"),
        },
        "models": ["qwen2.5:0.5b", "hf.co/LiquidAI/LFM2.5-1.2B-Instruct-GGUF:latest"],
        "agent_variants": ["no_memory", "trajectory_lexical_top3"],
        "reader": {"temperature": 0, "seed": 0, "max_new_tokens": 96},
        "scoring": "Upstream evaluation.qa_eval_metrics.eval_from_spec; deterministic graders only",
        "restrictions": ["no screenshot cases", "no LLM-judge cases",
                         "not official harness end-to-end", "no LAFS leaderboard claim",
                         "no use of gold answers or hidden task metadata in retrieval"],
        "question_count_per_variant": 6
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    if OUT.exists():
        if json.loads(OUT.read_text()) != frozen:
            raise RuntimeError("frozen manifest would change; create a successor")
    else:
        OUT.write_text(json.dumps(frozen,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"ids":ids,"sha256":digest(OUT),"dataset_trajectory_size":(DATA/"trajectories.jsonl").stat().st_size},indent=2))

if __name__ == "__main__":
    main()
