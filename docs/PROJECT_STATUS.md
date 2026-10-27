# ULTIMATE AI CONTROL 4.0 — current checkpoint

Updated 2026-10-27 UTC. This is the resume point for later owner-authorized development. Historical
deployment records retain their original observations; this file identifies the latest state.

## Installed state

Application: `341d127784643af3b12e41cf08e9c439f9ac990e`, draft
[PR #56](https://github.com/matrix12345695-afk/ultimate-ai-control/pull/56), stacked on PR #55.
No publisher or merge/deployment adapter is enabled.
Runtime: `/home/maksim/.ultimate-review-runtime`; SQLite:
`/home/maksim/.ultimate-review-data/live/control.db`. Own rootless cron/flock supervisors manage
one Telegram dispatcher and one operations worker. No separate systemd service was created.
The bot is @UltimateAIControl_bot. Inventory is protected and remains unchanged.

The typed short-lived broker and durable generation/test jobs are installed. The demonstrated
bundle uses fixed offline source, not a model. Provider policy and broker paid policy are both
disabled. No real model key is installed; no real API request, hold or spend was recorded.
Private key transport preflight is verified; see [PRIVATE_MODEL_SETUP.md](PRIVATE_MODEL_SETUP.md).
The owner setup request was delivered as notification 36 / Telegram203. It and the older
runtime setup request were resolved as **deferred**, with the owner's reason retained in
settings and audit. This does not mean a key was provisioned. Do not recreate these requests.

Owner update 2026-10-23: **continue without API-key setup for now**. Do not request or install
a key, enable paid calls, or repeat the setup notification. provider_setup_deferred=true is
persisted on the VPS; existing setup requests were resolved as deferred, not completed provisioning.
Private setup may resume only when the owner returns to it; then review the helper's pinned
runtime before attempting installation. The hourly development automation remains disabled.

## Evidence

Latest prepared project increment: [Kinder transactional accounting](KINDER_ACCOUNTING.md),
Draft PR1 in Kinder-Spa-android, sourced9a63e3957a58a26bfad671c3c4b10db43b5f32e.
Bounded work status **done: code draft and PostgreSQL acceptance**, whole Kinder/UAC
stage7 still active. Actual category balances, reserved visits, one-time QR, strict
previous-day19:00 pool cancellation and reasoned staff restoration/audit/superadmin
outbox are implemented. Local44/44 and hosted CI40559051879/job122382809521, plus PR CI40559055608,44/44
with zero skips pass. Downloaded artifact12758741901 digest and all source hashes
match the exact commit. Android, password/HTTP authentication, physical capacity,
real outbox-to-Telegram sender and production setup remain unfinished. Main and
render.yaml unchanged, no live publication or UAC runtime code/permission change.
Completion notification176/Telegram416 is persisted via bridge40559215441/
job122383382744 at23:21 Asia/Tashkent. It marks only this bounded work complete;
real Kinder outbox delivery and the Android app remain unfinished.
Independent server verification40559412369/job122384079458 passes at23:23
Asia/Tashkent: same UAC341d1277, worker3311622/dispatcher3312003, Inventory
unchanged, original metadata jobs/reports preserved, actual paid requests0, API
deferred, genuine voice confirmations0. No UAC source or permission activation
was needed for this external project draft. The notification is the live bot
completion record; this documentation checkpoint is separate from installed code.

Latest installed UAC increment: [public repository branch freshness](REPOSITORY_HEADS.md), deployed27 October
at16:25 Asia/Tashkent. [Rollout record](REPOSITORY_HEADS_ROLLOUT.md). Installed341d1277,
exact-source CI40494650796/40494656259 passes. Local and VPS full674/674 tests with zero
skips, all18 host-dependent checks executed; VPS146.879 seconds.21 new cases cover fixed
public identity/ref GET scope, bounded/sanitized network failures, manual/schedule admission
and pause/gate/epoch, duplicate/late heads, scoped recovery, immutable snapshots, typed memory,
corrupt-result isolation and views. Transport93/93; synthetic restored-copy drift/error/
recovery/dedup/gate/tamper probes preserve original notes/context/cost/schedules/weekly data.
Activation40495445976/job122159605470 succeeds; backup/restore at
/home/maksim/.ultimate-review-data/backups/before-uac4-1793100211513031815.sqlite3.
Own credential-free worker3311622 and dispatcher3312003; Inventory PID67760/source/config unchanged.

Real worker NOVA metadata job1417 observes public main1a23239a0a9c7d79905c91505a8741d8350d7e75,
report4a6d6b201ce1e2e4637fff4b699d8a8d5842e787110c4c5144d09ecc9a46f183,
typed memory1418. Kinder job1418 observes public main0ef936334629accfd59ae33987462c3c693d33f9,
report924bcd112d02f4ac8dafa4ee73ed604d1928a1e33eadf4bcf410f7b3f65ac952,
typed memory1419. Both match original reviewed baselines at this read. Telegram accepts one
consolidated notice411; not reading/approval. No live branch is moved to test a drift alert.
Synthetic new heads exist only in unit/copy fixtures. /repo_heads reads normalized metadata;
/repo_head nova or kinder queues one manual check per15-minute bucket. Two explicit six-hour
operations schedules are installed; existing schedule definitions are preserved. Admission
and advance are atomic; disabled gates/owner pause/emergency are respected. Unknown config
is not overwritten. Out-of-order observations retain history without replacing cache/notices.
Read failures are failed jobs/unknown snapshots, not healthy checks; repeated states stay quiet
and recovery closes only this monitor's own proven scope notices. No credentials/source text
are fetched; only two fixed GET endpoints per public repository are allowed. Redirects,
identity/default-ref changes, oversized/malformed data and deadline failures fail closed.

The separate repo_head_gate is enabled after gates. Source and CI pins never advance with
main. New commits remain untested, matching commits do not execute tests, and GitHub metadata
does not verify a deployed production version. Inventory/Mini App remain denied. Stage7 stays
active with the verified branch-monitor part; broader mappings and execution/change preparation
remain unfinished. Paid policies remain disabled/deferred with0 actual API spend; no model key
request, permission expansion, code execution, GitHub write or publication. Hourly coding
automation stays disabled. Existing owner requests157/Telegram380 and168, voice confirmation0,
original calendar snapshot/job1359/receipt405/02.11.2026 09:00 due, observations and emergency
implementation314aa918... are preserved. Independent final verification40496212372/
job122162192571 succeeds at16:27 Asia/Tashkent, with matching app/PIDs, both SHA/report hashes
and job/memory identities, preserved Telegram411 receipt and unchanged Inventory/paid policy.
Documentation checkpoint is separate from installed source.

Preceding increment: [observed worker waits and completion audit](WORKER_OBSERVATION.md),
deployed27 October15:53 Asia/Tashkent. [Rollout record](WORKER_OBSERVATION_ROLLOUT.md).
Installed app40eca95a; exact-source CI40491086924/40491094177 passes. Local and VPS full
suites653/653 with zero skips, all18 host-dependent checks executed; VPS149.789 seconds.
22 new cases include a real daemon lifecycle, completed waits/clean shutdown, session takeover,
clock/drop/gap, known-work overlap, conflicting/corrupt waits, explicit handle closure,
read-only views and completion flags, old weekly compatibility and typed daily-result memory.
Transport89/89 and local/VPS restored-copy synthetic gates pass. Activation40491352812/
job122145799028 succeeds; backup/restore verified at
/home/maksim/.ultimate-review-data/backups/before-uac4-1793098288016851645.sqlite3.
Own credential-free worker3275993 and dispatcher3276334 under existing rootless supervisors;
Inventory PID67760/source/config unchanged. No new schedule or independent service action.

Actual daemon sessionf7a96af0258c8db3908b1b229991f62e records20 completed polling waits by
activation verification, with100.44599962234497 observed wait seconds at that read. Real daily
job1406 stores25.109049558639526 wait seconds and86257.35529279709 unobserved seconds in its
24-hour snapshot; union coverage by recorded work accounts for the remainder. Saved
observation digest9e1a255d4aebabbfe0dc9b344f96c2964f96613f5de27e9c22b23ed6a00b9460,
typed memory1407; Telegram accepted announcement409 and report410. Receipts do not prove
reading/approval. Live acceptance inserts no synthetic wait: only the active daemon PID/current
session's completed intervals qualify. Synthetic clocks/session records exist only on the copy.

Each process has a current-session fence; old sessions cannot pulse/write/claim through the
instrumented worker. Completed waits require monotonic/wall agreement and at most8 seconds;
clock jumps, unfinished crash intervals and pre-installation history remain unknown. Queue
reasons are sampled at both boundaries; transitions between samples may be missed. Known job
work is excluded from wait totals. Immutable hash-bound rows and bounded read projections
avoid fabricated idle; stale/closed/missing signals are distinct and do not prove VPS downtime.
One row per completed5-second wait; indexed last-session lookup; existing disk monitoring and
normal worker/voice limits retained. /worker4 24h or7d and /agents expose partial observations.
Daily and future weekly snapshots include the summary. Legacy idle_seconds remains unknown;
the original calendar snapshot/hash/job1359/memory1360/Telegram405/next_due02.11.2026 09:00
remains unchanged. New typed daily evidence binds the observation summary to its saved result.

/finish4 reads all16 stage states and separates existing owner requests/deferred setup from
unfinished engineering. It never treats manual done flags, fixture success, Telegram delivery
or one confirmed voice as a complete autonomous company. Plan11 stays active with the completed
observation subtask; complete model-agent activity, historical coverage and external invoice
reconciliation remain pending. Provider setup remains explicitly deferred, paid policies off,
zero paid requests/costs/holds. Owner voice confirmation remains0 and request168 is not duplicated;
original NOVA request157/Telegram380, approvals/candidates, memory/rules, schedules and emergency
implementation314aa918... are preserved. General multi-project/model execution and the live
publication/rollback adapter remain unfinished engineering, not completed owner setup.
Independent final verification40492217165/job122148689749 succeeds27 October15:56
Asia/Tashkent. Same app/PIDs, session, saved observation digest/job/memory/Telegram receipt;
actual wait rows increase20→54 and current observed wait100.44599962234497→271.24679923057556
seconds. The saved daily snapshot is unchanged. Inventory unchanged, paid calls0; original
weekly snapshot and next delivery remain intact. Documentation checkpoint is separate from source.

Preceding increment: [calendar weekly analytics](WEEKLY_REPORTS.md), deployed27 October,
initial source421acd3b at13:35 and final display correction6ad68431 at13:43 Asia/Tashkent.
[Rollout record](WEEKLY_REPORTS_ROLLOUT.md). Local full631-test suite passes with zero skips;
17 new weekly cases cover period boundaries, atomic queue/outbox/success, concurrency/replay,
pause/epoch, unknown schedule isolation, immutable/reopened snapshot, typed memory and tamper.
VPS631/631 full native tests on421acd3b pass in104.963 seconds with zero skips, all18
host-dependent checks executed. Exact-source CI40473602905/40473607683 passes. Final source
6ad68431 differs only by one reviewed display literal inroadmap.py; its gate compares old/new
bytes and permits no other file/change. All45 affected plan/weekly/analytics/runtime tests
pass locally and on VPS; exact-source CI40474996902/40475003219 also passes. Native execution
code is unchanged by that caption patch; the631-case native proof is retained, not relabeled
as a second full native run on6ad68431. Transport84 initially/85 final tests pass.

Initial activation40474134650/job122088055472 succeeds; final literal patch40475251117/
job122091776519 succeeds. Restored DB report/replay/typed-memory/unchanged-state probes pass;
backup before calendar installation
/home/maksim/.ultimate-review-data/backups/before-uac4-1793090025330924166.sqlite3;
backup before caption patch
/home/maksim/.ultimate-review-data/backups/before-uac4-1793090506450263877.sqlite3.
Own credential-free worker3138409 and Telegram dispatcher3138760 under the existing rootless
supervisors; Inventory PID67760/source/config unchanged. Existing daily/monitor schedule
definitions, voice policy/gate and original owner follow-up157/Telegram380 are preserved.
Only reviewed weekly-analytics-v1 is added to the operations queue. Monday09:00 Asia/Tashkent
covers the preceding closed Monday00:00–Monday00:00 week. Late restart admits the latest
eligible week only; exact period keys and atomic schedule advance prevent duplicate jobs.
Unknown definitions are not overwritten, and owner disable/pause/emergency are respected.

Live report job1359, period1792954800 (19–25 October), measured work918.8121018409729 seconds;
immutable snapshot5bfb65e564ea28afd6cb6babca6f30e926adc193d5c55e932f31e3114e584edd,
typed memory1360. Snapshot, one period-scoped INFO notice and job success commit together
under the lease/current epoch. Waiting is summed by task; idle remains unknown. Costs are
known settled receipts, while holds/incomplete receipts are separate and snapshot-timed.
A report is not evidence of a full model-agent team. Telegram accepted announcement404,
report405 and final caption verification406; receipts do not prove reading or approval.
The same report/job/memory/hash/receipt survives the caption update. Next scheduled report:
02.11.2026 09:00 Asia/Tashkent. /weekly_report reads saved calendar data, /weekly_auto shows
schedule status; /weekly remains a rolling7-day view. Rolling report dates now use Tashkent.
Plan11 remains active with the saved-calendar-report part completed; full observed idle,
model-agent work and external invoice reconciliation remain pending. Voice stage10 remains
active, genuine confirmed voice/task pairs0; its sample request168 is not duplicated.
Provider/broker policies remain disabled/deferred, zero costs/holds and no new model key.
Hourly coding automation stays disabled; no Inventory/NOVA production or publishing change.
Independent final verification40475590945/job122092908320 succeeds at13:45 Asia/Tashkent.
Final app, process IDs, original snapshot/job/memory/Telegram receipt and next scheduled
time match. Inventory metadata/source/PID unchanged; zero paid requests; first voice sample
still pending. Documentation checkpoint is separate from installed app.

Preceding increment: [owner voice intake and explicit confirmation](OWNER_VOICE.md), deployed27 October
at12:39 Asia/Tashkent. [Rollout record](OWNER_VOICE_ROLLOUT.md). Installed appbc9a8b06,
exact-source CI40465293362 and40465297588 pass. Local full suite614/614, zero skips; VPS full
native suite614/614 in270.315 seconds, zero skips, all18 host-dependent checks executed.
The earlier baseline also passes614/614 in234.688 seconds.49 new tests cover bounded
owner-private transport, persistent previews, exact confirmation/replay, stale epochs/TTL,
private cleanup and anonymous sealed audio intermediates; native canary verifies the hard
file-size0 cap for both input modes. The final single complete native gate avoids repeating
the baseline while preserving every test. Transport79/79; activation40467710745/
job122067040419 succeeds. Earlier source-deadline attempts never activated the app.
Restored SQLite copy, synthetic capture/confirmation/replay and receipt tamper checks pass;
backup /home/maksim/.ultimate-review-data/backups/before-uac4-1793086619382517885.sqlite3.
Dispatcher3069531 and credential-free operations worker3069190 run under the existing own
rootless supervisors; Inventory PID67760/source/config metadata unchanged.

Separate0600 owner policy /home/maksim/.ultimate-review-data/live/voice-owner-policy-v1.json,
mode owner_preview, references unchanged native v2 assets/manifest and contractb66bd548...
The separate voice_intake_gate is explicitly enabled. Owner-only mono OGG/Opus input is
bounded to10 seconds/256KiB,5 active inputs/30 per rolling24 hours; previews expire15 minutes
from capture. A viewed transcript and exact project/current code are required before one
ordinary text task is inserted. Transport gets the bot credential only through stdin in a
bounded dedicated process; decoders/worker receive no credential. Raw source files are private
outside SQLite and deleted after recognition/rejection/expiry; intermediate audio is anonymous.
No transcript is treated as a Telegram command, publication/payment or business-rule approval.

Real queue acceptance job1339 passes one native public-English recognition plus8 explicitly
synthetic state-machine cases on a separate disposable DB; typed memory1340. Recognition
7.9678 seconds, reportadb15963e76a177c55d350148766bb91330450ec932eb40dd04b7a0820630360,
implementationf889714a1651fffceab2d623ad15f2e9dad04a0ed13fafd8d662ab20bc31bda6.
Telegram accepted announcement401, test result402 and first-real-sample request403
(notification168, stable event owner-voice-first-sample-v1); these receipts do not prove
owner reading or confirmation. Zero genuine confirmed receipt/task pairs were observed.
Plan10 stays active with the implemented pipeline subtask marked complete. Genuine incoming
owner Telegram round-trip/confirmation and RU/UZ accuracy remain pending. Confirmed text tasks
use the ordinary queue; general model-driven execution still waits for deferred key setup.
Provider/broker paid policies stay disabled, zero costs/holds, hourly coding automation stays
disabled, no publication/new schedule/Inventory or NOVA production change. Existing owner
follow-up157/Telegram380, approvals/candidates and emergency implementation314aa918... preserved.
Rollback uses only exact-version uac4_owner_voice_rollback: disable intake, drain its own work,
terminate its own in-flight transport, expire unconfirmed inputs, restore preceding appb8ed9187;
confirmed text tasks, receipts/history/assets and owner pauses remain. No live DB restore.
Independent post-install verification40468546671/job122069773584 succeeds27 October12:41
Asia/Tashkent. Source, report/implementation hashes, job/memory/Telegram receipt and process
IDs match. Genuine confirmed receipt/task pairs remain0; only the first-sample request stays
pending. Documentation checkpoint is separate from installed source.

Preceding increment: [offline speech acceptance pilot](LOCAL_VOICE.md), deployed26 October
at22:33 Asia/Tashkent. [Rollout record](LOCAL_VOICE_ROLLOUT.md). Installed native-host v2
app b8ed9187; exact source CI40303932769 and40303941488 pass. Local/VPS full suites565/565,
zero skips, including all17 host-dependent checks and14 new voice checks. Hosted baseline
skips17; transport70/70. First portable build failed closed during graph initialization
(SIGILL), without app activation; separate host-native v2 preparation40304032348 succeeds.
Source/model/decoder pins retained; compiled binary is host-specific and manifest-pinned.
Old candidate/policy retained. First activation40368389716 stopped before replacing the app
at its restored-copy stage-transition check; corrected gate now passes even with a freshly
planned voice stage. Final activation40369057736/job121734547934 succeeds; dispatcher2195006,
credential-free worker2194680; Inventory PID67760/source/config metadata unchanged.
Backup/restore: /home/maksim/.ultimate-review-data/backups/before-uac4-1793035912154328711.sqlite3.
Private assets /home/maksim/.ultimate-tools/voice-4979-tiny-q5-v2;600 policy
/home/maksim/.ultimate-review-data/live/voice-candidate-policy-v2.json (acceptance_only),
contractb66bd548624e82e1a41d6c7b47a303fa039d93b24c7a33d5931aebce4d189722.
Real queue job1056 runs the fixed public English OGG/Opus8-second fixture; recognition7.8751s,
report2d28565a56143cd1b41f699eacf351283077239dcca8f9a9123bc5c2804fd647,
manifest1bffbfd6f48f912da6e303f9b89f9c8131e205cc29a1e008f636bc2bfb04228b, typed memory1057.
Telegram accepted announcement390 and result391; not owner reading/approval. /voice4,
/test_voice4 and «Голос4.0» show the measured candidate. Plan10 remains active, with a completed
pilot subtask. **Owner Telegram voice ingestion, RU/UZ accuracy and transcript-confirmed
creation of a real task remain pending.** The present wrapper accepts only its pinned public
fixture; no arbitrary user-audio input or paid provider. Read-only native stages use network/
fork/host-file denial,1CPU/768MiB virtual-space caps and bounded time/output. The original
emergency implementation hash314aa918... remains unchanged, live epoch0/unlatched. Existing
owner follow-up157/Telegram380, approvals, candidates and deferred API setup unchanged; zero
live costs/holds and no new schedule. Independent verification40370142991/job121738363286
succeeds at22:36 Asia/Tashkent; exact report/manifest, queue/memory/Telegram and process IDs
match. Documentation checkpoint is separate from installed app source.

Preceding increment: [durable UAC emergency control](EMERGENCY_CONTROL.md), deployed26 October
at14:17 Asia/Tashkent. [Rollout record](EMERGENCY_ROLLOUT_RECORD.md). Exact-app CI40297441230
and40297445882 pass. Local and VPS full suites551/551, zero skips (all15 sandbox checks
executed); hosted baseline intentionally skips15. Transport67/67. Isolated activation
40297890272/job121488316872 succeeds. Dispatcher1681469, credential-free worker1681143;
Inventory PID67760, source/config metadata unchanged. Backup/restore verified at
`/home/maksim/.ultimate-review-data/backups/before-uac4-1793006158200625461.sqlite3`.
Live selftest job890 succeeded, report113c7b4d30d2ebda71639f5a497c69ac59acea04d4f7d41022f46bea508070af,
implementation314aa918ef73dfce63523abdb0aa345ca71e93403fca695aa4289fb6f05e118f,
typed memory891. Announcement Telegram388 and result389 are persisted API acceptances,
not owner reading or approval. `/emergency`, `/emergency_test`, emergency stop/status buttons
and evidence-derived completed Plan subtask verified. Actual stop/reset ran only on the
restored disposable DB and the eight-case in-memory acceptance; live latch remains false,
epoch0. New claims and GitHub/paid mutation admissions are fenced, old approval epochs stay
invalid after reset, and `/resume` cannot clear a latch. Admitted external requests may
finish; receipts and unknown outcomes are retained. Provider policy/paid broker remain
unchanged/disabled, zero live spend; owner follow-up157/Telegram380 unchanged.
Independent verification40298557723/job121490516058 succeeds26 October14:19 Asia/Tashkent;
same report/implementation hashes, queue job, memory, Telegram receipt and process IDs.
The checkpoint documentation commit is separate from the installed app SHA.

Preceding increment: exact encrypted application-copy draft and UAC read-only acceptance report.
NOVA [Draft17](https://github.com/matrix12345695-afk/nova-web-agency/pull/17) head
9df2a1c9fcc35e83f1a2fe35bee2480afac3254f adds standalone scripts/tests/doc only over
Draft16a3c3e77e; no server route, command, startup, schedule or dependency change. Original
NOVA checks40290768772 pass. Required hosted gate3901bc71308f1f473a02b519bf1c6c55e05789a4 /
push40290801445/job121465134159 passes30 checks:18 native fault/unit plus12 real PG18 cases.
5003 synthetic leads/all4 supported tables are read in one read-only snapshot, streamed
into standard CMS AES-256-GCM/RSA-OAEP-SHA256 and recovered to an empty loopback fixture
with transactional text readback. Bigint/raw JSON precision, microseconds, source state,
constraints, event sequence and Telegram/reminder dedup survive. Failed recovery rolls
back all newly created objects. Exclusive private files, cleanup, corrupt/wrong-key inputs,
limits, schema drift and read/commit faults are verified. These are fixture results, not
actual production export/retention/recovery or a formal cryptographic/dependency audit.

Node24.21.0/OpenSSL3.0.13/PG18.6 hosted acceptance; local native iteration used24.19.0/3.5.7
and is not mislabeled. Initial source/harnessd09def38/bfdec31b failed on PG18 NOT NULL catalog
differences; corrected before passing. Source manifest625080dec4cdce53139b8d5692ab8143a93413b919d45beb9ce67b35d5e33ca1.
Production lock unchanged9db9b93b90b4fbeabb5fb780eefe6345e5f87a08d9e2b530cd93335f46efafcf.
Verified archive12636252081/1424bytes/SHA256c290a6e7da296ac9091ee2bc0c08c45851f5c620eb693a2596efaae374a0fb3a
expires2026-11-25T08:14:12Z; only report.json and public source pins, no copy/key material.
Report-file SHA2564940583a2330b07d1cf0ab975bedb74dfa5ee3e9ea0c545dc73972ab6ad75850.

Current verified Render Free docs exclude SSH/Dashboard shell and one-off jobs. Internal
outbound DB access is possible subject to same workspace/region/isolation, but the current
tools provide no invocation path; runtime OpenSSL and live service binding are unverified.
Hosted SQL remains blocked by the empty external allowlist. Nothing was opened/upgraded.
An approved invocation, owner recipient/key custody, private durable storage and recovery
of the exact real object remain required before production_backup_verified can be true.
The known Free DB expires19November13:40 Tashkent. No publication or payment is authorized.
Existing release binding remainsa3c3e77e; Draft17 receives no implicit approval.

/nova_copy, /test_nova_copy, “🔐 Копия NOVA”: exact-contract GET-only App observation, separate
private0600 policy, immutable reports, typed memory and completed Plan9 subtask; the full
stage stays active. /nova_recovery links it. The delivered owner follow-up157/message380
keeps its exact original title/reason/action/receipt, with no duplicate decision. Production
key generation, retention, execution availability, production backup and publication flags
all remain false. See [NOVA_PRIVATE_COPY.md](NOVA_PRIVATE_COPY.md).
Local524 app tests pass with all15 sandbox cases executed, zero skips;61 transport tests.
Exact-app Safe unit CI40290990690 and extra private-copy acceptance40290990678 pass.

[UAC-only rollout40291224949](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40291224949)
passed61 transport and524 app tests on VPS: default pass skips15 host-dependent cases,
full explicit sandbox-enabled pass executes all15 without skips. Actual App read-only
CI authentication and restored-copy pending/report-tamper/memory probes pass. VPS job869,
report9b16c0fa183b178dfa4de2e6e7d5d6d84a221fb1364ee268985533a845a31abe,
memory870 and Telegram result384 accepted. Original owner-followup157/message380 content
and receipt unchanged. One dispatcher1622690, one credential-free worker1622307, Inventory67760
and source/config unchanged. Model setup deferred, paid calls/holds/spend0; no new coding
schedule, service, production key or NOVA/Render/DB/network/payment/publication mutation.
Own backup tested through isolated restored copy:
/home/maksim/.ultimate-review-data/backups/before-uac4-1793002788670285838.sqlite3.
Transportc5dcf0f53a85f6a07c793699fb1f30577846b94b; bridge-agenta468d1ae4d319efbf50695468e84ed7627a48c9a.
Installed appcd8aa269; subsequent checkpoint documentation does not change installed code.
[Independent verify40291828696](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40291828696)
passed with the same source/report/archive, result receipt, typed memory/Plan, original
owner-followup content, Inventory metadata and disabled paid policies.

The following recovery checkpoint is historical evidence from the preceding application:

Latest increment: PostgreSQL18 application-schema recovery fixture and private-backup readiness.
The actual hosted [24-check recovery gate40280260616](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/40280260616)
passes for harness25aeef847dd978b19a9807e147b532de6f8a57ca and exact NOVA Draft16a3c3e77e.
A SELECT-only export role produces a consistent custom-format public-schema dump while
another fixture writer adds a later record. All5003 synthetic leads and4 tables restore
with exact field/history/sequence/constraint/dedup/reminder checks. Corrupt/truncated/missing,
unsafe-mode/manifest, nonempty and foreign destinations are refused. The old lead-only JSON
export5000 limit is reproduced; no real production lead count is inferred. New observer
never reads live SQL or sets production_backup_verified/Render_rollback_eligible/publish_allowed.
Only dated Render metadata and exact GitHub CI/archive evidence are stored. /nova_recovery,
/test_nova_recovery and “💾 Восстановление NOVA”; typed memory and completed subtask in Plan9,
which remains active. The previous publication protocol remains unchanged/disabled.

Known NOVA database dpg-dbbii4gm7kps73f41k00-a is Free/PostgreSQL18/available, expiry
2026-11-19T08:40:50.912361Z (19November13:40 Tashkent). The historical NOVA runbook names it
as the working CRM; current service DATABASE_URL binding was not inspected. Current Render
docs exclude Free from managed PITR/logical exports. Hosted SQL metadata query is blocked
by the empty external allowlist; no network/access setting was changed.34 deployment records
were enumerated with a terminal empty cursor and no active status seen at observation;
a live baseline deploy record does not prove its build is retained. Private production
export/durable encrypted storage/restore of that exact export and baseline build eligibility
remain missing. A deduplicated owner follow-up records the private export need before expiry;
it does not authorize payment, access expansion, publication or resolve deferred model setup.

Archive12632235477/1522bytes/SHA256cb5778e8d25951e546910a9cfccdfb1e3752e487ebf9f2f75046f8e876e9142b
expires2026-11-25T06:31:20Z; ZIP/report/source pins verified. Only synthetic counts/digests
and public source pins are uploaded. The65806-byte test dump is private and discarded.
Report-file SHA2567c4265945ba647bda2007feb9d3a1113070963be01fea8e6cdf1de3c3af341d8.
See [NOVA_RECOVERY.md](NOVA_RECOVERY.md) and [review](../ci/nova-recovery/REVIEW.md).
Local515 app tests (all15 sandbox cases executed, zero skips),58 transport tests;
exact-app Safe unit CI40280599361 and extra recovery acceptance40280599383 pass.

[UAC-only rollout40280745551](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40280745551)
passed58 transport and515 app tests on VPS: default pass skips15 host-dependent cases,
full explicit sandbox-enabled pass executes all15 with zero skips. Actual App GET-only
CI authentication and restored-copy pending/tamper/typed-memory probes pass. VPS job835,
report8bcd9e6f93d53584a7e2fd0639c543a88a182076154821c94b69795ce356286f,
memory836; Telegram result382 and owner-followup157/message380 accepted. Delivery acceptance
is not owner approval/read. Sole dispatcher1516410 and one credential-free worker1516056;
Inventory67760 and source/config metadata unchanged. Paid calls/holds/spend0 and model setup
deferred. No new service, coding schedule, provider access or live NOVA/Render/DB mutation.
Own backup with restored-copy verification:
/home/maksim/.ultimate-review-data/backups/before-uac4-1792996687113260289.sqlite3.
Transport05b6d7ac4ed7a744aa248e108dbfd31924d175be; bridge-agent21ac4f1507cef2712c7034b53aefd05116467a85.
Installed app2ee77bd4; subsequent documentation records this checkpoint without reinstallation.
[Independent verify40281257729](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40281257729)
passed with same source/report/CI/archive, owner-followup and result receipts, memory/Plan,
Inventory metadata and disabled paid policies.

The following protocol checkpoint is historical evidence from the preceding application:

Latest increment: NOVA fixture-only publication protocol and a live read-only readiness report.
[Draft PR48](https://github.com/matrix12345695-afk/ultimate-ai-control/pull/48) adds
`/nova_deploy`, `/test_nova_deploy`, “🧭 План выпуска”, immutable report storage and typed
memory. Read-only App GETs revalidate the existing exact83-check CI/archive; three separate
in-memory fixtures exercise success, conditional rollback and an uncertain accepted write.
24 machine fault tests plus9 report/integration tests cover stale/foreign scope, concurrency,
restart, rollback limits, immutable evidence, delivery and no live approval side effects.
Local full sandbox-enabled suite:498 tests, no skips. Exact-app Safe unit CI40274845407
succeeds with15 host-dependent cases skipped; the separate real-host run is required.
Transport suite:55 tests. Protocol definition SHA256
419cd01001b024121dabbbd3462779b3711b879a4fed5f67c23e5cfb0d13f639.

The production planner is permanently dry_run_only in this revision. It never loads a Render
credential, sends Render requests, requests/consumes owner approval, or creates simulation
approvals/tables in live SQLite. Every plan is blocked with production_mutations=0 and
publish_allowed/may_request_approval/published=false. Its committed Render/repository snapshot
is a dated read-only observation, stale after15 minutes, not refreshed automatically by the
command. A20-deploy sample is not a complete queue proof. Real backup/retained build eligibility,
provider access, an audited live adapter and exact owner release approval remain outstanding.
Simulations and the existing PostgreSQL rehearsal do not prove a real Render rollback.
See [NOVA_PUBLICATION_PROTOCOL.md](../NOVA_PUBLICATION_PROTOCOL.md).

[UAC-only activation40275026458](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40275026458)
passed55 transport and498 app tests on VPS. Default app pass skips15 host-dependent
cases; full explicit sandbox-enabled pass executes all15 with zero skips. Actual read-only
App authentication and restored-copy immutable-plan/memory/approval-isolation probes pass.
VPS job814 saved report05663d69b28db209dd738097774050c262c42608a622e002326dbe5deab2c229,
scope9c2e80309df8550cd1cbb00dafe0592c1067a9913fce872f3ff39bc5c7201eaa, memory815.
Telegram accepted activation376/result377; this is delivery acceptance, not owner approval/read.
Plan9 remains active with verified protocol subtask. Sole dispatcher1453710, one credential-
free worker1453229, Inventory67760 and source/config metadata unchanged. Deferred API setup
and disabled paid policies remain; no paid request/hold/spend, new service or hourly coding
automation. Own backup/restore check:
/home/maksim/.ultimate-review-data/backups/before-uac4-1792993058814833351.sqlite3.
Transport commitb8010712daa0e8788d9581b56c985a4517e153d3, bridge agenta25ab4b7ba87a918eb51e8f1f4af004448c601d9.
Committed Render snapshot05:32:16 UTC still shows original1a23239a/live deploy and unchanged
settings. Public domain and Render origin GETs05:36 return original homepage Git blob
00d76b471b3675ab052bbe30526fb0f2e350ac42 and healthy PostgreSQL contract. Platform settings,
NOVA main, public site and business data were not written. Installed app45ddce6a; subsequent
checkpoint documentation does not change installed code.
[Independent verify40275467233](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40275467233)
passed with the same installed source/report/scope, Telegram receipt, typed memory, Plan and
unchanged Inventory metadata. No additional publication or owner approval was performed.

The following locked-build checkpoint is historical evidence from the preceding application:

Latest [locked NOVA build reporting rollout](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40271090255)
passed52 transport tests and465 app tests on VPS. Its default pass skipped15 host-dependent
cases; full sandbox-enabled pass included all15 real Python/Node cases without skips.
Exact-app Safe unit CI40270832706/40270836147 and83-check PR40270836000 succeed.
Actual App read-only authentication and restored-copy pending/tamper/memory probes passed.

NOVA Draft PR16(head a3c3e77e0e74d33241935d25dd3bdfdd306ccd90) is stacked on interface
PR15/495a7f1a. Six build/config files pin Node24.21.0, pg8.23.1 and the unchanged reviewed
14-package integrity tree; engine-strict plus production npm ci reject mismatches. Main/live
application/business code is unchanged. Blueprint proposes npm ci and auto-deployoff with
existing source/health; current Render JSON Schema validation passes. It is not platform
validation/sync or approval. Higher-priorityNODE_VERSION is not inspected/changed; build
fails safely on an incompatible runtime. Actual npm11.19.0 recorded; audit0 known advisories
at run, not a permanent security guarantee. NOVA project checks40269808859 succeed.

Combined hosted harness7d4081e9bdc86cdc620656b44cadb40067d12331 / push40270398506 and
PR40270404161 pass34 original app tests,15 real HTTP/PostgreSQL transition/data checks and
34 Chromium checks:83 total,0 skips,15 PNGs. Candidate installs its own committed production
lock; installed versions/integrity match all14 reviewed packages. Actual invalid lock/runtime
installs fail EUSAGE/EBADENGINE. Four fixture CRM tables survive baseline->candidate->baseline
including candidate-era writes, no DB restore. Browser form API is mocked; restart HTTP is
real. No production data, actual Render rollback, real-device/full-accessibility or zero-
downtime acceptance. Initial anonymous metadata rate-limit failure occurred before tests;
fixed parent scopes the ephemeral read-only token to exact compare URL and never to children.

Archive12628940071/12842301 bytes/digestab2beb587d10fef44c010ac9b4b3402d9e8cdb0a9c75b06065c7c802166d8953
expires2026-11-25T04:43:30Z. Downloaded ZIP/report hash and all15 PNG hashes/dimensions verified.
Report-file SHA256fd2f9385f4248bc6ba1e2becc4657cbe8bb9e74be87e21e0a1a9bdd9af812ec3.
Production lock SHA2569db9b93b90b4fbeabb5fb780eefe6345e5f87a08d9e2b530cd93335f46efafcf.

VPS job798 saved report00660427e84c91454de0cf23c93d8a8657459f69021c175b4ce5045d1a5b73dc.
Telegram accepted activation374/result375; memory799 binds report/contract/source/lock/archive.
/nova_build or 📦 Сборка NOVA shows83-check split and proposal status; /test_nova_build only
GET-revalidates fixed run/attempt/archive. Separate600policy/scope/lease before key use,
immutable report and typed memory. Shared CI observer explicitly supports mixed engine,
backend and upload-step contracts, with old defaults/history unchanged. /nova_release now
labels495a7f1a as the previous version and links the new build. Plan9 stays active; only
verified Draft work is completed. No production approval/candidate created/consumed.

Sole dispatcher1405948 and one credential-free worker verified; Inventory67760/source/config
metadata unchanged. Paid calls/holds/spend0, model setup deferred. No hourly coding schedule,
provider grant/key, new service, VPS browser/DB/dependency or live NOVA/Render change.
At04:51 UTC Render still usesdep-dbchlhqvcj2c738paun0/1a23239a, empty health path, commit
auto-deploy and npm install build; public homepage200/35735 bytes matches original00d76b47.
Backup/home/maksim/.ultimate-review-data/backups/before-uac4-1792990335786495219.sqlite3.
See [NOVA_LOCKED_BUILD.md](NOVA_LOCKED_BUILD.md) and non-executable
[NOVA_PUBLICATION_PLAN.json](NOVA_PUBLICATION_PLAN.json) for exact source/lock/evidence,
proposed actual build/health/off settings and remaining fresh platform/artifact/recovery/
access/owner approval. Lock is fixed in Draft, not deployed. Actual Render rollback and a
least-privilege exact-version publisher remain unverified/unconnected. Installed app95b172f3;
subsequent documentation commits record this checkpoint without changing installed code.

[Independent verify40271650507](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40271650507)
passed04:57 UTC with same report/archive/receipt/memory/Plan/source and Inventory state.
Fresh Render/main/public HTML observations05:00 UTC still show original service settings
and baseline1a23239a; all proposed build/health/off changes remain un-applied.

The following release-rehearsal checkpoint is historical evidence from the preceding application:

Latest [NOVA release-rehearsal reporting rollout](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40234805546)
passed49 transport tests and456 app tests on VPS. The default pass skipped15 host-dependent
cases; full sandbox-enabled pass included all15 real Python/Node cases without skips.
Exact-app Safe unit CI40234688758/40234692431 and rehearsal PR40234692424 succeed.
Real read-only App authentication and restored-copy pending/tamper/memory probes passed.

The owner confirmed Render workspace My Workspace,tea-d52kjcur433s73ca9810 for read-only
NOVA inspection. Service:srv-dbbhm5k9v7es73f9kf10; live deploydep-dbchlhqvcj2c738paun0,
source1a23239a. Main commits auto-publish, HTTP healthCheckPath is empty despite repository
render.yaml/health, and npm install with^pg is not reproducible. No Render setting, deploy,
restart, permission, credential or paid resource was changed. Available MCP trigger lacks
an exact commit option and has no rollback tool. Archived safe metadata is pinned in
nova_render_snapshot.json; VPS does not automatically refresh Render observations.

Hosted harnessce46dc1bbbdbc9c65b2706053b53dcffcb881f10 / push40234072189 and
PR40234075915 passes34 original candidate tests and15 actual loopback HTTP/PostgreSQL16
transition checks: exact baseline1a23239a -> candidate495a7f1a -> baseline. All four CRM
tables retain old and candidate-era fixed fixture writes without restoring DB. Failed local
candidate startup leaves baseline available. Socket guards reject external destinations;
server/helper children receive no real service secrets. This is a local process rehearsal,
not an executed Render/platform/zero-downtime rollback. No real lead or production DB access.
Archive12612949720/956 bytes/digest2e50bef068c70b16ab063608f7bae39e0dd94c1ac102a29d3fe96b125b00ec47
and report digest7db73ce6ef7dcea143bf7fcebaab3b68ca1e4bd3fe7719d85dc4fd74a3dd0db8
were independently verified after download. Archive expires2026-11-24T21:09:04Z.

Live VPS job646 saved reporte27459e3ca6de628c5932f4456765868456f20066dadf9d2cdb9ace47127f3b6.
Telegram accepted activation369/result370; memory647 binds CI/report/snapshot/blockers.
/nova_release or 🚦 Выпуск NOVA shows completion and pending conditions; /test_nova_release
GET-only revalidates fixed CI, not Render state and not a new test/deploy trigger. Plan9
stays active, showing completed34+15 rehearsal; no approval/candidate created or consumed.

[Independent verify40235182107](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40235182107)
passed21:22 UTC with unchanged exact report/receipt/memory and original baseline/browser/PG/
local Node/resource/recipe/PR preflight evidence. Sole poller940092 and one clean-env worker
verified. InventoryPID67760/source/config unchanged; model setup deferred, paid calls/holds/
spend0. New Render reads21:22 still show same live baseline/settings/deploy; main remains
1a23239a and public homepage200/35735 bytes matches original00d76b47 blob. No new daemon,
schedule, DB/browser/dependency on VPS, NOVA source change or production publication.

Backup/home/maksim/.ultimate-review-data/backups/before-uac4-1792963174109785797.sqlite3.
Details:[NOVA_RELEASE_REHEARSAL.md](NOVA_RELEASE_REHEARSAL.md). Non-executable exact-service
proposal:[NOVA_PUBLICATION_PLAN.json](NOVA_PUBLICATION_PLAN.json). Next: pin production
NOVA dependency/runtime versions in a new Draft revision and re-run exact-head acceptance;
prepare approval-scoped/health and auto-deploy change, fresh platform/retained-build/recovery
checks and least-privilege exact-version publisher before asking for publication approval.
No assumption that current GitHub App or Render MCP grants VPS NOVA publication rights.
Installed app stays9d036057; following commits record documentation only.

The following frontend-candidate checkpoint is historical evidence from the preceding application:

Latest [NOVA frontend candidate rollout](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40229896025)
passed46 transport tests and447 app tests on VPS; its default pass skipped15 host-dependent
cases, full sandbox-enabled pass included all15 real Python/Node cases without skips.
Exact-app Safe unit CI40229722955/40229726534 and candidate browser CI40229722962/40229726573 pass.

NOVA Draft PR15 contains only index.html fixes: reversible name/contact placeholders RU/UZ,
44x44 language targets and visible keyboard focus, plus mobile backdrop-filter containing-block
fix. Exact candidate495a7f1a1a3a25c45fd98101fffa9c02e58f3970, based on1a23239a. Its original
NOVA checks40229463007 succeed. All7 new regressions fail on the baseline; first candidate
failed mobile bounds and was corrected without weakening the test. Local Chromium154 passes34.
Exact hosted harness8bd210e3acefe36b92b2f55ff8d0a8135bd83bd6 / push40229505378 and
PR40229509407 pass34/34 with no failures/skips on Chromium151.0.7922.34,3 viewports,15 PNGs.
APIs are fixtures; no real lead/backend, physical-device or full localization/accessibility acceptance.

Archive12612513627 is12840836 bytes, sha256
2c17578aff9305de3576d7c7839d2bde26f6f00895e83ba6fa7a18c7fd2570fc, expires2026-11-24T20:11:41Z.
Downloaded archive digest, all15 PNG hashes/dimensions and report gate were verified; mobile UZ
screenshot visually sampled. Separate candidate contract/table/broker/memory preserve baseline
source reports and findings unchanged. No VPS browser/dependency, schedule, model key or publisher.

VPS job623 saved report82a45d58430d27a9b433238fcd803bfba095162c17f749886daf63989c2c85ca.
Telegram accepted activation363/result364; memory624 binds it. /nova_candidate or 🎨 Черновик NOVA
shows completed Draft work and pending publication; /test_nova_candidate revalidates only the
fixed CI/archive. Plan13 remains active, its Draft component is marked completed from valid
saved evidence. It does not approve or publish NOVA. Broader agent, voice, publishing/rollback,
model and project coverage remain incomplete. Paid calls/holds/spend stay0; setup deferred.

[Independent verify40230295351](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40230295351)
passed20:20 UTC with unchanged exact report/archive/receipt/memory and partial Plan. One UAC
worker and sole dispatcher874510 verified; Inventory67760/source/config metadata unchanged.
NOVA main remains1a23239a; public homepage GET200/35735 bytes matches original git blob
00d76b471b3675ab052bbe30526fb0f2e350ac42. No production approval/candidate, merge or deployment.
Backup/home/maksim/.ultimate-review-data/backups/before-uac4-1792959430844990896.sqlite3.
See [NOVA_UI_CANDIDATE.md](NOVA_UI_CANDIDATE.md). Next: verify the NOVA publication/rollback
path and exact owner approval before any publication. Installed app remainsa03e1cfd; later
checkpoint commits update documentation only.

The following browser-baseline checkpoint is historical evidence from the preceding application:

Latest [browser CI rollout](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40220228872)
passed43 transport tests and439 app tests on the VPS. The default pass skipped15 host-dependent
cases; the subsequent sandbox-enabled439-test pass included all15 real Python/Node cases with
zero skips. Exact-app CI40219927424/40219930241 succeeded, as did browser PR CI40219930277.
Actual scoped GitHub App read-only authentication, exact hosted CI/archive observation and
restored-copy pending/tampered-evidence probes passed. No browser/Python dependency or writable
capsule was installed on the VPS. The PG observer now shares metadata identity validation;
its pinned PG contract and earlier proof remain valid and were rechecked live.

Real [browser push CI40219630608](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/40219630608),
attempt1, used harness8c1292c489f6336c1310d287d970498e43b153e5 and NOVA source
1a23239a0a9c7d79905c91505a8741d8350d7e75. Chromium151.0.7922.34/Playwright1.62.0 ran27 checks
without failures/errors/skips and emitted15 screenshots for three emulated viewport sizes.
Page/API requests were intercepted fixture traffic; no actual lead was submitted. Two known
advisories were preserved: Russian UZ placeholders and language targets below44 CSS px. This
is not full localization/accessibility, pixel baseline, real-device/cross-browser or production
acceptance. The local development probe used preinstalled Chromium154 separately and also passed27.

Archive12608412193 is12842536 bytes, digest
`653af95268ada23e853a8337e8e2d44ed822164616aad96c82bbb358f75453e6`, expires2026-11-24T18:07:10Z.
The archive was downloaded through the GitHub connector; its ZIP digest, all15 PNG manifest
hashes/dimensions and JSON gate were verified locally. Report-file SHA-256 is
`70681038aa2666af078dd2d96f4f42c72e21f3ca2b6f00d8f199f49d1cfe1752`.
Mobile UZ and estate desktop CI screenshots were visually inspected; this is no design approval.
VPS verifies gate/upload/archive metadata and expiry, not PNG decoding or independent visual quality.

Real VPS queue job582 saved its own CI metadata report SHA-256
`f87dcf1f1a41e6aa86958e169987efb222ca9535796106512e982bc23fad248e`.
Telegram accepted activation359 and result360; evidence memory583 binds the report/findings.
Worker747665 and sole poller747994 were verified. Inventory remained PID67760 with unchanged
source/config metadata. Paid calls/holds/spend stayed zero, model-key setup stayed deferred,
and production approval/candidate counts were unchanged. Existing monitoring/resource/PG/local
Node/recipe/PR/approval preflight checks all passed again. No new daemon, schedule or publishing
executor was introduced. The initial YAML syntax failures occurred before any browser job and
were fixed before this verified harness; they are not represented as browser results.

Backup: `/home/maksim/.ultimate-review-data/backups/before-uac4-1792952109878862959.sqlite3`.
`/test_nova_browser` revalidates this fixed CI; `/nova_browser` and 🖼 Браузер NOVA show the
report, archive URL/expiry and unresolved findings. Stage13 shows its completed component but
remains active. See [BROWSER_CI.md](BROWSER_CI.md); review/requirements/harness are under ci/nova-browser.

[Independent verification40220619554](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40220619554)
passed at18:18 UTC, observing the same CI run/attempt/harness/source, archive ID/digest/expiry,
report hash, receipt360, memory583 and UAC process IDs. Inventory/approval/paid-policy state
was unchanged again. Subsequent documentation commits save this checkpoint; installed app
remains3fa30fefac0e8dc878f849283b253c9e52d67318.

The following PostgreSQL checkpoint is historical evidence from the preceding application:

Latest [NOVA PostgreSQL CI rollout](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40197421540)
passed41 transport tests and all428 app tests on the VPS. Its first default pass skipped15
host-dependent sandbox cases; its subsequent sandbox-enabled428-test pass had zero skips,
including all15 real Python/Node sandbox cases. Exact-app CI runs
[40197084941](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/40197084941)
and [40197088130](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/40197088130)
succeeded. The existing GitHub App actually authenticated with repository read-only scopes
and observed the pinned hosted test gate before activation. A restored-copy probe injected
pending CI and changed evidence with a fake API only on the copy; production notices and
project rules were not changed by those fixtures.

Real [hosted PostgreSQL CI40196637203](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/40196637203),
push attempt1, executed all34 original NOVA tests with zero failures/skips. SQL assertions
independently confirmed PostgreSQL16, persisted status/history/event rows and restored fields.
The exact harness commit is0a21efb320d65ae98c6788d5cd9825b124f2f4c4 and NOVA source is
1a23239a0a9c7d79905c91505a8741d8350d7e75. Node24.21.0, the separate14-package dependency
lock and official PG image/action commits are pinned. Original NOVA source/production and
its repository were not modified. The workflow used an ephemeral GitHub-hosted runner and
a disposable PG container with dummy credentials, not a VPS database. PR CI40196640109 and
later same-profile PR CI40197088153 also succeeded, but the VPS contract specifically pins
the first push head/attempt source. No scheduled coding automation was created.

Real VPS queue job484 used only GETs to verify exact workflow/head/repository, hosted runner,
run/attempt/job and required gate, then saved the CI evidence. Report SHA-256:
`0b1a60ea0325643d935fa936257dd8085d595751059e4efad9ee10e17e7818fb`.
Its34/34 counts are attested by that immutable workflow gate, not guessed or represented as
VPS-local SQL execution. Telegram accepted activation355 and result356; memory485 binds the
report. Worker449580 and sole dispatcher450023 were verified. Inventory stayed PID67760
with unchanged source/configuration metadata. Paid calls/holds/spend remain zero, API setup
is still deferred, and production approval/candidate counts did not change. No service,
VPS dependency, sandbox guard or resource schedule was altered by the CI profile.

Backup: `/home/maksim/.ultimate-review-data/backups/before-uac4-1792934735276458178.sqlite3`.
`/test_nova_pg` revalidates the pinned CI; `/nova_pg` and 🐘 PostgreSQL NOVA show stored
historical evidence. `/test_nova` remains the separate24-test read-only local sandbox profile.
Stage5 shows this completed PG component but remains active: browser/production-state and
broader project coverage are still pending. See [NOVA_POSTGRES_CI.md](NOVA_POSTGRES_CI.md).

[Independent verification40197785804](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40197785804)
passed at13:29 UTC, observing the same real CI run/attempt/harness/source and report hash,
receipt356, memory485, worker/poller PIDs and unchanged Inventory/approval/paid-policy state.
The latest documentation-only commit records this checkpoint; the installed application
remains562be5084d70fc71f7e07ddfaac44d176eaaa93b.

The following VPS-resource checkpoint is historical evidence from the preceding application:

Latest [VPS resource rollout](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40171830616)
passed 39 transport tests and all 416 app tests on the VPS. The first default pass skipped
15 host-dependent cases; the subsequent sandbox-enabled pass included all 15 real Python/Node
cases with zero skips. Exact-source CI runs
[40171645188](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/40171645188)
and [40171648112](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/40171648112)
succeeded. Alarm/recovery/debounce and transaction-failure injections ran only on a restored
copy, retaining the original notification rows and project rules unchanged. No production
resource-overload incident was deliberately generated.

Two real resource jobs sampled the VPS 65.60167455673218 seconds apart; the second was job360.
Its aggregate CPU was 0.78%, MemAvailable 6.257 GiB, available data-volume space 61.610 GiB and
available inodes 5952203. These are timestamped historical observations, not present resource
promises. Report SHA-256: `7e0965f51ceb8ff3043aadb9c95df31cf67aa226a4a5466bf9baf58f0a5b5b57`.
Telegram accepted activation352 and report353; source-linked evidence memory361 binds the
sample/report. Worker 68767 and sole dispatcher 69102 were verified; Inventory stayed PID67760 with
unchanged source and configuration metadata. Paid calls/holds/spend remain zero;
owner API-key setup is still deferred. Existing PR40 and release preflight338/receipt347
were rechecked successfully without changing approvals or publishing anything.

Backup: `/home/maksim/.ultimate-review-data/backups/before-uac4-1792912489789521934.sqlite3`.
One 300-second resource schedule uses the existing worker and queue pause; no new daemon,
cron entry or ChatGPT development automation was created. `/vps4` and 🖥 VPS show current
stored observations with staleness warnings; `/vps_check` requests another sample. Manual
bursts cannot advance alarm/recovery, and unknown data cannot establish health. Stage6
shows its completed resource component but remains active. See [VPS_RESOURCES.md](VPS_RESOURCES.md).

[Independent verification](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40172325629)
passed at07:20 UTC. It waited for actual periodic queue job362 created by the existing
scheduler, verified its fixed project/payload and source-bound report, and rechecked the
same UAC source/processes, initial two-sample evidence, Telegram353, memory361 and unchanged
Inventory/approval/paid-policy state. The periodic report SHA-256 is
`6914ad6fda52c7b90e6ca4357934317cfa7d007c25ca794e6aca6c0612712b84`.
This confirms an actual scheduled observation, not only a schedule configuration or unit fixture.
Documentation commits after this checkpoint do not change the installed applicationfe19f8220d7337cdc9f253cfb4d8948f4a06bb62.

The following release-preflight checkpoint is historical evidence from the preceding application:

Latest [release preflight rollout](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40162897144)
passed 37 transport tests and 404 application tests on the VPS. The initial default test pass
skipped 15 host-dependent sandbox cases; the subsequent sandbox-enabled 404-test pass had zero
skips and included all 15 real Python/Node cases. Exact-source CI runs
[40162843264](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/40162843264)
and [40162846314](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/40162846314)
succeeded. A restored-copy probe used the actual artifact 6 with simulated GitHub responses and
an artificial owner decision; none of these simulated approvals or calls touched production.

Real queue job 338 used an installation token restricted to repository read permissions and
re-read existing PR 40, its exact two-file diff, main/head and successful PR CI 40094408053,
attempt 1. Head `60dd3b13a53cdceb45bc2a11b90a59186bc7dad5` and
base `cb1536d55ed00190782470a74803cc67daf47151` remain unchanged. The durable report SHA-256 is
`d7fb2fca5458cf01073ee51907f7a6e54089e457c9442b2c21ad62ba2cdecea0`.
It found no owner approval and always records publish_allowed=false. The referenced base is
only a rollback reference; deployment rollback is not implemented or claimed as verified.
No remote branch/PR write, merge or publication was performed by this check.

Telegram accepted activation 346 and actual report 347; evidence memory 339 binds the report.
Worker 4107922 and sole dispatcher 4108276 were verified, Inventory remained PID 67760 with
unchanged source/configuration metadata. Approval count stayed unchanged, release candidates
remained zero, the API-key deferral stayed set and actual paid calls/holds/spend remained zero.
Backup: `/home/maksim/.ultimate-review-data/backups/before-uac4-1792903502575092908.sqlite3`.
The Plan4.0 stage 9 shows this completed component but remains active. `/release_check REQUEST_ID`
queues a fresh read; `/release_checks` displays historical reports and does not imply continuing
GitHub validity. No new daemon or schedule was created. See [RELEASE_PREFLIGHT.md](RELEASE_PREFLIGHT.md).

[Independent server verification](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40163145833)
passed at04:47 UTC with the same source, worker/dispatcher PIDs, real PR/head/base/CI,
report hash, Telegram receipt347 and memory339. Approval/candidate counts, disabled paid
policies and Inventory were verified again. Subsequent documentation commits save this
checkpoint; the installed application remains0621a2d82dd3cacc6702599ef821e83dc7469043.

The following artifact-PR checkpoint is historical evidence from the preceding application:

Latest [artifact Draft PR rollout](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40094272024)
passed all395 source tests on the VPS, including15 real Python/Node sandbox cases with zero
skips in that pass, plus35 transport tests. Exact-source CI runs
[40094165835](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/40094165835)
and [40094169182](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/40094169182)
passed. The existing GitHub App actually authenticated and returned the expected repository
identity. No key was provisioned, copied or printed. A restored-copy probe read the actual
artifact6, simulated uncertain GitHub creation with a fake network, reconciled without a duplicate,
and tested an artificial owner approval/other-head/project rejection only on that copy. None
of those fake PRs or approval decisions reached production.

Real VPS queue job206 created [Draft PR40](https://github.com/matrix12345695-afk/ultimate-ai-control/pull/40)
using the existing ultimate-ai-control-review[bot] GitHub App. The branch is
`ai-review/artifact-6-f896464ca9cbe465`; head `60dd3b13a53cdceb45bc2a11b90a59186bc7dad5`,
base `cb1536d55ed00190782470a74803cc67daf47151`. Exactly two new files match the original
artifact6 recipe bytes and independent-acceptance source/report/harness. No active application
module, other project or Inventory file was changed. No merge, deployment or publication was
performed. [Exact-head pull-request CI40094408053](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/40094408053)
succeeded, attempt1. Push CI40094405885 also succeeded but is not substituted for PR CI.
This PR was created by the VPS broker, distinct from the development PR39 created in this chat.

Telegram accepted activation344 and PR report345. Evidence-linked memory207 refers to the real
PR/CI result. Worker PID3111779, sole dispatcher PID3112145 and Inventory PID67760 were verified;
Inventory source/configuration metadata matched. Existing rules, test artifacts and API deferral
were retained; actual paid calls/holds/spend stayed zero. A further recipe artifact8 existed at
verification time and was observed without replacement. No new daemon or schedule was created.
Backup: `/home/maksim/.ultimate-review-data/backups/before-uac4-1792845149541339599.sqlite3`.

The own600 artifact-pr-policy.json permits only two control recipes, draft-only. Credentials
remain in a short-lived broker; worker/candidate environments do not receive them. Progress,
finite retry and deterministic branch reconciliation handle interrupted creation. Requests are
limited to three new drafts per UTC day. /artifact_pr ID, /artifact_prs, /artifact_pr_status ID
and GET-only /artifact_pr_refresh ID are installed. /artifact_release ID can explicitly prepare
a pending owner decision bound to exact project/repository/base/head/artifact/report/CI, with
15-minute verification freshness and60-minute decision expiry. Renewal preserves old decisions.
No production candidate or approval was created by installation. A future publisher must do a
new live check immediately before acting; no publisher/merge adapter is enabled here. Stages8/9
remain active, showing their completed components. Main branch protection was not readable with
the chat connector; it is not claimed as verified.

[Independent verification after cleanup](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40115551837)
passed at17:19 UTC, more than four hours after activation, with the same worker/dispatcher PIDs,
unchanged PR40 head/base/diff and exact successful PR CI. Receipt345 and memory207 were retained;
245 evidence entries were observed from ongoing operations. This is evidence of the VPS operations
continuing, not model-driven coding. The live approval/candidate counts stayed unchanged/zero,
respectively; Inventory and disabled paid policies were verified again. Subsequent documentation
commits save this checkpoint and are not another runtime deployment.
See [ARTIFACT_DRAFT_PRS.md](ARTIFACT_DRAFT_PRS.md) for boundaries.

Earlier pinned NOVA test observations follow as historical evidence:

Latest [pinned NOVA test rollout](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40091932006)
passed all382 source tests on the VPS, including the12 original real Python sandbox cases
and3 real Node sandbox cases (six isolated Node executions), with zero skips in that pass,
plus33 transport tests. Exact-source CI runs
[40091672787](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/40091672787)
and [40091675945](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/40091675945)
passed. The restored-copy probe also executed the real24-test subset and adopted the exact
saved report on retry with a runner that would fail if called. Original project rules/inbox
remained unchanged; artificial copy events stayed out of production.

The existing root-owned Node v24.21.0/compiler were reused. An own NAPI TSYNC guard was built
from reviewed first-party C; no npm packages, system upgrade or new supervisor were installed.
Only23 pinned public source files entered a separate private cache. Source manifest:
`ea67901588811ea194d773e3cc0b0c3248da45003f7be5c3f340be4e6103f7e6`.
Node SHA-256 `7fde7b8afa198da66257f42ee2001d874c7355631e6d1579a5fb5ef1f246df4c`;
compiled guard SHA-256 `484e404fb368be43bf4c0dba4f3fa2feaa307df1deb209662f5dbc8c7d9375e9`.
The worker retains384MiB soft address space and has768MiB hard space for the bounded Node
child; Python children remain320MiB. Concurrency stays one. Node uses one CPU,8-second CPU/wall
limits, read-only root/tmp, no network/processes or new threads after guarded initialization.
Startup threads are not described as absent. No fallback executes project code on the host.

Real queue job197 passed24/24 tests from10 original test files, with zero failures, skips,
cancelled or todo. These cover pure functions, mocked readiness/reminders and source/markup
assertions. They are not PostgreSQL integration, full npm test, browser tests or verification
of the deployed site version. No pg dependency, server.js/crm.js module, live database or
external sender was used. The source profile remains pinned to NOVA commit
`1a23239a0a9c7d79905c91505a8741d8350d7e75`. NOVA source, hosting, data and credentials were unchanged.
/test_nova and the NOVA WEB button queue only that fixed scope; /nova_tests shows its persisted
report. Source-linked memory entry197 refers to the real run;197 total observations were
verified at that time. The tester stage stays active and shows this completed component.
No new schedule or development automation was created.

Telegram accepted activation327 and actual test report328. Worker PID3075811, sole dispatcher
PID3076147 and Inventory PID67760 were verified; Inventory source/configuration metadata matched.
Actual paid requests/holds/spend remained zero; paid policies stayed disabled and owner API setup
deferred. Existing artifact reports and project-rule rows were preserved. Backup:
`/home/maksim/.ultimate-review-data/backups/before-uac4-1792843107392652155.sqlite3`.
[Independent verification after runner cleanup](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40092227502)
passed for the exact installed source, same worker/dispatcher PIDs, unchanged job197/report,
24/24 counts, persisted receipt328, source-linked memory197 and both enforced worker resource
limits. Saved report recovery did not rerun Node tests. All earlier UAC checks, deferred API
setup and unchanged Inventory passed again. Subsequent documentation commits save this checkpoint
and are not another runtime deployment. See [NOVA_ISOLATED_TESTS.md](NOVA_ISOLATED_TESTS.md)
for the exact execution boundaries.

Earlier evidence-memory observations follow as historical evidence:

Latest [evidence-memory rollout](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40089769620)
passed all371 source tests on the VPS, including twelve real sandbox integrations with zero
skips in that pass, plus31 transport tests. Exact-source CI runs
[40089518037](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/40089518037)
and [40089521763](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/40089521763)
passed. A disposable restored database copy verified bounded backfill, idempotent cursor replay,
atomic rollback of both cursor and entries, project scope, read-only views and invalidation
when a referenced source changes. Artificial failures/source edits stayed on that copy.

The live operations worker indexed192 committed observations at verification time. All seven
existing artifact identities/reports were linked, including the two independently checked
recipes, plus the pinned NOVA/Kinder source reads. Every indexed source fingerprint verified.
Original business-rule rows matched byte-for-byte, and existing artifact reports were retained.
Viewing history did not alter inbox/settings/project context. /memory_log [project] [page] and
/memory_item ID work; the История проектов button uses the selected project. Historical and
current task state remain distinct. This does not assert current file integrity, semantic
learning, a model call, source execution or publication. Stage12 stays active with its completed
history component shown in Plan4.0. No new schedule was created.

Telegram accepted activation326, with its receipt persisted. Worker PID3041094, sole dispatcher
PID3041473 and Inventory PID67760 were verified; Inventory source/configuration metadata matched.
Paid policies remained disabled, provider setup stayed deferred and actual requests/holds/spend
were zero. Backup:
`/home/maksim/.ultimate-review-data/backups/before-uac4-1792841132577297635.sqlite3`.
[Independent verification after runner cleanup](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40089978418)
passed for the exact installed source, same worker/dispatcher PIDs, persisted receipt326, all192
source-linked entries, seven artifact reports, both repository observations, read-only views
and the partial Plan4.0 component. Existing UAC checks, original project rules, owner API deferral
and unchanged Inventory passed again. Subsequent documentation commits save this checkpoint;
they are not another runtime deployment. See [EVIDENCE_MEMORY.md](EVIDENCE_MEMORY.md) for boundaries.

Earlier recipe-acceptance observations follow as historical evidence:

Latest [recipe-contract rollout](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40087392409)
passed all 361 source tests on the VPS, including twelve actual sandbox integrations with
zero skips in that pass, plus 29 transport tests. Exact-source CI runs
[40086330119](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/40086330119)
and [40086333162](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/40086333162)
passed. Real sandbox mutation cases reject four faulty implementations despite passing
candidate tests. A disposable restored DB copy tested both recipes and crash-after-rename
recovery with the exact profile/harness and no re-execution. Those fixtures were not live jobs.

Real queue jobs184/185 created artifacts6/7. Paths passed three candidate tests and eight
independent requirements; Git SHA passed two candidate tests and eight independent requirements.
Both await owner review and have not been published or adopted. Telegram accepted artifact
messages319/320 and activation321. Their complete reports were reused through transport retries
without re-running production artifact tests or creating duplicates. Existing artifact reports
remained unchanged; old recipes were not retroactively assigned new acceptance evidence.
Manifest digests: paths `f896464ca9cbe4652b528faa1195717bf48552ee580fc2e98a49c70da4b86210`;
Git SHA `ae4d9d1660570f29e99ce261a4d0c216ebac0c14dc7db4db4df86e94bd25c95f`.
Acceptance harness hashes: review-path-v1
`10df4ae82f46f8df0db746b83b4d66c192ea73ce502c597b237242221f96f150`;
git-commit-v1 `04c484d354d6fba86d329795f436dfd0499799ba41cf9d803451cd5600836698`.
The bounded-percent-v1 hash remains unchanged.

Two earlier transport attempts rolled back UAC code while preserving the valid reports:
first, a 55-second activation wait was shorter than the priority outbox drain (INFO actually
arrived after about62 seconds behind two artifact decisions); then the verifier incorrectly
expected three candidate tests for the SHA recipe instead of two. The helper now allows120
seconds while still requiring an actual receipt and validates recipe-specific counts on the
restored copy before activation. The diagnostic run confirmed every delivery succeeded once.
These were installer verification failures, not failed acceptance results or Inventory changes.

Final worker PID3002756, sole dispatcher PID3003115 and Inventory PID67760 were verified.
Inventory source/configuration metadata matched. Paid policies stayed disabled, provider setup
stayed deferred and actual requests/holds/spend stayed zero. No new schedule was created.
The live catalog and Plan4.0 component passed; stage5 remains active for broader task contracts
and other languages. A real scheduled NOVA readiness run186 was also observed, healthy=true,
beyond the earlier initial job176. Backup:
`/home/maksim/.ultimate-review-data/backups/before-uac4-1792838980101758356.sqlite3`.
[Independent verification after runner cleanup](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40087624691)
passed for the exact installed source, same worker/dispatcher PIDs, both unchanged artifacts
and delivery receipts, recovery without repeat execution, the live catalog/Plan4.0 and the
scheduled readiness observation. Original artifact reports, owner deferral and Inventory
remained unchanged. Subsequent documentation-only checkpoint changes are not runtime deployments.

Earlier readiness observations follow as historical evidence:

Latest [NOVA readiness rollout](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40082699315)
passed all 352 source tests on the VPS, including ten actual sandbox integrations with zero
skips in that pass, plus 27 transport tests. Exact-source CI runs
[40082403544](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/40082403544)
and [40082406438](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/40082406438)
passed. Artificial API/page incidents and transaction failure were confined to a restored
database copy. That probe verified independent recoveries, preservation of other decisions,
transaction rollback and scheduler tick deduplication. No synthetic incident reached production.

Real initial queue job176 returned the expected readiness contract: HTTP200, valid JSON,
application ready, storage postgres and the reviewed version. Its body fingerprint matched
the independent local GET:
`b941ccde69a2d9bf809b2c40886e08caa5a521913226ea8a25c8288262d6517c`.
Only booleans/status/size/fingerprint were stored, not the response body. The existing operations
scheduler now has nova-api-readiness-v1 at a 900-second interval, separate from the unchanged
homepage monitor. The initial observation is real; a later periodic run is not claimed from
that initial observation alone. The canceled hourly development automation stays disabled.
Plan4.0 reports the verified readiness component while stage6 remains active. Telegram accepted
activation318; no incident/recovery notice was required for the initial healthy sample.
Worker PID2927915, sole dispatcher PID2928249 and Inventory PID67760 were verified; Inventory
source/configuration metadata remained unchanged. NOVA source, hosting, data and credentials
were not modified. Paid OpenAI policies stayed disabled, provider setup stayed deferred and
actual paid requests/holds/spend stayed zero. Backup:
`/home/maksim/.ultimate-review-data/backups/before-uac4-1792834706897462629.sqlite3`.
[Independent verification after runner cleanup](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40082919503)
passed for the exact installed source, same worker/dispatcher PIDs, initial readiness job176,
all five positive checks, body fingerprint and enabled 15-minute schedule. The homepage schedule,
existing analytics/registry/owner-deferral checks and unchanged Inventory were verified again.
Subsequent documentation-only commits save this checkpoint and are not runtime deployments.

Earlier measured-analytics observations follow as historical evidence:

Latest [measured-analytics rollout](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40080570299)
passed all 340 source tests on the VPS including ten actual sandbox integrations with zero
skips in that pass, plus 24 transport tests. Exact-source CI runs
[40080380120](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/40080380120)
and [40080381992](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/40080381992)
passed. A disposable restored DB copy used clearly artificial work/wait/receipt/hold fixtures
to verify arithmetic and read-only behavior. None of those artificial records entered the
production database or its Telegram reports.

Real daily-report job173 persisted the new summary. Its measured work (441.06966757774353
seconds for the preceding 24-hour window) matched the original stored work intervals. Owner
waiting total604800 seconds is the sum across waiting tasks, not seven days of agent work or
VPS idle time. Idle remained unknown; actual receipt cost and unresolved holds were zero.
Live daily/weekly/cost commands and the partial Plan4.0 component passed. Telegram accepted
activation312 and actual daily report313. No new schedule was added.
Worker PID2894412, sole dispatcher PID2894770 and Inventory PID67760 were verified; Inventory
source/configuration metadata remained unchanged. API setup stayed deferred and actual paid
requests/holds/spend remained zero. Backup:
`/home/maksim/.ultimate-review-data/backups/before-uac4-1792832767862148570.sqlite3`.
[Independent verification after runner cleanup](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40080755713)
passed with the same worker/dispatcher PIDs, exact installed application, daily job173 and
receipt313. Daily/weekly commands, cost views, the journal comparison and the partial-stage
guard passed; registry jobs, owner deferral and unchanged Inventory were verified again.
Subsequent documentation commits save this checkpoint and are not further runtime deployments.

Earlier pinned-registry observations follow as historical evidence:

Latest [pinned-project registry rollout](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40079722673)
passed all 330 source tests on the VPS including ten real sandbox integrations with zero
skips in that pass; 23 transport tests passed. Exact-source CI runs
[40079453773](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/40079453773)
and [40079455801](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/40079455801)
passed. Restored-copy probes confirmed the project view is read-only and protected/unmapped
projects cannot enter the new handler.

Real VPS queue jobs169/170 read four pinned NOVA files and two Kinder documentation files.
Their manifest digests matched the independently observed values in PROJECT_REGISTRY.md;
all file lengths and Git blob IDs matched. Each job has measured work spans and a committed
succeeded result. The project view and Plan4.0 show those verified parts while stage7 stays
active. No remote source, test or package hook was executed; no inspected project was modified
or published. No new schedule was created. Telegram accepted activation307.
Worker PID2879972, sole dispatcher PID2880313 and Inventory PID67760 were verified; Inventory
source/configuration metadata remained unchanged. API setup remained deferred and actual paid
requests/holds/spend stayed zero. Backup:
`/home/maksim/.ultimate-review-data/backups/before-uac4-1792831991021306212.sqlite3`.
[Independent verification after runner cleanup](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/40079913809)
passed with the same worker/dispatcher PIDs, exact installed source, activation307, jobs169/170
and both source digests. Existing owner follow-ups, artifact acceptance and scoped incident
recovery checks also passed. The installed application SHA above is distinct from subsequent
documentation-only checkpoints.

Earlier owner-follow-up observations follow as historical evidence:

Latest [owner-follow-up rollout](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/39916216925)
passed all 318 source tests on the VPS, including ten real sandbox integrations with zero
skips in that pass, plus 20 transport tests. Exact-source CI runs
[39915976109](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/39915976109)
and [39915983107](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/39915983107)
passed. Consistent restored-copy probes proved that pagination reaches every pending actionable
request and that viewing pages/details changes no inbox, job or setting record. Live commands
and the Plan4.0 component were also verified. Six active owner requests were observed; the API
deferral is retained separately. owner_followups_later=true and the owner's instruction are
persisted in settings/audit. No new decision or critical request was created for deferred setup.

Telegram accepted activation234. Worker PID1294476, sole dispatcher PID1294879 and Inventory
PID67760 were verified; Inventory source/configuration metadata remained unchanged. The saved
NOVA sample was HTTP200 with zero open availability incidents and 12 recovered alarms.
Paid policies stayed disabled, provider setup stayed deferred and actual API requests/holds/spend
stayed zero. Backup: `/home/maksim/.ultimate-review-data/backups/before-uac4-1792739562982258956.sqlite3`.
[Independent verification after runner cleanup](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/39916497814)
passed with the same worker/dispatcher PIDs, exact installed source, activation234, six
actionable owner requests, retained API deferral and unchanged Inventory. Both copy-backed
read-only checks and live commands/Plan4.0 passed. All workflow and cleanup steps succeeded.
The application commit above is installed; subsequent documentation commits only save this
checkpoint and the preliminary repository audit.

Earlier monitoring-recovery observations follow as historical evidence:

Latest [monitoring incident rollout](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/39915156776)
passed all 311 source tests on the VPS, with ten real sandbox integrations and zero skips in
the sandbox-enabled pass, plus 19 transport tests. Exact-source CI runs
[39910990095](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/39910990095)
and [39911623524](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/39911623524)
passed. On an independently restored DB copy an artificial outage and an injected transaction
failure verified rollback, recovery and unrelated-decision preservation. No synthetic outage
was written to the production database.

Real queued check62 obtained NOVA HTTP200 and closed 12 proven older availability alarms.
Telegram accepted activation232 and recovery233; their delivery receipts are persisted, not
owner-read confirmations. `/monitor4`, its menu button and Plan4.0 expose the saved results.
Worker PID1283255, sole dispatcher PID1283609 and Inventory PID67760 were verified. Inventory
source fingerprints and configuration metadata were unchanged. Paid policies remained disabled;
provider setup remained deferred and actual API requests/holds/spend stayed zero.
Verified backup: `/home/maksim/.ultimate-review-data/backups/before-uac4-1792738954559458835.sqlite3`.

[Independent verification after runner cleanup](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/39915382746)
also passed for the exact installed release, same worker/dispatcher, check62 and recovery233.
Artifact5 and its independent acceptance evidence remain valid. The first transport attempt
stopped before activation because the helper path was wrong; only the isolated staging path
was corrected before the successful rollout. Documentation commits after the installed source
are checkpoints, not separate runtime deployments.

Earlier artifact-recovery observations follow as historical evidence:

Latest [artifact recovery update](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/39908603525)
passed all 302 tests on the VPS with zero skipped in its sandbox-enabled pass, including ten
real sandbox integrations; 18 transport tests passed. Exact-source CI runs
[39908362274](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/39908362274)
and [39908368423](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/39908368423)
passed. An actual Bubblewrap recipe ran on an independently restored DB copy, an artificial
stop was injected after durable publication before SQLite insertion, and retry2 recovered the
same report without running the sandbox again. A separate failure case validates directory
sync before orphan registration. The production worker/database were not crashed for this test.

The live pipeline retained tested artifact5 (test job55, Telegram receipt215), with four
candidate tests and seven independent acceptance tests. A live read/validation probe reused
that exact private artifact for a later-attempt identity without executing code or inserting
another artifact. The final directory-sync update reused the earlier demo event rather than
creating another generation. The Plan4.0 now displays completed recovery verification.
Activation receipt217 is persisted. Worker PID1215646 and sole dispatcher PID1216004 were
verified; Inventory remained PID67760 with matching source/configuration metadata. Both paid
policies remain disabled, model key untouched, real API requests/holds/spend zero.
Verified backup: `/home/maksim/.ultimate-review-data/backups/before-uac4-1792735089650217999.sqlite3`.

[Independent verification after the final runner exited](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/39908858316)
also passed: exact release, same worker/poller PIDs, retained artifact5/receipt215, activation217,
owner deferral with no pending key requests, zero paid API requests, NOVA HTTP200 and unchanged
Inventory. The application commit above is deployed; the later documentation checkpoint is not
claimed as a separate runtime deployment.

The VPS NOVA monitor's next sample recovered to HTTP200, confirming recovery of its stored
health after the earlier timeout. No NOVA code, service, deployment or configuration changed.

Earlier independent-acceptance and roadmap observations follow as historical evidence:

Latest [independent acceptance deployment](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/39905953902)
passed all 290 source tests on the VPS, including nine real sandbox integrations with zero
skipped in that pass, and 17 transport tests. Source CI runs
[39905738255](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/39905738255)
and [39905919549](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/39905919549)
succeeded. Fresh generation job 51 created test job 52, which ran four candidate tests and a
separate seven-test first-party acceptance suite. Artifact 4 passed both and awaits owner
review. Telegram accepted artifact message 210 and activation message 211. The live plan
shows four passed-test artifacts, one with independent acceptance; legacy artifacts are not
retroactively assigned new verification. This remains a fixed offline demo with no real LLM.

Candidate SHA-256: `d5228c581931a20bd7bc984d74e3c6e15804ad9b1af404bffedfa5bb10d56e0f`.
Acceptance harness SHA-256: `8cffda1476120f659477edd388a8e49cfec71f6f73b584bde5cc38d3a8be96cc`.
Worker PID 1184613, sole dispatcher PID 1185015. Inventory remained PID 67760 with matching
source/configuration metadata; paid policies stayed disabled and actual API requests remained
zero. Backup/restore was checked at
`/home/maksim/.ultimate-review-data/backups/before-uac4-1792733389884837718.sqlite3`.

[Independent verification after runner cleanup](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/39906291903)
passed with the same worker/poller PIDs, exact release, artifact receipt 210, unchanged
Inventory and zero API requests. The current-runtime
[private key check-only run](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/39906291795)
passed four helper tests; secret installation was skipped, key absent and paid policies disabled.

During this rollout the existing NOVA monitor recorded a TimeoutError. Separate bounded GET
requests from the development environment then returned HTTP 200 for both novaweb.uz/ and
/health in about two seconds. This confirms those external probes, not recovery of the VPS
monitor's stored state. Its existing 15-minute check and transition notification remain active;
verify the next VPS sample before resolving its alarm. No NOVA source, service or deployment
was changed.

Earlier roadmap and broker observations follow as historical evidence:

Latest [roadmap update](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/39904617064)
passed all 283 source tests on the VPS including eight real sandbox integrations with zero
skipped in that pass, plus 16 transport tests. Source CI runs
[39904429748](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/39904429748)
and [39904588606](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/39904588606)
passed. Telegram accepted update message 206. The live plan showed completed stages 1/2,
44 succeeded jobs, 5 waiting for owner input, 3 artifacts with passed tests, 37 availability
checks, 49 measured spans and 9 project contexts. These are observed journal counts, not
claims of live model generation or completion of other roadmap stages. Worker PID 1168676,
sole dispatcher PID 1169005; Inventory remained PID 67760 with matching fingerprints and
configuration metadata. Paid policies stayed disabled and actual API requests stayed zero.
Verified backup: `/home/maksim/.ultimate-review-data/backups/before-uac4-1792732511765529650.sqlite3`.

[Independent post-cleanup verification](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/39904885859)
also passed with the same worker/poller PIDs, update receipt 206, the live roadmap assertions
and unchanged Inventory. The refreshed private-key
[check-only preflight](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/39904885830)
passed four helper tests; installation was skipped, key absent and paid policies disabled.

The preceding broker installation evidence remains below as historical proof:

- [Rollout](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/39861820710):
  all 279 source tests passed on the VPS with eight actual Bubblewrap integration tests and
  zero skipped in the sandbox-enabled pass; 13 transport tests passed. Default CI skips the
  eight host-dependent integrations. These tests make no paid calls.
- Source CI: [39861542085](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/39861542085)
  and [39861547850](https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/39861547850)
  succeeded on the preceding broker source commit.
- Generation job 19 succeeded, atomically creating test job 20. That child ran four tests in
  Bubblewrap, saved artifact 3 and entered awaiting_owner. Two actual work intervals were
  recorded. Source SHA-256:
  `d5228c581931a20bd7bc984d74e3c6e15804ad9b1af404bffedfa5bb10d56e0f`.
  Telegram accepted artifact message 181 and activation message 182; these are delivery
  receipts, not evidence the owner read them or approved publication.
- [Independent verification after runner cleanup](https://github.com/matrix12345695-afk/inventory-bot/actions/runs/39903213154)
  succeeded on 2026-10-23: worker PID 722759, sole dispatcher PID 723104, live heartbeat,
  NOVA HTTP 200, retained artifacts, disabled paid policies and zero API requests.
  Inventory PID remained 67760; source fingerprints/configuration metadata matched.
- Verified backup:
  `/home/maksim/.ultimate-review-data/backups/before-uac4-1792706525589637139.sqlite3`.

## Development schedule

The owner requested hourly continuation and a first start after the usage limit replenishes.
A platform automation titled “ULTIMATE · продолжение проекта” was created and subsequently
disabled at the owner's explicit request on 2026-10-23. Disabled state was confirmed by the
platform. Do not re-enable it or create another development schedule. No scheduled execution
was confirmed before cancellation. The platform's ChatGPT/Codex quota/reset time is not exposed
to the project or VPS. A quota reset does not enable paid API calls.

Each owner-authorized development run must inspect this checkpoint, open PRs, CI and current runtime before
choosing a small verifiable unfinished step. Avoid competing deployments and duplicate work;
record changes, evidence, blocker and next step here. Never work around quota using paid APIs.
The canceled platform schedule is separate from the existing VPS queue/monitor supervisor. It does not
give the VPS automatic access to new messages in this conversation. The private return-chat
URL is still unknown; do not invent one or claim the chat is subscribed to Telegram.

## Required progress updates

Completed subtask of stage10: [offline OGG/Opus speech candidate](LOCAL_VOICE.md), native
hash-pinned build, real isolated English fixture recognition and compiled sandbox canary,
queue report/typed memory/Telegram receipt/partial Plan. Full voice control is not complete;
private owner audio capture, RU/UZ quality and explicit transcript/task confirmation remain.

Completed increment: [durable emergency control](EMERGENCY_CONTROL.md), including persistent
stop, separate epoch-specific reset, ordinary-resume refusal, old-capability invalidation,
new-action admission journal, notification-outbox retry and source replay protection. Local,
hosted and VPS gates pass; restored-copy stop/reset and live queue selftest/Plan/memory/
Telegram receipts verified. This does not activate a publisher, model, new schedule or full
autonomous development. Inventory is unchanged.

Completed increment: [independent recipe acceptance](RECIPE_ACCEPTANCE.md), adding reviewed
eight-test contracts to both existing offline recipes in separate sandboxes, harness-bound
recovery and a live catalog. Legacy recipe artifacts retain their original evidence; no
retroactive acceptance pass is assigned. VPS rollout and real artifact delivery passed. This is not arbitrary-task
acceptance or enabled model generation; no paid call, publication or new schedule is included.

Completed increment: [NOVA application readiness](READINESS_MONITOR.md), a separate bounded
GET /health JSON contract, independent API/DB-readiness incidents, explicit command and a
15-minute entry in the existing operations queue. The canceled hourly development automation
stays disabled. Local and initial VPS real readiness probes passed. No NOVA production
or Inventory change is authorized by this increment.

Completed increment: [measured daily/weekly analytics](WORK_ANALYTICS.md), clipping recorded
work spans, reconstructing logged queue/owner waiting, separating receipts from unresolved
holds and showing task-specific costs. Missing work/idle history remains unknown. VPS rollout
and live daily report delivery passed; no new schedule or provider permission is part of this change.

Completed increment: [pinned project registry](PROJECT_REGISTRY.md), restricted public source
reads for NOVA and Kinder, verified identities/commits/file hashes and journal-backed project
status. Local and VPS real GETs matched all six allowlisted files. VPS rollout passed; reading
source must not be reported as executing project tests, developing code or completing stage7.

Owner update 2026-10-23: continue independent authorized work, and retain actions requiring
the owner so they can be handled later. Do not repeatedly interrupt development for deferred
setup. Record a concrete action and its reason; a deferred action is not completed or approved.
Current owner follow-ups:

- API setup: explicitly deferred. Resume only when the owner returns to it; never ask for a
  secret in Telegram or this chat. Paid generation remains disabled in the meantime.
- Return-chat link: optional and still unknown. The owner can later use `/chat_bind` with the
  actual private conversation URL; its absence does not block independent VPS operations.
- Publications: each future release requires its own project/version/digest approval after
  tests and a reviewable result exist. No blanket approval or action is needed now.

These follow-ups do not authorize payments, policy changes, or Inventory modifications.

Completed increment: [owner follow-up view](OWNER_FOLLOWUPS.md), a read-only paginated
list of critical/decision requests with full details and deferred setup context. Server rollout
and live command verification passed. No automatic reminder or new schedule is added. The new
keyboard is returned after `/start`; `/owner_later` and `/owner_item ID` work directly.

Completed increment: [availability incident lifecycle](HEALTH_INCIDENTS.md), atomic with
job completion and the health snapshot. It recognizes scoped legacy alarms, closes only
eligible older alerts after a newer successful check, preserves other owner decisions and
adds /monitor4. Server rollout and independent verification evidence are recorded above.

Completed increment: [durable artifact recovery](ARTIFACT_RECOVERY.md), covering the
rename-to-SQLite gap, later retry attempts, changed/missing evidence, finite-attempt exhaustion
alerts and the owner's API deferral. Local and VPS tests include an actual Bubblewrap report
recovered without re-running tests. Server evidence is recorded above.

Completed increment: [independent demo acceptance](INDEPENDENT_ACCEPTANCE.md), with a
separate reviewed seven-test suite, three real mutation-rejection checks and failure/timeout
gates. All 290 source tests passed locally and on the VPS including nine real sandbox
integration tests. Stage 5 remains active because custom contracts and wider stacks are pending.

The owner explicitly requested on 2026-10-23 that completed work be marked “выполнено” in the
Telegram Plan 4.0 after every task. Keep this checkpoint and the runtime roadmap consistent
after each verified increment. Mark an entire stage done only when its acceptance criteria
are satisfied. Record partial verified work without treating a draft, prepared code, fake
provider test or a delivery receipt as a complete development team, publication or owner approval.

The installed Plan 4.0 change reads committed task outcomes, tested-artifact counts, Telegram
receipts and measured spans from the existing journal whenever the owner opens the plan.
There is no synchronization write that could lose a completion after a crash, no model call,
and no new scheduler. Completed stages display “✅ выполнено”; ongoing stages retain their
state and show their completed parts. Previously sent Telegram messages remain snapshots;
press Plan 4.0 again for current state. Server rollout confirmation is recorded above.

## Roadmap and next work

The full 16-stage handover is retained in roadmap.py/project_memory.json and the live database.
Stages below describe partial capabilities, not a declaration that every acceptance gate passed.

| Stage | State and next acceptance gate |
| --- | --- |
| 1. Owner notifications | Live delivery, durable receipts/retries/inbox; continue connecting real agent events. |
| 2. Scheduler/queue | Live jobs, leases, pause, serialized worker and verified complete-artifact crash recovery; durable emergency latch, separate reset/resume, stale-approval invalidation and action admission journal verified. |
| 3. API / $30 | Transport/holds implemented; key setup explicitly deferred by owner; paid policies disabled. |
| 4. Developer | Typed broker, capsule and two-job flow installed; live model task and broader code changes pending. |
| 5. Tester | Pinned NOVA read-only subset plus hosted PostgreSQL, browser, locked-build and recovery fixtures have source-bound evidence; production-state, other projects and wider stacks remain pending. |
| 6. Monitoring | Separate NOVA page/API readiness plus VPS CPU/MemAvailable/data-volume/inode observations, confirmed alarms/recovery and telemetry checks; full business checks and more targets pending. |
| 7. Multiple projects | NOVA/Kinder pinned read scopes plus credential-free main-ref watchers live, with six-hour checks, durable drift/access transitions and typed metadata evidence. Other mappings and isolated execution/change preparation remain pending. Inventory excluded. |
| 8. Draft PRs | VPS broker created and exact-diff/CI verified a real Draft PR from a tested control recipe; broader project/model patches pending. |
| 9. Publication approval | Exact-version candidates plus GET-only live artifact/diff/base/head/CI and existing approval preflight implemented, with durable reports and Telegram receipts; real owner decision, publisher and tested deployment rollback pending. |
| 10. Voice | Owner-private10-second intake, local recognition, preview and exact project/code confirmation are enabled; native public-English and synthetic state cases are verified. Genuine incoming owner confirmation and RU/UZ quality remain pending. No paid API. |
| 11. Analytics | Daily/rolling weekly and delivered calendar snapshots, measured work, logged task waiting and observed polling waits/reasons with explicit unknown gaps are live. Current-session fences, typed result evidence and cost/hold separation verified; full model-agent activity/external billing reconciliation pending. |
| 12. Memory | Rules, owner follow-ups and append-only source-verified job/artifact/repository history live; semantic retrieval, controlled business-rule editing and model learning pending. |
| 13. Design/browser | Hosted Chromium/viewport/screenshots with source-bound evidence; localization/touch fixes are prepared in Draft15 and retained in later candidates. Cross-browser, real-device, pixel and full accessibility coverage remain pending. No production publication. |
| 14. Open source | Initial research exists; choose only after license/security/dependency/resource review. |
| 15. Autonomous cycle | Operations run on VPS; general development, approvals/recovery and measured end-to-end acceptance pending. |
| 16. NOVA commerce | Requirements retained; no NOVA production changes authorized by this checkpoint. |

Initial [repository audit](PROJECT_REPOSITORY_AUDIT.md) found the NOVA Node.js project and
the four-file Kinder Android scaffold, separately from an older Python Kinder candidate.
The original audit itself granted no access; the current registry permits only its pinned
public source reads. No inspected project was modified, installed or deployed. Unknown
project mappings remain unassigned; Inventory remains denied. Stage 7 is not complete.

Owner-private voice intake and exact transcript/project confirmation are now installed; keep
stage10 active until a genuine owner round-trip and speech quality are checked. The stable
first-sample request is already delivered; do not send duplicate requests or reopen deferred
API setup. Observed polling waits/reasons and /finish4 are now installed; historical and
missing-signal time stays unknown. The NOVA/Kinder branch watcher now detects changed refs without
advancing any source/test pin. Independent engineering still includes the broader project
execution/change preparation and a separately reviewed live publication/rollback adapter. Exact owner approval is still mandatory before any real merge
or deployment of another project. Do not stop or clean independent services. NOVA hosted
PostgreSQL/browser/locked-build/recovery fixture gates and Draft UI fixes are retained;
production backup and platform publication/retained-artifact conditions remain blockers.
Pinned repository-registry observations remain reads; executed subset reports are separate. [Private model setup](PRIVATE_MODEL_SETUP.md) is explicitly deferred by the owner.
After the owner resumes it, a single bounded real generation → exact-bundle tests → owner
notification with an actual financial receipt will be required. Artificial-response tests
must never be represented as actual model access.

## Boundaries and rollback

Never modify/restart Inventory code, configuration, data, tokens or services. Use only isolated
ULTIMATE actions through the pinned transport, never the standard Inventory deploy. Never
raise the $30 ceiling, buy services, disclose secrets or publish another project without its
owner's specific approval. A model answer or a passed artifact does not authorize publication.

Current UAC rollback: `uac4_repo_heads_rollback`, only for installed341d1277, restores40eca95a.
State `.ultimate-review-data/live/uac4-repository-heads-rollout.json`. It gate-fences manual/
scheduled admissions, disables only its two recognized metadata schedules, cancels only queued
matching jobs and restarts only UAC. Immutable metadata/memory, original weekly/voice/observer
history/schedules, owner pauses/emergency state, accounting and policies remain. No live DB
restore or independent service change; no live rollback performed. Older readers need the new
code to display repository-head memory refs.

Preceding UAC rollback: `uac4_worker_observer_rollback`, only for installed40eca95a,
restores calendar/voice-aware app6ad68431. State
`.ultimate-review-data/live/uac4-worker-observation-rollout.json`. It drains/restarts only UAC
and retains passive observations, reports/memory, task history, weekly schedules/snapshots,
private policies, owner pauses/emergency state and accounting. No live DB restore or
independent service action. No live rollback performed. New observation detail requires
newer readers, while existing daily/weekly fields remain compatible.

Preceding UAC rollback: `uac4_weekly_reports_label_rollback`, only for installed6ad68431,
restores calendar/voice-aware app421acd3b while retaining its weekly schedule/report, voice
inputs, history and owner pauses. State `.ultimate-review-data/live/uac4-weekly-report-label-patch.json`.
To remove the calendar feature after that exact transition, `uac4_weekly_reports_rollback`
accepts only421acd3b, disables its recognized weekly schedule, cancels only unsupported queued
calendar jobs and restoresbc9a8b06; state `.ultimate-review-data/live/uac4-weekly-reports-rollout.json`.
Immutable report/history remain; older readers require the newer app for typed weekly refs.
No live rollback/DB restore, independent service action or unrelated schedule change performed.

Preceding UAC rollback: `uac4_owner_voice_rollback`, only for
installedbc9a8b06, restores voice-pilot appb8ed9187. State
`.ultimate-review-data/live/uac4-owner-voice-rollout.json`. It disables voice intake, drains
UAC work, terminates its own in-flight transport and expires unconfirmed private inputs;
confirmed ordinary tasks, receipts/history/assets and owner pause/emergency state remain.
See OWNER_VOICE_ROLLOUT.md. No live DB restore or independent-service action.

Preceding UAC rollback: `uac4_voice_rollback`, only for installedb8ed9187, restores the preceding
emergency-aware appa37642bf; state `.ultimate-review-data/live/uac4-local-voice-rollout.json`.
It drains only UAC and retains private assets/policy/evidence, cancelling only unsupported
queued public-pilot jobs. Older readers need newer code for voice evidence references.
After any owner control change, retain compatible code and never override the pause/latch.

Preceding UAC rollback: `uac4_emergency_rollback`, only for installeda37642bf, restores
`cd8aa26964d27c2cea06360fc92a88b8fa2a3275` only while the control epoch is0 and unlatched.
State: `.ultimate-review-data/live/uac4-emergency-rollout.json`. The downgrade gate holds the
writer lock through UAC dispatcher/worker replacement, refusing any concurrent stop. After
ANY real emergency stop/reset, the old code would ignore epoch bindings: rollback must
refuse before pausing/signalling or changing source; retain compatible code and forward-fix.
It drains only UAC, preserves owner pauses and additive emergency/approval/receipt/memory/
accounting history, cancels only unsupported queued emergency-control-v1 selftests and
never restores an older live DB. No schedule/external-service action or live rollback was
performed. Typed emergency evidence requires the new reader.

Preceding UAC rollback: `uac4_private_copy_rollback`, only for installedcd8aa269, restores
`2ee77bd4830ae242834c9ebc5baee75aca69b1b7`; state
`.ultimate-review-data/live/uac4-nova-private-copy-rollout.json`. It drains only UAC,
restores its own dispatcher/worker and cancels only unsupported queuednova-private-copy-ci-v1
jobs, preserving owner pauses, reports/history/typed refs/notifications/accounting/policies.
No live DB restore, schedule change or independent service action; no live rollback executed.
Older readers require newer code for private-copy memory references.

Preceding UAC rollback (only when that app is current): `uac4_nova_recovery_rollback`, restores
`45ddce6aed88e2dd2fc4f23aa072d20415efcc11`; state
`.ultimate-review-data/live/uac4-nova-recovery-rollout.json`. It drains only UAC, restores
its dispatcher/worker and cancels only unsupported queuednova-recovery-ci-v1 jobs, preserving
owner pauses, recovery reports/archive metadata, owner follow-up, typed references, policy,
receipts and accounting. No live DB restore, schedule or independent service change; no
live rollback executed. Older readers require newer code for recovery memory references.

Preceding UAC rollback (only when that app is current): `uac4_nova_deploy_rollback`, restores
`95b172f38cfefe93e9dd31c2ebcf027f65a50940`; state
`.ultimate-review-data/live/uac4-nova-deploy-protocol-rollout.json`. It drains only UAC,
restores its worker/dispatcher, cancels only unsupported queuednova-deploy-plan-v1 jobs,
retains owner pauses and all reports/typed refs/receipts/policy/accounting. No schedule,
Render or independent service change; no live rollback executed. Older code requires
newer readers for publication-plan references.

Preceding UAC rollback (only when that app is current): `uac4_locked_build_rollback`, restores
`9d0360570284a7c18b39246af4cad1632dc2fb94`; state
`.ultimate-review-data/live/uac4-locked-build-rollout.json`. It drains/pauses only UAC,
restores its own worker/dispatcher and cancels only unsupported queuednova-locked-build-v1
checks, retaining owner pauses, additive reports/archive/policy/receipts/history/typed refs
and accounting. No DB restore, schedule/external-service change or actual Render rollback;
no live rollback executed. Older readers require newer code for locked-build memory refs.

Preceding UAC rehearsal rollback (only when that app is current): `uac4_nova_release_rollback`, restores
`a03e1cfd22b8e807a2afa41ea6a92d6b578c3141`; state
`.ultimate-review-data/live/uac4-nova-release-rollout.json`. It drains/pauses only UAC,
restores its dispatcher/worker and cancels only unsupported queuednova-release-rehearsal-v1
checks. Owner pauses and additive snapshot/policy/report/delivery/history/accounting/typed refs
are retained. No DB restore, schedule/external-service change or actual Render rollback; no
live rollback was executed. Older code needs the newer reader for rehearsal memory references.

Preceding UAC candidate rollback (only when that app is current): `uac4_browser_candidate_rollback`, restores
`3fa30fefac0e8dc878f849283b253c9e52d67318`; state
`.ultimate-review-data/live/uac4-browser-candidate-rollout.json`. It pauses/drains only UAC,
retains owner pauses and all accounting/report/notification/history data, replaces its dispatcher
and cancels only unsupported queued nova-browser-candidate-v1 checks with audit. No external
service, schedule or DB restore; older code may require the newer reader for candidate references.
No live rollback was executed. This does not establish a NOVA deployment rollback.

Preceding UAC browser-baseline rollback (only when that app is current): `uac4_browser_ci_rollback`, old app
`562be5084d70fc71f7e07ddfaac44d176eaaa93b`, state
`.ultimate-review-data/live/uac4-browser-ci-rollout.json`. No schedule, database or external
service is changed; the read-only CI policy/report history is retained. It pauses/drains only UAC, replaces
the dispatcher, cancels only unsupported queued browser CI jobs with audit, restarts its worker
and restores only its own temporary pause. Owner pauses are retained. Remote branches/Draft PRs
and private request/report/approval/memory history are kept without merge, deletion or publication.
Older memory code may require the newer reader for browser CI references. Existing GitHub App
key/activation and other services are not changed by rollback. It validates exact current code
and recorded version transition, restores only UAC code, restarts only its worker/dispatcher and
retains the task journal, incident history, valid resolutions, artifacts and the owner's API deferral. No policy/credential change is part of this update or
rollback. Do not replace live accounting/history with an older backup. Reassess this rollback
gate after any later activation or policy change.
The preceding readiness rollback (only when that release is current) disables only its matching schedule, drains UAC work, replaces its dispatcher
before cancelling unsupported queued readiness checks with audit, and restores only its own
temporary pause if the owner has not replaced it. It retains successful observations and incident
history, and leaves the homepage monitor and independent services alone.
The preceding registry rollback (only when that registry release is current) temporarily drains only the UAC queue, replaces its dispatcher before
cancelling unsupported queued registry reads with an audit event, restarts its worker and
restores its own temporary pause only if the owner has not replaced it. Existing owner pauses
and successful source-read history are preserved. Inventory is never paused or restarted.
