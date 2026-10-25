# ULTIMATE AI CONTROL 4.0 — current checkpoint

Updated 2026-10-25 UTC. This is the resume point for later owner-authorized development. Historical
deployment records retain their original observations; this file identifies the latest state.

## Installed state

Application: `3fa30fefac0e8dc878f849283b253c9e52d67318`, draft
[PR #44](https://github.com/matrix12345695-afk/ultimate-ai-control/pull/44), stacked on PR #43.
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
| 2. Scheduler/queue | Live jobs, leases, pause, serialized worker and verified complete-artifact crash recovery. |
| 3. API / $30 | Transport/holds implemented; key setup explicitly deferred by owner; paid policies disabled. |
| 4. Developer | Typed broker, capsule and two-job flow installed; live model task and broader code changes pending. |
| 5. Tester | Python contracts and24 local guarded read-only NOVA tests plus all34 pinned NOVA tests on disposable hosted PG16 CI with persistence/restore SQL gates; exact CI evidence is verified on VPS. Browser, production-state and broader project coverage pending. |
| 6. Monitoring | Separate NOVA page/API readiness plus VPS CPU/MemAvailable/data-volume/inode observations, confirmed alarms/recovery and telemetry checks; full business checks and more targets pending. |
| 7. Multiple projects | NOVA/Kinder pinned read scopes and real queue observations live; other mappings, isolated execution and change preparation pending. |
| 8. Draft PRs | VPS broker created and exact-diff/CI verified a real Draft PR from a tested control recipe; broader project/model patches pending. |
| 9. Publication approval | Exact-version candidates plus GET-only live artifact/diff/base/head/CI and existing approval preflight implemented, with durable reports and Telegram receipts; real owner decision, publisher and tested deployment rollback pending. |
| 10. Voice | Pending transcription choice, budget accounting and task confirmation. |
| 11. Analytics | Daily/weekly measured work, role/project/worker grouping, logged task waiting and per-task receipts/holds live; full idle observation and external billing reconciliation pending. |
| 12. Memory | Rules, owner follow-ups and append-only source-verified job/artifact/repository history live; semantic retrieval, controlled business-rule editing and model learning pending. |
| 13. Design/browser | Hosted Chromium:27 frontend checks/3 emulated viewport sizes/15 screenshots with source-bound CI/archive verification on VPS. Two localization/touch findings retained; fixes, cross-browser/real-device/pixel/full accessibility pending. |
| 14. Open source | Initial research exists; choose only after license/security/dependency/resource review. |
| 15. Autonomous cycle | Operations run on VPS; general development, approvals/recovery and measured end-to-end acceptance pending. |
| 16. NOVA commerce | Requirements retained; no NOVA production changes authorized by this checkpoint. |

Initial [repository audit](PROJECT_REPOSITORY_AUDIT.md) found the NOVA Node.js project and
the four-file Kinder Android scaffold, separately from an older Python Kinder candidate.
The original audit itself granted no access; the current registry permits only its pinned
public source reads. No inspected project was modified, installed or deployed. Unknown
project mappings remain unassigned; Inventory remains denied. Stage 7 is not complete.

Next priorities: extend the read-only preflight toward a separately reviewed publisher and
tested deployment rollback; no live merge/deployment before exact owner approval. Extend resource observation toward measured capacity planning and extend project coverage
without model access. Do not automatically stop or clean independent services. NOVA now has a separate disposable hosted PostgreSQL/pg gate; the24-test VPS-local profile
still does not cover PG or browser. The separate hosted browser profile is now live; next prepare reviewable fixes for UZ
placeholders and small language controls, then broader accessibility/device/cross-browser coverage.
Pinned repository-registry observations remain reads; executed subset reports are separate. [Private model setup](PRIVATE_MODEL_SETUP.md) is explicitly deferred by the owner.
After the owner resumes it, a single bounded real generation → exact-bundle tests → owner
notification with an actual financial receipt will be required. Artificial-response tests
must never be represented as actual model access.

## Boundaries and rollback

Never modify/restart Inventory code, configuration, data, tokens or services. Use only isolated
ULTIMATE actions through the pinned transport, never the standard Inventory deploy. Never
raise the $30 ceiling, buy services, disclose secrets or publish another project without its
owner's specific approval. A model answer or a passed artifact does not authorize publication.

Current UAC rollback: `uac4_browser_ci_rollback`, old app
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
