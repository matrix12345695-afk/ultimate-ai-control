# Calendar weekly analytics

Weekly reports use Asia/Tashkent and the preceding closed Monday00:00–Monday00:00 period.
Delivery is Monday09:00. Installation adds only the reviewed weekly-analytics-v1 row to the
existing UAC operations queue. It does not enable hourly coding automation or paid calls.
The existing daily and monitoring schedules are preserved. /weekly still shows a rolling
seven-day view; /weekly_report [period_end] reads a saved calendar report; /weekly_auto shows
its next scheduled delivery. Rolling daily/weekly view dates now also use Asia/Tashkent.

A late restart admits at most the latest eligible week, then advances directly to the next
Monday09:00. Historical weeks do not create a catch-up flood. Exact period keys prevent a
manual check, retry, concurrent tick or restart from creating a second task for that week.
Task insertion and schedule advancement share one SQLite writer transaction. Owner disable,
queue pause and emergency latch are respected; an unrecognized schedule is not overwritten
and produces one bounded notice while independent jobs continue.

Reports use recorded active/test spans, state events and settled cost receipts. Task waiting
is summed by task and never presented as worker idle time. Missing observations stay unknown.
Unresolved holds and incomplete receipts are distinguished from confirmed cost. Holds reflect
the time of snapshot preparation, not a historical provider balance. Zero recorded cost does
not certify an external provider invoice. These metrics do not prove that a complete AI team
or model developer is operating.

Report snapshot/hash, period-scoped notification and task success commit atomically under the
current lease/emergency epoch. The immutable snapshot does not change when later tasks arrive.
The typed evidence-memory reference checks its report and original job. Telegram delivery
has a separate durable receipt; API acceptance is not reading, task approval or publication.
An ambiguous Telegram outcome may still cause duplicate delivery of the same persisted notice.
No voice/transcript, source code, credential or arbitrary task text is copied into analytics.

Rollback disables only this reviewed weekly schedule and cancels only its queued unsupported
calendar jobs before restoring the previous voice-aware UAC app. Reports/history, confirmed
voice tasks, private policies, the old daily/monitor schedules and owner pauses are retained.
No live database restore or independent service action is performed. Older readers may need
the newer app to display typed weekly evidence. Server activation and receipts belong in
WEEKLY_REPORTS_ROLLOUT.md and PROJECT_STATUS.md; prepared source alone is not live deployment.
