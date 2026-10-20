# SNEAK-030 Cognee custody chain (over time)

- Cognee live: **True**
- Custody merkle root: `2a89def65e0238d5452d65057e3a90a732586dcf1bb55dfa2dbb43376581ba25`
- All leaf travels verify: **True**
- MVP root (SNEAK-029): `8d1036e3bbaa64231dee0e0873a5f3e040192a14752967b5f9526d18ab5dc6ef`
- Pre-audit captured: **['SNEAK-015', 'SNEAK-016', 'SNEAK-018', 'SNEAK-019', 'SNEAK-024']** gaps: **1**
- Post-audit captured: **['SNEAK-015', 'SNEAK-016', 'SNEAK-018', 'SNEAK-019', 'SNEAK-024', 'SNEAK-029']** gaps: **0**
- Backfill SNEAK-029: **True**
- BAND finalize ok: **True** planner_online: **True**
- MMR: **NOT_COMMITTED**; signed: **False**; bonus awarded: **False**

## Why the chain was incomplete

- **SNEAK-029** (`sneak_working_memory`): run_mvp_hash_travel.py posted BAND awareness but never called MemoryAdapter/DataBackend; mvp_root stayed receipt-local only

- Intermediate SNEAK-020–028: expected receipt/BAND-only (not every successor writes Cognee).

## Epoch recall (post-audit)

| Epoch | Dataset | Captured | Hits | Missing markers |
|---|---|---|---|---|
| SNEAK-015 | `sneak_working_memory` | **True** | 6 | `—` |
| SNEAK-016 | `Data` | **True** | 8 | `—` |
| SNEAK-018 | `Data` | **True** | 8 | `—` |
| SNEAK-019 | `Data` | **True** | 8 | `—` |
| SNEAK-024 | `sneak_working_memory` | **True** | 6 | `—` |
| SNEAK-029 | `sneak_working_memory` | **True** | 6 | `—` |

## Planner finalize

- Room: `7e218ad7-4d4e-4a07-a3b2-d4db8a03b4c3`
- Message id: `ed15232f-87d1-4ffc-ba3f-2b6c1a0367a8`
- Active tasks: **10** (human #6/#7 remain open)

