# NOVA application readiness

Availability of the homepage and readiness of the application are separate observations.
The new nova-readiness target performs only GET https://novaweb.uz/health, with no database
credentials or application write request. The response contract was reviewed in the pinned
NOVA server and independently observed as HTTP200 JSON with ok=true, storage=postgres and
version=sales-funnel-v1. This is the application's public database-ping/readiness report,
not direct database administration or acceptance testing of all business operations.

The monitor requires HTTP200, application/json, identity content encoding, at most 8192 body
bytes, strictly parsed JSON with unique keys, a boolean readiness verdict, PostgreSQL storage
and the reviewed response version. Redirects, HTML200 pages, ambiguous/nonstandard JSON,
temporary/unavailable storage and unexpected versions cannot pass. The request timeout is
12 seconds inside the existing 30-second worker limit. No body or connection/error payload
is persisted: the journal contains only fixed check names, booleans, status, byte count,
contract ID and a SHA-256 fingerprint. A successful HTTP code alone cannot resolve an alarm.

Readiness has its own target snapshot and incident history. Job identity still belongs to
the nova project. Health completion, outbox messages, recovery resolution and queue completion
remain one SQLite transaction under the current job lease. Page checks can close only page
alarms; readiness checks can close only readiness alarms. Other owner decisions and criticals
remain untouched. Repeated failures retain one incident; a later valid ready response closes
it and creates a recovery notification. Delivery is retryable and distinct from owner approval.

`/readiness4` and the Check API button enqueue a read-only check. `/monitor4` shows both saved
targets, timestamps and per-check verdicts. The existing VPS operations scheduler gains a
single 15-minute readiness entry; no new process, cron service or hourly ChatGPT development
automation is created. That canceled development automation remains disabled. The shared
queue pause and concurrency/resource limits still apply to both monitors.

Only ULTIMATE is updated. NOVA source, hosting, webhooks, credentials, business data and
deployment are unchanged; Inventory remains protected. Readiness failure is reported as an
actual observation, not fixed by modifying the production site. Rollback disables only the
matching readiness schedule, drains ULTIMATE work and cancels unsupported queued readiness
checks with audit while retaining successful results and incident history. It preserves any
owner pause and leaves the homepage monitor alone.

Tests cover false-positive HTTP200, content limits/types, duplicate/deep/nonstandard JSON,
redirects, errors without private payload leakage, fake evidence, independent incidents,
deduplication, expired leases, rollback on transaction error and the live journal view.
Actual server rollout/check/Telegram evidence belongs in PROJECT_STATUS.md after verification.
