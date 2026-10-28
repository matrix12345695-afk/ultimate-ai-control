# Kinder Spa client/staff Telegram draft checkpoint

Date:28 October2026. Owner selection: clients AND administrator.
**DONE: review code and216-check acceptance. NOT DONE: live Kinder bot/pilot.**

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
The uninstalled service template uses DynamicUser, read-only opt source,
private systemd credentials, inaccessible home directories,512MiB/half-CPU caps.
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
on every development turn. Do not resolve this request as a real bot provision.
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
