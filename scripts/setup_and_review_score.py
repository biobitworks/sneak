#!/usr/bin/env python3
"""Pin Javier app-security-score, review requirements, update @Data, hash-message BAND.

Score scale is 0–10 (10 = clean with full SCA+SAST). Event Snyk bonus is up to +10%
and is NOT awarded by this script. Without SNYK_TOKEN, live application_score stays null.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.aok import entry_gate, successor_from_registry, summarize_optional_mandatory
from sneak.band_adapter import BandAdapter
from sneak.data_backend import DataBackend
from sneak.evidence import EvidenceStore, digest_payload
from sneak.merkle import breakpoint_receipt, canonical, leaf, root
from sneak.score import (
    NON_LOW_CUTOFF,
    UPSTREAM_COMMIT,
    UPSTREAM_REPO,
    WEIGHTS,
    compute_score,
    score_with_coverage,
)
from sneak.secrets import export_to_environ, presence_receipt
from sneak.scanner import digest_tree, live_scan_availability


ASS_DIR = ROOT / "sources" / "app-security-score"


def verify_javier_pin() -> dict:
    """Confirm local clone commit + Node helper matches Python pin (no live Docker scan)."""
    out = {
        "upstream_repo": UPSTREAM_REPO,
        "required_commit": UPSTREAM_COMMIT,
        "local_clone_present": ASS_DIR.is_file() or (ASS_DIR / "package.json").is_file(),
        "license": "UNKNOWN_ROOT_LICENSE_404",
        "node_helper_match": None,
        "python_helper": {
            "zero_findings": compute_score(
                {"critical": 0, "high": 0, "medium": 0, "low": 0},
                {"critical": 0, "high": 0, "medium": 0, "low": 0},
            ),
            "one_high": compute_score(
                {"critical": 0, "high": 1, "medium": 0, "low": 0},
                {"critical": 0, "high": 0, "medium": 0, "low": 0},
            ),
            "eleven_medium": compute_score(
                {"critical": 0, "high": 0, "medium": NON_LOW_CUTOFF + 1, "low": 0},
                {"critical": 0, "high": 0, "medium": 0, "low": 0},
            ),
            "weights": WEIGHTS,
            "non_low_cutoff": NON_LOW_CUTOFF,
        },
        "coverage_gate": score_with_coverage(
            sca_counts={"critical": 0, "high": 0, "medium": 0, "low": 0},
            sast_counts={"critical": 0, "high": 0, "medium": 0, "low": 0},
            sca_coverage=True,
            sast_coverage=False,
        ).to_dict(),
        "scale": "0_to_10_tool_score_where_10_is_clean",
        "event_bonus": "up_to_plus_10_percent_NOT_AWARDED_BY_TOOL_SCORE",
        "target_for_bonus_path": "application_score_10_with_sca_and_sast_coverage",
        "meaning": (
            "A tool score of 0 means many findings (worst). "
            "Extra event marks (up to +10%) come from real Snyk integration evidence, "
            "not from forcing tool score to 0."
        ),
    }
    if (ASS_DIR / ".git").exists() or (ASS_DIR / "package.json").exists():
        try:
            commit = subprocess.check_output(
                ["git", "-C", str(ASS_DIR), "rev-parse", "HEAD"], text=True, timeout=10
            ).strip()
        except Exception as exc:  # noqa: BLE001
            commit = f"UNAVAILABLE:{type(exc).__name__}"
        out["local_commit"] = commit
        out["commit_matches_pin"] = commit == UPSTREAM_COMMIT
        # Cross-check Node computeScore if node available
        node = subprocess.run(
            [
                "node",
                "-e",
                "import('./docker/lib.mjs').then(m=>{"
                "const z={critical:0,high:0,medium:0,low:0};"
                "console.log(JSON.stringify({"
                "zero:m.computeScore(z,z),"
                "one_high:m.computeScore({...z,high:1},z),"
                "eleven_medium:m.computeScore({...z,medium:11},z)"
                "}));})",
            ],
            cwd=str(ASS_DIR),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if node.returncode == 0 and node.stdout.strip():
            try:
                js = json.loads(node.stdout.strip().splitlines()[-1])
                out["node_helper"] = js
                out["node_helper_match"] = (
                    js.get("zero") == out["python_helper"]["zero_findings"]
                    and js.get("one_high") == out["python_helper"]["one_high"]
                    and js.get("eleven_medium") == out["python_helper"]["eleven_medium"]
                )
            except json.JSONDecodeError:
                out["node_helper_error"] = node.stdout[:200] + node.stderr[:200]
        else:
            out["node_helper_error"] = (node.stderr or node.stdout)[:300]
    return out


def requirements_review() -> dict:
    path = ROOT / "data/verification/requirements_sneak_014.jsonl"
    if not path.exists():
        path = ROOT / "data/verification/requirements_sneak_011.jsonl"
    verdicts = successor_from_registry(
        path, successor_suffix="SNEAK-018", reason="score-setup review"
    )
    summary = summarize_optional_mandatory(verdicts)
    # Highlight Snyk/Flex/BAND/Cognee atoms
    focus = {
        "entry_gate": summary["entry"],
        "counts": summary["counts"],
        "snyk_bonus_atoms": [
            x for x in summary["buckets"].get("bonus_selected", []) if "S0" in x["id"] or "S01" in x["id"] or "S02" in x["id"]
        ]
        + [
            x
            for bucket in summary["buckets"].values()
            for x in bucket
            if "REQ-AOK-S" in x["id"]
        ][:12],
        "mandatory_still_unverified": summary["entry"]["mandatory_unverified"],
        "live_connectors": {
            "band_cognee_approved": True,
            "snyk_live": live_scan_availability().get("observed_outcome"),
            "demo_digest": digest_tree(ROOT / "apps/security-demo"),
        },
    }
    return focus


def main() -> int:
    export_to_environ()
    out_dir = ROOT / "receipts/connectors"
    out_dir.mkdir(parents=True, exist_ok=True)
    store = EvidenceStore(ROOT / "local-runs/evidence-score-review")

    pin = verify_javier_pin()
    req = requirements_review()
    avail = live_scan_availability()
    secrets = presence_receipt()

    review_body = {
        "id": "SNEAK-018-REVIEW",
        "parent": "SNEAK-017B",
        "javier_app_security_score": pin,
        "requirements": req,
        "snyk_availability": {
            "cli": bool(avail.get("snyk_cli")),
            "token_in_env": bool(avail.get("token_in_env")),
            "observed_outcome": avail.get("observed_outcome"),
        },
        "secret_presence": secrets,
        "claims": {
            "live_application_score": None,
            "tool_score_scale": "0-10",
            "clean_target": 10,
            "score_zero_means": "worst_many_findings_NOT_bonus",
            "event_snyk_bonus_up_to_plus_10_percent": "NOT_AWARDED",
            "entry_gate": req["entry_gate"]["entry_gate"],
        },
    }

    # Persist review package bytes + merkle over canonical review
    review_digest = digest_payload(review_body)
    review_body["artifact_digest"] = review_digest

    data = DataBackend(store, live=True)
    data_ref = data.write_breakpoint(
        breakpoint_id="SNEAK-018",
        merkle_root=review_digest,
        payload={
            "kind": "javier_score_setup_and_requirements_review",
            "pin_commit": UPSTREAM_COMMIT,
            "node_helper_match": pin.get("node_helper_match"),
            "entry_gate": req["entry_gate"]["entry_gate"],
            "live_snyk": avail.get("observed_outcome"),
            "application_score": None,
            "event_bonus": "NOT_AWARDED",
            "artifact_digest": review_digest,
        },
        wait_seconds=45.0,
    )

    # Hashed message for BAND agents to review
    message_record = {
        "id": "SNEAK-018-BAND-REVIEW-MSG",
        "kind": "agent_review_request",
        "artifact_digest": review_digest,
        "data_receipt": data_ref.external_id,
        "javier_commit": UPSTREAM_COMMIT,
        "python_node_score_match": pin.get("node_helper_match"),
        "entry_gate": req["entry_gate"]["entry_gate"],
        "live_snyk": avail.get("observed_outcome"),
        "application_score": None,
        "note": (
            "Please review: Javier app-security-score pinned; scale 0-10 where 10 is clean; "
            "event bonus up to +10% is separate and not awarded yet; live SCA/SAST blocked without SNYK_TOKEN; "
            "Cognee @Data holds this review package."
        ),
    }
    msg_leaf = leaf(message_record).hex()
    msg_root = root([leaf(message_record)]).hex()

    band = BandAdapter(store, live=True)
    band_ref = None
    if band.live_available:
        content = (
            f"SNEAK-018 REVIEW REQUEST for Claude(Tom) and ChatGPT(Jerry).\n"
            f"Merkle message leaf={msg_leaf}\n"
            f"Merkle message root={msg_root}\n"
            f"Review package digest={review_digest}\n"
            f"Javier pin={UPSTREAM_COMMIT} node_match={pin.get('node_helper_match')}\n"
            f"Tool score scale=0..10 (10=clean zero findings + full SCA/SAST). "
            f"Score 0 = worst (many findings), NOT the path to bonus marks.\n"
            f"Event Snyk bonus up to +10% = NOT_AWARDED until live scans.\n"
            f"Live Snyk={avail.get('observed_outcome')}; application_score=null; entry_gate={req['entry_gate']['entry_gate']}.\n"
            f"Cognee @Data receipt={data_ref.external_id}.\n"
            f"Please reply with: ACK leaf, whether you independently recompute leaf/root, "
            f"and any requirement gaps you see. Do not print secrets."
        )
        band_ref = band.message_claude_and_chatgpt(content)

    events = [
        {"id": "SNEAK-018-PIN", "kind": "javier_pin", "payload": {
            "commit": UPSTREAM_COMMIT,
            "commit_matches_pin": pin.get("commit_matches_pin"),
            "node_helper_match": pin.get("node_helper_match"),
            "python_zero": pin["python_helper"]["zero_findings"],
            "python_one_high": pin["python_helper"]["one_high"],
            "python_eleven_medium": pin["python_helper"]["eleven_medium"],
        }},
        {"id": "SNEAK-018-REQ", "kind": "requirements_review", "payload": req},
        {"id": "SNEAK-018-DATA", "kind": "cognee_data_update", "payload": {
            "receipt_id": data_ref.external_id,
            "digest": data_ref.artifact_digest,
            "observed": json.loads(Path(data_ref.receipt_path).read_text())["payload"].get("observed_outcome"),
        }},
        {"id": "SNEAK-018-HASHMSG", "kind": "band_hashed_review_message", "payload": {
            "message_leaf": msg_leaf,
            "message_root": msg_root,
            "review_digest": review_digest,
            "band_receipt": band_ref.external_id if band_ref else None,
            "band_outcome": (
                json.loads(Path(band_ref.receipt_path).read_text())["payload"].get("observed_outcome")
                if band_ref else "SKIPPED"
            ),
        }},
    ]
    bp = breakpoint_receipt(
        schema="sneak.score-setup-review.v1",
        breakpoint_id="SNEAK-018",
        parent_id="SNEAK-017B",
        records=events,
        meaning=(
            "Javier score pin + requirements review + @Data update + hashed BAND review request; "
            "not a live 10/10 claim or awarded event bonus"
        ),
    )
    bp["human_decision"] = "APPROVE_PATH_RECORDED"
    bp["application_score"] = None
    bp["event_snyk_bonus"] = "NOT_AWARDED"
    bp["review_digest"] = review_digest
    bp["message_leaf"] = msg_leaf
    bp["message_root"] = msg_root

    (out_dir / "SNEAK-018_SCORE_SETUP_REVIEW.json").write_text(
        json.dumps(bp, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "SNEAK-018_JAVIER_PIN.json").write_text(
        json.dumps(pin, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "SNEAK-018_SCORE_SETUP_REVIEW.md").write_text(
        "\n".join(
            [
                "# SNEAK-018 Javier app-security-score setup + requirements review",
                "",
                f"- Breakpoint root: `{bp['root']}`",
                f"- Review package digest: `{review_digest}`",
                f"- BAND hashed message leaf: `{msg_leaf}`",
                f"- BAND hashed message root: `{msg_root}`",
                f"- Javier pin: `{UPSTREAM_COMMIT}` match={pin.get('commit_matches_pin')} node_match={pin.get('node_helper_match')}",
                f"- Tool score scale: **0–10** (10 = clean; **0 = worst**, many findings)",
                f"- Event Snyk bonus: up to **+10%** → **NOT_AWARDED** (needs live SCA/SAST)",
                f"- Live Snyk: **{avail.get('observed_outcome')}** (SNYK_TOKEN missing)",
                f"- Application score: **null** (coverage incomplete — correctly rejected)",
                f"- AoK entry_gate: **{req['entry_gate']['entry_gate']}** "
                f"({req['entry_gate']['mandatory_verified']}/{req['entry_gate']['mandatory_count']})",
                f"- Cognee @Data: **{events[2]['payload']['observed']}** receipt `{data_ref.external_id}`",
                f"- BAND review request: **{events[3]['payload']['band_outcome']}**",
                "",
                "## Clarification",
                "Forcing tool score to 0 does **not** earn the extra ten marks. "
                "The bonus path is real Snyk integration + clean coverage toward **10/10**, "
                "and judges separately may award up to +10%.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    # Machine-readable requirements successor snapshot
    sneak018 = ROOT / "data/verification/requirements_sneak_018.jsonl"
    base = ROOT / "data/verification/requirements_sneak_014.jsonl"
    if not base.exists():
        base = ROOT / "data/verification/requirements_sneak_011.jsonl"
    lines = []
    for row in base.read_text().splitlines():
        if not row.strip():
            continue
        obj = json.loads(row)
        pred = obj.get("predecessor_requirement_id") or obj.get("id")
        lines.append(
            json.dumps(
                {
                    "id": f"{pred}-SNEAK-018" if "SNEAK-018" not in str(obj.get("id")) else obj["id"],
                    "predecessor_requirement_id": pred.split("-SNEAK-")[0] if "-SNEAK-" in str(pred) else pred,
                    "verified": False,
                    "observed_outcome": "NOT_TESTED",
                    "required_for_entry": str(pred).startswith("REQ-AOK-M") or str(obj.get("id", "")).startswith("REQ-AOK-M"),
                    "evidence": [
                        {
                            "provider": "sneak.review",
                            "external_id": "SNEAK-018",
                            "artifact_digest": review_digest,
                            "receipt_path": "receipts/connectors/SNEAK-018_SCORE_SETUP_REVIEW.json",
                            "observed_at": "review-script",
                        }
                    ],
                    "reason": (
                        "Javier score pinned and reviewed; live Snyk still NOT_TESTED without token; "
                        "BAND/Cognee path approved earlier; entry_gate remains false"
                    ),
                },
                sort_keys=True,
            )
        )
    sneak018.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "id": "SNEAK-018",
                "root": bp["root"],
                "review_digest": review_digest,
                "message_leaf": msg_leaf,
                "message_root": msg_root,
                "node_helper_match": pin.get("node_helper_match"),
                "commit_matches_pin": pin.get("commit_matches_pin"),
                "data_outcome": events[2]["payload"]["observed"],
                "band_outcome": events[3]["payload"]["band_outcome"],
                "application_score": None,
                "event_bonus": "NOT_AWARDED",
                "entry_gate": req["entry_gate"]["entry_gate"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
