# Observed worker waits and completion audit

The operations worker records only completed polling waits. Wall and monotonic clocks must
agree within250ms; a wait must be positive and at most8 seconds. Only their common duration
is credited. Clock jumps, long suspension, the unfinished interval of a crash and all time
before installation remain unknown. No24h-minus-work idle estimate is made.

Each process gets a session and a current-session fence. An older/superseded session cannot
pulse, write observations or pass the pre-claim instrumentation. Wait rows are immutable and
hashed. A new session never fills a gap left by its predecessor. Clean shutdown closes only
its own session. The existing rootless supervisor,5-second polling cadence,30-second job
alarm, resource limits and emergency/approval policies are preserved.

Reasons come from consistent queue/control snapshots before and after the actual sleep:
empty queue, no available jobs with owner requests pending, delayed jobs, concurrency limit,
ready jobs during polling, owner pause, emergency latch, state transition or tick-error backoff.
Reasons describe sampled boundaries; transitions between samples may be missed. Owner-pending
requests are not claimed to be the sole cause of idle time. Task waiting and worker waits
are different measurements. The worker status also distinguishes a current leased task from
a stale, closed or absent observation signal. Silence never proves VPS downtime.

/worker4 24h and /worker4 7d show measured waits/reasons, union coverage by recorded job spans
and the remaining unobserved time for operations-1. Known work overlaps are excluded from
wait totals. Overlapping wait timelines invalidate that wait projection; corrupt/hash-invalid
rows are excluded. Reads have a31-day/600000-row bound and keep missing data unknown. A single
worker emits at most one row per completed5-second poll (about17280/day); no historical rows
are automatically deleted. Existing VPS disk monitoring continues.

Daily and future weekly snapshots include the observation summary. Older weekly snapshots
remain unchanged and state that they lack new observations. Full legacy idle_seconds stays
unknown; the new observed_wait_seconds is explicitly partial. Typed daily memory binds the
summary to the saved job result, without copying task text, transcripts, keys or code.

/finish4 is a read-only16-stage handover status. It preserves API deferral, points to existing
owner requests and separates them from remaining engineering. Stage flags, test fixtures,
Telegram delivery and one voice confirmation cannot prove a full autonomous AI company.
The live publisher and broad multi-project/model execution remain unfinished; no new key
request, paid call, permission or publication is triggered by the audit.

Rollout requires full source/native tests, a restored-copy gate, actual daemon wait rows,
a real daily queue report/typed memory/Telegram receipt and independent verification.
A safe rollback restores the preceding calendar/voice-aware app and retains all history,
weekly schedules/reports, owner pauses, accounting and private policies. It controls only
ULTIMATE's own dispatcher/worker, with no live DB restore or independent-service action.
