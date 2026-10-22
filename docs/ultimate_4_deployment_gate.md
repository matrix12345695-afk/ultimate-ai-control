# ULTIMATE AI CONTROL 4.0: isolated deployment gate

Status: NOT DEPLOYED. This is a read-only checklist, not a deployment authorization bypass.

## Preconditions (all required)
1. Run full unit tests on the exact Git commit: `python3 -m unittest discover -s tests -v`.
2. Execute a separate dry-run in a temporary directory with temporary SQLite and no Telegram credentials.
3. Confirm existing Inventory Bot location, runner user, services, occupied ports, free RAM/disk and backup health using read-only host diagnostics.
4. Create dedicated non-privileged service user and directory for ULTIMATE; never reuse `/home/maksim/inventory-bot`, its `.env` or its database.
5. Ensure only one Telegram polling process handles the ULTIMATE bot token. Do not reuse the Inventory Bot token.
6. Back up existing ULTIMATE data and verify restore in an isolated location before switching any service.
7. Do not deploy if tests, isolation, backup, or rollback checks fail. Request owner approval for any risky action or cost.
8. After an isolated installation, send one explicit test notification; verify Telegram delivery and that Inventory Bot remained healthy.
9. Run `/owner_inbox` on the ULTIMATE bot; confirm it contains pending items.
10. Record deployed SHA, health status, rollback route, and actual outcome.

## Notes
The server bridge in `inventory-bot` has a default project path pointing to Inventory Bot. Its `deploy` action MUST NOT be used to deploy ULTIMATE.
Local notification queue delivery is at-least-once, not strictly exactly-once. Retry after ambiguous Telegram network failures may duplicate messages.
The current notification producer is not wired into all real agent blockers. Deploying the dispatcher alone does not constitute a complete end-to-end owner notification feature.
