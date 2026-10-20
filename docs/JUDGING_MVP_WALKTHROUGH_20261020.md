# SNEAK — judge walkthrough and human-readable technical stack

**As of:** 2026-10-20 · **Status:** protected MVP candidate; acceptance BLOCKED. **Source:** private biobitworks/sneak, unmerged evidence branches. Do not claim official submission or score.

## One-sentence pitch
**SNEAK — So Now Every Agent Knows:** a verifiable team workspace where AI agents pass context through BAND, use Cognee to remember decisions, and leave a Merkle/MMR evidence trail so a human can see what really happened, what changed, and what remains unproven.

## The actual problem and the user's outcome
Long-running multi-agent workflows lose context between models and tools. Agents can say they completed a task without preserving inputs, evidence, approvals or changed plans. SNEAK records every authorized decision/handoff as a source-bound FCO, stores bounded reusable context in Cognee, and lets a human inspect the chain instead of trusting a generated summary.

## Demo: 2 minutes 40 seconds (record screen only when each step is real)

| Time | On screen | Narration for judges | Evidence requirement / status |
|---|---|---|---|
| 0:00–0:20 | SNEAK protected Vercel home → evidence graph | Agents need one shared understanding, plus proof of decisions. This is SNEAK. | Deployed preview observed; access requires Vercel sign-in |
| 0:20–0:55 | Actual BAND Desktop room, @mentions and shared task board | The planner delegates to distinct agents; a task has a real owner, state and handoff. | **BLOCKED** pending BAND CLI login, agent/room IDs, board and native message IDs. Do not fake this segment |
| 0:55–1:30 | Cognee OSS real write, independent recall, changed action | An agent remembers a failed security gate and asks for a rescan instead of claiming Done. | Local Cognee 1.6.5 write and separate-process read OBSERVED; no live BAND planner readback yet |
| 1:30–2:05 | Vercel /conversations → select question/actor MMR breakpoints | Every captured message has an input hash, deterministic script, FCO output and append-only root. We can reproduce the hashes but cannot use the hash to claim the model improved. | Historical 3-message BAND receipt, 2 actor MMRs, 3 progressive breakpoints; no full chat coverage |
| 2:05–2:25 | Vercel /heatmap: 80 actor×component grid | Removing one required context binding makes deterministic authorization fail closed. | 80 synthetic structural LOMO trials verified; real agent ablations NOT_TESTED |
| 2:25–2:40 | /judge human review + Snyk gate | Judges can see every missing requirement and decide exactly what proof is needed before a real release. | Snyk currently BLOCKED; all 30 mandatory atoms unverified |

**Recording rule:** If live BAND does not work, show a clearly labeled pre-recorded historical room receipt or state the gap. No false live demo, no fake billing, no claim of organizer acceptance.

## Technical stack mapped to customer value

| Layer | Implementation in SNEAK | Why it exists | Evidence state |
|---|---|---|---|
| Orchestration UI | **BAND Desktop 0.4.16 / band CLI**, shared rooms, work board, native @mentions, Claude peer plugin | Agents claim work, share context, request human approvals | App/daemon installed, historical room events; current CLI NOT_AUTHENTICATED, live planner unknown |
| Agent harnesses | **Claude Code and Codex CLI** (plus optional local Ollama models) | Different agents can build, scan, verify independently | Host authentication observed, BAND binding NOT_VERIFIED |
| Working memory | **Cognee Open Source 1.6.5**, local Python 3.12 and graph/persistent state; local **Ollama** qwen3:1.7b and nomic-embed-text | Recover a learned gate after a separate process and change the next decision | Real local write and recall EXECUTED; runtime-wide agent memory not proven |
| Trust/data model | Source-bound **FCO/AoK**, FCG links, canonical JSON/JSONL and SHA-256, domain-separated Merkle trees and append-only MMRs; Python + independent Node replay | Detect altered inputs, scripts, outputs, transitions and missing provenance | Scoped export, conversation and Cognee successor roots computed; partial coverage |
| Product frontend | **Vercel**, static HTML/CSS/JS, JSON evidence projections, protected by **Vercel Authentication** | Human-readable graph, LOMO grid, conversation timeline and requirement review | Protected Vercel preview READY, exact-byte checks PASS; not live backend |
| Security/release | **Snyk CLI** Code and Open Source, container only with actual bound image; optional Javier app-security-score | Prevent unsafe task completion | Prior LOW findings remain; new Code AUTH_ERROR and OSS dependency-resolution ERROR; release BLOCKED |
| Optional metering | **Flexprice** test-mode SDK/integration | Trace token/cost-based features and billing | SDK import observed in branch; live usage/pricing effect NOT_VERIFIED |
| Source control and science | Private **GitHub**, stacked draft PRs, receipts/Jupyter notebooks/tests, machine acceptance registry | Reproduce evidence, keep unverified branches out of release | Commits pushed, PR review/merges pending |

## Reading the dashboard
- **Graph:** FCOs and dependencies — a custody node is not a proof of scientific correctness.
- **Conversations:** progressive question/global/actor MMR; missing per-model identities explicitly NOT_COMPUTED.
- **Heatmap:** local deterministic single-component ablation grid; switch modes to reveal untested live-agent/Snyk events.
- **Human review:** 46 acceptance-test atoms (30 mandatory, 16 bonus/enrichment) and the separately anchored official source inventory of 56; editable annotations export to JSON without changing verified flags.
- **Audit:** original exact machine outcomes. Acceptance remains 0/30 until independently supported and approved.

## Evidence governance
Source PDF lists judging category weights BAND 25%, Cognee 25%, startup product 20%, execution 20%, innovation 10%; re-check with organizers if rules changed. Snyk and Flexprice are bonus opportunities, not substitutes for mandatory BAND/Cognee behavior. The brief requires a 2–3 minute video; exact submission URL, deadline and judge access are still to be independently confirmed.

**Proven limits:** current connected BAND room/plan/board/approval and cost display NOT_VERIFIED; whole corpus and actual model-version MMR incomplete; cross-agent Cognee behavior NOT_VERIFIED; Snyk gate BLOCKED; bonus scores NULL or NOT_COMPUTED; raw data remains private; no global final MMR or scientific outcome invented.

## Human owner review before submission
1. Open the protected preview and the new human reviewer; export filled JSON only after observing proof.
2. Finish BAND CLI authentication, create/verify planner agent and room IDs, record real @mentions, task transitions and explicit HITL decision; attach room receipts.
3. Run Cognee from two independently bound harnesses, demonstrate recall changing actual room task state; record source output and independent replay.
4. Re-authenticate Snyk CLI; run Code + OSS for exact target commit and resolve findings. Run Container only if a real image exists; score Javier with real accepted coverage.
5. Record a 2–3 minute video, confirm official submission destination, and give judges explicit access to BAND/Vercel as appropriate.

**Release/merge policy:** the human may approve continued development and can sign off their review, but neither approval nor hashes automatically satisfy the official hackathon acceptance gates.
