"""Conversation FCOs, LongMemEval answer-diff FCOs, and per-token ROI.

Each conversation turn-bundle is an FCO. A second FCO captures how a model
answer differs from the LongMemEval gold answer. Token ROI is deterministic
from (token_count × unit_cost) and benefit from match quality.
"""

from __future__ import annotations

import json
import re
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

from .actor_audit import ActorAuditTrail, deterministic_roi, fco_identity
from .evidence import EvidenceStore, digest_payload, utc_now
from .merkle import breakpoint_receipt
from .model_clients import (
    TOKEN_UNIT_COST,
    LiquidClient,
    OpenJevClient,
    estimate_tokens,
)


def normalize_answer(text: str) -> str:
    t = (text or "").strip().lower()
    t = re.sub(r"[\"'`]", "", t)
    t = re.sub(r"\s+", " ", t)
    return t


def answer_match_quality(gold: str, candidate: Optional[str]) -> dict[str, Any]:
    """Deterministic match metrics vs LongMemEval gold (not LLM-as-judge)."""
    if candidate is None:
        return {
            "exact": False,
            "gold_in_candidate": False,
            "token_overlap": "0",
            "benefit_units": "0",
            "observed_outcome": "NOT_TESTED",
        }
    g = normalize_answer(gold)
    c = normalize_answer(candidate)
    exact = g == c
    contained = g in c or c in g
    g_tokens = set(g.split())
    c_tokens = set(c.split())
    if not g_tokens:
        overlap = Decimal("0")
    else:
        overlap = Decimal(len(g_tokens & c_tokens)) / Decimal(len(g_tokens))
    if exact:
        benefit = Decimal("1.0")
        outcome = "PASS"
    elif contained:
        benefit = Decimal("0.75")
        outcome = "PARTIAL"
    elif overlap >= Decimal("0.5"):
        benefit = Decimal("0.5")
        outcome = "PARTIAL"
    else:
        benefit = Decimal("0.0")
        outcome = "FAIL"
    return {
        "exact": exact,
        "gold_in_candidate": contained,
        "token_overlap": str(overlap.quantize(Decimal("0.000001"))),
        "benefit_units": str(benefit),
        "observed_outcome": outcome,
    }


def per_token_roi(
    *,
    total_tokens: int,
    unit_cost_per_token: Any,
    benefit_units: Any,
) -> dict[str, Any]:
    tokens = max(0, int(total_tokens))
    unit = Decimal(str(unit_cost_per_token))
    cost = unit * Decimal(tokens)
    roi = deterministic_roi(cost_units=cost, benefit_units=benefit_units)
    benefit = Decimal(str(benefit_units))
    benefit_per_token = (
        None
        if tokens == 0
        else str((benefit / Decimal(tokens)).quantize(Decimal("0.000001")))
    )
    return {
        **roi,
        "total_tokens": tokens,
        "unit_cost_per_token": str(unit),
        "benefit_per_token": benefit_per_token,
        "roi_per_token_basis": "aggregate_roi_spread_across_tokens_via_unit_cost",
    }


def load_longmemeval_fixture(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_prompt(item: dict[str, Any]) -> list[dict[str, str]]:
    sessions = item.get("haystack_sessions") or []
    history_bits = []
    for sess in sessions:
        for turn in sess:
            history_bits.append(f"{turn.get('role')}: {turn.get('content')}")
    history = "\n".join(history_bits)
    user = (
        "You are answering a LongMemEval-style memory question.\n"
        f"History:\n{history}\n\n"
        f"Question ({item.get('question_date')}): {item.get('question')}\n"
        "Answer briefly with only the factual answer."
    )
    return [{"role": "user", "content": user}]


class ConversationEvalHarness:
    """Run Liquid + OpenJev scenarios; emit conversation/diff FCOs + token ROI."""

    def __init__(
        self,
        store: EvidenceStore,
        *,
        liquid: Optional[LiquidClient] = None,
        openjev: Optional[OpenJevClient] = None,
        audit: Optional[ActorAuditTrail] = None,
    ):
        self.store = store
        self.liquid = liquid or LiquidClient()
        self.openjev = openjev or OpenJevClient()
        self.audit = audit or ActorAuditTrail(store)
        self.conversation_fcos: list[dict[str, Any]] = []
        self.diff_fcos: list[dict[str, Any]] = []
        self.token_roi_rows: list[dict[str, Any]] = []

    def _conversation_fco(
        self,
        *,
        scenario_id: str,
        model_provider: str,
        model_id: str,
        agent_id: str,
        messages: list[dict[str, str]],
        response_text: Optional[str],
        usage: dict[str, Any],
        observed_outcome: str,
    ) -> dict[str, Any]:
        body = {
            "id": f"CONV-{scenario_id}-{model_provider}-{agent_id}",
            "kind": "ConversationFCO",
            "scenario_id": scenario_id,
            "model_provider": model_provider,
            "model_id": model_id,
            "agent_id": agent_id,
            "messages_digest": digest_payload({"messages": messages}),
            "response_prefix": (response_text or "")[:240],
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "observed_outcome": observed_outcome,
            "observed_at": utc_now(),
            "verified": False,
            "qwen25_retired": True,
        }
        body["fco_candidate_sha256"] = fco_identity(body)
        self.conversation_fcos.append(body)
        self.store.append_receipt("conversation_fco", body, provider=model_provider)
        return body

    def _diff_fco(
        self,
        *,
        scenario_id: str,
        model_provider: str,
        agent_id: str,
        gold: str,
        candidate: Optional[str],
        match: dict[str, Any],
        conversation_fco_id: str,
    ) -> dict[str, Any]:
        body = {
            "id": f"DIFF-{scenario_id}-{model_provider}-{agent_id}",
            "kind": "LongMemEvalDiffFCO",
            "scenario_id": scenario_id,
            "dataset": "longmemeval",
            "gold_answer": gold,
            "candidate_answer_prefix": (candidate or "")[:240],
            "match": match,
            "conversation_fco_id": conversation_fco_id,
            "model_provider": model_provider,
            "agent_id": agent_id,
            "observed_outcome": match["observed_outcome"],
            "observed_at": utc_now(),
            "verified": False,
        }
        body["fco_candidate_sha256"] = fco_identity(body)
        self.diff_fcos.append(body)
        self.store.append_receipt("longmemeval_diff_fco", body, provider=model_provider)
        return body

    def _record_token_roi(
        self,
        *,
        scenario_id: str,
        model_provider: str,
        agent_id: str,
        total_tokens: int,
        benefit_units: str,
        conversation_fco_id: str,
        diff_fco_id: str,
    ) -> dict[str, Any]:
        unit = TOKEN_UNIT_COST.get(model_provider, TOKEN_UNIT_COST["local-stub"])
        roi = per_token_roi(
            total_tokens=total_tokens,
            unit_cost_per_token=unit,
            benefit_units=benefit_units,
        )
        row = {
            "scenario_id": scenario_id,
            "model_provider": model_provider,
            "agent_id": agent_id,
            "conversation_fco_id": conversation_fco_id,
            "diff_fco_id": diff_fco_id,
            "token_roi": roi,
        }
        self.token_roi_rows.append(row)
        benefit = Decimal(str(benefit_units))
        if benefit >= Decimal("1"):
            outcome = "PASS"
        elif benefit > 0:
            outcome = "PARTIAL"
        elif total_tokens == 0:
            outcome = "NOT_TESTED"
        else:
            outcome = "FAIL"
        self.audit.record_action(
            actor_id=agent_id,
            actor_role=model_provider,
            action="longmemeval_scenario",
            quantity=max(1, total_tokens),
            unit_cost=unit,
            outcome=outcome,
            meter_event_name="model_tokens",
            properties={
                "scenario_id": scenario_id,
                "roi": roi.get("roi"),
                "benefit_per_token": roi.get("benefit_per_token"),
                "total_tokens": total_tokens,
            },
        )
        return row

    def run_scenario(self, item: dict[str, Any]) -> dict[str, Any]:
        scenario_id = str(item["question_id"])
        gold = str(item["answer"])
        messages = build_prompt(item)
        results: dict[str, Any] = {"scenario_id": scenario_id, "models": {}}

        # Liquid generation path
        liquid_resp = self.liquid.chat(messages)
        if not liquid_resp.get("ok") and liquid_resp.get("observed_outcome") == "NOT_TESTED":
            # Local stub for structure only — clearly labeled, not claimed live.
            stub = gold  # optimistic stub would cheat; use empty to stay honest
            liquid_resp = {
                **liquid_resp,
                "text": None,
                "provider": "liquid",
                "model": self.liquid.model,
                "completion_tokens": 0,
                "total_tokens": liquid_resp.get("prompt_tokens", estimate_tokens(messages[0]["content"])),
                "stub": True,
            }
            _ = stub
        conv_l = self._conversation_fco(
            scenario_id=scenario_id,
            model_provider="liquid",
            model_id=str(liquid_resp.get("model") or self.liquid.model),
            agent_id="liquid-agent",
            messages=messages,
            response_text=liquid_resp.get("text"),
            usage=liquid_resp,
            observed_outcome=str(liquid_resp.get("observed_outcome")),
        )
        match_l = answer_match_quality(gold, liquid_resp.get("text"))
        diff_l = self._diff_fco(
            scenario_id=scenario_id,
            model_provider="liquid",
            agent_id="liquid-agent",
            gold=gold,
            candidate=liquid_resp.get("text"),
            match=match_l,
            conversation_fco_id=conv_l["id"],
        )
        roi_l = self._record_token_roi(
            scenario_id=scenario_id,
            model_provider="liquid",
            agent_id="liquid-agent",
            total_tokens=int(liquid_resp.get("total_tokens") or 0),
            benefit_units=match_l["benefit_units"],
            conversation_fco_id=conv_l["id"],
            diff_fco_id=diff_l["id"],
        )
        results["models"]["liquid"] = {
            "conversation_fco": conv_l["id"],
            "diff_fco": diff_l["id"],
            "match": match_l,
            "token_roi": roi_l["token_roi"],
            "live": bool(liquid_resp.get("ok")),
        }

        # OpenJev decision path: judge whether a candidate matches gold.
        # Prefer Liquid candidate; if missing, use empty candidate (honest NOT_TESTED/FAIL).
        candidate_for_judge = liquid_resp.get("text") or ""
        oj = self.openjev.decide_match(
            question=str(item["question"]),
            gold_answer=gold,
            candidate_answer=candidate_for_judge,
        )
        conv_j = self._conversation_fco(
            scenario_id=scenario_id,
            model_provider="openjev",
            model_id=str(oj.get("model") or self.openjev.model),
            agent_id="openjev-agent",
            messages=[{"role": "user", "content": f"judge:{scenario_id}"}],
            response_text=oj.get("text"),
            usage=oj,
            observed_outcome=str(oj.get("observed_outcome")),
        )
        # Diff FCO for OpenJev: compare its yes/no decision to deterministic match.
        oj_says_match = False
        if oj.get("ok") and oj.get("answers"):
            dumped = json.dumps(oj.get("answers")).lower()
            oj_says_match = "yes_match" in dumped or '"a"' in dumped
        oj_candidate = "yes_match" if oj_says_match else ("no_mismatch" if oj.get("ok") else None)
        gold_decision = "yes_match" if match_l["observed_outcome"] in ("PASS", "PARTIAL") and Decimal(match_l["benefit_units"]) >= Decimal("0.5") else "no_mismatch"
        match_j = answer_match_quality(gold_decision, oj_candidate)
        if not oj.get("ok"):
            match_j = {
                "exact": False,
                "gold_in_candidate": False,
                "token_overlap": "0",
                "benefit_units": "0",
                "observed_outcome": str(oj.get("observed_outcome") or "NOT_TESTED"),
            }
        diff_j = self._diff_fco(
            scenario_id=scenario_id,
            model_provider="openjev",
            agent_id="openjev-agent",
            gold=gold_decision,
            candidate=oj_candidate,
            match=match_j,
            conversation_fco_id=conv_j["id"],
        )
        roi_j = self._record_token_roi(
            scenario_id=scenario_id,
            model_provider="openjev",
            agent_id="openjev-agent",
            total_tokens=int(oj.get("total_tokens") or 0),
            benefit_units=match_j["benefit_units"],
            conversation_fco_id=conv_j["id"],
            diff_fco_id=diff_j["id"],
        )
        results["models"]["openjev"] = {
            "conversation_fco": conv_j["id"],
            "diff_fco": diff_j["id"],
            "match": match_j,
            "token_roi": roi_j["token_roi"],
            "live": bool(oj.get("ok")),
            "judged_liquid_candidate": bool(candidate_for_judge),
        }
        return results

    def run_fixture(self, path: Path) -> dict[str, Any]:
        items = load_longmemeval_fixture(path)
        scenarios = [self.run_scenario(item) for item in items]
        receipt = breakpoint_receipt(
            schema="sneak.liquid-openjev-longmemeval.v1",
            breakpoint_id="SNEAK-021",
            parent_id="SNEAK-020",
            records=(
                [
                    {
                        "id": c["id"],
                        "kind": "ConversationFCO",
                        "payload": {
                            "fco_candidate_sha256": c["fco_candidate_sha256"],
                            "scenario_id": c["scenario_id"],
                            "model_provider": c["model_provider"],
                            "agent_id": c["agent_id"],
                            "total_tokens": c["total_tokens"],
                            "observed_outcome": c["observed_outcome"],
                        },
                    }
                    for c in self.conversation_fcos
                ]
                + [
                    {
                        "id": d["id"],
                        "kind": "LongMemEvalDiffFCO",
                        "payload": {
                            "fco_candidate_sha256": d["fco_candidate_sha256"],
                            "scenario_id": d["scenario_id"],
                            "model_provider": d["model_provider"],
                            "match": d["match"],
                        },
                    }
                    for d in self.diff_fcos
                ]
                + [
                    {
                        "id": f"ROI-{i:04d}-{r['model_provider']}-{r['scenario_id']}",
                        "kind": "TokenROI",
                        "payload": r,
                    }
                    for i, r in enumerate(self.token_roi_rows)
                ]
            ),
            meaning=(
                "Liquid AI + OpenJev conversations as FCOs; LongMemEval answer-diff FCOs; "
                "per-token ROI per model/agent/scenario; Qwen 2.5 retired; mmr NOT_COMMITTED"
            ),
        )
        receipt["mmr"] = "NOT_COMMITTED"
        receipt["scenarios"] = scenarios
        receipt["token_roi_rows"] = self.token_roi_rows
        receipt["qwen25_retired"] = True
        receipt["models_baseline"] = ["liquid", "openjev"]
        return receipt
