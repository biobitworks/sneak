# SNEAK R15 — FCO/FCG × MMR successor acceptance record

**Parent code:** ba1ba7925137855792fed76d4f7a377fc689b1d2 (connector/custody branch).
**Predecessor evidence:** SNEAK-016 (Merkle root 72e7a22ae6e2e46be6b09f60af3f5efb13603fd84a4dee08b8706fd11543f6ae), which explicitly says \`mmr: NOT_COMMITTED\`.
**Source receipt exact-byte SHA-256:** f8de91405ee4d924bfbd13703477f63b817a3e5957eae984b6526264dfe46b4b.

## Implemented and executed

- \`src/sneak/fcg_registry.py\`: append-only, filesystem-locked registry. One canonical JSON occurrence yields one full SHA-256 FCO identity, with a typed FCG edge set, actor/model/parent checks, prior MMR root, leaf position, ordered peaks and independent inclusion proof. Zero plaintext credentials are required or written.
- \`src/sneak/mmr_reference.py\`: reference position-committed SHA-256 MMR. MMR is **not** interchangeable with the legacy balanced Merkle root or with Grin's byte format.
- \`scripts/replay_sneak_receipt_fcg.py\`: validates the SNEAK-016 Merkle leaves, canonical bytes, ordered root and all inclusion proofs **before** deriving successor objects. It never overwrites prior receipts.
- \`scripts/contribution_fco.py\` and \`docs/onboarding/TEAMMATE_HANDOFF.md\`: imported teammate FCO/commit binding from prior onboarding branch; one existing contribution FCO verifies. No new teammate is falsely asserted as onboarded.
- \`data/fcg/sneak-016-replay.jsonl\`: 55 FCO occurrences, 64 FCG edges, **105 MMR nodes**, four baseline-vs-ablation root-change records, eight scan outcomes, eight nullable scores, and typed classifications and BAND/Cognee receipt claims. All records are bound to the exact-byte source digest.

**Computed successor MMR root:** \`089e49c083f1d6170402a366cfa76f3b939cbdcefce262ff39a732061463dadc\` (55 leaves, 105 nodes). Independent last-event inclusion proof: PASS. This root establishes ordered evidence integrity only; it does not prove secure code, third-party service truth, scientific truth, rights, or signatures.

## Live provider acceptance

- BAND API: authenticated GET \`/api/v1/me\` returned HTTP 200 using pre-existing operator credentials. The local BAND CLI daemon is installed but the local CLI account is not configured. A successful API message must be independently recorded before claiming handoff.
- Cognee Cloud: authenticated service health HTTP 200, with Postgres, pgvector, graph and S3 components healthy. A successful \`@Data\` write, cognify, and exact recall must be recorded separately.
- Snyk CLI \`1.1307.2\`: operator CLI identity observed. **SAST exit 1; 7 findings** (six \`note\` / one \`warning\`). Raw report retained locally outside Git, SHA-256 \`a38fdda389604dea1aabb8e2a1a448cfda3d5b11d7a41e54b16146a4a96205cc\`.
- Snyk Open Source \`--all-projects\`: **exit 2**, failed dependency resolution because the staged demo requirements file is intentionally empty. Zero discovered vulnerable paths here **does not** imply zero vulnerable dependencies or completed coverage. Raw report retained locally, SHA-256 \`4e840e75217fe925534c93c6097f1ec22ac713db47701548ab036a7c4fd2df16\`.
- Javier \`app-security-score\` helper is pinned to upstream \`6e1f27605fe278eed347b10dab6f39b3501f1486\`. A zero-*finding* fully covered app would receive **10/10**, not 0. This run has **no accepted application score** because SCA and SAST have not cleared. Event bonus is not awarded by running a helper.

## Precise non-admissions

- The prior eight SNEAK-016 LOMO scan results remain **NOT_TESTED**; the eight application scores remain **NULL**. They were not retroactively rescanned.
- Every **registered** output event can be checked as an FCO in this replay. Complete global coverage of every autonomous process, model, agent spawn or third-party provider is **NOT_TESTED** without instrumenting and gating all emitters.
- One source receipt replay and synthetic tamper tests do not establish cross-host independent custody; those acceptance gates remain open.
- Prior Merkle receipts are append-only predecessors; no Merkle or MMR hash claims authorship, authenticity, causality, safety or correctness. Signatures remain **NOT_TESTED**.
- The entire original security requirements list remains open as a whole; these are per-control verified sub-results, not an assertion that all mandatory event requirements passed.

## Reproduce

\`\`\`bash
python3 -m unittest discover -s tests -q
python3 scripts/contribution_fco.py verify
python3 - <<'PY'
import sys
sys.path.insert(0, 'src')
from sneak.fcg_registry import FCGRegistry
from pathlib import Path
r = FCGRegistry(Path('data/fcg/sneak-016-replay.jsonl'))
print(r.verify())
print(r.inclusion_proof(r.rows()[-1]['fco_id'])['verified'])
PY
\`\`\`

Do not rerun \`scripts/replay_sneak_receipt_fcg.py\` on the same output path: it refuses to overwrite an existing lineage. Use an isolated output path when running a new reproduction. Any corrections must be new FCO successors, not edits to existing records.
