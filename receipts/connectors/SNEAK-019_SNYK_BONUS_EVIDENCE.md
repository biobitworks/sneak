# SNEAK-019 Snyk event-bonus evidence (LOMO × merkle × Javier × BAND)

- Chain root: `e630fe1ef0be1d37eb10435aa0ef674119286f9310b48a0cfb72d0622774c097`
- Package digest: `5de2ed18d2061a7547de740d5532945b5ed1e555d901c954822bf8c60469ee3e`
- BAND message leaf/root: `11d0558aef0db4b1f161a3e7e0bc0ce0e51f94ead97cc656a6fb6ef0a0aea102`
- Event bonus claim: **EVIDENCE_PREPARED** (awarded=false)
- Javier scoring source: `https://github.com/javiergarza-snyk/app-security-score` @ `6e1f27605fe278eed347b10dab6f39b3501f1486`
- Javier pin match: **True** (node_helper_match=True)
- LOMO breakpoints scored: **8**
- Live Snyk: **NOT_TESTED**
- Staged digest: `9ec4bcb4838610330c72e2017950bbfbb197e471c1349cb0023f5b490f05984a`
- BAND review: **PASS**
- Cognee lesson: **PASS**

## Criteria

| ID | Status | Observed |
|---|---|---|
| J-007 | EVIDENCE_PREPARED | WORKFLOW_INTEGRATED_PENDING_LIVE_SCAN |
| SNYK-001 | PARTIAL | NOT_TESTED |
| SNYK-002 | PARTIAL | BAND_HANDOFFS_AND_COGNEE_LESSON_RECORDED |
| REQ-AOK-S01 | PARTIAL | NOT_TESTED |
| REQ-AOK-S02 | PASS | STAGED_DIGEST_BOUND |

Judges decide any +10%. This package only prepares custody-bound evidence.
Add `SNYK_TOKEN` to complete live SCA/SAST toward tool score 10/10.
