# Cognee memory + AoK/FCO provenance — PROPOSED

The project needs **Cognee Open Source as active shared agent memory**, not just a static graph import.

## Two complementary systems

1. **AoK/FCO/FCG intake:** deterministic source attribution, context-specific candidate requirements, typed evidence links, local cryptographic snapshot. Source quotes are distinguished from operational conclusions. Candidate status is not canonical admission.
2. **Cognee OSS:** memory store that agents *write during work and later retrieve*, changing subsequent agent actions across restart or between independently identified agents. Memory records link back to requirement ID, source SHA-256, AoK occurrence, and contextual FCO candidate ID.

## Memory events and acceptance

| Memory event | Expected content | Test |
|---|---|---|
| `requirement_imported` | req ID, source anchor, optionality, candidate FCO ID | Search for the matching requirement and cite its source span |
| `decision_recorded` | Human decision, scope, superseded option, signer/room receipt | Second agent retrieves and changes its plan |
| `review_finding` | Snyk scan evidence or independent finding, artifact revision, block status | Builder retrieves issue and fixes without restating it |
| `usage_policy` | Flexprice meter/entitlement decision, current revision | Billing agent retrieves and respects limit |
| `memory_corrected` | Correction with predecessor preserved | Updated retrieval selects successor, old value remains traceable |

**Replay experiment (NOT_TESTED):** Agent A obtains a requirement and writes a consequential interpretation or human-approved decision. Kill/restart A or start agent B. Agent B first responds without that memory, then retrieves from Cognee and takes a different, attributable action. Persist request IDs, query, results, decision/action diffs, and optional negative control.

**Controls:** If a Cognee LLM vendor or storage sends data off-device, exclude proprietary source bytes and personal information until confidentiality and licenses are reviewed. Cognee-generated inferred edges are not automatically source-backed AoKs. `improve` or `forget` are optional extra credit but require a proof of effect, not just an API response. Do not infer success from a static import.