"""Conversation custody: hashed I/O, FCO steps, true/false merkle breakpoints, model MMR deltas.

Pipeline per conversation turn:
  input_hash → deterministic script steps (FCO chain) → output_hash
  unique merkle breakpoint with pass: true|false
  per-model candidate MMR peaks vs root-question leaf (delta over time)

Project MMR remains NOT_COMMITTED. Candidate peaks are local custody only.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from .actor_audit import fco_identity
from .evidence import EvidenceStore, digest_payload, utc_now
from .merkle import breakpoint_receipt, canonical, leaf, root


def xor_distance(a_hex: str, b_hex: str) -> int:
    """Hamming distance over XOR of two equal-length hex digests."""
    a = bytes.fromhex(a_hex)
    b = bytes.fromhex(b_hex)
    if len(a) != len(b):
        raise ValueError("digest_length_mismatch")
    return sum(bin(x ^ y).count("1") for x, y in zip(a, b))


def bag_peaks(peaks: list[bytes]) -> bytes:
    """Simple MMR-shaped bagging: pairwise parent until one peak (odd promote)."""
    if not peaks:
        raise ValueError("empty_peaks")
    row = list(peaks)
    while len(row) > 1:
        nxt: list[bytes] = []
        for i in range(0, len(row), 2):
            if i + 1 < len(row):
                nxt.append(hashlib.sha256(b"\x01" + row[i] + row[i + 1]).digest())
            else:
                nxt.append(row[i])
        row = nxt
    return row[0]


@dataclass
class ModelMMRTrail:
    model_id: str
    root_question_leaf: str
    peaks: list[str] = field(default_factory=list)  # leaf hexes append-only
    roots: list[str] = field(default_factory=list)  # bagged root after each append
    deltas: list[dict[str, Any]] = field(default_factory=list)

    def append_peak(self, peak_hex: str) -> dict[str, Any]:
        self.peaks.append(peak_hex)
        bagged = bag_peaks([bytes.fromhex(p) for p in self.peaks]).hex()
        self.roots.append(bagged)
        delta = {
            "index": len(self.peaks) - 1,
            "peak": peak_hex,
            "model_mmr_root": bagged,
            "vs_root_question_xor_distance": xor_distance(self.root_question_leaf, peak_hex),
            "vs_prev_model_root_xor_distance": (
                None
                if len(self.roots) < 2
                else xor_distance(self.roots[-2], bagged)
            ),
            "mmr": "NOT_COMMITTED",
        }
        self.deltas.append(delta)
        return delta

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "root_question_leaf": self.root_question_leaf,
            "peak_count": len(self.peaks),
            "peaks": list(self.peaks),
            "roots": list(self.roots),
            "deltas": list(self.deltas),
            "mmr": "NOT_COMMITTED",
        }


@dataclass
class ConversationCustodyLedger:
    """Append-only custody for conversations that must reconnect at project end."""

    store: EvidenceStore
    root_question: dict[str, Any]
    breakpoints: list[dict[str, Any]] = field(default_factory=list)
    update_fcos: list[dict[str, Any]] = field(default_factory=list)
    model_trails: dict[str, ModelMMRTrail] = field(default_factory=dict)

    def __post_init__(self) -> None:
        body = {
            "id": "ROOT-QUESTION",
            "kind": "RootQuestionFCO",
            "text": self.root_question.get("text"),
            "requirements": self.root_question.get("requirements") or [],
            "observed_at": utc_now(),
            "verified": False,
        }
        body["fco_candidate_sha256"] = fco_identity(body)
        self.root_question_fco = body
        self.root_question_leaf = leaf(
            {
                "id": body["id"],
                "kind": body["kind"],
                "payload": {
                    "fco_candidate_sha256": body["fco_candidate_sha256"],
                    "text_digest": digest_payload({"text": body["text"]}),
                },
            }
        ).hex()
        self.store.append_receipt("root_question_fco", body, provider="sneak.custody")

    def _trail(self, model_id: str) -> ModelMMRTrail:
        if model_id not in self.model_trails:
            self.model_trails[model_id] = ModelMMRTrail(
                model_id=model_id, root_question_leaf=self.root_question_leaf
            )
        return self.model_trails[model_id]

    def run_turn(
        self,
        *,
        conversation_id: str,
        model_id: str,
        agent_id: str,
        input_payload: dict[str, Any],
        steps: list[dict[str, Any]],
        output_payload: dict[str, Any],
        pass_predicate: Callable[[dict[str, Any], dict[str, Any], list[dict[str, Any]]], bool],
        parent_breakpoint_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Execute one custody turn: hash in → FCO steps → hash out → breakpoint."""
        input_hash = digest_payload(input_payload)
        step_fcos = []
        for i, step in enumerate(steps):
            fco = {
                "id": f"STEP-{conversation_id}-{i:04d}",
                "kind": "DeterministicStepFCO",
                "conversation_id": conversation_id,
                "model_id": model_id,
                "agent_id": agent_id,
                "step_index": i,
                "step": step,
                "input_hash": input_hash,
                "observed_at": utc_now(),
                "verified": False,
            }
            fco["fco_candidate_sha256"] = fco_identity(fco)
            step_fcos.append(fco)
            self.store.append_receipt("deterministic_step_fco", fco, provider="sneak.custody")

        output_hash = digest_payload(output_payload)
        passed = bool(pass_predicate(input_payload, output_payload, step_fcos))

        records = [
            {
                "id": f"IN-{conversation_id}",
                "kind": "HashedInput",
                "payload": {"input_hash": input_hash, "conversation_id": conversation_id},
            },
            *[
                {
                    "id": s["id"],
                    "kind": "DeterministicStepFCO",
                    "payload": {
                        "fco_candidate_sha256": s["fco_candidate_sha256"],
                        "step_index": s["step_index"],
                        "step_name": (s.get("step") or {}).get("name"),
                    },
                }
                for s in step_fcos
            ],
            {
                "id": f"OUT-{conversation_id}",
                "kind": "HashedOutput",
                "payload": {"output_hash": output_hash, "conversation_id": conversation_id},
            },
            {
                "id": f"PASS-{conversation_id}",
                "kind": "BreakpointGate",
                "payload": {"pass": passed, "conversation_id": conversation_id},
            },
        ]
        bp_id = f"BP-{conversation_id}"
        receipt = breakpoint_receipt(
            schema="sneak.conversation-custody-breakpoint.v1",
            breakpoint_id=bp_id,
            parent_id=parent_breakpoint_id or "ROOT-QUESTION",
            records=records,
            meaning=(
                "Unique conversation merkle breakpoint (pass true/false); "
                "connectable at project end; mmr NOT_COMMITTED"
            ),
        )
        receipt["pass"] = passed
        receipt["input_hash"] = input_hash
        receipt["output_hash"] = output_hash
        receipt["conversation_id"] = conversation_id
        receipt["model_id"] = model_id
        receipt["agent_id"] = agent_id
        receipt["mmr"] = "NOT_COMMITTED"
        receipt["root_question_leaf"] = self.root_question_leaf

        peak = leaf(
            {
                "id": bp_id,
                "kind": "ConversationBreakpointPeak",
                "payload": {
                    "breakpoint_root": receipt["root"],
                    "pass": passed,
                    "input_hash": input_hash,
                    "output_hash": output_hash,
                    "model_id": model_id,
                },
            }
        ).hex()
        delta = self._trail(model_id).append_peak(peak)
        receipt["model_mmr_delta"] = delta

        self.breakpoints.append(receipt)
        self.store.append_receipt(
            "conversation_breakpoint",
            {
                "breakpoint_id": bp_id,
                "root": receipt["root"],
                "pass": passed,
                "model_id": model_id,
                "agent_id": agent_id,
                "input_hash": input_hash,
                "output_hash": output_hash,
                "model_mmr_delta": delta,
                "mmr": "NOT_COMMITTED",
            },
            parent_id=parent_breakpoint_id,
            provider="sneak.custody",
        )
        return receipt

    def track_update(
        self,
        *,
        update_id: str,
        parent_fco_id: str,
        change: dict[str, Any],
    ) -> dict[str, Any]:
        """Hash an update through an FCO tracking successor (never rewrite)."""
        body = {
            "id": update_id,
            "kind": "UpdateTrackingFCO",
            "parent_fco_id": parent_fco_id,
            "change": change,
            "change_digest": digest_payload(change),
            "observed_at": utc_now(),
            "verified": False,
        }
        body["fco_candidate_sha256"] = fco_identity(body)
        self.update_fcos.append(body)
        self.store.append_receipt("update_tracking_fco", body, parent_id=parent_fco_id, provider="sneak.custody")
        return body

    def project_connector_receipt(self, *, breakpoint_id: str = "SNEAK-024") -> dict[str, Any]:
        """Merkle over all conversation breakpoints + model MMR trails for end-of-project join."""
        records: list[dict[str, Any]] = [
            {
                "id": "ROOT-QUESTION",
                "kind": "RootQuestionFCO",
                "payload": {
                    "fco_candidate_sha256": self.root_question_fco["fco_candidate_sha256"],
                    "leaf": self.root_question_leaf,
                },
            }
        ]
        for bp in self.breakpoints:
            records.append(
                {
                    "id": bp["id"],
                    "kind": "ConversationBreakpoint",
                    "payload": {
                        "root": bp["root"],
                        "pass": bp["pass"],
                        "model_id": bp["model_id"],
                        "input_hash": bp["input_hash"],
                        "output_hash": bp["output_hash"],
                        "model_mmr_delta": bp.get("model_mmr_delta"),
                    },
                }
            )
        for model_id, trail in sorted(self.model_trails.items()):
            records.append(
                {
                    "id": f"MMR-{model_id}",
                    "kind": "ModelMMRTrail",
                    "payload": trail.to_dict(),
                }
            )
        for u in self.update_fcos:
            records.append(
                {
                    "id": u["id"],
                    "kind": "UpdateTrackingFCO",
                    "payload": {
                        "fco_candidate_sha256": u["fco_candidate_sha256"],
                        "parent_fco_id": u["parent_fco_id"],
                        "change_digest": u["change_digest"],
                    },
                }
            )
        receipt = breakpoint_receipt(
            schema="sneak.conversation-custody-project.v1",
            breakpoint_id=breakpoint_id,
            parent_id="ROOT-QUESTION",
            records=records,
            meaning=(
                "End-of-project connector over unique conversation breakpoints and "
                "per-model candidate MMR deltas vs root question; mmr NOT_COMMITTED"
            ),
        )
        receipt["mmr"] = "NOT_COMMITTED"
        receipt["root_question_leaf"] = self.root_question_leaf
        receipt["breakpoint_count"] = len(self.breakpoints)
        receipt["pass_count"] = sum(1 for b in self.breakpoints if b.get("pass"))
        receipt["fail_count"] = sum(1 for b in self.breakpoints if not b.get("pass"))
        receipt["model_trails"] = {k: v.to_dict() for k, v in sorted(self.model_trails.items())}
        return receipt


# Custody requirements derived from the operator ask (mandatory vs optional).
CUSTODY_REQUIREMENTS = [
    {
        "id": "REQ-CUSTODY-01",
        "kind": "mandatory",
        "statement": "Unique merkle breakpoints for each conversation so they reconnect at project end",
    },
    {
        "id": "REQ-CUSTODY-02",
        "kind": "mandatory",
        "statement": "Each merkle breakpoint carries pass true|false",
    },
    {
        "id": "REQ-CUSTODY-03",
        "kind": "mandatory",
        "statement": "Each model has candidate MMR vs root question with delta over time",
    },
    {
        "id": "REQ-CUSTODY-04",
        "kind": "mandatory",
        "statement": "input hashed → deterministic script steps/FCO → output hashed",
    },
    {
        "id": "REQ-CUSTODY-05",
        "kind": "mandatory",
        "statement": "Updates hashed through FCO tracking successors",
    },
    {
        "id": "REQ-CUSTODY-06",
        "kind": "mandatory",
        "statement": "BAND used to ask and respond among agents",
    },
    {
        "id": "REQ-CUSTODY-07",
        "kind": "mandatory",
        "statement": "Cognee @Data captures sneak custody information for breakpoints",
    },
    {
        "id": "REQ-CUSTODY-08",
        "kind": "mandatory",
        "statement": "All agents and planner updated in the conversation",
    },
    {
        "id": "REQ-CUSTODY-09",
        "kind": "mandatory",
        "statement": "Check with planner in band.ai chat that has a planner",
    },
    {
        "id": "REQ-CUSTODY-10",
        "kind": "optional",
        "statement": "Live model inference (Liquid/OpenJev) bound into custody turns",
    },
    {
        "id": "REQ-CUSTODY-11",
        "kind": "optional",
        "statement": "Project MMR Overwatch commitment (SIGNED/MMR_COMMITTED)",
    },
]


def verify_custody_requirements(
    ledger: ConversationCustodyLedger,
    *,
    band_ok: bool,
    cognee_ok: bool,
    planner_checked: bool,
    agents_updated: bool,
    live_model_inference: bool = False,
    mmr_committed: bool = False,
) -> list[dict[str, Any]]:
    """Independently score each custody requirement (including optional)."""
    bps = ledger.breakpoints
    unique_ids = {b["id"] for b in bps}
    has_pass_flags = all("pass" in b and isinstance(b["pass"], bool) for b in bps) if bps else False
    trails = ledger.model_trails
    has_mmr_deltas = bool(trails) and all(t.deltas for t in trails.values())
    hashed_io = all(b.get("input_hash") and b.get("output_hash") for b in bps) if bps else False
    updates_ok = bool(ledger.update_fcos)

    observed = {
        "REQ-CUSTODY-01": ("PASS" if bps and len(unique_ids) == len(bps) else "FAIL", bps and len(unique_ids) == len(bps)),
        "REQ-CUSTODY-02": ("PASS" if has_pass_flags else "FAIL", has_pass_flags),
        "REQ-CUSTODY-03": ("PASS" if has_mmr_deltas else "FAIL", has_mmr_deltas),
        "REQ-CUSTODY-04": ("PASS" if hashed_io else "FAIL", hashed_io),
        "REQ-CUSTODY-05": ("PASS" if updates_ok else "FAIL", updates_ok),
        "REQ-CUSTODY-06": ("PASS" if band_ok else "NOT_TESTED", band_ok),
        "REQ-CUSTODY-07": ("PASS" if cognee_ok else "NOT_TESTED", cognee_ok),
        "REQ-CUSTODY-08": ("PASS" if agents_updated else "NOT_TESTED", agents_updated),
        "REQ-CUSTODY-09": ("PASS" if planner_checked else "NOT_TESTED", planner_checked),
        "REQ-CUSTODY-10": ("PASS" if live_model_inference else "NOT_TESTED", live_model_inference),
        "REQ-CUSTODY-11": (
            "PASS" if mmr_committed else "NOT_TESTED",
            mmr_committed,
        ),
    }
    out = []
    for req in CUSTODY_REQUIREMENTS:
        rid = req["id"]
        outcome, verified = observed[rid]
        # Optional never blocks; unverified optional stays verified=false.
        if req["kind"] == "optional" and outcome == "NOT_TESTED":
            verified = False
        if req["id"] == "REQ-CUSTODY-11":
            # Never claim committed without explicit receipt — default false.
            verified = bool(mmr_committed)
            outcome = "PASS" if mmr_committed else "NOT_TESTED"
        out.append(
            {
                **req,
                "observed_outcome": outcome,
                "verified": bool(verified),
                "required_for_entry": req["kind"] == "mandatory",
            }
        )
    return out
