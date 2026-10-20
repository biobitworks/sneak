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
No blanket third-party license; original sources retain their rights. Public release HOLD.

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


