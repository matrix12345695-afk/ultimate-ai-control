# Read-only VPS resource monitoring

`/vps4` (or 🖥 VPS after /start) shows the latest timestamped report; `/vps_check`
queues a new fixed-scope observation. One 300-second operation schedule uses the
existing serialized worker and owner pause. It is not a ChatGPT development automation
or another daemon. Pausing the queue also pauses resource sampling; stale data are
explicitly labelled after 15 minutes and do not establish present health.

The collector reads bounded /proc/stat, /proc/meminfo and /proc/loadavg and calls
statvfs only on UAC's own data directory. CPU/memory are host-level observations;
disk/inodes refer to that data volume. No environment, process command, secret,
Inventory data or other project directory is inspected. No shell, cleanup, restart,
kill, package installation or paid API call exists in this module. Writes go only
to UAC's own database/outbox/evidence journal.

CPU is aggregate busy ticks excluding idle+iowait, divided by all ticks, across
reported online CPUs. Guest ticks are not added twice. Two same-boot/core-count
observations 60–900 seconds apart are required. Counter resets, reboots, short or
stale intervals leave CPU unknown. Load 1/5/15 is reported separately, never labelled
as CPU percent. MemAvailable is used rather than free RAM. f_bavail/f_favail exclude
blocks/inodes unavailable to the service account.

Opening an incident requires two bad accepted observations 60–900 seconds apart;
manual bursts cannot advance either failure or recovery. Reboot/gap resets streaks,
unknown values cannot recover an incident, and two good observations are required
for recovery. Intermediate bands reset confirmation without closing the alarm.
Thresholds: CPU>=90%, recovery<75%; memory/disk available<=10% or respectively
512MiB/2GiB, recovery>15% and>768MiB/3GiB; free inode<=5%, recovery>8%.
Missing collectors have a separate telemetry incident. This confirms observations;
it does not prove every instant between checks was overloaded or healthy.

Job completion, stored sample, report hash, debounce state, scoped incident and notification
commit together under the queue lease. One open incident per metric suppresses
repeated alerts. Recovery resolves only the linked resource notice; unrelated critical
or owner-decision messages retain their states. Telegram delivery ambiguity may still
produce duplicates. Reports/evidence remain historical and are not permission to
modify a service. No automatic remediation is enabled.

Acceptance requires real VPS samples at least 60 seconds apart, CPU delta evidence,
a stored report and memory, Telegram receipt, the exact 300-second schedule, and
unchanged Inventory/source/config metadata, paid policy and owner deferral. Alarm,
recovery, missing-data and transaction-failure injections run only in temporary DBs.

## Verified activation, 2026-10-25 UTC

App `fe19f8220d7337cdc9f253cfb4d8948f4a06bb62`, Draft PR42, is installed only in UAC.
Rollout40171830616 passed416 app tests including15 real sandbox cases with no skips
in its sandbox-enabled pass, plus39 transport tests. Real job360 was the second
sample,65.60167455673218 seconds after the first: aggregate CPU0.78%, MemAvailable
6.257GiB, volume available61.610GiB and5952203 available inodes. These observations
are historical and timestamped in the DB. Telegram accepted activation352/report353,
with evidence memory361. Controlled failures/recoveries ran only on a restored copy.

Independent verification40172325629 also observed actual periodic job362 from the
existing scheduler (not an injected fixture), validated its report hash and repeated
all live UAC/Inventory/disabled-paid-policy gates with the same worker/poller PIDs.
No new daemon/cron or hourly ChatGPT development automation was created.

Current UAC-only code rollback action: uac4_vps_resources_rollback, only while this
exact app is current. It checks and disables only its resource schedule, drains UAC,
restores0621a2d82dd3cacc6702599ef821e83dc7469043, cancels only unsupported queued
resource checks and preserves existing owner pauses. All reports, incident/delivery
history and memory remain; an older memory reader may need this new version to read
resource references. It never cleans disk or stops/restarts Inventory. This rollback
was reviewed/tested but not executed on the successful live deployment.
