# SNEAK Flexprice ROI instrumentation (candidate, NOT live metering)

## Controlled comparison

Use identical, pre-registered task IDs with and without SNEAK shared memory, identical model parameters and task success rubric. Record actual input/output token counts from model providers, Band run IDs, human active minutes, agent/model IDs, and human pseudonyms. Freeze the outcome rubric before inspecting runs. A human approval action is not automatically a successful task. Missing meter receipts are UNKNOWN, not $0.

The included fixture in data/demo/roi_trial_fixture.json is **SIMULATED**, with hypothetical USD-per-million-token and human hourly rates. It is a calculation fixture, not evidence of production savings, a model provider price quote, or event acceptance by Flexprice.

## Event contract

One Flexprice event per agent step, with deterministic event_id, external_customer_id, properties.tokens, prompt_tokens, completion_tokens, agent_id, model_id, human_id, task_id, scenario, evidence_class, and input_sha256. The content-addressed identity is NOT a project Merkle root. Before actual billing, provision a disposable test customer and check deduplication/readback and ledger reconciliation.

## Calculations

- Tokens consumed = prompt_tokens + completion_tokens
- Estimated token cost = tokens × assumed USD per million / 1,000,000
- Human time cost = active verified minutes × assumed hourly rate / 60
- Total estimated cost = token cost + human time cost; inference compute, infrastructure and retrieval charges omitted unless measured and included explicitly
- Token reduction = (baseline tokens - SNEAK tokens) / baseline tokens, when tasks match
- Cost reduction = (baseline cost - SNEAK cost) / baseline cost, when success quality matches
- Cost per verified successful task = total measured cost / independently verified successes. Zero successes means NULL (not infinity or zero)
- Gross ROI requires monetized incremental benefit and complete implementation cost. Cost reduction alone is not ROI.

## Test execution and state

Run `python3 -m unittest tests.test_flexprice_roi_trial -v` and `python3 scripts/flexprice_roi_trial.py`. Tests exercise deterministic serialization, source matching, per-agent/model/human aggregation, and **local mock HTTP 202**. A mock acceptance is NOT live Flexprice metering.

A real endpoint is intentionally blocked for simulated fixture inputs even with --send. Integrate real per-step telemetry, then construct a distinct receipt-bound live protocol. Do not put real API keys in Git or Vercel public static data.

State: Flexprice-compatible payload BUILT/LOCAL_MOCK_TESTED; real billing NOT_TESTED; historical run ROI NOT_COMPUTED; SNEAK global project MMR/Anticube/ΔG* NOT_COMPUTED.
