#!/usr/bin/env python3
"""Run local Ollama models against one root question and record every step as a breakpoint.

Rounds (the 'over time' axis):
  1  question only, no context            -> what the model knows on its own
  2  question + committed source context  -> effect of the input
  3  exact replay of round 2              -> determinism check (output hash should repeat)

Steps per round, each a deterministic script step with hashed input and output:
  build_prompt -> model_call (temperature 0, seed 42; tokens recorded) -> normalize_answer

Root question (placeholder until the planner sets the real one):
  "How many mandatory requirement atoms does Sneak have?"  answer rule: \\b30\\b
  context: START_HERE_SNEAK.md bytes at a fixed commit.
"""
import argparse, hashlib, json, re, subprocess, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from breakpoint_ledger import Ledger, sha, canon  # noqa: E402

SCRIPT_SHA = sha(Path(__file__).read_bytes())
QUESTION = "How many mandatory requirement atoms does Sneak have? Answer with a single number."
ANSWER_REGEX = r"\b30\b"
CONTEXT_PATH = "START_HERE_SNEAK.md"
CONTEXT_COMMIT = "979a4f7af5821e197a71eb960ca2ff2722f2e0e3"
OPTIONS = {"temperature": 0, "seed": 42, "num_predict": 48, "num_ctx": 4096}


def ollama(model, prompt, url):
    body = json.dumps({"model": model, "prompt": prompt, "stream": False, "options": OPTIONS}).encode()
    req = urllib.request.Request(f"{url}/api/generate", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.load(r)
    return d["response"], {"prompt_tokens": d.get("prompt_eval_count", 0), "completion_tokens": d.get("eval_count", 0),
                           "total_tokens": d.get("prompt_eval_count", 0) + d.get("eval_count", 0),
                           "duration_ms": round(d.get("total_duration", 0) / 1e6)}


def model_digest(model, url):
    with urllib.request.urlopen(f"{url}/api/tags", timeout=30) as r:
        for m in json.load(r)["models"]:
            if m["name"] == model or m["name"] == model + ":latest":
                return m["digest"]
    raise SystemExit(f"model {model} not installed")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=["qwen2.5:1.5b", "qwen2.5:0.5b",
                                                    "lfm2-1.2b-longevity-q4km:latest", "longhorizon-liquid-230m:latest"])
    ap.add_argument("--ollama", default="http://localhost:11434")
    ap.add_argument("--parent", help="breakpoint this run hangs from (e.g. the planner's request)")
    a = ap.parse_args()

    context = subprocess.check_output(["git", "-C", str(ROOT), "show", f"{CONTEXT_COMMIT}:{CONTEXT_PATH}"]).decode("utf-8")
    L = Ledger()
    rq = L.root_question(QUESTION, ANSWER_REGEX, sha(context.encode("utf-8")), a.parent,
                         label=f"{CONTEXT_PATH}@{CONTEXT_COMMIT[:12]}")
    root_bp = rq["bp_id"]
    summary = {"root_bp": root_bp, "script_sha256": SCRIPT_SHA, "options": OPTIONS, "runs": []}

    for model in a.models:
        digest = model_digest(model, a.ollama)
        stream = f"model:{model}@{digest[:12]}"
        parent = root_bp
        for rnd in (1, 2, 3):
            # step 1: build_prompt (pure function of question, context and round)
            ctx = "" if rnd == 1 else f"Project notes:\n{context}\n\n"
            prompt = f"{ctx}Question: {QUESTION}\nAnswer:"
            inp = sha(canon({"question": QUESTION, "context_sha256": sha(context.encode()) if rnd > 1 else None, "round": rnd}))
            s1 = L.step(root_bp, stream, rnd, "build_prompt", SCRIPT_SHA, inp, sha(prompt.encode("utf-8")),
                        parent_bp=parent, model=model)
            # step 2: model_call (temperature 0, fixed seed; digest pins the weights)
            response, tokens = ollama(model, prompt, a.ollama)
            s2 = L.step(root_bp, stream, rnd, "model_call", SCRIPT_SHA, sha(canon({"prompt_sha256": sha(prompt.encode()), "digest": digest, "options": OPTIONS})),
                        sha(response.encode("utf-8")), output_text=response, parent_bp=s1["bp_id"], tokens=tokens, model=model)
            # step 3: normalize_answer (first integer, or empty)
            m = re.search(r"-?\d+", response)
            norm = m.group(0) if m else ""
            s3 = L.step(root_bp, stream, rnd, "normalize_answer", SCRIPT_SHA, sha(response.encode("utf-8")),
                        sha(norm.encode("utf-8")), output_text=norm, parent_bp=s2["bp_id"], model=model)
            summary["runs"].append({"stream": stream, "round": rnd, "answer": norm, "breakpoint": s3["identity"]["breakpoint"],
                                    "response_sha256": s2["identity"]["output_sha256"][:16], "tokens": tokens,
                                    "step_bps": [s1["bp_id"], s2["bp_id"], s3["bp_id"]], "replayed_existing": not s2["_new"]})
            parent = s3["bp_id"]
    summary["deltas"] = L.deltas(root_bp)
    out = ROOT / "data/breakpoints/runs" / f"{root_bp}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps([{k: r[k] for k in ("stream", "round", "answer", "breakpoint", "response_sha256", "replayed_existing")} | {"tok": r["tokens"]["total_tokens"]}
                      for r in summary["runs"]], indent=0))


if __name__ == "__main__":
    main()
