# Kinder Spa accounting: completed prototype,27 October2026

Status of this bounded work: **done — code draft and PostgreSQL acceptance**.
The complete Kinder application and UAC stage7 remain **in progress**.

Repository `matrix12345695-afk/Kinder-Spa-android`, ID1427568609.
Draft [PR1](https://github.com/matrix12345695-afk/Kinder-Spa-android/pull/1),
branch `feature/accounting-core`, exact source
`d9a63e3957a58a26bfad671c3c4b10db43b5f32e`.
Main remains `0ef936334629accfd59ae33987462c3c693d33f9`; render.yaml is unchanged.
No production release, server installation, customer data, API key or paid resource.

| Component | Status and acceptance |
| --- | --- |
| Category allowances | Done: massage10, hydromassage10, pool4/8/12; combined quotas remain separate |
| Booking accounting | Done: one reserved allowance per booking; serialized last-session balance prevents overspending |
| Working hours | Done: Monday–Saturday09:00–19:00 Asia/Tashkent; pool45min, last start18:15 |
| Pool cancellation | Done: return reservation strictly before19:00 the preceding calendar day; exact19:00 forfeits |
| Opaque single-use QR | Done:256-bit random token, only hash stored; at most2min and within session; staff redemption and replay protection |
| Exceptional restoration | Done: admin/superadmin only, required reason; one credit, audit and superadmin outbox in one transaction |
| PostgreSQL race/failure gates | Done: real concurrent last-visit booking, QR consumption/restoration, audit/outbox failure rollback, idempotency |
| Real superadmin Telegram delivery | Not implemented: durable outbox is not a delivery receipt |
| Authentication/Android/public API | Not implemented: trusted server must derive actor identity from a verified session before using Store |
| Facility capacity and other business rules | Not inferred: staff/capacity, non-pool cancellation, freezing/expiry and pricing require separate implementation |

Local exact-component suite:44/44, zero skips, PostgreSQL18,1.534s.
Hosted [push CI40559051879](https://github.com/matrix12345695-afk/Kinder-Spa-android/actions/runs/40559051879),
job122382809521:44/44, zero errors/failures/skips,1.550s. PR CI40559055608
also completed successfully against the same head.
The first workflow attempt40558868075 stopped before jobs because of YAML syntax;
the fixed commit above, not the failed attempt, is the accepted source.

Artifact12758741901 contains only `report.json`, no database dump, customer
information, token or connection string. Archive digest
`sha256:a46209ba8ad99b2aecdfa6508c040b7a162c64fb9ed498a4c27428854aaedcec`.
The downloaded archive SHA, tested revision and every component source hash were
independently checked against the reviewed source. Report explicitly marks Android,
HTTP authentication, Telegram delivery and publication false.

Dependencies: exact hash-locked CPython3.12/Linux x86_64 wheels for psycopg3.3.6,
psycopg-binary3.3.6 (LGPL-3.0-only), typing-extensions4.16.0 (PSF-2.0), with
bundled notices retained. Version-specific PyPI metadata returned no listed
vulnerabilities for those three versions at this check; that is not a complete
OS/transitive security audit. Official PostgreSQL18 image is pinned by digest;
tests use a disposable local `kinder_test` database and random synthetic schemas.

UAC runtime remains installed341d1277. Its pinned public Kinder source reader
still reads the old reviewed main scaffold; this draft does not promote that pin,
install an executor or claim a working Android app. UAC completion audit remains
false; model setup remains deferred and hourly coding automation disabled.
Inventory is outside this component's source, database and test execution scope.

Owner completion notification176 was accepted by Telegram as message416 through
bridge run40559215441/job122383382744 (27 October23:21 Asia/Tashkent). This is
a completion notice for the prototype, not real Kinder restoration delivery or
publication approval. Independent VPS preservation verification is recorded in
PROJECT_STATUS.md. Verification40559412369/job122384079458 succeeded at
23:23 Asia/Tashkent: UAC app/worker/dispatcher preserved, Inventory unchanged,
paid API0 and model deferral intact. No new runtime scope or project executor
was installed.
