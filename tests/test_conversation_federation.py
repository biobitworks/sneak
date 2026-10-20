"""Regression tests for SNEAK's corrected question-level MMR federation."""
from __future__ import annotations
import hashlib,importlib.util,json
from pathlib import Path
from tempfile import TemporaryDirectory
import pytest
ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT/"src"))
sys.path.insert(0,str(ROOT/"scripts"))
from sneak.fcg_registry import FCGRegistry,verify_rows
from sneak.mmr_reference import MMR,mmr_verify
from federate_sneak_conversations import commit_mmr,sha
from correct_federation_question_leaves import parse_canonical_requirements
V0=ROOT/"receipts/evaluations/SNEAK_20261020_CONVERSATION_FEDERATION.json"
V1=ROOT/"receipts/evaluations/SNEAK_20261020_CONVERSATION_FEDERATION_V1_CORRECTED.json"

def test_question_leaf_uses_zero_byte_not_literal_escape():
 x=b"example question"
 a=sha(bytes([0])+x)
 b=sha(bytes([92,120,48,48])+x)
 assert a!=b
 assert a==hashlib.sha256(b"\x00example question").hexdigest()

def test_model_mmr_positive_and_mutation_negative():
 source=[{"t":"question","sha":sha(b"question")},{"t":"output","sha":sha(b"output")}]
 result=commit_mmr(source)
 assert result["leaf_count"]==2 and result["node_count"]==3
 assert result["inclusion_verified"] and result["tamper_rejected"]
 mmr=MMR(); raw=[json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode() for x in source]
 for x in raw:mmr.append(x)
 assert mmr.root().hex()==result["root"]
 assert mmr_verify(raw[1],mmr.proof(1),mmr.root())
 assert not mmr_verify(raw[1]+b"x",mmr.proof(1),mmr.root())

def test_requirements_source_includes_optional_and_bonus():
 text=(ROOT/"docs/requirements/HACKATHON_REQUIREMENTS.md").read_text()
 rows=parse_canonical_requirements(text)
 from collections import Counter
 counts=Counter(x["category"] for x in rows)
 assert len(rows)==56 and counts["OPTIONAL"]==1 and counts["BONUS"]==6
 assert counts["MANDATORY"]==16 and counts["EXTRA_CREDIT"]==3
 assert {"SUB-005","SNYK-001","COG-X01"}.issubset({r["id"] for r in rows})

def test_predecessor_correction_and_federation_roots():
 old=V0.read_bytes()
 assert old.endswith(bytes([92,110]))  # preserve failed v0 receipt unchanged
 old_record=json.loads(old[:-2])
 new_record=json.loads(V1.read_text())
 ledger=FCGRegistry(ROOT/"data/fcg/sneak-016-replay.jsonl")
 rows=ledger.rows()
 assert old_record["successor"]["fco_count"]==174
 assert verify_rows(rows[:174])["mmr_root"]==old_record["successor"]["mmr_root"]
 assert new_record["parent"]["mmr_root"]==old_record["successor"]["mmr_root"]
 assert verify_rows(rows[:243])["mmr_root"]==new_record["successor"]["mmr_root"]
 assert new_record["federation"]["inclusion_verified"]
 assert new_record["federation"]["tamper_rejected"]
 assert new_record["coverage_state"]=="PARTIAL"
 assert not new_record["all_conversations_captured"]
 assert new_record["live_band_planner"]=="NOT_TESTED_AUTH_BLOCKED"
 assert new_record["security_admission"]=="DENY"

def test_model_question_anchors_are_corrected():
 old=json.loads(V0.read_bytes()[:-2])
 corrected=json.loads(V1.read_text())
 question_path=Path("/tmp/sneak-lmev2-dataset/questions.jsonl")
 if not question_path.is_file():
  pytest.skip("Official pinned input dataset not staged on this test machine")
 allq={q["id"]:q for q in (json.loads(x) for x in question_path.read_text().splitlines() if x.strip())}
 for model,v in corrected["model_roots"].items():
  assert v["model_mmr"]["leaf_count"]==4
  assert v["model_mmr"]["node_count"]==7
  assert v["model_mmr"]["inclusion_verified"] and v["model_mmr"]["tamper_rejected"]
  for current,previous in zip(v["questions"],old["models"][model]["questions"]):
   expected=sha(bytes([0])+allq[current["question_id"]]["question"].encode())
   assert expected==current["correct_question_leaf_sha256"]
   assert expected != current["rejected_v0_leaf_sha256"]
   assert previous["question_root"]==current["rejected_v0_leaf_sha256"]
   assert current["per_question_mmr"]["node_count"]==3

def test_two_manifests_are_independent_not_total_distinct_requirements():
 new=json.loads(V1.read_text())
 assert new["official_source_requirement_count"]==56
 assert new["manifest_only_requirement_count"]==59
 assert new["requirement_source_occurrences_in_both_manifests"]==115
 assert new["cross_manifest_identity_deduplication"]=="NOT_COMPUTED"
