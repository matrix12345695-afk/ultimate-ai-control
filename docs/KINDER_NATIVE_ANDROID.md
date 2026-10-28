# Kinder Spa native Android client — bounded review increment

Status: **DONE — native review-client draft,146 checks and APK evidence.**
The full Kinder product and UAC stage7 remain active.
Date:28 October2026, Asia/Tashkent.

Current source:ee7ce3686f7d689458cd8ce3a94086e1fa848127. Draft PR4 in
Kinder-Spa-android is stacked on admin-panel PR3. It introduces a
native Java/platform-view Android8+ client with RU/UZ, admin-issued client login,
own subscriptions, upcoming appointments/history, real one-time QR rendering and
pool cancellation through the existing authenticated PostgreSQL API. No public
registration, new capacity rule or production release is introduced.

Review APK and fixture APK have separate app IDs. The review artifact has a
placeholder origin and disabled login; API binding is a reviewed build-time
choice. Session tokens and accounting rows stay in process memory, only language
is persisted. Backup/cleartext/redirects/credential autofill are blocked. Review
windows and QR dialogs prohibit screenshots. QR display uses server-relative
lifetime minus request time and a monotonic countdown, clears on background and
never includes user information in the opaque payload. Cancellation keys survive
ambiguous responses within the session and are fenced against stale completions.

The synthetic fixture uses a local-only PostgreSQL18 schema and different client
accounts, with no production data, remote listener or test route in the real API.
Its debug-only emulator-host HTTP and screenshot exceptions do not enter review
builds. Screenshots never record a QR. No fixture APK is a distribution artifact.

Builds pin Gradle8.13 distribution SHA256, AGP8.13.2 and all verified dependency
hashes; runtime dependency ZXingCore3.5.3 includes its Apache2 license in-app.
TargetSDK36, minSDK26, INTERNET only, disposable debug signing. A compile minimum
does not establish Android8 physical-device coverage. Real SDK35 device tests,
JVM tests, lint, backend/browser tests and source-bound artifact receipts are
required before this work is recorded as done.

Still pending: reviewed deployment/gateway and database lifecycle, real server
binding, production signing/distribution, actual devices/accessibility, complete
client/guardian/photo/catalog operations, physical booking capacity, real Kinder
superadmin outbox delivery and exact owner publication approval. General UAC
model-agent development, live publisher/rollback and the wider16-stage plan are
not made complete by this client draft. Existing key deferral, $30 cap and
disabled hourly coding automation remain unchanged.

Independent preservation check40656293389/job122708013268 passed28October
13:23 Asia/Tashkent. All15 named observer flags are true, invalid rows0 and
known overlap0; worker owner_pending and roadmap3228chars. UAC app341d1277,
worker3311622 and dispatcher3312003 remain installed. Inventory unchanged,
paid API requests0, model setup deferred and existing owner requests preserved.
No runtime source, permissions, service restart or new development schedule
was needed. This check precedes final native artifact collection.

Final native source25756ca02f492fadf1f9a0ec4ece990150ce72b1. Backend/API and browser
source remains byte-identical to9773597fde35631a5e23f6c5bfb95aafa51a3be4. Backend CI40657033765/
job122710474443 passes95 checks in12.675s and24 Chromium checks in23.321s,
zero skips. PR backend CI40657038417 is a separate run. Archive12802620021,
SHA256fd940778c7dd6e0ac1e8f1d222eb5e06b98955f9168739c87f41bd4ccc3748ab;
both reports bind this revision and all23 source hashes were rechecked. Backend
reports deliberately do not certify Android: the native report is separate.

The first native CI40656240494/job122707840912 proved16 JVM +10 fixture +1
review device tests with zero errors/failures/skips. Its workflow failed after
those tests because standard AGP uninstall removed external screenshot files.
The CI-only correction retains test APKs until collection using the verified
stable AGP8.13.2 option android.injected.androidTest.leaveApksInstalledAfterRun,
then destroys the disposable emulator. No mandatory test is bypassed. First
diagnostic archive12801339270 digest443bf84560b1d2095e135dd2b104ab8c39daed742c8fa6b4b1d30a2e2986ef88
and actual XML totals were independently checked; it is not the final accepted
APK artifact.

Kinder main remains0ef936334629accfd59ae33987462c3c693d33f9; render.yaml blob
c90fd6634acdfd66f41ad9f93dce9ee959735dec matches main and candidate. No production
endpoint, schema/customer data, release signing key, deployment, billing write or
Inventory operation was introduced.

Intermediate native source9773597f passed both push40657033776 and PR
40657038434. Its push artifact12802745384, archive SHA256
a9761c9d79e86ed3ae6861a73dd582eec80fd9ee7aeb125cee37eba72dc5cb14,
was independently checked: exact revision,35 source hashes,6 screenshot hashes,
16 JVM +10 fixture +1 review device checks,335622-byte APK. During visual
inspection the Uzbek navigation label was visibly clipped despite that earlier
functional success. Final9401edce fixes adaptive equal-height navigation and
adds a device assertion for text height/no ellipsis; final acceptance below
must cover this corrected source. The intermediate PR report uses the synthetic
merge revisione9047a5488dded924042086dc03f46520310360a, not the source head;
its archive is not relabeled as an exact-source artifact.

The9401edce native push40657872857/job122713230612 and PR40657878887
passed the strengthened localized-text assertion. Manual image review confirmed
that Uzbek labels now fit, but some screen captures still showed an earlier
loading frame. The final25756ca0 test-only change requires loaded data, empty
status, a committed render frame and accessibility idle before capture. Runtime
application code remains byte-identical to9401edce; the final artifact must
include this capture gate and actual reviewed images. Earlier gate success is
not used to conceal that incomplete visual evidence.

Final PR backend CI40658712285/job122716042923 also passes95+24 without
skips. Archive12803261213 SHA25602b033a97fb809d440799b42e56f97d66bc14d64dc95cd0d84ae478c06870d19
is verified: all23 source hashes match. Both report revisions are the PR test
mergea055ecde076b9a3b8be0ab8dbf5cda3811faffe1. GitHub Git commit metadata
proves that merge and final source25756ca0 share the identical root tree
2a1ed3870a9213e406ca3581562bfb72857c9599; the PR merge has final source as its
second parent. This is tree-equivalent evidence, not a claim that their commit
identifiers are equal.

## Accepted application before CI selection correction

Exact-source push CI40658703651/job122716013721 passes build/lint,16 JVM,
10 fixture-device and1 review-device scenarios, zero errors/failures/skips.
Fixture execution60.5s, review2.99s. Artifact12803625524 (30-day retention),
archive SHA25657a783fd511c24203a6c5d568cbd6fd4583610a17ce52ed7a3ea94ff3fa277a1.
Exact source25756ca02f492fadf1f9a0ec4ece990150ce72b1, all35 native/critical-source
hashes and all6 screenshot hashes match. Exact8 archive files checked; all6
images were visually reviewed with complete localized navigation and loaded
records. APK335630 bytes; SHA256c8a066cc6f2da603b7f1b386e2bc44e88d8f10d2536def236469d58d2af319ec.
Actual downloaded APK signature and INTERNET-only permission were independently
rechecked in addition to the CI manifest/SDK/privacy gate. Fixture APKs and
QR screenshots are excluded.

Review artifact:
https://github.com/matrix12345695-afk/Kinder-Spa-android/actions/runs/40658703651/artifacts/12803625524

Local delivery folder /workspace/kinder-spa-review contains the exact accepted
APK, native report and six synthetic images. Review login remains intentionally
disabled without a reviewed real HTTPS origin. No owner release-signing key or
production Play upload exists. Restoring a draft means selecting its pinned
branch/source; no live rollback was needed because no Kinder service changed.

Completion notice179 / Telegram419 was persisted via bridge40659558245/
job122718874403 at13:49 Asia/Tashkent. It identifies the actually accepted
25756ca0 APK review increment. API acceptance is not owner reading, release
approval or Kinder business-outbox delivery.

The parallel PR Android run40658712379 failed with RootViewWithoutFocusException
in all10 scenarios (actual root has-window-focus=false), while the identical
source-tree push succeeded. A device lock or overlay is suspected; no diagnostic
established the exact external cause. Follow-up CI-only f9e2230d explicitly wakes
and unlocks the disposable emulator and keeps its screen on before mandatory
checks. Application/test source remains unchanged. Final follow-up CI results
are recorded below; this does not weaken assertions or increase retry counts.

## Runner preparation follow-up

Current branch headf9e2230dcd347a6229d708edccff4d3633b1643a changes only CI
bootstrap; all35 native/critical source hashes remain equal to the accepted
25756ca0 application/test code. PR native CI40659812181/job122719720487 passes
all27 Android checks; backend PR CI40659812378/job122719721536 also passes
95+24. PR native artifact12802624945 digest
fa63a4f6879596a59f19aef269fefec62bdb7c444dceadcb6af53fef2601d7f7 is checked.
Its report revisione7cd35a4880834f6205ad222d8fb81963c1d8111 and sourcef9e2230d
share root tree03aa8d015929290efcaac73a0f914f0d54cf1ac8; the merge has source
as second parent. APK335630bytes, SHA256
630a64716e7bddf6516a115d9adaa9cce6fe7b0db1cf15521f91f174a0f8579c; all35 source
and6 screenshot hashes verified.

Push40659806111 attempt1/job122719700085 still failed one of10 fixture tests
with an unfocused BASE_APPLICATION root; nine other scenarios passed. No exact
external cause is established and wake/unlock is not represented as a proven
root-cause fix. One manual full-job retry on a fresh hosted runner was requested
without source, assertion, timeout or test-count changes. Preserve this failed
attempt in the history; test-infrastructure focus stability remains a known
follow-up even when a subsequent run passes.

Failure diagnostic artifact12803497471 SHA256
cba87010a1bd96ae88abbb91b0d67e74825dce54b195fb8b1f750213c2b23bf0
was inspected as actual XML. The remaining single failure is waitId(qr_image)
inside test02, after login, rather than signIn. It selects BASE_APPLICATION
while a QR dialog is open. Test-only sourceee7ce368 explicitly targets
RootMatchers.isDialog for QR visibility, bitmap reading and expiry assertions.
The real opaque-token decode and expired-image assertions remain mandatory.
This diagnoses that specific selection error; it does not establish the cause
of the earlier all-window failure. Runtime app source stays unchanged. Local
fixture-test APK build and lint pass in17s. The next independent engineering
increment is bounded Kinder outbox sender/retry/recipient-binding acceptance,
without enabling real customer-event delivery or publishing a service.

The manual retry of earlierf9e2230d push40659806111 attempt2/
job122722286614 succeeds without changing source or assertions. The original
failed attempt remains recorded. Finalee7ce368 additionally corrects the QR
window selector; its new acceptance is independent of that retry. Latest
backend PR40661017122/job122723753228 succeeds, runtime/API hashes unchanged.

## Final current source and delivery

Final sourceee7ce3686f7d689458cd8ce3a94086e1fa848127, root tree
14724b1b22da69a66f6fcbf05d099925cad52bb6. Both independent Android runs
pass on their first attempts after the dialog selector correction: exact-source
push40661006666/job122723720196 and PR40661017130/job122723753421. Each
requires build, lint,16 JVM +10 fixture +1 review-device tests with zero
errors/failures/skips. Backend/browser PR40661017122/job122723753228 passes
95+24. Its test merge921322adbfcb93b6bdc26499d4c0cc09fbead6b9 has the same
root tree as final source (actual GitHub Git commit metadata checked). Earlier
failed attempts are retained above; one successful pair is not a statistical
guarantee against future hosted-device focus problems.

Final artifact12804725651,30-day retention until27November2026, archive SHA256
02286bcea55a9ece3fee4e07a2ad0bb133efa9161af4d94393ca540b7e08643a.
All8 files, exact source revision,35 critical/native source hashes and6 image
hashes checked; all6 synthetic images reviewed. Actual downloaded APK signature
and INTERNET-only permissions rechecked. APK335630 bytes; SHA256
ded79768c6e577a03a6fbd9101637782528d9f4a2ef3740d78e2353498ee120d.
Current local delivery: /workspace/kinder-spa-review/kinder-spa-review-debug.apk,
native-report.json, six original PNGs and a self-contained preview.html gallery.
The gallery embeds the unmodified screenshots; it is not another application
or a production service.

https://github.com/matrix12345695-afk/Kinder-Spa-android/actions/runs/40661006666/artifacts/12804725651

**Bounded milestone DONE: first reviewed native client draft and146 actual
checks.** Whole Kinder and UAC stage7 remain active. Review APK remains
unconfigured/login-disabled; there is no live backend binding, release signing,
production rollout, real Kinder outbox sender or new model/billing authorization.

Final current completion notice181 / Telegram421 is persisted via bridge
40661835521/job122726501711 at14:08 Asia/Tashkent. It identifies finalee7ce368
and artifact12804725651. This is progress delivery, not owner reading or approval.
Final backend archive12804490545 SHA256
911d83cfb3189ceb436ebdac0857d9ce38244a212eea125552c6f121418a6e2b is independently
verified: both reports use merge921322adbfcb93b6bdc26499d4c0cc09fbead6b9,95+24
checks without failures/errors/skips, and all23 source hashes match final backend.
No production service changed; original API-key deferral and owner follow-ups remain.
