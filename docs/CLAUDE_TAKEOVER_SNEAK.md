# Sneak: Claude takeover and independent red team
Status: handoff IMPLEMENTED; Claude execution NOT_EXECUTED.
Read AGENTS.md, START_HERE_SNEAK.md, .planning/ATOMIC_ACCEPTANCE_R5.md, docs/EXPERIMENT_PROTOCOL.md and docs/superpowers/plans/2026-10-20-sneak-requirements-build-r8.md.

## Resume without trusting chat memory
1. Fetch origin; inspect branch, HEAD and git status. Do not discard user work.
2. Read receipts/repository_bootstrap/SNAPSHOT.json and receipts/repository_bootstrap/EXECUTION.json.
3. Independently verify the declared commit and actual bytes:
   - python3 scripts/custody_snapshot.py verify receipts/repository_bootstrap/SNAPSHOT.json
   - node scripts/verify_custody_snapshot.mjs receipts/repository_bootstrap/SNAPSHOT.json
   - python3 -m unittest discover -s tests -v
4. Run notebooks/06_sneak_repository_handoff.ipynb in an authenticated local Jupyter runtime. It verifies evidence; it does not perform provider setup.
5. Start a named branch for changes. Append findings/receipts and successor checkpoints; never rewrite the intake or predecessor failure.
6. If chat stalls, resume from committed checkpoint plus actual provider state. No running agent lease or automatic failover has been implemented. Do not start duplicate work solely because a session looks silent.

## Red-team proof obligations
- Reimplement hashing independently; check file bytes, canonical records, leaves, membership paths and root.
- Deliberately tamper one copied file, one leaf, root, ordering, proof direction and missing manifest member. Assert rejection. Keep evidence on a separate red-team branch.
- Review every requirement atom against its source quote and optionality. TRUE requires a real provider/execution receipt; keep all NOT_TESTED states intact.
- For each actor/component LOMO row, remove one component in a successor; recompute custody and observe the actual action/authorization effect separately.
- All current LOMO assignments are planned, not executed attack outcomes.
- Test copied synthetic fixtures inside verified isolation only. Do not inspect real secrets, attempt host escapes or write to Overwatch.
- Verify complete SCA and SAST stages for Javier scoring. Errors/unsupported projects are not zero findings. Score is not event bonus.
- Report findings as Markdown and JSONL with source commit, actual model/version, capability manifest, command, exit code, expected/observed outcome, evidence refs and successor ID.

## Human checkpoints
Use docs/HUMAN_CHECKPOINTS_SNEAK.md. Report REQUESTED, HUMAN_REPORTED, INDEPENDENTLY_OBSERVED and VERIFIED separately. Only an actual human response can be a human approval. BAND room evidence is needed for event human-in-loop acceptance.
