# SNEAK-014 connector review

- Parent breakpoint: SNEAK-013
- Merkle root: `47520bd79734519d9f28a7191496818ff6f0ac594e84000140bb8ed11de971a7`
- Demo staged digest: `72ba2e707fdcc01721e8e8e0a33e6378d303d446eee3f75271cfcb98c23c1fc2`
- Entry gate: **False** (0/30 mandatory verified)
- Live connectors all ready: **False**
- Javier helper pin: `6e1f27605fe278eed347b10dab6f39b3501f1486`
- Live SCA/SAST: NOT_EXECUTED (no SNYK_TOKEN / snyk CLI in this environment)
- Human decision: PENDING (loaded BAND receipt does not approve)
- LOMO connector trials: 4 one-component successors; all roots differ
- Local ablation cognee_changes_behavior=True, band_removal_blocks_approval=True

Mandatory vs bonus/optional remain distinct. A local 10/10 helper result under a
fixture is not a live scan and is not an awarded event bonus.
