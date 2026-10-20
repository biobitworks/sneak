# SNEAK — GitHub branch/PR review for humans

**Snapshot:** 2026-10-20T21:47:55.166023+00:00 · **Repository:** private biobitworks/sneak
**PRs:** 15 observed, 14 open draft, 1 merged. No unauthorized merges/closures. All branch heads below are observed origin refs, not claims that integration tests passed.

## Review queue and evidence gates

| PR | Lane | Base | State | Head SHA | Human decision | Reviewer / source-proof URL |
|---|---|---|---|---|---|---|
| [#2](https://github.com/biobitworks/sneak/pull/2) | `custody/markdown-exact-20261020` | `main` | DRAFT | `d93dc18c7453` | ☐ KEEP ☐ MERGE ☐ CLOSE ☐ NEEDS_FIX | __________ |
| [#3](https://github.com/biobitworks/sneak/pull/3) | `integration/band-cognee-snyk-20261020` | `main` | DRAFT | `b81526598873` | ☐ KEEP ☐ MERGE ☐ CLOSE ☐ NEEDS_FIX | __________ |
| [#4](https://github.com/biobitworks/sneak/pull/4) | `redteam/claude-20261020` | `main` | DRAFT | `9050deb164ed` | ☐ KEEP ☐ MERGE ☐ CLOSE ☐ NEEDS_FIX | __________ |
| [#5](https://github.com/biobitworks/sneak/pull/5) | `cursor/connector-custody-review-0c2f` | `main` | MERGED | `e8766554ca39` | ☐ KEEP ☐ MERGE ☐ CLOSE ☐ NEEDS_FIX | __________ |
| [#6](https://github.com/biobitworks/sneak/pull/6) | `onboarding/teammate-fco-handoff` | `main` | DRAFT | `2e236b745564` | ☐ KEEP ☐ MERGE ☐ CLOSE ☐ NEEDS_FIX | __________ |
| [#7](https://github.com/biobitworks/sneak/pull/7) | `feature/sneak-mvp-20261020` | `main` | DRAFT | `7793cfe68427` | ☐ KEEP ☐ MERGE ☐ CLOSE ☐ NEEDS_FIX | __________ |
| [#8](https://github.com/biobitworks/sneak/pull/8) | `docs/merkle-mmr-knowledge-base` | `onboarding/teammate-fco-handoff` | DRAFT | `edf9cbe2e776` | ☐ KEEP ☐ MERGE ☐ CLOSE ☐ NEEDS_FIX | __________ |
| [#9](https://github.com/biobitworks/sneak/pull/9) | `integration/sneak-consolidation-20261020` | `feature/sneak-mvp-20261020` | DRAFT | `87349928e19a` | ☐ KEEP ☐ MERGE ☐ CLOSE ☐ NEEDS_FIX | __________ |
| [#10](https://github.com/biobitworks/sneak/pull/10) | `cursor/snyk-bonus-lomo-band-0c2f` | `main` | DRAFT | `40fdb8c6e63b` | ☐ KEEP ☐ MERGE ☐ CLOSE ☐ NEEDS_FIX | __________ |
| [#11](https://github.com/biobitworks/sneak/pull/11) | `deploy/sneak-vercel-preview-20261020` | `feature/sneak-mvp-20261020` | DRAFT | `17089227b2c2` | ☐ KEEP ☐ MERGE ☐ CLOSE ☐ NEEDS_FIX | __________ |
| [#12](https://github.com/biobitworks/sneak/pull/12) | `integration/sneak-audit-fco-20261020` | `main` | DRAFT | `89b96e98f1b6` | ☐ KEEP ☐ MERGE ☐ CLOSE ☐ NEEDS_FIX | __________ |
| [#13](https://github.com/biobitworks/sneak/pull/13) | `evaluation/lmev2-security-20261020` | `integration/sneak-audit-fco-20261020` | DRAFT | `6a7b342c0e00` | ☐ KEEP ☐ MERGE ☐ CLOSE ☐ NEEDS_FIX | __________ |
| [#14](https://github.com/biobitworks/sneak/pull/14) | `feat/breakpoint-mmr-ledger` | `docs/merkle-mmr-knowledge-base` | DRAFT | `727cd02469c9` | ☐ KEEP ☐ MERGE ☐ CLOSE ☐ NEEDS_FIX | __________ |
| [#15](https://github.com/biobitworks/sneak/pull/15) | `feature/conversation-federation-mmr-20261020` | `evaluation/lmev2-security-20261020` | DRAFT | `5a9c5a73f6d0` | ☐ KEEP ☐ MERGE ☐ CLOSE ☐ NEEDS_FIX | __________ |
| [#16](https://github.com/biobitworks/sneak/pull/16) | `integration/cognee-flexprice-r14` | `main` | DRAFT | `e2b69c1ddd5b` | ☐ KEEP ☐ MERGE ☐ CLOSE ☐ NEEDS_FIX | __________ |

## Owner review before any merge or close

1. Check the PR diff, exact HEAD, tests, provenance and security scan for that HEAD; list any merge-base conflicts.
2. Preserve FAILED, NEGATIVE, NULL, NOT_TESTED and NOT_COMPUTED predecessor artifacts; a branch's root is not a universal global root.
3. For merge: independently verify matching acceptance atoms, source rights, Snyk Code/OSS coverage and owner approval. Do not merge stacked dependencies out of order.
4. For close: cite exact duplicate/superseding PR and retained commits/receipts. No PR has been closed by this snapshot.
5. Reconcile private devices separately. Local magicPRObox main remains diverged; do not force-push origin/main. Custody change is preserved on its own branch.

## Status that is not PR readiness

The 30 mandatory hackathon atoms remain unverified in the existing registry. BAND live planner room authorization and board transitions remain unverified. Cognee OSS local write/read and read-only Vercel rendering passed in bounded receipts. Snyk Code and OSS are blocked by authentication/dependency errors; Flexprice billing evidence remains incomplete. The user authorized development, not an organizer award.

## Source identity

GitHub PR listing bytes SHA-256: `7484f70c10d45249157742033d277f65e8cf78e9eb506c1e5d736622c94af4ce`.
GitHub main tracked commit: `a67be28f278e9131ff585cb6861e3500b671ab18`.
PR states may have changed after the snapshot; use a new dated audit before relying on it.
