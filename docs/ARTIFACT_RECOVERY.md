# Recovery of complete tested artifacts

A worker can exit after a private bundle was durably renamed but before the artifact row
was inserted, or after insertion before the job was completed. Retry attempts now recover
that complete result for the same job rather than rerun code or create another artifact.
Generation capsules already survive lease renewal and keep a stable paid-request identity;
a regression test verifies that a completed artificial provider receipt is not charged twice.
No real model key or paid request is needed by this increment.

New source, manifest and report files are written privately with fsync. Their directories are
synced before the atomic rename, and the destination directory is synced afterwards. The
report includes versioned job/attempt/project/engine/source identity and original creation
time. Only after publication is the SQLite artifact row committed.

Recovery validates current-user ownership, mode0700 directories, mode0600 regular files,
symlink-free exact paths, every expected source byte, manifest, report/source digest, engine,
original attempt, provenance and acceptance profile/harness. Registered legacy artifacts may
use their existing DB identity; unregistered directories require the new identity receipt.
An adopted orphan retains its original attempt, path, report and creation time. A reused
result is labeled tests_reused, not reported as another test execution. Actual recovery time
is measured independently by the queue worker.

Unknown, partial, missing, changed or ambiguous evidence stops the job with a critical notice;
it is not deleted, overwritten or followed by an automatic host fallback/retest. Failed test
outcomes remain failed. More than one published artifact attempt for a job requires review.
A crash before a complete artifact is published can still require re-running interrupted tests.
The finite attempt cap is unchanged. Exhaustion caused by an expired lease now creates one
durable critical notice instead of failing silently. Notification delivery can still be
ambiguous; this is not an exactly-once messaging guarantee.

Trusted host code and storage still share one Linux user. These checks detect incomplete or
changed evidence, not a malicious same-UID operator capable of rewriting both data stores.
Only existing Bubblewrap execution runs candidate code; recovery never imports candidate source.

The owner explicitly deferred API-key setup on 2026-10-23. provider_setup_deferred=true keeps
model-dependent jobs waiting without recreating key requests. Existing key/setup requests
are resolved as deferred, with the reason retained in settings/audit; this does not authorize
or enable any API call. The separate hourly development automation stays disabled.
