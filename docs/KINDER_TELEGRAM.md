# Kinder Spa client/staff Telegram draft checkpoint

Date:28 October2026. Owner selection: clients AND administrator.
**DONE: review code, Render gateway/inspection preparation and258 hosted checks.
NOT DONE: live Kinder bot/pilot. Historical evidence is retained below.**

## 29 October2026 — one-click Render handoff

Read-only Render recheck in the previously confirmed My Workspace still finds
no Kinder service; dedicated kinder-spa-db remains available in Frankfurt,
PostgreSQL18, external allowlist empty. No service/env/network/data write or
VPS action was performed. Worker creation through the current connector is
still unsupported; the environment has no configured Render CLI credential.
Do not extract the connector credential or introduce another API key.

**DONE:** provider-supported Deploy to Render shortcut, an isolated deployment-only
branchkinder-render-inspection-20261029, source6bce0cc67572575e7abb06d380f7fc0906ddd08b,
parentc5aa4dc9. Only rootrender.yaml andRENDER_START_RU.md differ; all application,
backend, Android, dependency and test source is unchanged. Root Blueprint is the
already tested inspection worker descriptor, with its service branch pointing
to the new frozen deployment branch. Existing application/PR6 branch is untouched.
Current public Render price0.5c-512mb is still$7/month; that expense is already
approved. No new DB/disk/cron/web service or automatic deploy is defined.

The shortcut returns the official dashboard.render.com/blueprint/new form.
Opening it is not an authenticated deployment. The owner needs only to select
My Workspace and confirm the one approved worker; branch/path entry is no longer
required. No bot secret is needed. Read-only inspection, then idle standby,
remains the default; no Telegram polling, customer data read, migration, grants
or staff bootstrap is added. Underlying tested sourcec5aa4dc9 and its258 checks
remain historical source evidence; deployment-branch CI40829538517 passes207 backend +24 browser checks.
Native checks were not rerun for the manifest/docs-only diff; the27 native
checks belong to unchanged application sourcec5aa4dc9. No fresh Android or
live Render acceptance is claimed.
See the updated [Russian creation form instructions](KINDER_RENDER_START_RU.md).

**PENDING:** actual provider creation and real Render TLS/schema/role report.
Owner notice183/Telegram425 remains the existing request; its instruction URL
now points to this updated shortcut. Do not send another duplicate setup request
or mark live deployment/delivery as complete. The $7 approval and API-key setup
deferral are unchanged. Full Kinder/UAC stage7 is still active.

## Kinder Render API/admin increment — current

Date28 October2026. Owner said “Продолжай” directly after the additional$7/month
worker-cost question. Treat this as approval of that bounded worker expense;
never re-request the same cost approval or authorize higher plans/customer release.
All Kinder hosting/secrets remain Render-only. No Kinder installation, token
transfer, deployment or database probe is permitted on VPS. An existing
ULTIMATE owner-notification may carry progress/action metadata only; it does
not host or execute Kinder.

**DONE in source:** native Render API/admin launcher, fixed Gunicorn26.2.0 gateway
with exact MIT wheel/notice, metadata-only read-only DB preflight, role/grant/audit
checks, repaired root API Blueprint and scoped Render-private TLS configuration.
Kinder Draft PR6, branchfeature/render-api-pilot, source
c5aa4dc911d1ecdf91ee8eecce3e74efc06d8280, treea5e8b9228abb7afc21b76dda406f7a15c76f1284,
stacked on bot PR5/sourcefb313305. Local207 checks47.461s, zero skips, plus28 targeted startup/standby guards. Hosted backend push40714325561 and PR40714334823 PASS207 backend +24 browser
checks. Artifact12827817441 SHA256cb36459569d6ab5067a73704dfa7080f503b9688b37caa2da0a9014fe32bb4db:
both exact report revisions, all37 source hashes and both deployment hashes
verified. Flags retain actual Render TLS/deployment/delivery=false. Native push40714325500/job122907745785 and PR40714335214/job122907819005
PASS16 JVM+10 fixture+1 review checks on their first attempts:258 unique checks
total. Artifact12828750114 digest090c79040d6097fdaec17ae8a9958741d859c7574a60323c924590a8783eadce:
exact revision,36 source hashes,27 tests,APK/six images/eight-file set verified.
APK89eb27419e0cbabe139b624b645146ed083bbc38f2df8f41d9775fed76a3f92d. Historical224-check evidence below is the preceding source.

The API adapter retains exact canonical Host/Origin and current bearer/session/
ownership rules. It sets public HTTPS from Render's documented edge topology,
strips forwarding claims and retains actual socket-peer throttling, not verified
end-user IPs. Private workspace callers are trusted transport peers; this is not
an untrusted-network TLS attestation. Fixed single-worker Gunicorn bounds request
line/headers/timeouts and suppresses raw request/exception logging. Real Gunicorn
HTTP/login/me/header-limit flows and PostgreSQL roles/grants are fixture-tested.

Read-only inspection rejects elevated/owner/member roles, schema/database CREATE,
missing tables/per-operation grants and audit mutation rights. It checks presence/
role/grants, not full schema/constraint/backup equivalence. --inspect may run from
the future API or Kinder worker; only the API can serve HTTP. It prints metadata,
never customer/account/session/password/QR rows. No migration/grant/staff bootstrap
is executed. api-role.sql is a review-only example, not an approved live change.

Current Render documentation says internal PostgreSQL uses self-signed TLS and
does NOT support verify-ca/verify-full. The previous unconditional remote gate
was incompatible. Explicit render-private-tls now pins databasekinder_spa_db and
hostdpg-dbbtkol9fdbs73a7tvqg-a, requires sslmode=require/TLS1.2+, disables GSS
fallback and checks negotiated SSL before schema queries. This relies on Render
private-network/DNS trust, not certificate identity; external/default connections
retain verify-full. Six scope/status fixtures are synthetic. Real Render TLS and
actual internal endpoint confirmation remain unverified. No allowlist change.
Reference: https://render.com/docs/postgresql-creating-connecting#ssl-modes-for-internal-connections

Read-only Render list still shows no Kinder API/bot service. Kinder PostgreSQL
metadata remains available in Frankfurt, PostgreSQL18, same instance and closed
external allowlist; no connection credentials or actual schema were retrieved.
Current connector has NO worker/Blueprint creation operation and cannot import
GitHub Secrets. Supported handoff: provider New→Blueprint, Kinder repo/branch
feature/render-api-pilot, custom pathbackend/deploy/render-telegram.yaml, private
provider token entry. No additional Render key, cron/VPS relay or other service
reuse is requested. Creation costs money even with live mode disabled. Root
render.yaml separately proposes a free API pilot, no DB/disk, manual deploys;
it sleeps on idle and is not an always-on production commitment.

The final worker template starts explicit read-only inspection standby: Render
resolves the existing Kinder connection only asKINDER_INSPECTION_DATABASE_URL,
never as an API/polling fallback. It prints metadata once (including negotiated
TLS flag), then waits without HTTP, Telegram/token reads or data writes even
when the inspected role is not runtime-safe. No bot token/ID is needed for
initial provider creation. For this pinned private host, an omitted sslmode is
forced to require; plaintext/prefer/external fallback remains denied. Before
polling, remove the temporary operator binding from both service and manifest
and supply a separate reviewed runtime role/token. No such transition occurred.

The parentc6cfd631 native push passed but its PR job122901525703 failed ten
fixture cases with RootViewWithoutFocusException. Final Android test-only code
now wakes/unlocks/collapses system UI and waits for an actual focused window
before each activity's assertions. Bounded failure diagnostics contain booleans,
not UI/password dumps. Existing assertions/test totals and customer APK source/
permissions are unchanged. Historical failure is retained; final push/PR native checks pass first attempts.

Provider handoff: [Russian one-time creation steps](KINDER_RENDER_START_RU.md).
The branch is frozen pending this provider setup; use new branches for later
changes and verify the actual Render commit before any operator/runtime actions.

**PENDING:** one-time provider worker creation/secret entry, internal DB/schema/
least-privilege role/TLS/backup/migration/bootstrap review, exact live release,
real Telegram/QR acceptance and operational/customer admission. Owner-reported
GitHub token storage remains unread and is NOT Render binding. No Render resources/secrets/network/data/permissions, installed application
code, Inventory or paid API calls changed. No current Telegram plan/status update is claimed. Existing ULTIMATE owner
DECISION183 / Telegram425 was delivered by bridge40716620739/job122915960664
at20:30 Asia/Tashkent on28 October2026, stable eventkinder-render-inspection-create-v1.
The bridge's94 operator tests pass; only the owner-notification metadata was
added to UAC. No Kinder application/token/data was installed on VPS and no
Inventory source/config/service command was changed. First attempt40716282864
failed the500-character inbox field bound before any delivery receipt; the
shortened request was validated against the exact installed notification module
in a local in-memory database, then delivered under the same event key. This is
ULTIMATE's setup instruction, not a Kinder business-event receipt, owner reading,
customer publication approval or completed provisioning. Latest Render service
list still contains no Kinder service. The owner's provider creation is pending. Full Kinder/UAC stage7
remains active; source preparation only is done.

## Previous hosting decision and status

Owner decision28 October2026: all Kinder hosting, credentials and database must
be on Render; do not deploy anything for Kinder to VPS. Current source is
`fb3133051d23d1a9a27ce4ef2f9ef92ed4341946`, tree
`f809fdf335a7bd8318716651b9eb84dc9e310a4c`, existing Draft PR5. Removes the
uninstalled systemd/env-file templates, reads only the dedicated Render token
variable, refuses non-Render/wrong-service launches before token lookup and
checks exact bot ID/token prefix. These host markers are not an attestation.
Eight new synthetic Render startup checks plus the prior165 pass locally in
38.584s with zero skips. Hosted backend push40694774592/job122838500779 and
PR40694786316 pass173 backend +24 browser checks. Artifact12818128701 SHA256
7f39feb4a678bc450260c297355b3a8d0226ff182833a4012c9fc499867e6101 is downloaded;
both exact report revisions/all31 hashes verified, with real delivery=false.
Native push40694774494 passes16 JVM+10 fixture+1 review emulator checks;
224 total on the exact source. Native PR40694786339/job122838539324 failed
first-attempt fixture checks because all ten windows lacked focus. The exact
source push passed; only the failed job was rerun. Attempt2/job122841754383
PASSES all27 native checks on the same source. All current CI runs succeed;
no test was weakened and the original failure remains recorded. Artifact
12819660735 digest9d1506d9fdb2c5c2f7826dcd86cc7723436f0843a511d9fbac5551c4b06ba499:
exact revision,35 source hashes,27 tests,APK/six image hashes/eight-file set verified.
APK SHA256762d328e8b5288cd679454e6205fc77c0f38b52ae0ee540b70b39912cf92e4f8. Older acceptance below belongs tofd54f218.

Render read-only audit: My Workspace, matrix12345695@gmail.com,
`tea-d52kjcur433s73ca9810`. Existing `kinder-spa-db` is available in Frankfurt,
PostgreSQL18,1GiB/0.1c-256mb, ID `dpg-dbbtkol9fdbs73a7tvqg-a`, database
`kinder_spa_db`. No Kinder API or bot service exists. Empty external allowlist
prevented MCP schema inspection; no networking or data changed.

Owner reports separate BotFather token creation and storage as GitHub Actions
secret `KINDER_TELEGRAM_BOT_TOKEN`. Value/real identity is not verified, and it
is NOT yet connected to Render. Connector cannot import/read back GitHub Secrets.
Use the eventual Kinder Render service Environment form, **Save only**, for
private entry after the exact service/configuration exists. Never request token
text in chat or retrieve it through logs. No VPS token relay is permitted.

`backend/deploy/render-telegram.yaml` is a reviewed-source proposal for one
Frankfurt paid worker, manual deploys, no new DB/disk/cron. It is not applied.
Creation costs money even with default live mode disabled. Public Render
pricing currently lists0.5c-512mb at$7/month, additional to the existing database
(https://render.com/pricing). Account checkout/taxes/usage must be reviewed;
separate owner cost and exact release approval are required.
Internal DB inspection, least-privilege
role, verified TLS/CA, reviewed migrations/backup/restore, Render HTTPS API
bootstrap and a real Telegram acceptance/QR round trip remain pending.
Root render.yaml is still an unfinished API scaffold (missing Dockerfile).
Existing-webhook handling, database singleton admission and safe Render
rollout/rollback must be verified during the pilot; the current lock refuses
a second process and does not implement platform rollout orchestration.
No resource, secret, schema, deployment, UAC runtime or Inventory changed in this
correction. No current bot-plan/owner-notification update is claimed.

## Previous source checkpoint (historical)

Repository: matrix12345695-afk/Kinder-Spa-android. Draft PR5, feature/telegram-bot,
sourcefd54f2184b66a02c54b870a157f7a2200463273f, tree43721e202bfa36bd865aabf4c6c5fe5e4a6dd70d,
stacked on Android PR4/sourceee7ce368. Main/render.yaml and Android Java source
remain unchanged. The existing ULTIMATE runtime remains341d1277; this is an
external project source increment, not an installed runtime update.

## Behavior and limits

Separate RU/UZ private bot for clients and staff. Admin-issued account identity
is linked using a one-use10-minute hash-only code, over trusted bearer/API or a
staff-issued client link. The runner binds the exact getMe bot ID/username. No
Telegram username grants a role; no password is accepted in chat. Private sender
must equal chat ID; forwards/groups/bot senders/foreign callbacks are rejected.
Enabled account, credential version, binding and current role are rechecked at
reads, mutations and delivery. Reset/unlink/role changes invalidate old authority,
including queued private replies. Existing active bindings cannot be taken over.

Client: own subscriptions, upcoming visits/history in20-row pages, one-time QR,
confirmed pool cancellation under the original strict19:00 prior-day rule.
Staff: center records, client link issuance, QR photo or opaque-token checking,
confirmed visit redemption and reasoned restoration. QR decode alone never debits
an allowance. Core accounting, idempotency result and applied confirmation state
commit atomically, with a per-action confirm/decline lock. Pending redemption
retains only a token hash; the existing HTTP API still accepts only raw QR tokens.
No massage policy, capacity rule, child/guardian model or commercial promise is
invented. Password issuance/account creation remain in the existing web/API path.

Restoration queues durable jobs for current valid bound superadmins, separately
per target. No targets leave an event waiting. Current-language messages retain
record/event/staff IDs and remaining count, but omit sensitive reason text.
Delivery states/receipts are separate from approval or reading. Lease45s,8-attempt
limit, bounded backoff/429 retry-after and permanent-error blocking. Crash after
remote acceptance but before receipt commit may duplicate delivery; this is
explicitly tested and is not claimed to be exactly-once. QR cleanup is best effort;
Telegram history can retain an expired image. The server enforces expiry/use.

Fixed Telegram HTTPS host/method/file scope, no redirects/URLs from a message.
Photo bounds2MiB/4million pixels/JPEG-PNG/single opaque43-character QR; fixed
child decoder4s wall/2s CPU/384MiB, no token/DSN in its environment. This is
resource confinement, not a general untrusted-code sandbox. qrcode8.2,
Pillow13.0.0 and zxing-cpp3.1.1 wheels/hash-locked requirements plus full packaged
licenses are committed (BSD-3-Clause/MIT-CMU/Apache-2.0 primary licenses).
The earlier uninstalled DynamicUser/systemd template was removed by the
Render-only correction above; it must never be installed on the VPS.
No service or migration auto-installs. Existing webhooks are not deleted; a DB
singleton lock admits one poller and Telegram401/409 stops the runner.

## Acceptance

Local165/165 in38.153s, zero skips:95 prior checks +70 Telegram cases. Hosted
push40688806179/job122818017713 and PR40688811581/job122818037734 succeed.
Push165 checks33.877s,24 actual Chromium browser checks25.904s. Native
push40688806158/job122818017764 and PR40688811472/job122818034816 each pass
16 JVM +10 fixture +1 review device cases. Total216, first attempts. No synthetic
wire reply is relabeled as a real Telegram receipt.

Backend artifact12816605641 archive digest
b802b0373b1d52c57e4fd89efe3d046d0f166be1fb826b6339d87428072cb84d; both report
revisions are exact sourcefd54f218 and all30 source hashes match local committed
bytes. Report explicitly says real_telegram_delivery_verified=false.

Native artifact12816690805 digest
01f3988825e48568d89331b7c05029626d6499f76171c99ad4f0d071eef022cc; exact source,
35 source hashes,16/10/1 test totals,APK hash/six image hashes/eight-file set checked.
Regression APK SHA256eb4dc1e5345eb7403c0ce7d51143063960277c691e21f2be5834c0fc3c9d583c.
The existing prior review APK is unchanged; no production server is bound.
Artifacts retain for30days; both downloaded archives live in
/workspace/kinder-telegram-work. No fixture credentials/tokens/customer photos
are included in reports. Complete third-party notices are in the source.

## VPS and actual owner notice

Preservation40689032199/job122818782283 succeeds at17:36 Asia/Tashkent. Installed
UAC341d127784643af3b12e41cf08e9c439f9ac990e, worker3311622,dispatcher3312003,
all15 named observer flags true, invalid rows0, overlap0,current owner_pending,
roadmap3228chars. Inventory unchanged. No actual paid API request/model key change.
No new worker/service/permission/cron/development automation was installed.
Owned local Docker fixture was removed; no customer/prod database was touched.

Decision notice182 / Telegram424 was persisted via bridge40689829523/
job122821496149 at17:41 Asia/Tashkent. It names the actual remaining owner action:
create a SEPARATE bot with /newbot in real @BotFather and share only @username.
Do not put its token in chat, GitHub or a command argument; provision privately
once a reviewed pilot configuration exists. Tools cannot create a BotFather
identity. Stable event keykinder-telegram-botfather-setup-v1 avoids a new request
on every development turn. Owner now reports token creation/storage, but do not resolve the entire
provisioning/delivery request as complete; Render binding and live checks remain.
This is an actual ULTIMATE notice, NOT a new Kinder bot/customer event, reading,
release approval or authorization to enable deferred OpenAI API calls.

## Remaining and next work

Dedicated live bot identity/token, reviewed DB/role/migrations/backup/restore,
private configuration and explicit pilot deployment/release approval remain open.
Then verify a real superadmin restoration notification and client/staff QR round
trip with synthetic pilot accounts. Public admission/rate controls, retention,
operational alerts, physical devices/accessibility, client/guardian/catalog and
wider autonomous development remain unfinished. Existing $30/model-key deferral,
owner follow-ups157/168, voice confirmation and Inventory safeguards persist.
The full Kinder/UAC stage7 is active; only the bounded source increment is done.

Source instructions: backend/TELEGRAM.md. No paid resources, external project
publication, real token read, Inventory edit or independent service restart.



