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
Measured VPS work spans cover CI verification, not the remote runner execution time.
Stored timestamps are historical. Updating the tested source/harness requires a
new reviewed contract/version. Existing model-key deferral and zero paid policy remain.
No coding schedule, new daemon, VPS dependency or database access is introduced.

## Verified activation, 2026-10-25 UTC

App562be5084d70fc71f7e07ddfaac44d176eaaa93b / Draft PR43 is installed only in UAC.
Rollout40197421540 passed428 app tests (all15 real sandbox cases, zero skips in the
sandbox-enabled pass) and41 transport tests. Actual scoped App authentication and
read-only CI observation passed before activation; artificial API/error/memory cases
were confined to a restored copy.

Real queue job484 observed hosted CI40196637203, attempt1, harness0a21efb320d65ae98c6788d5cd9825b124f2f4c4,
source1a23239a0a9c7d79905c91505a8741d8350d7e75. That actual hosted run executed34/34 tests
and PG16 SQL gates. Telegram accepted activation355/report356; evidence memory485 binds
the stored report hash0b1a60ea0325643d935fa936257dd8085d595751059e4efad9ee10e17e7818fb.
Independent verify40197785804 repeated these observations at13:29 UTC. InventoryPID67760
and source/configuration metadata stayed unchanged, paid calls/holds/spend stayed zero,
and model-key setup remains deferred. No production approval/candidate was created.

Worker449580, sole poller450023, app directory/home/maksim/.ultimate-review-runtime.
Backup/home/maksim/.ultimate-review-data/backups/before-uac4-1792934735276458178.sqlite3.
Rollback action uac4_nova_ci_rollback (only while this exact app is current) drains UAC,
restoresfe19f8220d7337cdc9f253cfb4d8948f4a06bb62, cancels only unsupported queued NOVA CI
checks and preserves existing owner pauses, report/policy/delivery/memory history. It
changes no database service, resource schedule, dependency or independent application.
An older reader may need this newer version for CI memory references. Live rollback
was not executed on the successful deployment. The whole tester stage remains active;
browser/production-state and wider project coverage are pending.
