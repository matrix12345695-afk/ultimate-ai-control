# Availability incident lifecycle

Availability results, queue completion, the saved health snapshot, incident recovery and
notification creation now share one SQLite transaction. A crash rolls them back together;
delivery to Telegram remains a separate retryable operation. There is no exactly-once delivery
claim, and closing an availability incident does not approve a publication or resolve another
owner decision.

Only the configured NOVA HTTPS target is enabled. An active check_site lease must match the
stored project/payload, URL, observation timestamp and HTTP verdict. Expired leases cannot
close an alarm; an observation older than the persisted sample is recorded as superseded and
does not replace health or resolve incidents. Repeated bad samples keep one incident open;
a new outage after recovery opens a new one.

Legacy queue alarms are imported only when their exact health-job identifier/task binding,
project, title and committed failing source result prove the target. Older hourly-poller
alarms have no job ID: they require the fixed first-party project/title, canonical URL,
WARNING/DOWN unavailable format, original UTC creation hour and reproducible SHA-256 event
fingerprint. Unknown, unrelated, future-dated, malformed or uncommitted records are retained.
Imports are bounded to 100 candidate records per sample.

A newer successful check resolves eligible critical notes for that target, keeps their
Telegram receipts and original text, and writes incident audit records pointing to the exact
recovery job and informational notification. Pending critical notes are then omitted from the
owner inbox and no longer eligible for a new delivery claim. An already claimed Telegram send
can still race with recovery; a later recovery notification explains the observed restoration.
Manual decisions, key deferral, sandbox failures and other targets are not cleared.

/monitor4 and the Monitoring4.0 button show the persisted sample time in UTC and incident
counts. Plan4.0 reflects the same journal. This is HTTP availability monitoring, not full
functional/API/database acceptance testing of the website. No NOVA source or hosting change
is part of this increment; API-key setup stays deferred and hourly development stays disabled.
