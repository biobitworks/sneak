#!/usr/bin/env python3
"""Record this Claude red-team session (2026-10-20) as breakpoints so it can be joined at project end.

Requests are stored as Claude-written summaries, not the user's raw text: two raw messages
contained API keys, and secrets must never enter the ledger or the Cognee outbox.
Deliverables are `link` entries pointing at real PRs, commits, FCOs and receipts.
Idempotent: re-running adds nothing (identical identities).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from breakpoint_ledger import Ledger  # noqa: E402

CONV = "claude-session-01XKcMH77EYJTVYe5TzHa8M5"
EVENTS = [  # (kind, a, b, text/note)
    ("msg", "req-01", "byron (summary by claude-redteam)", "Use biobitworks/sneak with BAND as cross-talk; set up Tom & Jerry agents."),
    ("msg", "req-02", "byron (summary by claude-redteam)", "Act as independent red-team reviewer of Sneak; reproduce custody; successor branch and PR; no change to main."),
    ("link", "pr", "https://github.com/biobitworks/sneak/pull/4", "red-team review branch redteam/claude-20261020"),
    ("msg", "req-03", "byron (summary by claude-redteam)", "Run Flexprice self-hosted on magicstudio."),
    ("link", "receipt", "redteam/findings_SNEAK-013.jsonl#RT-27", "Flexprice v2.17 running; /health 200; F01-F05 NOT_TESTED"),
    ("msg", "req-04", "byron (summary by claude-redteam)", "Onboard a teammate; their work becomes FCOs with unique ids."),
    ("link", "pr", "https://github.com/biobitworks/sneak/pull/6", "teammate onboarding and contribution FCO tooling"),
    ("link", "fco", "FCO-8b904d2cf8f265d9", "onboarding kit"),
    ("msg", "req-05", "byron (summary by claude-redteam)", "Write a Merkle tree and MMR how-to and knowledge base for teammate review."),
    ("link", "pr", "https://github.com/biobitworks/sneak/pull/8", "Merkle/MMR knowledge base"),
    ("link", "fco", "FCO-cb3b6ef299f35553", "Merkle/MMR knowledge base"),
    ("msg", "req-06", "byron (summary by claude-redteam)", "Set up Javier app-security-score, review requirements, update Cognee, post a hashed message in BAND."),
    ("link", "commit", "97f09049fcc1ccf5fccef45a5dfd6c2af5724abb", "requirements review, Snyk scans, RT-29..RT-33"),
    ("link", "receipt", "redteam/BAND_MESSAGE_SNEAK-RT-CLAUDE-002.json", "hashed BAND message root 77090045..., body e25b3a09..."),
    ("msg", "req-07", "byron (summary by claude-redteam)", "Compare Cognee OSS raw upload vs SeedGraph-transformed LongMemEval (30 questions)."),
    ("msg", "req-08", "byron (summary by claude-redteam)", "Every step is a unique Merkle breakpoint: per-model MMR vs root question, true/false, hashed input/output, FCO tracking, BAND ask/respond, Cognee capture, planner in the loop."),
]


def main():
    L = Ledger()
    parent = None
    out = []
    for kind, a, b, text in EVENTS:
        if kind == "msg":
            row = L.message("chat", CONV, a, b, text, parent_bp=parent)
        else:
            row = L.link(a, b, parent_bp=parent, note=text)
        out.append((row["bp_id"], row["_new"], kind, a))
        parent = row["bp_id"]
    # Root question from the model run, if present, hangs off the latest request.
    roots = [r for r in L.rows if r["identity"]["kind"] == "root_question"]
    if roots:
        row = L.link("breakpoint", roots[-1]["bp_id"], parent_bp=parent, note="model breakpoint run for req-08")
        out.append((row["bp_id"], row["_new"], "link", "root"))
        parent = row["bp_id"]
        ask = L.ask_band(roots[-1]["bp_id"], "@planner",
                         "Planner: please confirm or replace the placeholder root question "
                         f"({roots[-1]['bp_id']}: mandatory atom count, answer rule \\b30\\b) and say how ROI 'value' should be counted.",
                         parent_bp=parent)
        out.append((ask["bp_id"], ask["_new"], "ask", "planner"))
    for o in out:
        print(*o)


if __name__ == "__main__":
    main()
