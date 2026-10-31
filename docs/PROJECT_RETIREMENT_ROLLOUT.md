# Verified UAC project retirement —31 October2026

Installed source de7afc198400175e4441625eeb973b42c330b225 (Draft PR66), prior341d1277.
Preflight, application and independent verification are all successful.
[Exact receipt](evidence/PROJECT_RETIREMENT_20261031.json).

The typed bridge adds only uac4_retire_projects_preflight/deploy/verify. It routes
before all Inventory handlers/directory setup and rejects extra request fields.
Original bridge functions are unchanged by AST comparison apart from the one
early dispatch branch. Existing Inventory source/config/service actions are not
invoked. No workflow definition was changed. The operator/test source is fixed
to Inventory transport commit db4ffc48c92292df4fe7efddf9e44adc368a1382; only
uac_transfer/ops/retire_projects_rollout.py and its8 tests are extracted.
Application release, host paths and three phase names are fixed, not caller supplied.

Preflight41197098488/job124525373491 executes684 source checks in124.853s
with18 existing host-dependent skips and validates retirement twice on a restored
copy. Deployment41197359053/job124526113610 repeats684 checks in132.471s,
drains/pauses only UAC, removes only its supervisor markers temporarily, and
signals only exact own argv matches. Inventory is never a signal target.
It backup/restores the own SQLite DB, checks out the fixed release, applies the
atomic migration, restores only existing supervisors and then restores only its
own temporary queue pause. Existing cron definitions are never edited.

Migration removes4 schedules and2 contexts and resolves89 old notices. Actual
queued/waiting project jobs, unconfirmed voice and linked approval counts were0;
their rejection/cancellation/revocation paths were exercised in fixtures.
No recovery/delivery/approval is fabricated when a request is closed for retirement.
Old receipts and terminal history remain. Source and SQL guards fence old writers.

Independent action41197719245/job124527163662 at16:39 Asia/Tashkent verifies
the same release, ledger/guards/menu/commands, dispatcher1344126, worker1343925,
Inventory2590664 and unchanged source/config metadata. Queue is unpaused.
Financial/deferred state is unchanged. Updated keyboard443 and notice444 have
actual saved Telegram receipts, not owner-read confirmations.

State/backup reference: /home/maksim/.ultimate-review-data/live/uac-project-retirement.json.
Its backup path names a verified SQLite snapshot. No live DB restore was executed.
Post-retirement failure must keep the retired work fenced and retain a safe own
pause/stopped runtime for inspection. Never blindly install an old monitor-capable
application or restore an old database over current accounting/history. The
historical bridge actions keep old source pins; do not bypass them to perform
future notifications/deployments—prepare a reviewed compatible typed operator.

This rollout does not delete Render services/databases, GitHub repositories,
Telegram bots or domains and does not install a new product. It has no paid
model request or additional schedule. See the owner-approved replacement product
[requirements](NEXT_PRODUCT_AI_OPERATOR.md). Inventory remains independent.
