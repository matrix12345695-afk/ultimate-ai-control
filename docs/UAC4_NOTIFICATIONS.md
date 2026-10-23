# ULTIMATE 4.0 owner notifications

This increment preserves the installed 3.1 code base (3e66bea9d9ff02b33167578695d2702beb638a97).
The older feature/uac4-owner-notifications-20261022 branch supplied the initial inbox module.
No Inventory source, configuration, database, process or service is modified.

## Delivery

SQLite is the durable outbox. INFO, DECISION and CRITICAL are prioritized. Event keys deduplicate
producer events across dispatcher restarts. One Telegram receipt stores the message ID and time.
Delivery does not resolve a decision and never grants deployment/payment approval.
Failures use exponential backoff, respect Telegram retry_after and stop after eight attempts.
Permanent HTTP failures are retained for inspection, not retried continuously.
Crash recovery reclaims a delivery lease after five minutes. Network ambiguity can cause a duplicate.
`/owner_inbox` shows unresolved requests, including delivered requests awaiting a decision.
Website transitions, GitHub monitoring and backup failures now produce durable notifications.
Other agent blockers still need producer integration.

## Existing host supervision

The audited installation is /home/maksim/.ultimate-review-runtime, with SQLite in
/home/maksim/.ultimate-review-data/live/control.db. It uses ops/start-rootless.sh,
a private owner-provisioned configuration, flock, a restart loop, and a per-minute cron entry.
It has no dedicated systemd unit. Do not start a second polling process or reuse Inventory credentials.

## Rollout

Use the pinned script in inventory-bot/uac-transfer-staging-20261023/uac_transfer/ops.
The bridge only transports this script. Application source comes from the ULTIMATE repository
at a full commit SHA. Preflight tests the exact release with a temporary HOME and DB, verifies
the installed SHA, token separation, backup and restored-copy integrity, and Inventory identity.
Deployment backs up the existing DB, checks out the tested descendant commit, creates a single
test event, restarts only the exact ULTIMATE dispatcher and verifies its persisted Telegram receipt.
The prior SHA and backup path are recorded in a private rollout state file.
Rollback checks out that prior SHA and restarts only ULTIMATE. Additive notification tables can
remain in the database; this avoids discarding tasks/messages created after the backup.
Full database restore requires stopping ULTIMATE and explicitly choosing the verified backup.

## Scope retained from the owner's handover

One VPS; OpenAI API budget USD 30/month; no purchases or budget increases.
Production publication requires approval for that specific release/project.
Inventory is excluded from changes. Draft development, tests and isolated ULTIMATE installation
are authorized. No permission expansion or disabling of safeguards during self-improvement.
The full autonomous company, speech input, detailed work-time accounting and universal project
integration are future increments, not capabilities delivered by the notification rollout.
