# LEVEL 2: AI EXECUTOR POLICY
Version: 0.2 (architecture specification, not active AI execution)

## Operating contract
The supervisor orchestrates tasks. Project adapters are separate and have least-privilege credentials. An external AI model is optional and DISABLED by default. No paid service may be activated without explicit owner approval.

## Permissions
AUTO (non-destructive): read allowlisted project metadata and logs, health checks, prepare local sandbox changes, create proposals in isolated branches, test in sandbox, summarize and report. Never include secrets in reports.
APPROVAL REQUIRED: deploy or merge to production branches, modify live data, create billable resources, send external messages representing the owner, change access controls, delete anything, rotate credentials.
DENIED: bypass approval, run arbitrary shell from Telegram messages, expose tokens, disable audit logs, transfer sensitive Kinder Spa client/child information to unapproved AI vendors.

## Task state machine
queued -> triage -> analyzing -> preparing -> testing -> awaiting_approval -> approved -> executing -> verifying -> completed
Failure from any step -> failed, with audit entry. Rejection -> rejected. Halt after rejected; no automatic retry of sensitive action.
Approval binds task ID, immutable artifact digest, target environment, exact action, expiry and approver ID. Changed artifact requires new approval.
A Telegram reply alone does not confer approval unless validated against an active approval request.
Timeout and outage must fail closed.

## Isolation / limits
Each project has separate scopes, data root and tokens. Production credentials never enter model prompts. Max concurrent jobs 1 at first. Per-project budgets default to zero. Build/test jobs are time and resource constrained and do not have prod access.
Idempotency key for external side effects; backups and rollback planned before approved deployment. Hourly heartbeat; alert only for real failures, approvals or completed tasks.

## Initial connectors roadmap
1. NOVA WEB: HTTPS monitor and read-only GitHub inspection.
2. Inventory: read-only metrics and alerts.
3. SAP/iiko: manual upload and reconciliation in isolated runner.
4. Kinder Spa: specification and dev-only tests; no child data until reviewed safeguards.
5. QualiSift: dev workspace only.

## Launch gates
GitHub stores source code, not an always-on process. A running host, dedicated Telegram token, admin ID, secrets management, audit log, backups, test runner, external integration credentials and explicitly authorized model provider are needed before describing the system as autonomous.
