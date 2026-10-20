# SNEAK R21/R22 — registered per-breakpoint FCO/MMR and live Snyk triage

Base code commit: \`97d1a7b3093dd0348a6bc8858604e8e1ab305c19\`. Historic parent ledger root (58 leaves) \`f0579f511bccecf09c588f1d564e33a12af3409502a56b7868c4b61eab87587a\`.

## Executed local R21

- Four synthetic connector LOMO trials, each with a baseline and one-component-ablated Merkle breakpoint; **8** checkpoint receipts independently recomputed.
- Each breakpoint emitted typed FCOs: breakpoint, scan attempt, score value, classification. Each ablation also emitted a deterministic root-identity delta FCO.
- **36 new FCOs**; ledger prefix at 94 FCOs / 106 typed edges / 183 MMR nodes, root \`e214642bb3e8153c8a2a16a0b63444e6534afb95cc0c5853e808948df9903e78\`.
- Source Merkle chain SNEAK-021 root \`b54c5450ab5512c96f437bb8d78cd97e70d013b82bbdb2a0f8de19ff5d737b8c\`; **this is distinct from the FCG MMR root**.
- Credential-free run, with all eight Snyk score receipts \`NOT_TESTED\` for SCA and SAST; application scores **NULL**. Cognee and BAND per-event live delivery **NOT_TESTED** in R21. Source receipts are versioned under \`receipts/lomo-fcg-r21-evidence/\`.

## Observed live Snyk R22

- Snyk Code CLI \`1.1307.2\` on hardened branch: **5 SAST notes**, **0 warnings**, tool exit **1**. Raw local report SHA-256 \`1709834553a04a4a57748ba81f15d3690b5685d75dae133a43ee59bfeba789a0\`.
- Previous baseline: **7 SAST findings** (6 notes, 1 warning), exact prior report SHA-256 \`e1de109d67136b1a73ceb40eb114959db2dc340152ae80ac4b1d23b87dd5a647\`.
- Count delta = **-2 findings**, OBSERVED on scanner outputs only. This is **not proof of threat elimination, exploitability or overall risk reduction**.
- Snyk Open Source CLI failed **exit 2** due empty demo requirements manifest. SHA-256 of raw report: \`4e840e75217fe925534c93c6097f1ec22ac713db47701548ab036a7c4fd2df16\`.
- Javier scorer application value = **NULL**, complete coverage **FAILED**, admission = **DENY**, external event bonus = **NOT_VERIFIED**. The correct target for Javier scoring is **10/10 from zero findings on complete scans**, not numeric score 0.
- New provenance FCOs: code artifact, SAST scan, finding count, finding-count delta, failed SCA scan, null app score, deterministic DENY classification (**7 FCOs**).

Final computed ledger at R22: **101 FCOs, 113 FCG edges, 198 MMR nodes**, root \`40a1df7aac73fcdc5897752a342823cf9aa312ae7fb29bf0f0c401b64332587d\`. Merkle identity, MMR inclusion, and predecessor prefix integrity were verified. Hashes prove identity/inclusion, not semantic correctness, causal improvement, model performance or authorization.

## Remaining required work

Global enforcement for every external actor, model invocation, job spawn, value and classification is **NOT_TESTED**; this scoped hook covers registered LOMO calls only. Five remaining Snyk path-traversal findings require review; SCA remains **FAILED**. Live two-way BAND agent acknowledgments, shared board, human decision, complete VM isolation and release rights are also **NOT_TESTED/NOT_OBSERVED**. Keep GitHub repo private and PR #12 a draft; do not merge or claim bonus.

Reproduce: \`python3 -m unittest discover -s tests -q\` and execute \`notebooks/12_lomo_security_mmr_r22.ipynb\`. As-executed local original scan reports remain outside Git; their hashes are versioned inside SNEAK-022. Source receipt reproduction uses versioned saved \`receipts/lomo-fcg-r21-evidence\`, not rerunning the original one-time transaction.
