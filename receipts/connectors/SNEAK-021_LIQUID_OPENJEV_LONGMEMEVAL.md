# SNEAK-021 Liquid AI + OpenJev × LongMemEval (FCO + token ROI)

- Qwen 2.5: **retired**
- Models: **Liquid AI LFM** + **OpenJev**
- Candidate Merkle root: `fec8ca93aa7f7638c881a6627cb729cd86c651680801e60505e7b1851653ced7`
- Conversation FCOs: **6**
- LongMemEval diff FCOs: **6**
- Live Liquid key: **False**
- MMR: **NOT_COMMITTED**

## Per-token ROI by scenario / model / agent

| Scenario | Model | Agent | Tokens | Cost | Benefit | ROI | Benefit/token |
|---|---|---|---:|---:|---:|---:|---:|
| fixture_lme_gps_001 | liquid | liquid-agent | 110 | 0.00000330 | 0 | -1.000000 | 0.000000 |
| fixture_lme_gps_001 | openjev | openjev-agent | 36 | 7.2E-7 | 0 | -1.000000 | 0.000000 |
| fixture_lme_bike_002 | liquid | liquid-agent | 92 | 0.00000276 | 0 | -1.000000 | 0.000000 |
| fixture_lme_bike_002 | openjev | openjev-agent | 28 | 5.6E-7 | 0 | -1.000000 | 0.000000 |
| fixture_lme_phone_003 | liquid | liquid-agent | 86 | 0.00000258 | 0 | -1.000000 | 0.000000 |
| fixture_lme_phone_003 | openjev | openjev-agent | 32 | 6.4E-7 | 0 | -1.000000 | 0.000000 |

Full LongMemEval corpus stays under `sources/` (gitignored) when downloaded;
this run uses `data/fixtures/longmemeval_oracle_sample.json`.
