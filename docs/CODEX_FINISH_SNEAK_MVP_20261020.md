# SNEAK MVP — Codex Implementation Recovery Task
Base feature branch: feature/sneak-mvp-20261020 in private biobitworks/sneak. Parent commit 979a4f7af5821e197a71eb960ca2ff2722f2e0e3. Read docs/CLAUDE_BUILD_SNEAK_MVP_20261020.md for frozen scope and security boundaries. Claude first pass stopped at max-turns=24; preserve its apps/sneak_mvp source files and build on them. Never mark incomplete work PASS.
Implement now, not just explain:
- Complete runnable Python 3.12 stdlib SNEAK HTTP server at 127.0.0.1 with polished public-facing graph/UI, actual graph/audit JSON endpoints; no badges on main page for every requirement.
- Complete deterministic context-aware AoK and security-gated Snyk CLI adapter, with explicit fail-closed semantics and source hashing. Integrate existing Cognee adapter as real OSS optional runtime, no fake mocked memory success.
- Add command-line python -m apps.sneak_mvp.server --port 8773 or documented real equivalent, .planning/SNEAK_MVP_20261020.md, README instructions, explicit Band Desktop human verification checklist (not observed yet), tests in tests/.
- Commit ONLY after executing unit tests and local HTTP smoke; log actual test counts, SHA identities and failures. Keep Snyk output in local-runs (gitignored), secrets never in logs or repo, no external uploads, no forced pushes.
- We have Band Desktop 0.4.16 installed and Claude plugin v0.5.33, daemon running but Band account NOT AUTHENTICATED. Cognee OSS CLI official demo PASSED with 47 nodes / 86 edges but SNEAK memory cross-session NOT_TESTED. Snyk CLI v1.1307.2 authenticated (snyk whoami byron); actual app scan pending. Mark mandatory atoms accordingly, do not claim acceptance or video.
- Avoid deleting predecessor and old receipts. No git clean, no reset, no push/merge or changes to main.
- Include tests for bad JSON, scanner exit >1, tampered evidence, same canonical bytes deterministic, HTTP endpoints. Don’t hard-code successful/healthy status for absent dependencies.
- After successful build, commit to current feature branch and report concise path, commit and pass counts; if blocked, write exact blocker and stop.
