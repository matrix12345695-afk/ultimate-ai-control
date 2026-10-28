# Kinder Spa client/staff Telegram draft checkpoint

Date:28 October2026. Owner selection: clients AND administrator.
**DONE: review code, prior216-check acceptance, Render-only hosting correction
and173 local backend/Render checks. NOT DONE: live Kinder bot/pilot.**

## Current hosting decision and status

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

