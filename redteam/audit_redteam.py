#!/usr/bin/env python3
"""Independent red-team audit of Sneak custody, AoK identity and LOMO graph ablation.

Deliberately does NOT import project code. Reads Git objects via `git archive`
(a different path from the project's `ls-tree`/`cat-file`), reimplements the
documented construction from its prose spec, and runs tamper cases against the
project's own Python and Node verifiers inside a disposable clone.

Writes only under redteam/out/. Never touches main, receipts/ or sources/.
"""
import hashlib, io, json, re, shutil, subprocess, sys, tarfile, tempfile, unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "redteam" / "out"
OUT.mkdir(parents=True, exist_ok=True)


def sh(args, cwd=REPO, check=True):
    p = subprocess.run(args, cwd=cwd, capture_output=True)
    if check and p.returncode:
        raise RuntimeError(f"{args}: {p.stderr.decode()[:400]}")
    return p


def canon(rec):
    return json.dumps(rec, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("ascii")


def sha(b):
    return hashlib.sha256(b).digest()


def merkle_root(leaves):
    level = list(leaves)
    while len(level) > 1:
        level = [sha(b"\x01" + level[i] + level[i + 1]) if i + 1 < len(level) else level[i]
                 for i in range(0, len(level), 2)]
    return level[0]


def records_from_archive(commit):
    raw = sh(["git", "archive", "--format=tar", commit]).stdout
    recs = []
    with tarfile.open(fileobj=io.BytesIO(raw)) as t:
        for m in t.getmembers():
            if m.isdir() or m.name == "pax_global_header":
                continue
            if not m.isfile():
                raise ValueError(f"non-regular member {m.name}")
            b = t.extractfile(m).read()
            recs.append({"path": m.name, "size_bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()})
    recs.sort(key=lambda r: r["path"].encode("utf-8"))
    return recs


def independent_snapshot(receipt_path):
    rc = json.loads((REPO / receipt_path).read_text())
    recs = records_from_archive(rc["snapshot_commit"])
    root = merkle_root([sha(b"\x00" + canon(r)) for r in recs]).hex()
    declared = [x["record"] for x in rc["leaves"]]
    ok = root == rc["root"] and recs == declared and len(recs) == rc["leaf_count"]
    return {"receipt": receipt_path, "snapshot_commit": rc["snapshot_commit"],
            "declared_root": rc["root"], "independent_root": root,
            "declared_leaf_count": rc["leaf_count"], "independent_leaf_count": len(recs),
            "records_identical": recs == declared, "state": "SUPPORTED" if ok else "FAILED"}


def run_verifiers(clone, receipt_rel):
    py = sh([sys.executable, "scripts/custody_snapshot.py", "verify", receipt_rel], cwd=clone, check=False)
    nd = sh(["node", "scripts/verify_custody_snapshot.mjs", receipt_rel], cwd=clone, check=False)
    return {"python_exit": py.returncode, "node_exit": nd.returncode,
            "python_out": py.stdout.decode()[-300:], "node_out": (nd.stdout + nd.stderr).decode()[-300:]}


def tamper_suite():
    base = "receipts/repository_bootstrap/SNAPSHOT.json"
    tmp = Path(tempfile.mkdtemp(prefix="sneak-rt-"))
    clone = tmp / "clone"
    sh(["git", "clone", "--quiet", "--no-hardlinks", str(REPO), str(clone)])
    head = sh(["git", "rev-parse", "HEAD"]).stdout.decode().strip()
    sh(["git", "checkout", "--quiet", head], cwd=clone)
    original = json.loads((clone / base).read_text())
    results = []

    def flip(h):
        return ("0" if h[0] != "0" else "1") + h[1:]

    def case(name, mutate_receipt=None, mutate_file=None, expect="REJECT"):
        sh(["git", "checkout", "--quiet", "--", "."], cwd=clone)
        rc = json.loads(json.dumps(original))
        if mutate_receipt:
            mutate_receipt(rc)
        rel = f"redteam_tamper_{name}.json"
        (clone / rel).write_text(json.dumps(rc))
        if mutate_file:
            mutate_file(clone)
        r = run_verifiers(clone, rel)
        (clone / rel).unlink()
        both_reject = r["python_exit"] != 0 and r["node_exit"] != 0
        both_accept = r["python_exit"] == 0 and r["node_exit"] == 0
        r.update({"case": name, "expected": expect,
                  "observed": "REJECT" if both_reject else ("ACCEPT" if both_accept else "SPLIT")})
        r["state"] = "SUPPORTED" if r["observed"] == expect else "FAILED"
        results.append(r)

    case("control_untampered", expect="ACCEPT")
    case("copied_file_byte", mutate_file=lambda c: (c / "AGENTS.md").write_bytes((c / "AGENTS.md").read_bytes() + b" "))
    case("leaf_hash", lambda rc: rc["leaves"][5].__setitem__("leaf", flip(rc["leaves"][5]["leaf"])))
    case("record_sha", lambda rc: rc["leaves"][5]["record"].__setitem__("sha256", flip(rc["leaves"][5]["record"]["sha256"])))
    case("root", lambda rc: rc.__setitem__("root", flip(rc["root"])))
    case("ordering_swap", lambda rc: rc["leaves"].__setitem__(slice(0, 2), [rc["leaves"][1], rc["leaves"][0]]))
    case("proof_direction", lambda rc: rc["leaves"][3]["proof"][0].__setitem__(
        "side", "left" if rc["leaves"][3]["proof"][0]["side"] == "right" else "right"))
    case("missing_manifest_member", lambda rc: (rc["leaves"].pop(7), rc.__setitem__("leaf_count", rc["leaf_count"] - 1)))
    case("snapshot_commit_swap", lambda rc: rc.__setitem__(
        "snapshot_commit", sh(["git", "rev-parse", "HEAD~1"], cwd=clone).stdout.decode().strip()))
    # Probe whether the verifier binds metadata outside the compared key set.
    case("claim_signed_true", lambda rc: rc.__setitem__("signed", True))
    case("claim_mmr_committed", lambda rc: rc.__setitem__("mmr", "COMMITTED"))
    case("rewrite_meaning", lambda rc: rc.__setitem__("meaning", "Certified source truth and security"))
    shutil.rmtree(tmp, ignore_errors=True)
    return results


def norm(s):
    s = unicodedata.normalize("NFKC", s).replace("\u200b", "")
    return re.sub(r"\s+", " ", s).strip()


def aok_audit():
    atoms = [json.loads(l) for l in (REPO / "data/rules/atomic_acceptance_r5.jsonl").read_text().splitlines() if l.strip()]
    excerpt_raw = (REPO / "sources/user_rules_excerpt_20261020.txt").read_bytes()
    excerpt = excerpt_raw.decode("utf-8")
    pdf_sha = hashlib.sha256((REPO / "sources/challenge.pdf").read_bytes()).hexdigest()
    pages = {}
    for line in (REPO / "sources/independent_extraction_pages.jsonl").read_text().splitlines():
        if line.strip():
            d = json.loads(line)
            pages[d.get("page_1based") or d.get("page")] = d.get("text", "")
    fcg = json.loads((REPO / "data/rules/atomic_fcg_r5.json").read_text())
    nodes = {n["id"]: n for n in fcg["nodes"]}
    edges = {e["from"]: e for e in fcg["edges"]}
    rows, groups = [], {}
    for a in atoms:
        o, q = a["occurrence"], a["source_quote"]
        hits = [m.start() for m in re.finditer(re.escape(q), excerpt)]
        stripped = {k: v for k, v in a.items() if k != "fco_candidate_sha256"}
        pages_with = [p for p, t in pages.items() if norm(q) in norm(t)]
        rows.append({
            "id": a["id"], "level": a["level"],
            "content_ok": hashlib.sha256(q.encode()).hexdigest() == a["content_sha256"],
            "context_ok": hashlib.sha256(canon(o)).hexdigest() == a["context_sha256"],
            "fco_ok": hashlib.sha256(canon(stripped)).hexdigest() == a["fco_candidate_sha256"],
            "offsets_ok": excerpt[o["start_codepoint"]:o["end_codepoint"]] == q,
            "excerpt_hash_ok": hashlib.sha256(excerpt_raw).hexdigest() == o["source_sha256"],
            "pdf_hash_matches_file": o["pdf_sha256"] == pdf_sha,
            "quote_occurrences_in_excerpt": len(hits), "start_is_first_hit": bool(hits) and hits[0] == o["start_codepoint"],
            "declared_pdf_page": o["pdf_page"], "pdf_pages_containing_quote": pages_with,
            "pdf_page_supported": o["pdf_page"] in pages_with,
            "fcg_node_identity_ok": nodes.get(a["id"], {}).get("identity") == a["fco_candidate_sha256"],
            "fcg_edge_context_ok": edges.get(a["id"], {}).get("context") == a["context_sha256"],
            "fcg_edge_target_is_pdf": edges.get(a["id"], {}).get("to") == pdf_sha,
            "fco_hash_covers_mutable_status": all(k in stripped for k in ("verified", "pass_gate", "observed_outcome", "evidence")),
        })
        groups.setdefault(q, []).append(a["id"])
    return rows, {q: ids for q, ids in groups.items() if len(ids) > 1}, fcg, sorted(pages)


COMPONENT_FIELDS = {
    "source-atom": ["source_quote", "content_sha256"],
    "occurrence-context": ["occurrence", "context_sha256"],
    "rights-binding": ["rights"],
    "policy-binding": ["verifier_policy"],
    "scan-receipt": ["scan_receipt"],
    "memory-reference": ["memory_reference"],
    "authorization-receipt": ["authorization_receipt"],
    "parent-breakpoint": ["parent", "predecessor_requirement_id"],
}


def lomo():
    atoms = [json.loads(l) for l in (REPO / "data/rules/atomic_acceptance_r5.jsonl").read_text().splitlines() if l.strip()]
    matrix = [json.loads(l) for l in (REPO / "data/lomo/actor_component_matrix.jsonl").read_text().splitlines() if l.strip()]

    def root(rs):
        return merkle_root([sha(b"\x00" + canon(r)) for r in rs]).hex()

    base = root(atoms)
    out = []
    for comp, fields in COMPONENT_FIELDS.items():
        present = sorted({f for a in atoms for f in fields if f in a})
        r = root([{k: v for k, v in a.items() if k not in fields} for a in atoms])
        out.append({"removed_component": comp, "fields_probed": fields, "fields_present_in_graph": present,
                    "graph_root_baseline": base, "graph_root_ablated": r, "graph_changed": r != base,
                    "graph_state": "EXECUTED" if present else "NOT_TESTED",
                    "graph_note": None if present else "Component absent from AoK graph; removal is a no-op and tests nothing.",
                    "runtime_behavior": "NOT_TESTED",
                    "runtime_note": "No app, agent action or authorization gate exists to observe; a graph change is not runtime evidence.",
                    "matrix_rows_for_component": sum(1 for m in matrix if m["removed_component"] == comp)})
    return out, len(matrix), sorted({m["actor"] for m in matrix})


def main():
    head = sh(["git", "rev-parse", "HEAD"]).stdout.decode().strip()
    env = {"python": sys.version.split()[0], "node": sh(["node", "--version"]).stdout.decode().strip(),
           "git": sh(["git", "--version"]).stdout.decode().strip(), "audited_head": head}
    snaps = [independent_snapshot("receipts/repository_bootstrap/SNAPSHOT.json"),
             independent_snapshot("receipts/repository_bootstrap/SNAPSHOT_MERGED.json")]
    tampers = tamper_suite()
    rows, shared, fcg, pages = aok_audit()
    lrows, nmatrix, actors = lomo()
    agg = {k: sum(1 for r in rows if r[k]) for k in
           ("content_ok", "context_ok", "fco_ok", "offsets_ok", "excerpt_hash_ok", "pdf_hash_matches_file",
            "start_is_first_hit", "pdf_page_supported", "fcg_node_identity_ok", "fcg_edge_context_ok",
            "fcg_edge_target_is_pdf", "fco_hash_covers_mutable_status")}
    result = {"env": env, "snapshots": snaps, "tamper": tampers,
              "aok": {"atoms": len(rows), "true_counts": agg, "shared_quote_groups": shared,
                      "ambiguous_quotes": [(r["id"], r["quote_occurrences_in_excerpt"]) for r in rows if r["quote_occurrences_in_excerpt"] > 1],
                      "page_unsupported": [(r["id"], r["declared_pdf_page"], r["pdf_pages_containing_quote"]) for r in rows if not r["pdf_page_supported"]],
                      "extraction_pages": pages, "fcg_nodes": len(fcg["nodes"]), "fcg_edges": len(fcg["edges"]),
                      "fcg_edge_targets": sorted({e["to"] for e in fcg["edges"]})},
              "lomo": {"matrix_rows": nmatrix, "actors": actors, "graph_ablations": lrows}}
    (OUT / "audit_result.json").write_text(json.dumps(result, indent=2) + "\n")
    with (OUT / "aok_identity.jsonl").open("w") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    print(json.dumps({"env": env, "snapshots": [(s["receipt"][-22:], s["state"], s["independent_root"][:16]) for s in snaps],
                      "tamper": [(t["case"], t["expected"], t["observed"], t["state"]) for t in tampers],
                      "aok": agg, "shared": shared, "ambiguous": result["aok"]["ambiguous_quotes"],
                      "page_unsupported": result["aok"]["page_unsupported"], "pages": pages,
                      "lomo": [(l["removed_component"], l["graph_state"], l["graph_changed"]) for l in lrows]}, indent=1))


if __name__ == "__main__":
    main()
