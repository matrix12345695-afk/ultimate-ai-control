# NOVA pinned production build: verified Draft, not publication

NOVA Draft PR16(feature/uac-nova-locked-build), head
a3c3e77e0e74d33241935d25dd3bdfdd306ccd90, stacked on interface Draft PR15/495a7f1a.
Only six build/config files change relative to15:package.json,package-lock.json,
.node-version,.npmrc,render.yaml,.github/workflows/checks.yml. Application/backend/HTML
business code stays byte-identical to15. Main/live source remains1a23239a.
Node24.21.0 and pg8.23.1 are exact; lock v3 pins14 packages with unchanged reviewed
version/registry/integrity/license records. engine-strict rejects a conflicting Node
runtime; production build usesnpm ci --omit=dev --ignore-scripts --no-audit --no-fund.
Original34 tests run serially with matching runtime/pinned actions and PG16 image.
NOVA project CI40269808859 succeeds.

Blueprint retains existing name/type/runtime/plan/region/health path and proposes
buildCommandnpm ci plusautoDeployTrigger off. Actual platform health path is a separate
condition: last observed empty, despite/health already in source. Render's current
Node docs and Blueprint specification/schema were retrieved/read. JSON Schema
validation passes; no Render CLI/platform validation or sync/deploy occurred. A
higher-priorityNODE_VERSION is not inspected or overwritten; engine-strict fails
rather than silently accepting it. All platform application/approval remains pending.

Combined83-check harness7d4081e9bdc86cdc620656b44cadb40067d12331:
push40270398506,attempt1,job121401777489; PR40270404161 also succeeds. Exact30 baseline/
33 candidate file blobs plus complete GitHub comparison restrict the diff. The
candidate installs its committed production lock and installed records are verified,
not an injected replacement lock. Real mismatched lock and runtime installs fail
withEUSAGE/EBADENGINE. Current npm audit0 known advisories(time-bound result, not a
security guarantee). Actual npm version11.19.0 is recorded, Node24.21.0/pg8.23.1 checked.
Then34 original app tests,15 real loopback HTTP/PostgreSQL upgrade/rollback tests and
34 Chromium151/Playwright1.62 tests pass with0 skips. Fifteen screenshots are hashed
and dimension-validated. Four disposable CRM tables, including candidate-era fixture
writes, survive baseline->candidate->baseline without DB restore. Browser form API
is mocked; HTTP/restart backend is real. No actual Render rollback, physical-device/
full-accessibility/production/zero-downtime acceptance or real lead is claimed.

The first harnessb029a202 stopped at anonymous GitHub metadata rate limits before
tests. Corrected parent uses the ephemeral job read-only token only for exact public
compare URL, rejects redirects and removes the token before raw source/test execution.
No token is persisted/printed or passed to clean server/browser/helper environments.
This is not a new account secret or permission grant. Hosted VM only; no browser,
SDK/database/npm dependency on VPS, paid model call, new service or schedule.

Archive12628940071,12842301 bytes,digest
ab2beb587d10fef44c010ac9b4b3402d9e8cdb0a9c75b06065c7c802166d8953,
expires2026-11-25T04:43:30Z. Report-file SHA256
fd2f9385f4248bc6ba1e2becc4657cbe8bb9e74be87e21e0a1a9bdd9af812ec3.
Production lock SHA2569db9b93b90b4fbeabb5fb780eefe6345e5f87a08d9e2b530cd93335f46efafcf.
Downloaded ZIP/report hashes and all15 PNG hashes/dimensions are verified separately.

/nova_build or 📦 Сборка NOVA shows this exact candidate's83-check split, lock facts,
archive and expiry. /test_nova_build queues only GET-only exact CI/attempt/archive
revalidation; it does not build, deploy or refresh Render state. Separate own600
nova-locked-build-policy.json/lease/scope/activation are checked before the existing
read-only App key. Immutable reports and typed memory are source/hash bound.
Previous source reports/contracts stay historical; /nova_release explicitly links
the new build. Plan9 remains active and marks only verified Draft work complete.
No approval is created or consumed; publication stays disabled. Shared CI observer
adds explicit engine/backend/upload contracts, with old profile defaults unchanged.
The mixed gate is83 total including34 browser checks, not83 browser-only tests.

Local465 app tests pass with15 actual Python/Node sandbox cases,0 skips under reviewed
policies. VPS activation/receipt are verified below; independent recheck follows in the checkpoint.
Remaining: fresh service/retained-build/backup/recovery checks, approved actual build/
health/auto-deploy settings, exact-version least-privilege publisher and precise owner
publication approval. Draft lock/Blueprint success does not change deployed dependencies
or platform settings and cannot transfer approval across source revisions/projects.

## Verified VPS activation,2026-10-26 UTC

Installed app95b172f38cfefe93e9dd31c2ebcf027f65a50940 / UAC Draft PR47 stacked on46.
Rollout40271090255 passed52 transport tests and465 app tests. First default pass
skipped15 host-dependent cases; full sandbox-enabled pass included all15 actual
Python/Node cases with0 skips. Exact-app Safe unit CI40270832706/40270836147 and
locked acceptance PR40270836000 succeed. Existing App read-only authentication
verified immutable83-check CI/archive before activation; pending/tamper/memory
invalidation probes ran only on a restored DB copy, retaining owner notes/rules.

VPS job798 saved report00660427e84c91454de0cf23c93d8a8657459f69021c175b4ce5045d1a5b73dc.
Telegram accepted activation374/result375; typed evidence memory799 binds it.
Plan9 stays active, marking only the locked Draft component complete. No production
approval/candidate created/consumed, key/policy budget override or hourly coding
schedule enabled. Existing browser/PG/rehearsal/Node/resources/recipe/PR/approval
preflight proof reverified with unchanged historical contracts and report hashes.
Sole poller1405948 and one credential-free worker verified. InventoryPID67760/source/
config metadata unchanged; paid calls/holds/spend0, provider setup still deferred.
No browser/SDK/pg package/database installed on VPS; no Render or NOVA deployment.

Backup/home/maksim/.ultimate-review-data/backups/before-uac4-1792990335786495219.sqlite3.
Transportdcb6f8ebe22d7c7dcf5d6a3ffae3c48e35d1ddba; state
.ultimate-review-data/live/uac4-locked-build-rollout.json. UAC-only rollback
uac4_locked_build_rollback requires exact95b172f3, drains only UAC, restores9d036057,
cancels only unsupported queuednova-locked-build-v1 checks and preserves owner pauses,
additive report/archive/policy/receipt/history/typed refs/accounting and external
services. Older readers need this newer code for locked-build memory references.
No DB restore or actual live rollback executed; this is not a Render rollback.

At04:51 UTC, control-room Render GETs still showed original live deploy
 dep-dbchlhqvcj2c738paun0/1a23239a, empty HTTP health path, auto-deploycommit and
npm install --omit=dev build. Public homepageGET200/35735 bytes matched original
blob00d76b471b3675ab052bbe30526fb0f2e350ac42. Proposed lock/build/health/off settings
remain un-applied. NOVA_PUBLICATION_PLAN.json now binds candidate16 and lock/83-check
evidence, but remains non-executable and requires fresh platform/retained-build/
backup/recovery/access checks and exact owner authorization before action.

Independent verification40271650507 at04:57 UTC repeated exact run40270398506/attempt1,
harness7d4081e9/sourcea3c3e77e, contract/archive/report hashes, receipt375, memory799,
partial Plan9 and source95b172f3. Poller1405948/one clean worker and Inventory/config
were unchanged; paid policy remained disabled and hourly coding automation disabled.
Fresh control-room Render reads at05:00 UTC still showed empty health path, commit
auto-deploy and old npm install build; NOVA main remained1a23239a. Public homepage
GET200 again matched original35735-byte blob00d76b47. These are separate timestamped
observations, not an automatic VPS Render feed or permission to change settings.
