"""Offline regression checks for the bounded LongMemEval-V2 diagnostic."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("sneak_lmev2_pilot", ROOT / "scripts/run_lmev2_pilot.py")
assert SPEC is not None and SPEC.loader is not None
pilot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pilot)


def test_case_selector_avoids_gold_in_prompt_and_images():
    rows = [
        {"id": "00", "domain": "enterprise", "question": "IMAGE", "image": "file.png",
         "eval_function": "norm_phrase_set_match|lower=true", "answer": "secret"},
        {"id": "01", "domain": "enterprise", "question": "ENTERPRISE", "image": None,
         "eval_function": "norm_phrase_set_match|lower=true", "answer": "secret"},
        {"id": "02", "domain": "web", "question": "WEB", "image": None,
         "eval_function": "mc_choice_match|strip_chars=.", "answer": "B"},
        {"id": "03", "domain": "web", "question": "JUDGE_ONLY", "image": None,
         "eval_function": "llm_judge|model=x", "answer": "secret"},
    ]
    with TemporaryDirectory() as td:
        source = Path(td) / "questions.jsonl"
        source.write_text("".join(json.dumps(x) + "\n" for x in rows))
        chosen = pilot.cases_for_diagnostic(source)
    assert [q["id"] for q in chosen] == ["01", "02"]
    assert [q["question"] for q in chosen] == ["ENTERPRISE", "WEB"]


def test_canonical_digest_stable_under_key_order():
    left = {"beta": 2, "alpha": 1}
    right = {"alpha": 1, "beta": 2}
    assert pilot.canonical(left) == pilot.canonical(right)
    assert pilot.digest(left) == pilot.digest(right)
    assert len(pilot.digest(left)) == 64


def test_pilot_prevents_missing_domain_claim():
    with TemporaryDirectory() as td:
        source = Path(td) / "questions.jsonl"
        source.write_text(json.dumps({"id": "A", "domain": "web", "question": "q",
            "eval_function": "mc_choice_match|strip_chars=.", "image": None}) + "\n")
        try:
            pilot.cases_for_diagnostic(source)
        except RuntimeError as exc:
            assert "one rule-evaluable" in str(exc)
        else:
            raise AssertionError("Missing domain was not rejected")
