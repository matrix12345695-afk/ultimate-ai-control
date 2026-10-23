# Metered provider rollout evidence

Observed 2026-10-22 UTC. Draft PR #26; source branch feature/uac4-metered-provider.

## Installed and checked

- Application commit: `ace13302ccf97e633d5bf84790c6944c0d873d8f`.
- Runtime: `/home/maksim/.ultimate-review-runtime`.
- SQLite: `/home/maksim/.ultimate-review-data/live/control.db`.
- Private provider policy: `/home/maksim/.ultimate-review-data/live/provider-policy.json`.
- Policy is mode 0600 and enabled=false. No real model key was read, provisioned or changed.
- Automatic queue/model calls remain disabled; the dispatcher and operations worker do not
  load a model key. No new credential process, shared service, Docker privilege or OS package
  was installed. Existing UAC cron/flock supervisors continue to manage one worker and poller.
- All 266 tests passed on the VPS with zero skipped, including seven real sandbox tests and
  eleven fake-response financial/transport tests. Twelve transport checks also passed.
- Backup restore and additive migration were verified on a separate SQLite copy.
- The live disabled guard was exercised with an absent key and a transport that raises if
  called: it rejected the request before network I/O or any reservation.
- /provider4, /sandbox, /artifact 2 and existing runtime commands were exercised against the
  live database. Earlier artifact source/report history and existing schedules were retained.
- A fresh queued sandbox boundary test succeeded after the final update.
- Accounting tables contain zero real API requests, zero held cost and zero settled spend.
- Telegram accepted activation message 168; the receipt is persisted. Acceptance is not a
  read receipt from the owner.
- Worker PID: 699889. Sole Telegram poller PID: 700270.
- Inventory PID remained 67760; source fingerprints and configuration metadata matched.
- NOVA recorded HTTP 200. No other project source, deployment, domain, database or service
  was modified. No paid call, purchase, merge or production publication occurred.

Final rollout: https://github.com/matrix12345695-afk/inventory-bot/actions/runs/39859094868
CI: https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/39859087399
Verified backup:
`/home/maksim/.ultimate-review-data/backups/before-uac4-1792705229206766448.sqlite3`.

## Financial fault coverage

The tests cover reservation-before-I/O, exact cached-token costs with integer rounding,
concurrent duplicate request keys, durable replay, disabled policy, missing/private keys,
wrong model or tier, missing/excessive usage, cache writes, redirects, secret-bearing prompts,
refusal/tool/incomplete output, the hard $30 ceiling, deduplicated budget notices, timeouts,
restart recovery, old unresolved holds and calls crossing into a new UTC billing month.
They use deterministic artificial API responses. Actual OpenAI billing receipts, model
quality and account access remain unverified until private configuration and an explicit
real test. The local application ledger does not observe unrelated OpenAI account activity.

## Rollback and next gates

Pinned action uac4_provider_rollback validates this exact release and its recorded prior
commit `9f778ce678a491f8b7b3f99c321b961a41d5cb2b`. It restores UAC code and restarts only its
exact worker and dispatcher. Known existing disabled policy, sandbox configuration, accounting
history, tasks and artifacts are preserved. Unknown/changed provider policies are rejected,
not overwritten. Restoring a stale database is not part of routine code rollback.

Roadmap stage 3 is active, not complete: a priced transport is installed but a private
credential broker, queue integration, key setup and real usage verification still remain.
Stage 4 still supplies fixed offline recipes rather than general LLM development. No new
automatic ChatGPT message ingestion or release permission was introduced.

Independent verification after the deployment Actions job exited also passed, with the same
worker/poller PIDs, disabled-policy network guard and persisted Telegram receipt:
https://github.com/matrix12345695-afk/inventory-bot/actions/runs/39859321039.
