#!/usr/bin/env python3
"""Build or verify the hashed red-team review message for the BAND room.

Artifacts are read from Git at a fixed commit and committed with Sneak's custody
construction: leaf = SHA256(0x00 || canonical{path,size_bytes,sha256}),
node = SHA256(0x01 || L || R), odd node promoted, records sorted by UTF-8 path.
The message body hash is SHA-256 over the exact UTF-8 body (everything before the
final 'body-sha256:' line).

  python3 redteam/band_message.py build   # writes BAND_MESSAGE_<ID>.txt/.json
  python3 redteam/band_message.py verify  # recomputes root and body hash from Git
"""
import hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MSG_ID = "SNEAK-RT-CLAUDE-002"
COMMIT = "97f09049fcc1ccf5fccef45a5dfd6c2af5724abb"
ARTIFACTS = [
    "redteam/REQUIREMENTS_REVIEW.md",
    "redteam/cognee_updates_SNEAK-RT-CLAUDE-002.jsonl",
    "redteam/findings_SNEAK-013.jsonl",
    "redteam/requirements_review.jsonl",
    "redteam/requirements_review.py",
    "redteam/requirements_review_summary.json",
]
TXT = ROOT / f"redteam/BAND_MESSAGE_{MSG_ID}.txt"
JSN = ROOT / f"redteam/BAND_MESSAGE_{MSG_ID}.json"
H = lambda b: hashlib.sha256(b).digest()
canon = lambda x: json.dumps(x, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("ascii")


def records():
    out = []
    for p in ARTIFACTS:
        b = subprocess.check_output(["git", "-C", str(ROOT), "show", f"{COMMIT}:{p}"])
        out.append({"path": p, "size_bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()})
    return sorted(out, key=lambda r: r["path"].encode("utf-8"))


def root(recs):
    lvl = [H(b"\x00" + canon(r)) for r in recs]
    while len(lvl) > 1:
        lvl = [H(b"\x01" + lvl[i] + lvl[i + 1]) if i + 1 < len(lvl) else lvl[i] for i in range(0, len(lvl), 2)]
    return lvl[0].hex()


def body(recs, r):
    s = json.loads(subprocess.check_output(["git", "-C", str(ROOT), "show", f"{COMMIT}:redteam/requirements_review_summary.json"]))
    return "\n".join([
        f"[{MSG_ID}] Red-team review update from Claude (posted by Byron). Information for review, NOT a human approval.",
        f"Commit: biobitworks/sneak@{COMMIT} (branch redteam/claude-20261020, PR #4)",
        f"Artifacts Merkle root ({len(recs)} leaves, Sneak custody construction): {r}",
        f"Requirements: mandatory SUPPORTED {s['mandatory_supported']}/{s['mandatory_total']} (M03 M04 M10 M11 M12, receipt-level). Entry gate FALSE. Security app score NOT_COMPUTED.",
        "RT-30 HIGH: PR #5 hard-codes human_decision=APPROVE; M13-M15 stay NOT_TESTED until Byron replies to SNEAK-H01 here.",
        "RT-33: Jerry runs the Claude SDK adapter; ChatGPT authorship of Jerry messages is UNKNOWN. Use one BAND identity per harness.",
        "RT-29: Snyk Code finds 4 low path-traversal notes in custody verifiers on main; PR #4/#6/#8 add none. SCA never completed.",
        "RT-32: Javier scorer pinned at 6e1f276, not run (no SNYK_TOKEN PAT). 10/10 = zero findings.",
        "@Tom @Jerry please verify with: git fetch && python3 redteam/band_message.py verify",
        "Reply 'VERIFIED <root-prefix>' or 'DISPUTE <RT-id> <reason>'. Do not claim any requirement from this message.",
    ])


def build():
    recs = records(); r = root(recs); b = body(recs, r)
    bh = hashlib.sha256(b.encode("utf-8")).hexdigest()
    TXT.write_text(b + f"\nbody-sha256: {bh}\n")
    JSN.write_text(json.dumps({"id": MSG_ID, "commit": COMMIT, "artifacts": recs, "artifacts_root": r,
                               "body_sha256": bh, "posted_to_band": "NOT_EXECUTED",
                               "note": "To be pasted by the human into the BAND room; a paste is not an approval."}, indent=2) + "\n")
    print(json.dumps({"artifacts_root": r, "body_sha256": bh, "leaves": len(recs)}))


def verify():
    recs = records(); r = root(recs)
    saved = json.loads(JSN.read_text())
    lines = TXT.read_text().rstrip("\n").split("\n")
    b, claimed = "\n".join(lines[:-1]), lines[-1].split(": ", 1)[1]
    ok = {"artifacts_match": recs == saved["artifacts"], "root_match": r == saved["artifacts_root"],
          "root_in_message": r in b, "body_hash_match": hashlib.sha256(b.encode("utf-8")).hexdigest() == claimed == saved["body_sha256"]}
    print(json.dumps({"root": r, **ok, "pass": all(ok.values())}, indent=1))
    sys.exit(0 if all(ok.values()) else 1)


if __name__ == "__main__":
    {"build": build, "verify": verify}[sys.argv[1] if len(sys.argv) > 1 else "verify"]()
