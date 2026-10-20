#!/usr/bin/env python3
"""Sneak breakpoint ledger: unique Merkle breakpoints for every question, step, message and link.

Every entry is a breakpoint (BP) with an immutable identity:
    bp_sha256 = SHA256(canonical(identity));  bp_id = "BP-" + bp_sha256[:16]
Identity always includes the parent breakpoint and, for messages, the source message id,
so the same text sent twice in different places gets two different breakpoints.

Kinds
  root_question  question, answer rule (regex), context sha256           -> the thing everything is compared to
  step           stream (model), round, step name, script sha256,
                 input sha256, output sha256, breakpoint (bool)            -> deterministic script step
  message        channel (band|chat|cognee|cli), conversation, source
                 message id, speaker, content sha256                       -> any conversation turn
  link           target type (commit|pr|fco|receipt), target id           -> ties outside artifacts in

Commitments (recomputed by `verify`)
  - global MMR over every entry in append order (one root for the whole project)
  - one MMR per stream (each model, each conversation)
  MMR construction = scripts/mmr_reference.py (SHA-256, 0-based positions, position-committed,
  size-committed bagging). Leaf data = canonical identity bytes.

Outboxes (append-only, sent later by connectors): data/breakpoints/outbox/{band,cognee,flexprice}.jsonl
Each outbox item names the bp_id it reports, so provider-side records can be joined back.

The ledger is append-only. Never edit or delete a line; correct with a new entry whose parent
is the entry being corrected.
"""
import argparse, datetime, hashlib, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import mmr_reference as M  # noqa: E402

LEDGER = ROOT / "data/breakpoints/ledger.jsonl"
OUTBOX = ROOT / "data/breakpoints/outbox"
SCHEMA = "sneak.breakpoint.v1"
KINDS = {"root_question", "step", "message", "link"}
CHANNELS = {"band", "chat", "cognee", "cli", "github"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def canon(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("ascii")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def bp_of(identity):
    h = sha(canon(identity))
    return "BP-" + h[:16], h


class Ledger:
    def __init__(self, path=LEDGER, outbox=OUTBOX):
        self.path, self.outbox = Path(path), Path(outbox)
        self.rows = [json.loads(l) for l in self.path.read_text().splitlines() if l.strip()] if self.path.exists() else []
        self.ids = {r["bp_id"]: r for r in self.rows}
        self.global_mmr, self.streams = M.MMR(), {}
        for r in self.rows:
            self._commit(r["identity"], r["stream"])

    # ---- commitments ----
    def _commit(self, identity, stream):
        leaf = canon(identity)
        self.global_mmr.append(leaf)
        self.streams.setdefault(stream, M.MMR()).append(leaf)
        s = self.streams[stream]
        return {"global_size": self.global_mmr.size, "global_root": self.global_mmr.root().hex(),
                "stream_size": s.size, "stream_root": s.root().hex()}

    def _append(self, identity, stream, extra=None):
        identity = {**identity, "stream": stream}   # stream is part of identity: same step in two streams = two BPs
        if identity["kind"] not in KINDS:
            raise ValueError(f"unknown kind {identity['kind']}")
        parent = identity.get("parent_bp")
        if parent is not None and parent not in self.ids:
            raise ValueError(f"parent {parent} not in ledger")
        root_bp = identity.get("root_bp")
        if root_bp is not None and (root_bp not in self.ids or self.ids[root_bp]["identity"]["kind"] != "root_question"):
            raise ValueError(f"root_bp {root_bp} is not a root_question in the ledger")
        bp_id, h = bp_of(identity)
        if bp_id in self.ids:            # identical identity: idempotent, nothing appended or re-sent
            return {**self.ids[bp_id], "_new": False}
        row = {"bp_id": bp_id, "bp_sha256": h, "stream": stream, "identity": identity,
               "commitment": self._commit(identity, stream), "recorded_at": now(), **(extra or {})}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as f:
            f.write(canon(row).decode() + "\n")
        self.rows.append(row); self.ids[bp_id] = row
        return {**row, "_new": True}

    def emit(self, box, payload):
        self.outbox.mkdir(parents=True, exist_ok=True)
        with (self.outbox / f"{box}.jsonl").open("a") as f:
            f.write(canon({**payload, "status": "PENDING_SEND", "queued_at": now()}).decode() + "\n")

    # ---- entry types ----
    def root_question(self, question, answer_regex, context_sha256, parent_bp=None, label=""):
        re.compile(answer_regex)
        if not HEX64.match(context_sha256):
            raise ValueError("context_sha256 must be 64 hex chars")
        ident = {"schema": SCHEMA, "kind": "root_question", "question": question, "answer_regex": answer_regex,
                 "context_sha256": context_sha256, "label": label, "parent_bp": parent_bp}
        row = self._append(ident, "root")
        if row["_new"]:
            self.emit("cognee", {"bp_id": row["bp_id"], "kind": "root_question", "text": f"Root question {row['bp_id']}: {question}"})
        return row

    def step(self, root_bp, stream, round_no, step_name, script_sha256, input_sha256, output_sha256,
             output_text=None, parent_bp=None, tokens=None, model=None):
        for v in (script_sha256, input_sha256, output_sha256):
            if not HEX64.match(v):
                raise ValueError("hashes must be 64 hex chars")
        if root_bp not in self.ids or self.ids[root_bp]["identity"]["kind"] != "root_question":
            raise ValueError(f"root_bp {root_bp} is not a root_question in the ledger")
        rq = self.ids[root_bp]["identity"]
        brk = None
        if output_text is not None:
            if sha(output_text.encode("utf-8")) != output_sha256:
                raise ValueError("output_text does not match output_sha256")
            brk = bool(re.search(rq["answer_regex"], output_text, re.I))
        ident = {"schema": SCHEMA, "kind": "step", "root_bp": root_bp, "parent_bp": parent_bp, "model": model,
                 "round": round_no, "step": step_name, "script_sha256": script_sha256,
                 "input_sha256": input_sha256, "output_sha256": output_sha256, "breakpoint": brk}
        row = self._append(ident, stream, {"tokens": tokens} if tokens else None)
        if not row["_new"]:
            return row
        if tokens:
            self.emit("flexprice", {"bp_id": row["bp_id"], "event_name": "llm_tokens", "external_customer_id": stream,
                                    "properties": {**tokens, "model": model, "round": round_no, "root_bp": root_bp}})
        if brk is not None:
            self.emit("cognee", {"bp_id": row["bp_id"], "kind": "breakpoint",
                                 "text": f"{stream} round {round_no} {step_name}: breakpoint={brk} for root {root_bp}"})
        return row

    def message(self, channel, conversation, source_id, speaker, content, parent_bp=None, root_bp=None):
        if channel not in CHANNELS:
            raise ValueError(f"channel must be one of {sorted(CHANNELS)}")
        ident = {"schema": SCHEMA, "kind": "message", "channel": channel, "conversation": conversation,
                 "source_id": source_id, "speaker": speaker, "content_sha256": sha(content.encode("utf-8")),
                 "parent_bp": parent_bp, "root_bp": root_bp}
        row = self._append(ident, f"conv:{conversation}")
        if row["_new"]:
            self.emit("cognee", {"bp_id": row["bp_id"], "kind": "message", "speaker": speaker, "text": content})
        return row

    def link(self, target_type, target_id, parent_bp=None, note=""):
        ident = {"schema": SCHEMA, "kind": "link", "target_type": target_type, "target_id": target_id,
                 "note": note, "parent_bp": parent_bp}
        return self._append(ident, "links")

    def ask_band(self, root_bp, to, question, parent_bp=None):
        """Queue a BAND question; the human/agent reply is recorded later as a `message` whose parent is this ask."""
        row = self.message("cli", "band-outbox", f"ask:{sha(question.encode())[:12]}:{parent_bp}", "planner", question, parent_bp, root_bp)
        if row["_new"]:
            self.emit("band", {"bp_id": row["bp_id"], "to": to,
                           "text": f"{question}\n[breakpoint {row['bp_id']}] Reply referencing this id."})
        return row

    # ---- analysis ----
    def deltas(self, root_bp):
        out = {}
        for r in self.rows:
            i = r["identity"]
            if i["kind"] == "step" and i["root_bp"] == root_bp:
                out.setdefault(r["stream"], []).append(
                    {"round": i["round"], "step": i["step"], "breakpoint": i["breakpoint"], "bp_id": r["bp_id"],
                     "output_sha256": i["output_sha256"][:16], "stream_root": r["commitment"]["stream_root"][:16]})
        for seq in out.values():
            prev = {}                      # compare like with like: same step name, previous round
            for s in seq:
                if s["breakpoint"] is not None:
                    p = prev.get(s["step"])
                    s["delta"] = "FIRST" if p is None else ("SAME" if s["breakpoint"] == p else ("TURNED_TRUE" if s["breakpoint"] else "TURNED_FALSE"))
                    prev[s["step"]] = s["breakpoint"]
        return out


def verify(path=LEDGER):
    rows = [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]
    errors, seen, g, streams = [], set(), M.MMR(), {}
    for n, r in enumerate(rows, 1):
        bp_id, h = bp_of(r["identity"])
        if (bp_id, h) != (r["bp_id"], r["bp_sha256"]):
            errors.append(f"line {n}: identity does not recompute")
        if r["identity"].get("stream") != r["stream"]:
            errors.append(f"line {n}: stream differs from identity")
        if r["bp_id"] in seen:
            errors.append(f"line {n}: duplicate {r['bp_id']}")
        p = r["identity"].get("parent_bp")
        if p is not None and p not in seen:
            errors.append(f"line {n}: parent {p} not earlier in ledger")
        leaf = canon(r["identity"]); g.append(leaf)
        s = streams.setdefault(r["stream"], M.MMR()); s.append(leaf)
        exp = {"global_size": g.size, "global_root": g.root().hex(), "stream_size": s.size, "stream_root": s.root().hex()}
        if r["commitment"] != exp:
            errors.append(f"line {n}: MMR commitment differs")
        seen.add(r["bp_id"])
    return {"pass": not errors, "entries": len(rows), "streams": {k: v.size for k, v in streams.items()},
            "global_root": g.root().hex() if rows else None, "errors": errors}


def main():
    ap = argparse.ArgumentParser(description="Sneak breakpoint ledger")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("verify")
    d = sub.add_parser("deltas"); d.add_argument("--root", required=True)
    m = sub.add_parser("message")
    for a in ("--channel", "--conversation", "--source-id", "--speaker", "--text"):
        m.add_argument(a, required=True)
    m.add_argument("--parent"); m.add_argument("--root")
    k = sub.add_parser("link")
    k.add_argument("--type", required=True); k.add_argument("--id", required=True)
    k.add_argument("--parent"); k.add_argument("--note", default="")
    a = ap.parse_args()
    if a.cmd == "verify":
        r = verify(); print(json.dumps(r, indent=1)); sys.exit(0 if r["pass"] else 1)
    L = Ledger()
    if a.cmd == "deltas":
        print(json.dumps(L.deltas(a.root), indent=1))
    elif a.cmd == "message":
        print(L.message(a.channel, a.conversation, a.source_id, a.speaker, a.text, a.parent, a.root)["bp_id"])
    elif a.cmd == "link":
        print(L.link(a.type, a.id, a.parent, a.note)["bp_id"])


if __name__ == "__main__":
    main()
