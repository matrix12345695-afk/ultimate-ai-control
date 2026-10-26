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
policies. VPS activation/receipt are pending verification in this source commit.
Remaining: fresh service/retained-build/backup/recovery checks, approved actual build/
health/auto-deploy settings, exact-version least-privilege publisher and precise owner
publication approval. Draft lock/Blueprint success does not change deployed dependencies
or platform settings and cannot transfer approval across source revisions/projects.
