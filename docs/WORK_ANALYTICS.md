# Measured daily and weekly work

`/daily`, `/weekly` and `/analytics4 24h|7d` read the same durable journal. They show measured
active/test intervals, work by queue role/project/actual worker, successful and failed finishes,
scheduled retries, expired leases, waiting in the queue and waiting for the owner. The weekly
button is a read-only view. No new schedule, service, model call or financial permission is added.
The existing daily_report job also saves a bounded version of this summary alongside its
backward-compatible report and budget fields.

Intervals are clipped to the requested half-open UTC period. Failed attempts remain counted.
Names such as Development and Testing are queue work categories, not a claim of activated
independent AI employees. Only recorded active/testing spans contribute to work; a running
lease, task age or absence of measurements never becomes measured work or inferred idle time.
Recorded waiting spans are separate from queue-state waiting.

Queue/owner waiting is reconstructed only from recognized persisted transitions in timestamp
and event-ID order. It clips intervals at report boundaries, includes retries, recognizes final
lease exhaustion and preserves waiting states that began before the window. Missing initial
events are not guessed from task age. An inconsistent current-state tail is excluded and
flagged unknown. Multiple tasks can wait simultaneously: their waiting durations are added,
so they are not a worker's elapsed or idle time. Current task counts and unresolved financial
holds are snapshot values; they are not reconstructed historical state counts.

API spend is summed only from settled, nonnegative actual receipts whose settled_at falls in
the period; token totals come from the same receipts. A request created earlier but settled
during this period belongs to this receipt-time report. Reserved/unknown entries are shown
separately as current outstanding holds, including holds from older UTC months. Missing cost
receipts are flagged and never presented as a verified zero total. `/cost4 ID` shows cumulative
receipts, tokens and holds for a specific task. These are local ledger figures, not a provider
billing statement. Reading a report never settles/releases a hold or raises the $30 ceiling.

All report queries use one read snapshot. Nested callers retain their existing transaction;
analytics does not commit their pending writes. No arbitrary task result or model response is
used to estimate work hours or costs. The original event/span/cost records remain the source
for later detailed analysis, even when a Telegram view abbreviates grouped rows.

Tests cover clipped intervals, failed work, retry/owner waiting across boundaries, overlapping
waits, missing history, final lease failures, receipt time, unresolved cross-month holds,
missing receipts, read-only transaction behavior, commands, bounded daily payloads and the
partial-stage guard. Full role execution, external billing reconciliation, complete idle
observation and automated weekly delivery remain separate unfinished work.
