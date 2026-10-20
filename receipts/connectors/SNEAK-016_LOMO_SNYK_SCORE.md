# SNEAK-016 LOMO × merkle × Snyk/score

- Parent: SNEAK-015
- Chain root: `72e7a22ae6e2e46be6b09f60af3f5efb13603fd84a4dee08b8706fd11543f6ae`
- Human decision: **APPROVE** (BAND + Cognee @Data)
- Breakpoints scored: **8**
- Live Snyk availability: **NOT_TESTED**
- Any clean 10/10 with full coverage: **False**
- @Data recall hits (final): **5**

| Trial | Breakpoint | Merkle root (16) | Scan | Coverage | App score | @Data |
|---|---|---|---|---|---|---|
| LOMO-CONN-01 | `LOMO-CONN-01-BASE` | `dbc43d5f362b6ecb…` | NOT_TESTED | False | None | PASS |
| LOMO-CONN-01 | `LOMO-CONN-01-ABLATE` | `48def50e96aa136c…` | NOT_TESTED | False | None | PASS |
| LOMO-CONN-02 | `LOMO-CONN-02-BASE` | `cdd65ba461238b88…` | NOT_TESTED | False | None | PASS |
| LOMO-CONN-02 | `LOMO-CONN-02-ABLATE` | `e65cc4ad3dfa8295…` | NOT_TESTED | False | None | PASS |
| LOMO-CONN-03 | `LOMO-CONN-03-BASE` | `e642ae865a99ad13…` | NOT_TESTED | False | None | PASS |
| LOMO-CONN-03 | `LOMO-CONN-03-ABLATE` | `4bd90ea263901381…` | NOT_TESTED | False | None | PASS |
| LOMO-CONN-04 | `LOMO-CONN-04-BASE` | `b48cb5a7c93f2e4f…` | NOT_TESTED | False | None | PASS |
| LOMO-CONN-04 | `LOMO-CONN-04-ABLATE` | `799a8683c88990e4…` | NOT_TESTED | False | None | PASS |

Incomplete SCA/SAST coverage cannot yield application 10/10. Add `SNYK_TOKEN` to `~/.secrets/sneak/providers.env` for live scans.
Secret values are not included in this receipt.
