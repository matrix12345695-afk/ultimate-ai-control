# ULTIMATE 4.0: installed operations runtime

Observed 2026-10-22 UTC. This record distinguishes deployed capabilities from planned agents.

## Deployment evidence

- Initial scheduler release: 1a53453f2ce6afb578eb6388cabb1d6d714fdb4f.
- Source branch: feature/uac4-scheduler-chat-control, draft PR #24.
- Runtime directory: /home/maksim/.ultimate-review-runtime.
- SQLite: /home/maksim/.ultimate-review-data/live/control.db.
- Dispatcher supervisor: existing ops/start-rootless.sh and cron; single Telegram poller.
- Scheduler supervisor: ops/scheduler-rootless.sh, own flock/log/marker and UAC-only cron line.
- Scheduler process at verification: 618706; dispatcher: 619053.
- Exact-release tests: 239 locally and on the VPS, plus 9 installer/transport tests; GitHub CI success.
- Deployment: https://github.com/matrix12345695-afk/inventory-bot/actions/runs/39848877945.
- Verification: https://github.com/matrix12345695-afk/inventory-bot/actions/runs/39849515912.
- Telegram scheduler announcement accepted: message 135.
- Owner request about missing model executor accepted: message 134.
- Current-chat URL request accepted: message 140, one attempt.
- One real site-check job and one real source-inspection job completed, with measured intervals.
- Workers use a 402653184-byte address-space limit, 128 descriptors, reduced priority and a
  30-second tick timeout. Verification read these effective limits from /proc.
- Worker environment was verified to contain no Telegram, GitHub or model credentials.
- Inventory PID remained 67760; source fingerprints and configuration metadata matched.
- No paid model call was made. Local accounting is separate from provider billing data.

Backup verified by restoring a separate SQLite copy:
/home/maksim/.ultimate-review-data/backups/before-uac4-1792700808232446198.sqlite3.

The full scheduler rollback action is uac4_rollback. It removes only ULTIMATE's scheduler
marker/cron line, stops its exact worker safely, restores the prior notification release and
restarts only the ULTIMATE dispatcher. Additive database tables and history are retained.

## Current-chat association

The handover, owner policies and 16-stage roadmap are explicitly imported. The notification
relay can now enqueue bounded owner requests from this active Codex conversation through
uac4_notify_owner. uac4_import_task imports explicit future tasks idempotently.

The ordinary private ChatGPT conversation URL is not yet known. /chat_bind stores that URL
and enables an owner-only return button in Telegram notifications. This is a return destination,
not an automatic subscription to the conversation. The VPS cannot read new ChatGPT messages,
write into the conversation, or independently resume Codex through an unavailable ChatGPT API.

## Monitoring correction

The first HEAD probe produced HTTP 404 for NOVA. Independent GET requests to /, www and /health
returned 200, with /health reporting postgres storage. The NOVA Node handler routes GET requests
but not HEAD requests. This was a monitor false alarm, not proof that the website was down.

A bounded GET probe and a regression test were prepared in
b6d2d201c995637f89ba67be4208d4c5048cc1f1 and verified on the VPS at 20:36 UTC.
This is now the installed application commit. All 240 source tests and 10 transport tests passed.
NOVA's recorded health is HTTP 200. Telegram accepted correction message 141. Confirmed recovered
availability alarms were resolved; owner decision records were preserved.
Current worker PID: 628833. Dispatcher PID: 629214. Inventory remained PID 67760 with matching
source/configuration metadata. Update run:
https://github.com/matrix12345695-afk/inventory-bot/actions/runs/39850144365.
Backup: /home/maksim/.ultimate-review-data/backups/before-uac4-1792701330424625496.sqlite3.
No NOVA deployment, DNS, database or source change was performed.

## Remaining implementation

The operations worker is not a complete autonomous development team. General text requests
are preserved as awaiting_owner when no isolated model executor exists; independent operational
checks continue. Model configuration, priced transport, isolated code/test execution, broad
project permissions, exact-release publication approval, speech and full designer/researcher
automation remain roadmap items. The roadmap never reports these as complete.
