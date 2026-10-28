# Kinder authenticated API: completed draft,28 October2026

This bounded work is **done: code draft, PostgreSQL and HTTP acceptance**.
The full Kinder application and UAC stage7 remain in progress.

Draft [PR2](https://github.com/matrix12345695-afk/Kinder-Spa-android/pull/2), stacked
on PR1/feature/accounting-core. Exact source
`07bea3ed737a41cebb360424b826f1d966096be1`, branch `feature/authenticated-api`.
Main remains `0ef936334629accfd59ae33987462c3c693d33f9`; render.yaml unchanged.

Completed: administrator-issued client credentials, salted scrypt password hashes,
opaque8-hour sessions with5-active-session cap, logout and client password reset
revocation, persistent concurrent login throttling, ownership-filtered lists,
authenticated subscription/booking/QR/cancellation/restoration endpoints. HTTP
clients cannot override actor/role. Session validity is rechecked inside each
accounting transaction; a reset/logout waits for an already-admitted transaction
before revocation. Reads check session inside their read transaction as well.

No raw password/session/QR token enters the audit or idempotency journal. No new
dependencies. Fixed login limits per10min are5/login,30/socket-IP,120/global.
JSON bodies are bounded8192 bytes with exact fields, no duplicate/nonfinite input,
no cookie/query-token auth, no browser Origin surface and no trusted forwarding
headers. Responses are no-store; database errors/stack traces are redacted.

Local real PostgreSQL18:83/83 tests, zero skips,14.180s (44 business+39 new
authentication/API cases). Exact push CI40638453032/job122650769779:83/83,
zero failures/errors/skips,15.510s. PR CI40638455878 also successful. The tests
include actual loopback HTTP login, authenticated WSGI business flows, client
isolation, rate-limit concurrency, credential changes during hashing, reset
genuinely blocked by an admitted transaction, revocation after earlier request
identification and malformed passwords distinct from dummy hashing input.

Artifact12794706529 contains only report.json. Archive digest
`sha256:cae7b0148e4b6069738828935778b20c493b3a5b806846ee5d80d4c70462b48c`.
Its archive bytes, exact revision and all14 component source hashes were checked
independently. Report says HTTP authentication true but HTTPS deployment, admin
UI, Android, real Telegram delivery and publication false. Synthetic fixtures only.

The default WSGI application requires trusted HTTPS scheme/address, but no listener,
public service, automatic migration, real DSN, credential bootstrap or production
configuration is installed. Bootstrap is a manual operator function that accepts
only an empty dedicated database; no HTTP bootstrap/staff-creation route exists.
A reviewed HTTPS gateway with time/resource/concurrency limits, controlled DB roles,
real migrations/backups, Android/RU-UZ and admin UI, capacity scheduling, staff
credential recovery/rotation and the actual superadmin outbox sender remain open.
Client creation uses unique logins; password reset is not an idempotent accounting
operation and repeating it revokes sessions again. See backend/API.md in PR2.

Independent VPS preservation verification40638503743/job122650933525 passes at
28 October10:33 Asia/Tashkent: installed UAC341d1277, worker3311622,
dispatcher3312003, Inventory unchanged, paid API0, deferred model setup preserved,
genuine voice confirmations0. No UAC source or worker permission was changed.
The hourly coding automation remains disabled. Completion notification177 was
accepted by Telegram as message417 in bridge40638744177/job122651678539 at
28 October10:34 Asia/Tashkent. This is a UAC progress receipt, not actual Kinder
outbox delivery, owner reading or publication approval.
