#!/usr/bin/env python3
"""One-shot, receipt-guarded Cognee @Data and BAND agent review handoff.

Requires explicit operator-authorized credentials in process environment.
Never prints or persists credential values. Never retries a partial delivery.
"""
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from subprocess import check_output

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.band_client import BandClient
from sneak.cognee_client import CogneeClient
from sneak.fcg_registry import FCGRegistry
from sneak.merkle import canonical
from sneak.secrets import export_to_environ

COMMIT = "4018d660cc090493b206b2ecd9c8ddc922f8751f"
OLD_ROOT = "089e49c083f1d6170402a366cfa76f3b939cbdcefce262ff39a732061463dadc"
LEDGER = ROOT / "data/fcg/sneak-016-replay.jsonl"
RECEIPT = ROOT / "receipts/connectors/SNEAK-018_R15_LIVE_REVIEW.json"
INTENT = ROOT / "local-runs/sneak-r15-publish-intent.json"


def main() -> None:
    export_to_environ()
    if RECEIPT.exists() or INTENT.exists():
        raise SystemExit("prior publish intent or receipt exists: inspect before any retry")
    assert check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip() == COMMIT
    registry = FCGRegistry(LEDGER)
    start = registry.verify()
    if start["mmr_root"] != OLD_ROOT or start["fco_count"] != 55:
        raise SystemExit("source commit's expected MMR predecessor not verified")
    if not os.getenv("COGNEE_BASE_URL") or not os.getenv("COGNEE_API_KEY"):
        raise SystemExit("Cognee credentials missing; no provider effects")
    bkey = os.getenv("BAND_USER_API_KEY") or os.getenv("BAND_API_KEY")
    if not bkey:
        raise SystemExit("BAND credentials missing; no provider effects")
    cognee = CogneeClient(dataset="Data")
    band = BandClient(api_key=bkey)
    if not (cognee.available and band.available and cognee.health().get("live") and band.me().get("ok")):
        raise SystemExit("provider authentication/health preflight failed; no provider effects")

    core = {
        "schema": "sneak.r15-review-message.v1",
        "repo": "biobitworks/sneak",
        "branch": "integration/sneak-audit-fco-20261020",
        "commit": COMMIT,
        "parent_commit": "ba1ba7925137855792fed76d4f7a377fc689b1d2",
        "source_merkle": "72e7a22ae6e2e46be6b09f60af3f5efb13603fd84a4dee08b8706fd11543f6ae",
        "successor_mmr_root": OLD_ROOT,
        "mmr_leaves": 55,
        "mmr_nodes": 105,
        "fcg_edges": 64,
        "tests": {"python": "PASS_82", "jupyter": "PASS_4", "node": "PASS"},
        "security": {
            "snyk_cli": "1.1307.2",
            "sast": "7 findings; exit 1",
            "sca": "FAILED dependency resolution; exit 2",
            "javier_application_score": None,
            "security_gate": "DENY",
            "event_bonus": "NOT_VERIFIED",
        },
        "agent_requests": {
            "Tom/Claude": "Independently review FCO/MMR identity, tampering, predecessor linkage, and Snyk source-to-sink findings. Respond in BAND with findings.",
            "Jerry/ChatGPT": "Verify BAND/Cognee receipts, requirements coverage, score NULL treatment, and scoped teammate handoff; never self-award review.",
        },
        "approval_scope": "BAND communication and Cognee @Data storage were operator-approved; no release/security approval implied.",
    }
    exact = canonical(core)
    digest = hashlib.sha256(exact).hexdigest()
    message = (
        "SNEAK R15 evidence review requested. sha256(canonical payload)=" + digest
        + " ; commit=" + COMMIT
        + " ; FCG/MMR root=" + OLD_ROOT
        + " ; Snyk 7 SAST findings and SCA FAILED; app score NULL; deny admission. "
        + "Tom: audit identity/MMR and Snyk. Jerry: audit Cognee/BAND/requirements. "
        + "Payload=" + exact.decode("ascii")
    )
    INTENT.parent.mkdir(parents=True, exist_ok=True)
    INTENT.write_text(json.dumps({"payload_sha256": digest, "commit": COMMIT, "state": "PUBLISH_ATTEMPT_STARTED"}) + "\n")

    packet = json.dumps({"message_sha256": digest, "content": core}, sort_keys=True, separators=(",", ":"))
    add = {"ok": False}
    cognify = {"ok": False}
    exact_recall = False
    recall_hits = 0
    band_result = {"ok": False}
    errors = []
    try:
        add = cognee.add_text([packet], dataset="Data")
        if add.get("ok"):
            cognify = cognee.cognify(dataset="Data")
        if cognify.get("ok"):
            for attempt in range(8):
                search = cognee.search(digest, dataset="Data", search_type="CHUNKS")
                recall_hits = len(search.get("hits") or [])
                if any(digest in str(hit.get("text", "")) for hit in search.get("hits") or []):
                    exact_recall = True
                    break
                if attempt < 7:
                    time.sleep(2)
    except Exception as exc:
        errors.append("cognee:" + type(exc).__name__)
    try:
        band_result = band.send_mention(
            message + " ; @Data add=" + str(bool(add.get("ok")))
            + " cognify=" + str(bool(cognify.get("ok")))
            + " exact_recall=" + str(exact_recall),
            ["claude", "chatgpt"],
        )
    except Exception as exc:
        errors.append("band:" + type(exc).__name__)

    # Capture the remote API status as evidence; authentication is not an agent acknowledgment.
    evidence = {
        "schema": "sneak.r15-live-review-receipt.v1",
        "parent_commit": COMMIT,
        "predecessor_mmr_root": OLD_ROOT,
        "payload": core,
        "payload_sha256": digest,
        "cognee": {
            "dataset": "Data",
            "add_status": add.get("http_status"),
            "add_ok": bool(add.get("ok")),
            "cognify_status": cognify.get("http_status"),
            "cognify_ok": bool(cognify.get("ok")),
            "recall_hits": recall_hits,
            "exact_digest_recall": exact_recall,
        },
        "band": {
            "room_id": band_result.get("room_id"),
            "post_status": band_result.get("http_status"),
            "post_ok": bool(band_result.get("ok")),
            "message_id": (band_result.get("message") or {}).get("id"),
            "recipients": band_result.get("recipients"),
            "agent_acknowledgment": "NOT_OBSERVED",
        },
        "errors": errors,
    }
    if not add.get("ok"):
        errors.append("Cognee write did not succeed")
    if not band_result.get("ok"):
        errors.append("BAND delivery did not succeed")
    # Every new provider result is another contextual FCO, not an assertion of remote correctness.
    anchor = registry.rows()[0]["fco_id"]
    reg_state = "OBSERVED" if add.get("ok") and cognify.get("ok") else "FAILED"
    registry.append(
        kind="memory",
        actor_fco=anchor,
        parent_fco=registry.rows()[-1]["fco_id"],
        payload={"alias": "@Data", "dataset": "Data", "payload_sha256": digest,
                 "add_ok": bool(add.get("ok")), "cognify_ok": bool(cognify.get("ok")),
                 "exact_recall": exact_recall},
        state=reg_state, source_sha256=digest,
        context={"source_commit": COMMIT, "remote": "cognee", "rights": "private_repo_hold"},
    )
    registry.append(
        kind="handoff", actor_fco=anchor, parent_fco=registry.rows()[-1]["fco_id"],
        payload={"payload_sha256": digest, "band_post_ok": bool(band_result.get("ok")),
                 "message_id": (band_result.get("message") or {}).get("id"),
                 "recipients": ["claude", "chatgpt"], "acknowledgment": "NOT_OBSERVED"},
        state="OBSERVED" if band_result.get("ok") else "FAILED", source_sha256=digest,
        context={"source_commit": COMMIT, "remote": "band", "rights": "private_repo_hold"},
    )
    evidence["successor_fcg_mmr"] = registry.verify()
    evidence["last_fco_inclusion"] = registry.inclusion_proof(registry.rows()[-1]["fco_id"])["verified"]
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "payload_sha256": digest,
        "cognee_add": bool(add.get("ok")),
        "cognee_cognify": bool(cognify.get("ok")),
        "cognee_exact_recall": exact_recall,
        "band_post": bool(band_result.get("ok")),
        "band_message_id": evidence["band"]["message_id"],
        "successor_mmr": evidence["successor_fcg_mmr"],
        "errors": errors,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
