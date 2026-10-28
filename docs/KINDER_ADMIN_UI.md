# Kinder staff panel: completed isolated draft,28 October2026

Bounded work status: **done — responsive RU/UZ staff panel and real browser/API/DB
acceptance**. Full Kinder, Android and the UAC16-stage plan remain in progress.

Draft [PR3](https://github.com/matrix12345695-afk/Kinder-Spa-android/pull/3), stacked
on PR2, branch `feature/admin-panel`. Exact source
`e26d2eadecfce97dba25579a94f70f31914a2ff9`.
Main remains0ef936334629accfd59ae33987462c3c693d33f9; render.yaml unchanged.
No publication, production listener/DB/schema change, real credentials/customer
data, Render/billing write, model key request or UAC worker permission activation.

Implemented: RU/UZ staff login, loaded-record overview, client creation and password
reset, category packages, bookings, pool cancellation/no-show/restoration with required
reason, manual one-time-code redemption and paged audit. Dashboard counts explicitly
refer to the loaded selection, not global totals. Notification outbox is labelled
queued, never delivered. Lists request50 at a time and cap500 per tab.

Browser access requires an explicit exact HTTPS origin and matching Host; default
API browser Origin denial remains. Foreign/null/near-match Origin and spoofed
forwarding headers do not expand scope. Only four fixed local assets are served.
No browser framework/CDN/tracker/remote font or production dependency is added.
Token stays in tab memory; no cookie/local/session-storage/URL token. Logout/expiry
clear private DOM, identity, counters, options and passwords; generation fencing
rejects stale in-flight responses. CSP forbids inline/eval/external script. Text uses
textContent; POST form fallbacks protect passwords even with JavaScript disabled.
Closing password/QR dialogs clears input, including Escape.

Accounting retries preserve the exact operation key after an ambiguous response;
credential operations instead block blind retry and clear the password. Real fault
tests lose an actual committed response and verify one row after a same-key retry.
Other tests cover double clicks, delayed reads after logout, unknown refreshes,
mandatory restoration reason/outbox, client role exclusion and malicious audit text.

Local93 PostgreSQL/API/origin/asset/audit checks pass with zero skips (23.100s);
local24 browser checks pass with zero skips (36.299s), Chromium154.0.8037.57.
Exact push CI40648920945/job122684152607 and PR CI40648925674 succeed.
CI93 checks16.757s,24 browser checks25.109s, Chromium151.0.7922.34. Six synthetic
desktop/mobile RU/UZ screenshots; no password/QR/trace/data-dump artifact.

Artifact12799315337, archive SHA256
`079edff3f0d37a5e87d801218be432c0e9fa472036bbe47f852f6467cc71b22d`.
The archive, both exact-revision reports, all22 component/static source hashes and
six screenshot names were independently verified. All117 checks are actual passes,
zero failures/errors/skips; HTTPS deployment, Android and Telegram sender remain false.

Browser-test wheels are independently hash-locked: Playwright1.62.0 (Apache-2.0),
pyee13.0.1 (MIT), greenlet3.5.5 (MIT/PSF-2.0), typing-extensions4.16.0 (PSF-2.0).
Version-specific PyPI metadata returned no listed advisories at this check; this
does not substitute for a complete OS/transitive audit. Test browser/DB are local
disposable fixtures; no permanent service or additional VPS resource was installed.

Remaining: Android/RU-UZ client, guardian/child profiles/photos, camera QR scanning,
capacity and richer administrative workflows/reports, actual outbox sender, reviewed
HTTPS gateway, controlled DB roles/migrations/backup/recovery and exact owner-approved
publication. See backend/ADMIN.md in the PR for origin, session and retry boundaries.

VPS preservation: initial run40649038530/job122684531717 passed the preceding
Inventory/UAC/policies/calendar checks, then the legacy worker verification exited
without a specific assertion name. This first failure was not reproduced; its
cause is unconfirmed. No app bug fix or runtime restart is claimed from this.

Minimal operator change names all15 existing worker checks and validates their
strict boolean map, failing closed for false/missing/malformed results. No acceptance
condition was removed. Only two helper/test files changed in the authorized transit
branch; operator suite94/94 passes locally and on VPS. New transport pin
908a47e15c42518ed64e62fbf27da45c952dc6ea, bridge agent a83407c570f4f70a6a4e0a4aa69bd9678b862346.
This changes diagnostic visibility, not UAC source, permissions or production Inventory.

Full repeat verification40649797193/job122686948931 succeeds at28 October12:25
Asia/Tashkent. All15 named worker checks true, current invalid rows0/overlap0,
fresh worker state owner_pending, roadmap3228 characters. Same UAC341d1277,
worker3311622/dispatcher3312003, Inventory unchanged, actual paid calls0 and model
deferral intact. Old weekly/voice/repository observations and memory remain valid.
Owner progress notification178 was accepted by Telegram as message418 in
40650132735/job122688029967 at28 October12:27 Asia/Tashkent. API acceptance
does not prove reading, a Kinder outbox delivery or approval of publication.
