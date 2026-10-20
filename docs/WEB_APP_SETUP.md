# Web app setup and evidence contract

Status: PREPARED; no authenticated workspace, room, scan or billing resource has been created.

| Product | Entry point | Required action | Evidence before claiming integration |
|---|---|---|---|
| BAND Desktop + web | https://app.band.ai and https://docs.band.ai/band-desktop | Sign in, install verified Desktop runtime on an available Mac, create private Skill Custody Lab room and connect two agents | Room/work-item IDs, actual handoffs, human decision, session/token/cost view |
| Cognee OSS web UI | https://docs.cognee.ai/api-reference/introduction | Deploy pinned OSS API/UI in project-isolated environment; create candidate/admitted namespaces | Actual write, restart or second-agent recall, resulting changed action |
| Snyk web | https://app.snyk.io/account | Operator supplies scoped token to the private local file; create/select project organization | Org/project/scan IDs, exact target digest, SCA/SAST coverage, raw reports and score |
| Flexprice web | https://docs.flexprice.io/docs/getting-started/cloud | Sign in and select test environment; create synthetic customer and skill_scan_completed/agent_task_completed meters | Meter/customer/event IDs, idempotent ingestion/readback, test usage totals |

The supplied rules explicitly call for Cognee Open Source. Hosted Cognee Cloud may assist evaluation but does not silently replace this requirement.
Current BAND documentation uses band CLI and jamd daemon; the supplied PDF mentions jam. Preserve both source versions and verify the installed runtime commands.
No provider cloud account creation, legal-term acceptance, paid plan, real invoice, payment collection or public release is claimed.
Flexprice uses synthetic events with idempotency keys bound to run receipts; token/cost values are recorded only when observed.
Billing must never grant security authority. Insufficient credits can block a task, but purchased credits cannot override failed security admission.
Connection failures remain BLOCKED or NOT_TESTED rather than becoming successful mock integrations.
