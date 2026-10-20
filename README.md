# SNEAK — So Now Every Agent Knows

Private MVP candidate: evidence-governed security and working-memory graph using BAND Desktop, Cognee OSS, Snyk, and optional Flexprice. Main page is the graph; technical acceptance is under /audit. Release remains BLOCKED until human-approved BAND collaboration and current scan evidence.

Local run on magicPRObox: python3 -m apps.sneak_mvp.server --port 8773. Browse http://127.0.0.1:8773/ on that machine. Read-only APIs: /api/graph, /api/audit, /api/stack, /api/check. The server binds loopback and does not accept writes or grant security approvals.

Run tests: PYTHONPATH=src:apps/security-demo/src:. python3 -m unittest discover -s tests -p 'test_*.py' -v, and node --test tests/test_verify_custody_snapshot.mjs. Verify import bytes: python3 scripts/prepare_sneak_consolidation.py verify.

See .planning/SNEAK_CONSOLIDATION_20261020.md and receipts/sneak_mvp/TEAMMATE_IMPORT_20261020.json for provenance. The predecessor and teammate branches are preserved. No canonical MMR or signature is claimed.

---

# Skill Custody Lab

Private requirements-first intake for skill/MCP/CLI security, source transformations, LOMO and independently recomputable custody.

Start with:
- [.planning/PROJECT.md](.planning/PROJECT.md)
- [.planning/REQUIREMENTS.md](.planning/REQUIREMENTS.md)
- [Every extracted rule atom](docs/RULE_ATOM_REVIEW.md)
- [Models and environments](docs/MODELS_AND_ENVIRONMENTS.md)
- [Experiment protocol](docs/EXPERIMENT_PROTOCOL.md)
- [Security boundaries and standards](docs/SECURITY_AND_STANDARDS.md)
- [Implementation plan](docs/IMPLEMENTATION_PLAN.md)
- [Claude Code red-team handoff](docs/CLAUDE_CODE_REDTEAM.md)
- [Replication notebook](notebooks/01_intake_recompute.ipynb)
- [Computed candidate custody](receipts/INTAKE_MERKLE.json)

Status: requirements/data preparation only. Application, BAND/Cognee integration, model runs, VM experiments and Snyk scans NOT_EXECUTED.
Source PDF bytes verified against predecessor. Merkle receipt is candidate project intake custody, not canonical Overwatch admission or an MMR.
Licensing (preferred split): original software **Apache-2.0**; original docs/narrative **CC BY-NC-ND 4.0** (most restrictive CC). See [`LICENSE`](LICENSE), [`LICENSING.md`](LICENSING.md), and [`NOTICE`](NOTICE). No blanket third-party license; upstream and inherited sources retain their rights. Public release of inherited research IP remains **HOLD**. Merge of the licensing lane is deferred until after the hackathon unless an operator merges earlier.

R5 successor: [.planning/ATOMIC_ACCEPTANCE_R5.md](.planning/ATOMIC_ACCEPTANCE_R5.md), [machine-readable atoms](data/rules/atomic_acceptance_r5.jsonl), [replication notebook](notebooks/02_atomic_requirements_r5.ipynb), [R5 Merkle receipt](receipts/INTAKE_MERKLE_R5.json).

Verified-successor candidate: [R6 notebook](notebooks/03_atomic_requirements_r6.ipynb), [R6 custody receipt](receipts/INTAKE_MERKLE_R6.json). R5 cross-language failure is retained.

## SNEAK local MVP
With Python 3.12, run from this repository root:

```sh
.venv/bin/python -m apps.sneak_mvp.server --port 8773
```

Open `http://127.0.0.1:8773/` for the graph and `/audit` for requirement status. JSON is available at `/api/graph` and `/api/audit`. The server binds loopback and serves read-only committed evidence. If Python 3.12 is on PATH, `python3.12 -m apps.sneak_mvp.server --port 8773` is equivalent.

Verify with `.venv/bin/python -m unittest discover -s tests -p 'test_sneak_mvp.py' -v`. Cognee's real optional runtime is at `.venv/bin/python -m apps.sneak_mvp.cognee_adapter status`; `demo` runs the official bundled demo without demonstrating SNEAK cross-session memory. Write and recall require an explicitly configured real Cognee runtime; `--allow-llm` opts into configured LLM/embedding provider access. Do not pass sensitive text.

The Snyk adapter is `.venv/bin/python -m apps.sneak_mvp.snyk_adapter scan --target .`. It invokes the authenticated local CLI; scan outputs remain in gitignored `local-runs/`. Source upload with `--mode code` requires `--allow-code-upload`. Only scan a consented target. A clean report on a dirty tree cannot open the completion gate. See [.planning/SNEAK_MVP_20261020.md](.planning/SNEAK_MVP_20261020.md) for the pending human Band Desktop checklist.

## Snyk dashboard view 
<img width="1589" height="334" alt="snyk" src="https://github.com/user-attachments/assets/bef80890-a064-4c0f-a47f-48df62333177" />


