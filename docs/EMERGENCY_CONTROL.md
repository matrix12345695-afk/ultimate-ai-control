# Durable UAC emergency control

The owner-only Telegram menu has `🚨 Аварийный стоп` and `🛡 Аварийная защита`.
`/emergency_stop` durably latches the control and pauses UAC queue admission. It does
not signal processes, stop a service, access Inventory data, change schedules or cancel
an external request already admitted. Ordinary `/pause` remains separate.

## Ordering and recovery

SQLite `BEGIN IMMEDIATE` serializes stop, queue claims, approval decisions and action
admission. A monotonic control epoch is stamped onto jobs, approval capabilities and
external-action admission records. Current GitHub Draft writes and paid-provider
dispatches require an admission against both the current epoch and live job lease.
Read-only observations and bookkeeping may finish after a stop. An admitted request
can reach the provider after the stop; there is no remote cancellation guarantee.
Acknowledged or ambiguous outcomes are recorded even while latched. Provider cost
settlement remains atomic with the receipt; ambiguous sends retain their budget hold
and block new calls until reconciliation. No paid policy is enabled by this module.

The stop transaction writes its own durable notification outbox before contacting the
ordinary inbox. Inbox failures cannot roll back the stop. The worker retries transferring
pending control events into the delivery inbox even while the queue is paused. Existing
Telegram retry/delivery tracking applies; acceptance is not owner reading or approval.
Replayed Telegram source keys cannot repeat an old stop or clear a newer stop.

`/emergency` shows the latch, epoch, running jobs, unresolved admission IDs, outstanding
control notifications and recent events in Asia/Tashkent. After running work has drained,
`/emergency_reset EPOCH` clears only that exact latch and increments the epoch again.
It keeps the queue paused. `/resume` is a separate owner command; it cannot clear a latch.
Old pending/approved capabilities remain invalid after reset. New publication decisions
must bind fresh exact artifacts and a fresh epoch. Missing/corrupt control state fails
closed; initialization does not reconstruct a missing singleton as an open control.

No real publication adapter is enabled. The existing NOVA publication state machine is
still fixture-only. Any future external mutation adapter must use this admission contract
and its existing exact-scope approval checks; a status check alone is insufficient.
This is an application control, not an OS permission boundary against code sharing its UID.

## Verification and status

`/emergency_test` queues `control/test_release/emergency-control-v1`. Eight operational
acceptance cases execute against an entirely separate in-memory DB: latch/deduplication,
no claims, ordinary-resume refusal, mutation refusal, drain-before-reset, separate reset
and resume, old approval invalidation, and replay safety. The worker saves an immutable
hashed report with an implementation digest, then a typed memory reference and a result
notification. `/roadmap` derives the completed subtask from validated evidence. This does
not finish the autonomous-development stage or exercise a live production stop.

The regression suite adds 27 fault/integration tests, including persistent DB reopen,
legacy migration, missing control state, two SQLite connections, inbox failure/retry,
stale approvals, actual command/menu/worker flows, GitHub stop between writes, stop before
credential access, provider stop during key read, admitted-response settlement, ambiguous
holds and evidence tampering. All credentials/transports in these tests are synthetic.
Full local execution: 551 tests, including all 15 sandbox-dependent checks, zero skips.
Hosted baseline CI intentionally skips those 15 checks unless its sandbox is configured.
The deployment gate additionally migrates a restored VPS backup and exercises stop/reset
only on that disposable copy; live latch activation is not part of deployment.

## Deployment and rollback constraints

Use the isolated UAC bridge only. Keep existing code, policies, accounting, owner follow-ups,
reports and Inventory untouched outside the selected UAC increment. Back up the live UAC
DB, validate restore/migration, drain UAC jobs before replacing its worker/dispatcher, and
refuse to override an owner pause or emergency latch. No live DB restore is part of rollback.

The emergency rollback helper may restore preceding app
`cd8aa26964d27c2cea06360fc92a88b8fa2a3275` **only if the live epoch is still zero and the
latch is false**. After any real emergency stop or reset, that older app would ignore the
new epoch bindings. The helper must refuse that downgrade before pausing/signalling or
changing source. Keep a compatible emergency-aware version and prepare a forward repair
instead. No live rollback is claimed to have been executed.
