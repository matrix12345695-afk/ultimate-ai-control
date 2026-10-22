# ULTIMATE notification rollout record

Observed time: 2026-10-22 UTC (the handover labels its date 2026-10-23).

## Installed increment

- Application commit: d3d055123bda41d6aac9862cb552bb1e9751afa1.
- Previous commit: 3e66bea9d9ff02b33167578695d2702beb638a97.
- Application: /home/maksim/.ultimate-review-runtime.
- Database: /home/maksim/.ultimate-review-data/live/control.db.
- Bot: @UltimateAIControl_bot; token remains on the VPS.
- Supervision: existing ops/start-rootless.sh, flock and restart loop; per-minute cron startup.
- No dedicated systemd service was created.
- Exact release: 209 tests passed locally and on the VPS; 5 transport/rollout tests passed.
- GitHub CI: https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/39845007163 (success).
- Deployment run: https://github.com/matrix12345695-afk/inventory-bot/actions/runs/39845580839 (success).
- Telegram accepted the notification at 2026-10-22T20:04:57.278570+00:00.
- Telegram message ID: 123; delivery attempts: 1; persisted in owner_notifications.
- This is an API delivery receipt. Human receipt/read confirmation was requested separately.
- ULTIMATE dispatcher PID after restart: 594738.
- Inventory PID remained 67760; its source fingerprints and configuration metadata matched.
- No Inventory code/configuration/database changes or process restarts were performed.
- No model API calls were made.

## Backup and rollback

Verified SQLite backup and restore-copy integrity:
/home/maksim/.ultimate-review-data/backups/before-uac4-1792699455135942533.sqlite3.

Private rollout state: /home/maksim/.ultimate-review-data/live/uac4-notifications-rollout.json.

Pinned transport commit: inventory-bot 0aed17b79204459cd65af2a9442903335b434d4f,
file uac_transfer/ops/notifications_rollout.py. The server bridge action
uac_notifications_rollback checks the installed version, restores the previous code commit
and restarts only ULTIMATE through its existing supervisor. Additive notification tables remain,
preserving tasks and delivery history. A database restore is a separate explicit recovery action.
Do not use Inventory's standard deploy/start/stop/restart actions for ULTIMATE.

## Remaining work

The installed increment is durable notifications, not a complete autonomous agent company.
The next branch introduces the queue library and measured work intervals. That library is not
yet imported by the deployed dispatcher and does not start workers. Worker isolation, Telegram
task creation, project memory, speech recognition and the full paid API accounting remain.
The live dispatcher environment has no enabled model provider. Do not enable paid calls until
a strict USD 30/month accounting/reservation gate and owner-provisioned key are in place.
