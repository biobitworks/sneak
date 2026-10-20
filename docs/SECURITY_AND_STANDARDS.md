# Security boundaries and standards mapping

## Secrets
Use /Users/byron/.secrets/skill-custody-lab/snyk.env (directory 0700, file 0600).
The file is created empty; the operator supplies the token privately. Expected key: SNYK_TOKEN.
Do not paste a real token into chat, commit it, or capture its value in receipts.
Read only the allowlisted key and export it to the approved scanner subprocess; do not execute a secret file as shell code.
Candidate builds, skills, model prompts and red-team guests never receive this credential.
Record presence/permission checks only. Do not hash secret values into public or shared receipts.

## VM and container boundaries
Use a dedicated disposable ARM64 Linux VM or isolated cloud VM. Actual provider/image is selected and pinned before execution.
No host home/filesystem shares, shared clipboard, agent forwarding, host Docker socket, production database mounts or credentials.
Control egress separately for package installation, scanner APIs and model broker; test denial and teardown.
Javier's two containers are useful nested stages but do not establish a dedicated VM security boundary.
Upstream scanner stage receives SNYK_TOKEN and may run package-manager code; test that path and use a scoped disposable token.
MagicStudio docker CLI exists, but docker info failed; no VM runtime was verified. No runtime is silently started.

## Governance
Overwatch retains portfolio truth. All demo truth is synthetic. Candidate skill delivery and memory recall cannot update policy.
BAND carries sanitized references, task states and required approvals. Cognee has separate candidate and admitted-memory namespaces.
A recalled candidate remains untrusted evidence; it cannot promote itself into instructions or modify an admission policy.
Gateway capability is task/action/object/expiry/nonce scoped, audience-bound and revocable. Policy checks are independent of model outputs.
Scanner findings, coverage errors, schema changes, stale receipts and dependency changes deny admission until a successor passes.
Optional Anticube/DeltaG* attachments cannot override a failed requirement.

## Control mapping, not certification
| Reference | Proposed controls |
|---|---|
| NIST SSDF SP 800-218 | Protect artifacts, review changes, provenance, dependency scanning, remediation |
| NIST AI RMF 1.0 | Document actors, scope, evaluation limits, monitoring and incident response |
| OWASP Top 10 for LLM Applications | Treat retrieved instructions as untrusted; control tools and sensitive data |
| OWASP agentic security guidance | Separate identity, memory, tool authority, handoffs and human decisions |
| SLSA provenance | Bind source, builder, inputs and output digests; no SLSA level claimed |
| SPDX / CycloneDX | Component/license inventory and AI supply-chain manifest; no completeness claim |

Official references: https://csrc.nist.gov/pubs/sp/800/218/final ;
https://www.nist.gov/itl/ai-risk-management-framework ;
https://genai.owasp.org/llm-top-10/ ; https://owasp.org/www-project-top-10-for-agentic-applications/ ;
https://slsa.dev/spec/ ; https://spdx.dev/ ; https://cyclonedx.org/ .
Pin exact applicable versions before standards-conformance assertions.

## Rights
Inherited research remains background IP. No blanket license is applied to third-party sources.
Javier root LICENSE returned 404 at the pinned commit; reuse license is UNKNOWN, not assumed permissive.

Preferred **original** authorship terms (split; see root `LICENSE` / `LICENSING.md`):
software Apache-2.0; docs and other non-code creative works CC BY-NC-ND 4.0.
Do not apply CC BY-NC-ND as a universal code license.
Downloaded upstream snapshots remain local and gitignored. Commit only hashes, URLs and review findings.
Public release remains HOLD pending BAND/event authorization, source rights and dependency review.
