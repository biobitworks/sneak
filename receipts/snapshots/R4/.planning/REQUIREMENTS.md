# Requirements: Skill Custody Lab

Defined: 2026-10-20. Status: requirements-first proposal, not implemented product.

Source classes distinguish supplied event rules from user requirements and proposed engineering controls. Every row remains unchecked until implemented, executed, verified and committed.

## v1 Requirements

- [ ] **BAND-01**: At least two agents collaborate in one BAND Desktop room. (Phase 2; PROVIDED_BRIEF)
- [ ] **BAND-02**: A lead agent publishes a shared plan and work board. (Phase 2; PROVIDED_BRIEF)
- [ ] **BAND-03**: Agents claim tasks and move work from To-do to Done. (Phase 2; PROVIDED_BRIEF)
- [ ] **BAND-04**: Direct agent mentions carry handoff context without human copy/paste. (Phase 2; PROVIDED_BRIEF)
- [ ] **BAND-05**: At least one real decision reaches the human through BAND. (Phase 2; PROVIDED_BRIEF)
- [ ] **BAND-06**: Demo shows rooms, board, per-agent sessions, tokens and estimated costs. (Phase 2; PROVIDED_BRIEF)
- [ ] **MEM-01**: Agents write working memory during work. (Phase 2; PROVIDED_BRIEF)
- [ ] **MEM-02**: Memory recall changes the next action across restart or different agents. (Phase 2; PROVIDED_BRIEF)
- [ ] **MEM-03**: Removing BAND or Cognee changes core product behavior. (Phase 2; PROVIDED_BRIEF)
- [ ] **DEMO-01**: Provide a live or local working prototype. (Phase 5; PROVIDED_BRIEF)
- [ ] **DEMO-02**: Provide a source repository link after rights/release approval. (Phase 5; PROVIDED_BRIEF)
- [ ] **DEMO-03**: Produce a 2-3 minute video showing BAND, a human decision, costs, and Cognee recall. (Phase 5; PROVIDED_BRIEF)
- [ ] **DEMO-04**: Describe the problem, agent roles/harnesses/handoffs, and integrations. (Phase 5; PROVIDED_BRIEF)
- [ ] **EVENT-01**: Confirm deadline, submission URL and support channel before submitting. (Phase 5; PROVIDED_BRIEF)
- [ ] **EVENT-02**: Confirm sponsor expectations, credits and judging weights. (Phase 5; PROVIDED_BRIEF)
- [ ] **SEC-01**: Security reviewer scans every candidate, blocks completion on failure, and recalls recurring issues. (Phase 3; PROVIDED_BRIEF)
- [ ] **BONUS-01**: Target the Snyk bonus stated as up to +10%; never represent it as an awarded score. (Phase 5; PROVIDED_BRIEF)
- [ ] **CUST-01**: Preserve original bytes, occurrence/context identity, actor and parent identities separately. (Phase 1; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **CUST-02**: Every transformation records input/output hashes, code identity, parameters and rights. (Phase 1; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **CUST-03**: Compute and independently verify ordered Merkle leaves, root and inclusion proofs. (Phase 1; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **CUST-04**: Tampering, leaf removal, context mutation and proof mismatch return FALSE; unknown stays UNKNOWN. (Phase 1; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **CUST-05**: Preserve append-only successor events and never equate hashes or inclusion with truth. (Phase 1; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **CUST-06**: Pin requirements and protocol to Git commit permalinks before experimental outcomes. (Phase 1; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **DATA-01**: Start with the supplied PDF and source-bound text/atom transformations. (Phase 1; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **DATA-02**: Create synthetic neutral, poison, antidote and neutral-context controls with paired original/transformed records. (Phase 1; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **DATA-03**: Compare originals against deduplicated content with preserved occurrence pointers; test lossless reconstruction. (Phase 1; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **DATA-04**: Keep test-split variants grouped by source family; record leakage and contamination limitations. (Phase 4; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **DATA-05**: Exclude restricted research datasets and inherited unpublished algorithms from demo execution. (Phase 1; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **MODEL-01**: Use licensed open-weight Qwen baselines on MagicStudio and pin actual model digests. (Phase 4; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **MODEL-02**: Cross model identity with explicit capability tiers rather than attributing permission effects to model size. (Phase 4; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **MODEL-03**: Treat model root predictions as proposals; deterministic verifiers independently compute TRUE/FALSE. (Phase 4; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **MODEL-04**: Capture rendered prompts, tokenizer/version and token IDs where available; otherwise token identity UNKNOWN. (Phase 4; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **LOMO-01**: Every actor has a full-versus-one-component-removed replay assignment and a result receipt. (Phase 4; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **LOMO-02**: Missing authorization context causes abstention or denial, never implicit permission. (Phase 4; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **LOMO-03**: Freeze primary outcomes and exploratory run counts before inspecting responses. (Phase 4; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **VM-01**: Run hostile payloads in disposable VMs with no shared home, clipboard, SSH agent or Docker socket. (Phase 2; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **VM-02**: Verify guest image/runtime identity, resource limits, network policy and teardown. (Phase 2; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **VM-03**: Build untrusted code without credentials; confine scanner credentials to a separate broker/stage. (Phase 3; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **VM-04**: Test scanner-stage package-manager execution and outbound paths; do not assume upstream isolation is sufficient. (Phase 3; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **GATE-01**: Candidate models and skills have no direct canonical read/write credentials. (Phase 2; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **GATE-02**: Independent gateway binds candidate digest, task, action, policy, expiry, nonce and authorization. (Phase 2; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **GATE-03**: Stale scans, replay, changed dependencies, missing coverage and unknown schema block admission. (Phase 3; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **GATE-04**: Only verified scoped capability permits a gateway operation; repair never rewrites historical evidence. (Phase 3; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **SNYK-01**: Pin Javier app-security-score implementation and record SCA and SAST coverage separately. (Phase 3; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **SNYK-02**: Report 10/10 only for both completed scans with zero findings; preserve raw score if wrapper rejects coverage. (Phase 3; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **SNYK-03**: Use Snyk Agent Scan for skill/MCP risks; pin adapter version and reject unrecognized result schema. (Phase 3; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **SNYK-04**: Keep SNYK_TOKEN out of prompts, logs, notebooks, git and candidate environments. (Phase 2; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **SNYK-05**: Keep secret file outside the repository with directory 0700/file 0600 and export only to scanner process. (Phase 2; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **RED-01**: Claude Code independently red-teams synthetic fixtures with bounded capabilities and its own receipts. (Phase 4; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **RED-02**: Do not grant red-team access to actual secrets, production truth stores or unrestricted host tools. (Phase 4; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **ENV-01**: Record MagicStudio, MagicPro, iPad and S26 availability, identities and supported roles independently. (Phase 2; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **ENV-02**: Cross-host and cross-client evidence is NOT_TESTED until an actual run occurs. (Phase 4; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **OPT-01**: Optional Anticube/DeltaG* evidence references a versioned formula and immutable core; otherwise NOT_COMPUTED. (Phase 4; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **STD-01**: Map controls to NIST SSDF, NIST AI RMF, OWASP agentic/LLM risks, SLSA and SPDX/CycloneDX; claim no certification. (Phase 1; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **REPRO-01**: Every protocol has a portable Jupyter notebook with parameters, sources and execution status. (Phase 4; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)
- [ ] **IP-01**: Keep repository private and resolve BAND/event rights before public release. (Phase 5; USER_REQUIREMENT_OR_PROPOSED_ENGINEERING_CONTROL)

## Traceability

| Requirement | Phase | Source atoms | Status |
|---|---:|---|---|
| BAND-01 | 2 | RULE-P02-L010 | Pending |
| BAND-02 | 2 | RULE-P02-L013 | Pending |
| BAND-03 | 2 | RULE-P02-L013 | Pending |
| BAND-04 | 2 | RULE-P02-L015 | Pending |
| BAND-05 | 2 | RULE-P02-L017 | Pending |
| BAND-06 | 2 | RULE-P02-L020 | Pending |
| MEM-01 | 2 | RULE-P02-L030 | Pending |
| MEM-02 | 2 | RULE-P02-L032 | Pending |
| MEM-03 | 2 | RULE-P02-L040 | Pending |
| DEMO-01 | 5 | RULE-P06-L014 | Pending |
| DEMO-02 | 5 | RULE-P06-L015 | Pending |
| DEMO-03 | 5 | RULE-P06-L016 | Pending |
| DEMO-04 | 5 | RULE-P06-L019 | Pending |
| EVENT-01 | 5 | RULE-P06-L042 | Pending |
| EVENT-02 | 5 | RULE-P07-L003 | Pending |
| SEC-01 | 3 | RULE-P03-L017 | Pending |
| BONUS-01 | 5 | RULE-P06-L007 | Pending |
| CUST-01 | 1 | User request / design | Pending |
| CUST-02 | 1 | User request / design | Pending |
| CUST-03 | 1 | User request / design | Pending |
| CUST-04 | 1 | User request / design | Pending |
| CUST-05 | 1 | User request / design | Pending |
| CUST-06 | 1 | User request / design | Pending |
| DATA-01 | 1 | User request / design | Pending |
| DATA-02 | 1 | User request / design | Pending |
| DATA-03 | 1 | User request / design | Pending |
| DATA-04 | 4 | User request / design | Pending |
| DATA-05 | 1 | User request / design | Pending |
| MODEL-01 | 4 | User request / design | Pending |
| MODEL-02 | 4 | User request / design | Pending |
| MODEL-03 | 4 | User request / design | Pending |
| MODEL-04 | 4 | User request / design | Pending |
| LOMO-01 | 4 | User request / design | Pending |
| LOMO-02 | 4 | User request / design | Pending |
| LOMO-03 | 4 | User request / design | Pending |
| VM-01 | 2 | User request / design | Pending |
| VM-02 | 2 | User request / design | Pending |
| VM-03 | 3 | User request / design | Pending |
| VM-04 | 3 | User request / design | Pending |
| GATE-01 | 2 | User request / design | Pending |
| GATE-02 | 2 | User request / design | Pending |
| GATE-03 | 3 | User request / design | Pending |
| GATE-04 | 3 | User request / design | Pending |
| SNYK-01 | 3 | User request / design | Pending |
| SNYK-02 | 3 | User request / design | Pending |
| SNYK-03 | 3 | User request / design | Pending |
| SNYK-04 | 2 | User request / design | Pending |
| SNYK-05 | 2 | User request / design | Pending |
| RED-01 | 4 | User request / design | Pending |
| RED-02 | 4 | User request / design | Pending |
| ENV-01 | 2 | User request / design | Pending |
| ENV-02 | 4 | User request / design | Pending |
| OPT-01 | 4 | User request / design | Pending |
| STD-01 | 1 | User request / design | Pending |
| REPRO-01 | 4 | User request / design | Pending |
| IP-01 | 5 | User request / design | Pending |

## Release criteria

Both scanner coverage flags TRUE, zero reported findings across completed SCA/SAST, required behavior tests PASS, custody independently verified, rights approval recorded, and exact artifact identities match. 10/10 app-security-score is a tool score; event bonus is not automatically awarded.

## Out of scope

No live Overwatch mutation, inherited research publication, actual secret-exfiltration exercise, arbitrary mobile inference claim, or production vulnerability-free claim.


## Successor scope: all four web apps

- [ ] **FLEX-01**: Use Flexprice test mode with a synthetic customer and actual idempotent usage ingestion/readback. (Phase 3; user-requested extension)
- [ ] **FLEX-02**: Meter observed scan/task/token events and bind each to the execution receipt without granting security authority. (Phase 3; user-requested extension)
- [ ] **APP-01**: Use the actual BAND, Cognee OSS UI/API, Snyk and Flexprice surfaces; record workspace IDs and login gaps. (Phase 2; user-requested extension)

| Requirement | Phase | Status |
|---|---:|---|
| FLEX-01 | 3 | Pending |
| FLEX-02 | 3 | Pending |
| APP-01 | 2 | Pending |
