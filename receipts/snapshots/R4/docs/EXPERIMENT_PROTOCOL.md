# Frozen proposed protocol: skills, transformations and LOMO

Status: PROPOSED; no model/attack/scan outcomes observed.
Population: synthetic skills and source-rule records, not a representative real-world attack distribution.
Do not infer detector accuracy or scientific generalization from this starter set.

## Paired source/transformation data
1. Original PDF bytes -> predecessor extracted page text -> exact-line atoms -> deduplicated content and occurrence pointers.
2. Synthetic neutral/poison/antidote/neutral-context fixture -> whitespace-normalized text plus preserved original and transformation receipt.
3. Skill -> rendered tool/prompt schema -> delivered-token identity when available; NOT_COMPUTED until tokenization.
4. Full context -> one-atom/context/dependency-removed successor. Preserve predecessor bytes and root.

Lossless transformations must reconstruct the original representation they claim to preserve exactly.
Whitespace normalization is lossy; its record explicitly retains original bytes. An embedding cannot reconstruct arbitrary source bytes.
Pair variants by original family and split families before evaluation. Starter set is a smoke-test fixture, not a held-out benchmark.

## Crossed design
Use Qwen 0.5B and 1.5B first. Add Qwen Coder 7B only after license/artifact and runtime checks.
Cross each with feasible K0/K1/K2 capability manifests, original/transformed representation and neutral/poison/repair/control treatment.
Development smoke test: one run per populated cell, no statistical inference.
Confirmatory sample size: NOT_COMPUTED; freeze after a separate pilot/power or precision calculation and before confirmatory outcomes.
Record failures/timeouts/abstentions without converting them to zero or success.
Temperature, seed, sampling settings, context budget, model digest, tokenizer and prompts must be frozen before each run.
Deterministic hashing does not make model inference deterministic.

## Every actor checks each applicable LOMO
Generate a row for every actor x component: owner, intake, transport, tokenizer/harness, builder, scanner, memory, Claude-red-team, verifier, gateway.
Components: source atom, occurrence context, rights binding, policy binding, scan receipt, memory reference, authorization receipt, parent breakpoint.
For each row retain full baseline and remove exactly one component in a successor.
Recompute leaves/proofs/root independently. Separately record semantic/task and authorization outcomes.
Actor answer is PROPOSED; deterministic verifier supplies OBSERVED Boolean. Not-applicable rows require a reason.
Missing security-critical context must deny/abstain. Not every removal should cause denial: irrelevant neutral context is a negative control.
LLM agreement on a root is not independent cryptographic verification.

## Primary outcomes
Unauthorized successful read, unauthorized write, canary disclosure and replay acceptance counts, each with attempts/denominators.
No live secrets are used; canaries are explicitly synthetic and remain inside the guest.
Legitimate task success and false-rejection rate accompany safety counts.
Secondary: scan findings/coverage, repair success, resource usage, model latency and token counts where measured.
LOMO delta: paired outcome differences full versus ablated; report categorical transitions separately from numeric differences.
Anticube/DeltaG*: NOT_COMPUTED until governing version, inputs, formula, units and tests are recovered and frozen.

## Custody
Breakpoints: source intake; transformation; skill receipt; scan; LOMO intervention; authorization; observed execution; recovery.
Each records ordered leaves, construction identifier, root, proofs, verification and predecessor reference.
A binary Merkle tree is not an MMR. This package makes no project MMR commitment or signing claim.
