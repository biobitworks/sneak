"""LOMO × merkle breakpoint pipeline with post-breakpoint Snyk + score.

After each merkle root breakpoint:
1. Persist the breakpoint into Cognee @Data
2. Notify BAND (Claude + ChatGPT)
3. Scan staged code with Snyk (fail closed if token/CLI missing)
4. Compute Javier app-security-score with coverage rejection rules
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from .band_adapter import BandAdapter
from .data_backend import DataBackend
from .evidence import EvidenceStore
from .lomo import matrix_connector_trials, run_one_component_trial
from .merkle import breakpoint_receipt
from .scanner import digest_tree, live_scan_availability, scan
from .score import UPSTREAM_COMMIT, is_clean_ten
from .secrets import presence_receipt
from .fcg_registry import FCGRegistry
from .lomo_fcg import register_breakpoint_result


def score_after_breakpoint(
    *,
    store: EvidenceStore,
    staged_path: Path,
    breakpoint_id: str,
    merkle_root: str,
    data: DataBackend,
    band: Optional[BandAdapter] = None,
    notify_band: bool = True,
    wait_data_seconds: float = 40.0,
    fcg: Optional[FCGRegistry] = None,
    actor_fco: Optional[str] = None,
    model_fco: str = "UNKNOWN",
    parent_fco: Optional[str] = None,
) -> dict[str, Any]:
    """Mandatory post-breakpoint gate: @Data write, optional BAND notify, Snyk+score."""
    if fcg is not None and not actor_fco:
        raise ValueError("FCO actor identity required for per-breakpoint MMR custody")
    data_ref = data.write_breakpoint(
        breakpoint_id=breakpoint_id,
        merkle_root=merkle_root,
        payload={"stage": "post_lomo_breakpoint", "staged_path": str(staged_path)},
        wait_seconds=wait_data_seconds,
    )

    band_ref = None
    if notify_band and band is not None and band.live_available:
        band_ref = band.message_claude_and_chatgpt(
            f"@Data backend recorded LOMO breakpoint {breakpoint_id} "
            f"root={merkle_root[:16]}…. Security reviewer: run Snyk+score on staged app before Done."
        )

    digest = digest_tree(staged_path) if staged_path.exists() else ""
    avail = live_scan_availability()
    scan_result = scan(digest, str(staged_path))
    # Always bind score receipt to this breakpoint even when scan is NOT_TESTED.
    score_receipt = store.append_receipt(
        "breakpoint_snyk_score",
        {
            "breakpoint_id": breakpoint_id,
            "merkle_root": merkle_root,
            "candidate_digest": digest,
            "snyk_availability": {
                "snyk_cli": bool(avail.get("snyk_cli")),
                "token_in_env": bool(avail.get("token_in_env")),
                "observed_outcome": avail.get("observed_outcome"),
            },
            "scan_observed_outcome": scan_result.observed_outcome,
            "score": scan_result.score.to_dict(),
            "clean_ten": is_clean_ten(scan_result.score),
            "score_upstream_commit": UPSTREAM_COMMIT,
            "data_receipt_id": data_ref.external_id,
            "band_receipt_id": band_ref.external_id if band_ref else None,
            "meaning": (
                "Score bound to LOMO merkle breakpoint; incomplete coverage cannot be a clean 10/10; "
                "not an awarded event bonus"
            ),
        },
        parent_id=breakpoint_id,
        provider="snyk+javier-score",
    )
    fcg_result = (
        register_breakpoint_result(
            fcg, actor_fco=actor_fco, model_fco=model_fco,
            breakpoint_id=breakpoint_id, merkle_root=merkle_root,
            score_receipt_path=Path(score_receipt.receipt_path),
            scan_outcome=scan_result.observed_outcome,
            application_score=scan_result.score.application_score,
            coverage_accepted=scan_result.score.coverage_accepted,
            candidate_digest=digest, parent_fco=parent_fco,
        )
        if fcg is not None else None
    )
    return {
        "fcg": fcg_result,
        "breakpoint_id": breakpoint_id,
        "merkle_root": merkle_root,
        "data": json.loads(Path(data_ref.receipt_path).read_text())["payload"],
        "band": (
            json.loads(Path(band_ref.receipt_path).read_text())["payload"]
            if band_ref
            else {"observed_outcome": "SKIPPED"}
        ),
        "scan": scan_result.to_dict(),
        "score_receipt_id": score_receipt.external_id,
        "score_digest": score_receipt.artifact_digest,
        "gate_ready_for_allow": (
            scan_result.score.coverage_accepted
            and scan_result.observed_outcome == "PASS"
            and is_clean_ten(scan_result.score)
        ),
    }


def run_connector_lomo_with_scores(
    *,
    store: EvidenceStore,
    staged_path: Path,
    parent_breakpoint: str = "SNEAK-015",
    live: bool = True,
    notify_band: bool = True,
    fcg: Optional[FCGRegistry] = None,
    actor_fco: Optional[str] = None,
    model_fco: str = "UNKNOWN",
    chain_breakpoint_id: str = "SNEAK-016",
) -> dict[str, Any]:
    """Run connector LOMO trials; score after each baseline and ablated merkle root."""
    if fcg is not None and not actor_fco:
        raise ValueError("FCO actor identity required for registered LOMO trials")
    data = DataBackend(store, live=live)
    band = BandAdapter(store, live=live)
    trials = matrix_connector_trials(parent_breakpoint=parent_breakpoint)
    scored: list[dict[str, Any]] = []
    predecessor_fco: Optional[str] = None

    for trial in trials:
        baseline_fco: Optional[str] = None
        for kind in ("baseline_breakpoint", "ablated_breakpoint"):
            bp = trial[kind]
            scored.append(
                {
                    "trial_id": trial["trial_id"],
                    "removed_component": trial["removed_component"],
                    "breakpoint_kind": kind,
                    "authorization_effect": trial["authorization_effect"],
                    "post": score_after_breakpoint(
                        store=store,
                        staged_path=staged_path,
                        breakpoint_id=bp["id"],
                        merkle_root=bp["root"],
                        data=data,
                        band=band,
                        notify_band=notify_band and kind == "ablated_breakpoint",
                        # Persist to @Data quickly; final recall verified once at end.
                        wait_data_seconds=0.0,
                        fcg=fcg,
                        actor_fco=actor_fco,
                        model_fco=model_fco,
                        parent_fco=predecessor_fco,
                    ),
                }
            )
            if fcg is not None:
                result = scored[-1]["post"]
                predecessor_fco = result["fcg"]["classification_fco_id"]
                if kind == "baseline_breakpoint":
                    baseline_fco = result["fcg"]["breakpoint_fco_id"]
                else:
                    delta = fcg.append(
                        kind="delta", actor_fco=actor_fco, model_fco=model_fco,
                        parent_fco=predecessor_fco,
                        edges=[{"relation": "ablates", "to": baseline_fco}],
                        payload={
                            "trial_id": trial["trial_id"],
                            "removed_component": trial["removed_component"],
                            "baseline_merkle_root": trial["baseline_root"],
                            "ablated_merkle_root": trial["ablated_root"],
                            "root_identity_changed": trial["roots_differ"],
                            "numeric_delta": "NOT_COMPUTED",
                        },
                        state="EXECUTED", source_sha256=result["score_digest"],
                        context={"source": "post_lomo_score_receipt_body_digest",
                                 "meaning": "root identity comparison, not metric improvement"},
                    )
                    result["fcg_delta_fco_id"] = delta["fco_id"]
                    predecessor_fco = delta["fco_id"]

    summary = {
        "parent_breakpoint": parent_breakpoint,
        "trial_count": len(trials),
        "breakpoint_score_count": len(scored),
        "data_backend": data.availability(),
        "band": band.availability(),
        "secrets": presence_receipt(),
        "any_clean_ten": any(s["post"].get("gate_ready_for_allow") for s in scored),
        "live_snyk": live_scan_availability().get("observed_outcome"),
        "scored_breakpoints": [
            {
                "trial_id": s["trial_id"],
                "breakpoint_id": s["post"]["breakpoint_id"],
                "merkle_root": s["post"]["merkle_root"],
                "scan_outcome": s["post"]["scan"]["observed_outcome"],
                "coverage_accepted": s["post"]["scan"]["score"]["coverage_accepted"],
                "application_score": s["post"]["scan"]["score"]["application_score"],
                "data_outcome": s["post"]["data"].get("observed_outcome"),
                "band_outcome": s["post"]["band"].get("observed_outcome"),
            }
            for s in scored
        ],
    }

    chain = breakpoint_receipt(
        schema="sneak.lomo-score-chain.v1",
        breakpoint_id=chain_breakpoint_id,
        parent_id=parent_breakpoint,
        records=[
            {
                "id": f"SCORE-{i:02d}-{row['post']['breakpoint_id']}",
                "trial_id": row["trial_id"],
                "merkle_root": row["post"]["merkle_root"],
                "scan_outcome": row["post"]["scan"]["observed_outcome"],
                "coverage_accepted": row["post"]["scan"]["score"]["coverage_accepted"],
                "score_receipt_id": row["post"]["score_receipt_id"],
            }
            for i, row in enumerate(scored)
        ],
        meaning=(
            "Chain of LOMO merkle breakpoints each followed by Snyk+score attempt; "
            "integrity only — not vulnerability-free or awarded bonus"
        ),
    )
    return {"summary": summary, "trials": trials, "scored": scored, "chain": chain}
