# Javier app-security-score (pinned)

- Upstream: https://github.com/javiergarza-snyk/app-security-score
- Pin: `6e1f27605fe278eed347b10dab6f39b3501f1486`
- Local clone: `sources/app-security-score/` (**gitignored**; license UNKNOWN)
- Python reimplementation: `src/sneak/score.py`

## Scale (important)

| Value | Meaning |
|---:|---|
| **10** | Clean: zero findings **and** both SCA + SAST coverage completed |
| **0** | Worst: many findings / hard cutoff — **not** a bonus |
| `null` application_score | Incomplete coverage — wrapper rejects even if raw math is 10 |

Event judging may separately award **up to +10%** for real Snyk integration. That bonus is **not** the tool score and is **not** awarded by this repo automatically.

## Setup / review

```bash
# clone stays local/gitignored
# python pin + node cross-check + @Data + hashed BAND review:
python3 scripts/setup_and_review_score.py
```

Live scan still needs `SNYK_TOKEN` in `~/.secrets/sneak/providers.env` and Snyk CLI.
