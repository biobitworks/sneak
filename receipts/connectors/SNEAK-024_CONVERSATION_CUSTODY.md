# SNEAK-024 Conversation custody (merkle breakpoints + model MMR deltas)

- Parent: SNEAK-023
- Root question leaf: `18a20558e2f1f8342c7c7e5352f9519af0e174fbca66502e5da2ea224e7a7634`
- Project connector root: `8987773f8f12d598d1d3ecda4b2a05a710ccc56005d011c443ba7bcdd426888f`
- Breakpoints: **4** (pass=3, fail=1)
- Update FCOs: **4**
- MMR: **NOT_COMMITTED** (never claimed)

## Pipeline

`input_hash` → deterministic step FCOs → `output_hash` → unique BP `pass: true|false`

Per-model candidate MMR peaks vs root question (XOR distance deltas over time).

## Model MMR trails

| Model | Peaks | Latest bagged root | Latest vs root-Q XOR |
|---|---:|---|---:|
| `liquid-lfm` | 2 | `878683303169a4aa…` | 123 |
| `openjev` | 1 | `00c9e0d61a2ecf68…` | 135 |
| `planner-remote` | 1 | `e49450f3ff512de6…` | 136 |

## BAND + Cognee + Planner

- Room: `7e218ad7-4d4e-4a07-a3b2-d4db8a03b4c3`
- Ask message ok: **True** id=`2f16e6f2-5d2b-4d53-946d-b6d22702b05f`
- Planner in room: **True**; online: **False**
- Board task #: **9**
- Cognee: outcome=`PASS` add_ok=True

## Requirements (mandatory + optional)

| ID | Kind | Outcome | Verified | Statement |
|---|---|---|---|---|
| REQ-CUSTODY-01 | mandatory | PASS | True | Unique merkle breakpoints for each conversation so they reco… |
| REQ-CUSTODY-02 | mandatory | PASS | True | Each merkle breakpoint carries pass true|false… |
| REQ-CUSTODY-03 | mandatory | PASS | True | Each model has candidate MMR vs root question with delta ove… |
| REQ-CUSTODY-04 | mandatory | PASS | True | input hashed → deterministic script steps/FCO → output hashe… |
| REQ-CUSTODY-05 | mandatory | PASS | True | Updates hashed through FCO tracking successors… |
| REQ-CUSTODY-06 | mandatory | PASS | True | BAND used to ask and respond among agents… |
| REQ-CUSTODY-07 | mandatory | PASS | True | Cognee @Data captures sneak custody information for breakpoi… |
| REQ-CUSTODY-08 | mandatory | PASS | True | All agents and planner updated in the conversation… |
| REQ-CUSTODY-09 | mandatory | PASS | True | Check with planner in band.ai chat that has a planner… |
| REQ-CUSTODY-10 | optional | NOT_TESTED | False | Live model inference (Liquid/OpenJev) bound into custody tur… |
| REQ-CUSTODY-11 | optional | NOT_TESTED | False | Project MMR Overwatch commitment (SIGNED/MMR_COMMITTED)… |
