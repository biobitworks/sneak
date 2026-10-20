# Models and environments

| Location | Model / runtime | Role | Verified status |
|---|---|---|---|
| MagicStudio, 32 GiB RAM, arm64 | Ollama qwen2.5:0.5b; observed ID a8b0c5157701 | Small baseline; K0/K1 permissions | Installed; inference NOT_TESTED |
| MagicStudio | Ollama qwen2.5:1.5b; observed ID 65ec06548149 | Builder/reviewer comparison; K0/K1/K2 | Installed; inference NOT_TESTED |
| MagicStudio | Qwen2.5-Coder-7B-Instruct | Stronger code/repair candidate | PROPOSED; not installed or benchmarked |
| MagicPro | Same pinned models where supported | Independent replay/cockpit | OFFLINE at attempted inventory; hardware/model availability UNKNOWN |
| iPad | Browser/BAND/remote operator client | Approvals and evidence inspection | User-reported device; workflow NOT_TESTED |
| S26 Ultra | Independent browser client; optional later local inference | Client/session/network boundary tests | User-reported device; local inference UNKNOWN |
| Separate Claude Code session | Actual selected model recorded at execution | Independent red team | NOT_EXECUTED |
| Host-independent Python and Node | SHA-256/Merkle verifier | Exact arithmetic oracle | Intake checks only; not model judgment |

Official Apache-2.0 model cards:
- https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct
- https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct
- https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct

Verify full local Ollama manifest/model digests, tokenizer/chat template and quantization before runs; displayed IDs are short inventory identifiers.
Do not assume installed local artifacts equal upstream model-card weights without lineage verification.
The installed custom Liquid models are excluded from the primary open-model baseline until their exact license/lineage is checked.
Open weights and an Apache license do not establish complete training-data transparency or formal open-source-AI certification.

K0: propose text only; K1: approved fixture reads; K2: temporary workspace tools in a disposable VM.
All models are crossed with all feasible tiers; no model gets canonical credentials at any tier.
Actual capability manifests are frozen per run. Larger-model feasibility is unbenchmarked.
Do not expose an unauthenticated Ollama endpoint to the public internet.
