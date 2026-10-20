# SNEAK-020 FlexPrice actor audit (FCO / FCG / candidate MMR)

- Upstream: https://github.com/flexprice/flexprice
- Candidate Merkle root: `83e03fdc47de0a2d20ceb2e50da12176ba68b32fd445de127fe4ce22cbad2432`
- FCG digest: `7e29107c6113171a8452dc618d55137f70fe88db9687908840cf7a9a8976eaa0`
- Live FlexPrice: **NOT_TESTED**
- MMR: **NOT_COMMITTED**
- Actors: cognee, human, jerry, scanner, tom

## Per-actor deterministic ROI

| Actor | Events | Cost | Benefit | ROI |
|---|---:|---:|---:|---:|
| cognee | 1 | 0.03 | 0.25 | 7.333333 |
| human | 1 | 0.00 | 0.0 | None |
| jerry | 1 | 0.01 | 0.25 | 24.000000 |
| scanner | 2 | 0.02 | 0.25 | 11.500000 |
| tom | 1 | 0.02 | 0.25 | 11.500000 |

ROI = (benefit_units − cost_units) / cost_units with ROUND_HALF_EVEN to 6 dp.
Benefit schedule is fixed in `src/sneak/actor_audit.py`; not an awarded bonus.
