# SNEAK — Final Video & Security Review
Release target: https://sneak-evidence-preview.vercel.app
Video start: https://sneak-evidence-preview.vercel.app/tokens
Judge review: https://sneak-evidence-preview.vercel.app/judge
Conversation MMR: https://sneak-evidence-preview.vercel.app/conversations
LOMO: https://sneak-evidence-preview.vercel.app/heatmap
Economics: https://sneak-evidence-preview.vercel.app/economics
Development repo (private pending authenticated source/secret audit): https://github.com/biobitworks/sneak
Integration PR: https://github.com/biobitworks/sneak/pull/11
Public judge kit (only after independently verified): https://github.com/biobitworks/sneak-judges

## One-sentence problem
Multiagent work loses the connection between a question, its answer, agent/model, measured tokens, outcome, human decisions and provenance, making trust and ROI difficult to reproduce.

## Three-minute recorded-demo sequence
0:00–0:25 /tokens: explain root question and whether answer is proven.
0:25–1:10 /tokens: first observed BAND question→acknowledgment; show actor, FCO, outcome; model/version and actual usage remain NOT_ATTESTED and NOT_MEASURED. Second question has no evidence-bound answer yet.
1:10–1:40 /tokens: show SIMULATED per-agent/per-model/token/human events. Baseline 8,000 vs synthetic SNEAK 5,000 tokens, illustrative 37.5% reduction, not measured ROI.
1:40–2:15 /conversations and /heatmap: navigate hashed input, deterministic transform, FCO output and per-actor MMR; note 80 structural fixture tests, not 80 live trials.
2:15–2:40 /judge: Cognee write and separate-process recall, but live BAND planner synchronization unverified. Human approval and full requirements not established.
2:40–3:00: security scan receipt and GitHub judge kit; release gate remains BLOCKED pending Snyk and teammate scoring.

## Teammate scoring requirements
Teammate must cite exact source commit, Snyk identity, Code SAST and OSS SCA outputs, count and severity of findings, dependency coverage, and Javier's security-app-score version and license. Numeric score is NULL until complete scanner coverage; zero findings from authentication errors cannot count.
Run Snyk Container only when an image digest is provided. Compare real provider token receipts per verified agent/model/human to frozen matched tasks, not synthetic assumptions.
Current status: Snyk Code exit 2 auth ERROR; OSS exit 2 dependency resolution ERROR; Snyk Container NOT_TESTED; score NOT_COMPUTED.

## Public-release boundary
Vercel is a bounded static projection. Public judge kit may include only publishable static assets, synthetic fixture, allowed hashes and documentation. Do not expose private repo, raw BAND conversations, partner datasets, credentials, source secret files, raw Snyk reports or local runs.
Never claim full submission acceptance, human/agent live verification, or measured ROI without actual provider and judge receipts.
