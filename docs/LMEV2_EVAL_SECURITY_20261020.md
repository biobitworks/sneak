# SNEAK LME-V2 × Snyk evaluation receipt — 2026-10-20

## Authority and scope

- Benchmark: [LongMemEval-V2 official repository](https://github.com/xiaowu0162/LongMemEval-V2), checkout `2cc8c540bdb87fe6761629b585e727e1c4704520`.
- Dataset: Hugging Face `xiaowu0162/longmemeval-v2`, revision `f152293e235517d504809563c833d7190b8c713b`.
- `questions.jsonl` exact-byte SHA-256: `0a3ae5ebea938c24d7800e1e0b0828e08ae1646f939a53853b2b8cdc08e292b7`.
- `haystacks/lme_v2_small.json` SHA-256: `9b5301defb23a088a5f06e45ff8d5f35e569d78305a66d492046a9fff9b46593`.
- Tested: two public questions (`01307e07` enterprise, `00aa905a` web), one per domain, text-only, deterministic local answer evaluator. Zero retrieval history.
- *Not* an official tier run. Trajectories (1.2 GB), screenshot archives (about 5.9 GB), retrieval systems, fixed reader, judge, full 451 questions, web + enterprise complete sets, and LAFS gain: NOT_TESTED / NOT_COMPUTED.
- Fixed no-retrieval condition means model differences are **not** measurements of memory-system benefit. The tiny sample is not statistically meaningful.

## Observed local model diagnostic

| Model | Scored | Correct | Accuracy (only 2 questions) | Enterprise time | Web time |
|---|---:|---:|---:|---:|---:|
| `qwen3:1.7b` | 2 | 0 | 0% | 16,437.27 ms | 1,314.28 ms |
| `hf.co/LiquidAI/LFM2.5-1.2B-Instruct-GGUF:latest` | 2 | 1 | 50% | 6,488.26 ms | 812.89 ms |

These are elapsed local HTTP inference times, not LongMemEval's memory-query latency metric. The original gold answers were not supplied to the models. Official deterministic scoring code was executed locally; the actual text output has local-only digest receipts.

### Append-only custody

- Predecessor FCOs: 58; FCG edges: 67; MMR nodes: 112; root `f0579f511bccecf09c588f1d564e33a12af3409502a56b7868c4b61eab87587a`.
- Successor FCOs: 74; FCG edges: 82; MMR nodes: 145; root `713334f89e48d44ea64b00651dfc1cf577e9aaab1e4b1d7be71d310f3e033f20`.
- Pilot receipt: `receipts/evaluations/LMEV2_20261020_PILOT.json`; exact receipt SHA-256: `8f65c60c626e784300e615bc0e6babb15bf6f172a2ba1430f8401f6f1cb68985`.
- Each observed model answer has a model FCO, agent FCO, result/value FCO, scorer FCO and linked custody predecessor. The MMR counts have been independently recomputed by `FCGRegistry.verify()` (source code verification; not scientific validation).
- No prior ledger entry was rewritten. BAND/Cognee delivery records are explicit `NOT_TESTED`, not pretend successes.
- Claude/Tom and ChatGPT/Jerry actual evaluations and acknowledgments: NOT_TESTED/NOT_OBSERVED. Never equate a message mentioning an agent with that agent's execution.

## Current actual Snyk result — scoped and fail-closed

Snyk Code CLI v1.1307.2, exactly git commit `83c70a5407ba4ee65940073e28ab42c8c6e5e37c` exported without dirty changes:
- exit `1`, five `note`/low findings, all path traversal;
- `scripts/verify_custody_snapshot.mjs:12`;
- `scripts/custody_snapshot.py:64,79,84`;
- `src/sneak/connectors.py:140`.
- Pinned Javier app-security-score `javiergarza-snyk/app-security-score@6e1f27605fe278eed347b10dab6f39b3501f1486` yields **raw 9.5/10** from SAST-only assumed-zero-SCA findings.
- Snyk Open Source `--all-projects` failed with exit `2`: an intentionally empty demo runtime `requirements.txt` is not scannable as a pip dependency project. The main `pyproject.toml` uses setuptools PEP 621, not a supported Poetry lock; `snyk test --file=pyproject.toml` also failed manifest parsing.
- A separately resolved *development* dependency inventory (`pytest` and its dependencies) was created in an isolated virtualenv, but Snyk Open Source returned `Use snyk auth to authenticate`. This is not valid SCA coverage.
- **Accepted application score: NULL. Security admission: DENY. Bonus award: NOT_OBSERVED.** A clean 10/10 requires supported complete SCA+SAST with zero findings, for the *same* evaluated candidate, and separate hackathon confirmation.

## Follow-up protocol

1. Rotate any externally shared Cognee API credential. Configure BAND, Cognee, and Snyk securely on the host (outside Git, notebook, or FCO contents).
2. Audit/repair each path traversal finding without hiding files or suppressing scanner rules merely to improve the score. Re-run Code and Open Source with the same candidate digest and retain raw scanner bytes outside Git.
3. Read LongMemEval's dataset rights, stage trajectories and images in an isolated workspace, validate source hashes and question/trajectory coverage before adding memory.
4. Freeze benchmark conditions: same reader model, question subset, parser, prompts, temperature, seed, judge, latency definition, and gold isolation for all B0–B5 memory methods.
5. Execute *full* official web+enterprise small tier for baseline and Cognee/FCO variants before claiming benchmark accuracy or LAFS gain. Record failed/unknown rows rather than dropping them.
6. After each model×agent×LOMO successor, append immutable FCOs with validated MMR prefix, POST digest+metrics to Cognee, send BAND mention and demand readback/independent acknowledgment. Publication and admission remain separate gates.

Hashes establish byte identity and an inclusion proof establishes ledger integrity, neither proves correctness, vulnerability absence, or causality.

## Executed notebook/security successor

- Notebook: `notebooks/12_lmev2_agent_model_security_diagnostic.ipynb`, 5/5 code cells executed, SHA-256 `657c2b0652efc1177539700777b1a7b6354f95aa572291cc707777832eb655d3`.
- Security successor receipt: `receipts/evaluations/LMEV2_20261020_SECURITY_SUCCESSOR.json` (sha256 `8b61c27f209ab0f37296a3318407fb20c184f2e12d024e7aecd47af274d96195`).
- Verified 77 FCO, 85 edges, 150 MMR nodes, root `be4fdb841cef03c132f5606f6673c7ac8c957b33c738b209be07eb513d260ef3`. Pilot root and receipt remain unchanged.
- No BAND or Cognee remote acknowledgment observed; their pilot statuses remain NOT_TESTED.
