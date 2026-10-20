# Claude independent red team — integration successor
Parent: SNEAK-008 / frozen R5; preserve all historical receipts. Repo branch: integration/band-cognee-snyk-20261020.
1. Verify exact scan target commit ee7432bf551451fc620df270a86a986a23000d46. Do not claim the branch's new code was scanned by that historical run.
2. Re-run unit tests, inspect every independent run result, confirm raw SARIF digest and Snyk CLI exit statuses. Confirm code PT findings, validate risk only with repros in disposable sandbox.
3. Inspect agent model/tool boundaries for injection, arbitrary executable paths, LLM control of approval, key exposure, dataset cross-tenant access, and inadequate prompt enforcement.
4. Reproduce Cloud tenant synthetic memory receipt WITHOUT trusting it as Cognee OSS compliance. Test OSS on authenticated, isolated persistent runtime after human authorizes its setup.
5. Check BAND/Desktop/CLI/daemon and all 30 mandatory atoms against live provider evidence. The human approval must occur IN BAND. Three agent definitions in source are not three connected runtimes.
6. Execute a LOMO control comparing no-memory vs Cognee recall and no-Band vs Band, recording actual task effects. Identity-only ablation is not behavioral evidence.
7. Check code/test license and source rights; never upload user's proprietary biological datasets to SaaS.
8. Create your own successor red-team branch and PR with FAIL/PASS/UNKNOWN receipts. Do not overwrite original branch or main. Ask the human to explicitly approve merging a reviewed patch.
