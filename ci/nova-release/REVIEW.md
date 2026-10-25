# NOVA release restart rehearsal,2026-10-25

Purpose: prove exact baseline1a23239a -> candidate495a7f1a -> baseline1a23239a
HTTP bytes/readiness and preservation of all four public CRM tables, including
fixture data written during the candidate phase. This is a hosted local process
rehearsal, not an executed Render rollback or a zero-downtime certification.

Both28-file snapshots are downloaded by immutable commit and Git blob; GitHub
comparison must show only index.html modified. The existing reviewed pg8.23.1
14-package integrity lock, Node24.21.0, official PG16 image digest, resource limits
and pinned actions are reused from ci/nova-postgres/REVIEW.md. No new dependency.
Original14 test files/34 tests run unmodified against the candidate, serially.
Then15 fail-fast checks start the exact NOVA server and send real loopback HTTP:
source scope; baseline bytes/headers/readiness/disabled intake; fixed fake rows in
leads/events/update dedupe/reminder tables; rejection of unauthenticated writes;
a failed candidate on a deliberately unused local DB port with old HTTP service
still available; candidate bytes/readiness/demo/SEO routes; unchanged old rows;
one fixture write per table while candidate is active; baseline restart and exact
bytes/readiness restored, retaining all old and candidate-era data without DB restore.
The failed-candidate test simulates local cutover policy; Render routing is not tested.

A test-only preloaded hook forces the server's0.0.0.0 listener onto127.0.0.1 and
denies unexpected socket destinations/ports; self-checks reject external connections.
Server/helper children get a clean fixed environment and only dummy local DB details,
no Telegram/OpenAI/GitHub/Render credentials. Intake stays disabled; public domains
and Telegram are never contacted by the workload. Runner parent fetches public exact
source/metadata and npm registry dependencies. Source is trusted/pinned; this is not
an arbitrary-code security sandbox. PostgreSQL and all fixture rows are disposable.
No VPS browser/database/dependency, paid resource, schedule or production mutation.

Actual Render read-only audit is separately recorded in nova_render_snapshot.json.
Its service healthCheckPath is empty despite repository render.yaml specifying/health;
main commits trigger auto-deploy; live deploy points to baseline1a23239a. A source
file is not proof of applied platform configuration. Retained build eligibility and
actual Render rollback execution are unverified. API rollback does not disable
auto-deploy; Dashboard rollback does, per current Render docs. Database/external
side effects are not reversed. Do not create a live publication approval or enable
a publisher merely because this local rehearsal passes.
