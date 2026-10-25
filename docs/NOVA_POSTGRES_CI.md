# NOVA PostgreSQL CI evidence

`/test_nova_pg` queues a read-only revalidation of a fixed hosted CI run;
`/nova_pg` or 🐘 PostgreSQL NOVA displays the stored evidence. It does not dispatch
workflows, install dependencies, start PostgreSQL on the VPS or touch NOVA production.
The original `/test_nova` remains a different read-only local Node sandbox profile.

The reviewed hosted harness commit is pinned in nova_ci_contract.json. It downloads
28 exact public files of NOVA revision1a23239a0a9c7d79905c91505a8741d8350d7e75,
runs all14 original test files serially and rejects anything except34 passed tests,
zero failures/skips/cancellations/todos and both named database tests. An independent
SQL gate checks PG16, persisted status/history/event rows and restored operational
fields. The separate lock, image digest, GitHub action SHAs, Node version and
review notes are under ci/nova-postgres. npm audit reported zero known advisories;
no comprehensive base-image/dependency source security certification is claimed.

Real initial CI40196637203 (push, attempt1) and40196640109 (PR) succeeded. Actual
logs contain34 tests/pass, zero failures/skips and successful SQL assertions.
This is real execution on a disposable GitHub runner/PG16, not a fake response,
VPS-local DB run, browser test or claim about current production state.

The existing short-lived GitHub App broker requests only read permissions on the
ULTIMATE repository. The exact queue scope/lease, private policy and existing owner
activation are checked before loading a key. Candidate/worker children never receive
credentials. Fixed-repository GETs match exact harness commit, workflow name/path,
push event and repository IDs; latest matching run, exact-attempt job and mandatory
successful test gate must agree. A second run read rejects an intervening rerun.
No PR/branch/deploy/merge/dispatch write endpoint is used.

The report records run/attempt/job IDs, exact source/lock/contract, CI location and
checked time. Counts are attested by the required gate in that exact immutable
workflow commit; VPS does not pretend to rerun SQL or independently parse its logs.
Failed CI has no fabricated passing counts or database proof. Pending/ambiguous
responses retry finitely; denial produces a scoped notification.

Saved reports are hash-bound, lease-checked, retained on retry and linked to evidence
memory. Changed evidence requires a new job; it never grants publication approval.
Stored timestamps are historical. Updating the tested source/harness requires a
new reviewed contract/version. Existing model-key deferral and zero paid policy remain.
No coding schedule, new daemon, VPS dependency or database access is introduced.
