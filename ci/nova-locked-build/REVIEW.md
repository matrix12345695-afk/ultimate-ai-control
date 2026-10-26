# NOVA locked build candidate acceptance

Candidatea3c3e77e0e74d33241935d25dd3bdfdd306ccd90, NOVA Draft PR16 stacked on15.
Node24.21.0 and pg8.23.1 are exact; root package-lock v3 pins the same14 package
records/versions/registry integrity/licenses reviewed under ci/nova-postgres/REVIEW.md.
No package source changes. npm ci --omit=dev --ignore-scripts is the proposed Render
build. engine-strict fails a higher-priority conflicting Render NODE_VERSION instead
of silently running an untested runtime. The environment override is not inspected
or changed. Render's current Node-version documentation confirms .node-version support
and precedence; blueprint matches the retrieved public Render JSON Schema.

Exact30 baseline/33 candidate file pins plus GitHub full comparison restrict all
changes from live1a23239a to the interface and six build/config files. Candidate
installs its own committed production lock; baseline uses the earlier isolated test
lock. Installed package integrity/version records must match the committed lock and
previous reviewed dependency tree. npm audit must report0 known advisories at run
(time-bound database result, not a security guarantee). Real invalid lock/runtime
installs must fail with EUSAGE/EBADENGINE; an arbitrary network failure cannot pass.

The required gate runs34 original application tests,15 real loopback HTTP/PG
transition checks and34 Chromium checks,83 total with0 skips. Fifteen PNGs are hashed
and dimension-validated. Existing browser/restart implementations are reused, without
changing their historical contracts; the source-scope check now allows exactly the
reviewed build files as well as index.html. Restart checks retain all four disposable
CRM tables including candidate-era fixture writes, no DB restore. Browser API remains
mocked, while restart HTTP is real. Neither is a physical device or actual Render
rollback/zero-downtime/production acceptance.

Pinned actions, official PG16 digest/resources and reviewed Playwright binary wheel/
Chromium151 revision are reused; no new dependency or production service. Clean
server/browser/helper children have no real service credentials; server socket guard
limits to loopback and unexpected listeners. Parent fetches public source/npm data.
Hosted runner only; no browser, pg package or DB installed on VPS.

Blueprint /health and autoDeployTrigger off are proposals requiring owner approval
and actual platform application/revalidation. No Render sync/config/deploy, main
merge, production data write or publication approval. Prior495a7f1a reports remain
historical and cannot stand in for this exact new commit. Retained artifact/access,
backup/recovery, publisher and actual platform rollback still need verification.

Initial harnessb029a202 failed on anonymous GitHub API rate limits before tests.
Parent metadata request now uses the job read-only ephemeral token only for the exact
public compare URL, rejects redirects, then removes it. Raw source and clean test
children never receive it. No credential is persisted or printed; no new secret.
