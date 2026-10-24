# Evidence-linked project history

The operations worker indexes committed job transitions in bounded batches of80 events per
tick, including while the queue is paused. It resumes its persisted cursor after restart.
The entry and cursor share one SQLite transaction; replay cannot duplicate an event. Original
project_memory business rules are retained without replacement. Inventory and Mini App jobs
are excluded by the existing executor project allowlist; their static requirements remain readable.

`/memory_log [project] [page]` (five observations per page) and `/memory_item ID` show historical
transitions and current job state separately. `/memory project` keeps the original requirements
and links to history. The new **История проектов** menu button uses the selected project.
These commands read a consistent snapshot and neither synchronize nor approve work.

Each append-only entry binds a job/event identity to SHA-256 of the original journal rows.
Test observations additionally bind the matching artifact, source digest, report and reviewed
acceptance profile/harness hash when available. Pinned repository reads retain the revision
and manifest digest with code/tests-executed=false. An awaiting-owner observation is never
reported as implemented or published. Retry and expired-lease observations are not successes.
The index contains typed facts, not task text, error text, test output, private URLs or source.

On every page/detail read the hashes are recomputed against the referenced SQLite rows. Changed
or missing sources invalidate the observation and require another check; old entries are never
rewritten or promoted. This verifies the saved journal, not current artifact files or a deployed
project. Hashes are not signatures against an administrator able to rewrite the whole database.
SQLite triggers prevent ordinary UPDATE/DELETE of the index. No automatic retention deletion,
network access, code execution, model call, new schedule or permission change is introduced.

This component is historical evidence retrieval. It does not yet implement general semantic
search, owner business-rule editing, model-driven learning or automatic avoidance of every
previously failed approach. Owner requests and API setup deferral keep their existing separate
views. Stage12 remains active; paid API setup and hourly development automation stay deferred
and disabled respectively.

Validation: ten focused tests cover atomic rollback, resume/idempotence, pagination/read-only
queries, changed/deleted sources, failures/retries, protected projects, historical vs current
state, artifact/profile provenance and source-read limitations. Full local suite:371 passing,
including twelve real namespace integration tests with UAC_SANDBOX_TEST_BINARY configured.
VPS rollout and Telegram receipt evidence will be recorded in PROJECT_STATUS.md after validation.
