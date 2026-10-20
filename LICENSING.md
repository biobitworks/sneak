# Licensing matrix (preferred)

Preferred repository policy after operator direction: **most restrictive
Creative Commons (CC BY-NC-ND 4.0) with Apache-2.0** — applied as a **split**
matrix, not as a single universal dual license.

Merge of this lane into the public default branch is deferred until after the
hackathon window unless an operator explicitly merges earlier.

| Artifact class | Preferred license | SPDX | Notes |
|---|---|---|---|
| Original software (`src/`, `apps/`, `scripts/`, `tests/`, packaging) | Apache License 2.0 | `Apache-2.0` | See `LICENSE-APACHE-2.0` |
| Original docs / planning / narrative non-code | CC BY-NC-ND 4.0 | `CC-BY-NC-ND-4.0` | Most restrictive CC; not for code |
| Machine-generated receipts / hashes | Evidence artifacts | n/a | Custody data; not a grant of third-party IP |
| Upstream deps / `sources/` snapshots | Upstream LICENSE | pin per digest | Keep local until licensing resolved |
| Challenge PDFs / inherited research | Original owners | HOLD | Private access ≠ clearance |
| Vendor SaaS (BAND, Cognee Cloud, Snyk, Flexprice cloud) | Vendor ToS / plan | n/a | Separate from OSS file licenses |

## Why split (G7)

Do not apply CC BY-NC-ND as a universal code license. Do not assume public web
pages or datasets are CC BY 4.0. Preserve a license/SBOM inventory for code,
docs, figures, datasets, models, embeddings, videos, and logos.

## Files

- `LICENSE` — split overview (controlling map)
- `LICENSE-APACHE-2.0` — Apache 2.0 legal text
- `LICENSE-CC-BY-NC-ND-4.0` — CC BY-NC-ND 4.0 legal text
- `NOTICE` — attribution and third-party pointers

## Release posture

Public release of inherited research IP remains **HOLD**. This licensing lane
declares preferred terms for **original** BiobitWorks/sneak authorship only.
