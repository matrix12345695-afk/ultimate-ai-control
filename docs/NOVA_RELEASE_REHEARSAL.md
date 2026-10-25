# NOVA release readiness and restart rehearsal

2026-10-25: owner confirmed Render workspace My Workspace,tea-d52kjcur433s73ca9810.
Read-only Render connector identifies NOVA servicesrv-dbbhm5k9v7es73f9kf10,
https://novaweb-agency.onrender.com,repositorynova-web-agency,branchmain,free plan,
Node/npm start. Live deploydep-dbchlhqvcj2c738paun0 points to1a23239a. Main commits
trigger auto-deploy; previews are off. Runtime healthCheckPath is empty even though
repositoryrender.yaml specifies/health. Therefore current platform readiness is TCP,
not PostgreSQL-aware HTTP. No platform setting, deploy, restart, domain or DB changed.
Snapshotnova_render_snapshot.json records only safe service/deploy fields and time;
it is an archived connector observation, not a continuously refreshed VPS Render feed.
Public GETs/ and/health returned200; HTML matches original blob00d76b47, health
reportsok/storagepostgres/sales-funnel-v1. No real lead/write was submitted.

Current references read directly from Render docsdeploys.md,health-checks.md,rollbacks.md:
HTTP GET health accepts2xx/3xx within5 seconds; new instances gate for15min. API/CLI
specific-commit deploy and API rollback do not disable auto-deploy; Dashboard specific
commit/rollback do. Retained build eligibility depends on platform retention and cannot
be inferred from a historical deploy ID/status. Rollback uses a retained artifact;
DB/external writes/disks are not reverted. This is reference guidance, not platform
rollback verification. The available Render MCP deploy tool lacks a commit parameter
and exposes no rollback action, so it is not an exact-version publication adapter.
No Render API key or extra rights were requested/read/provisioned on VPS.

Exact hosted harnessce46dc1bbbdbc9c65b2706053b53dcffcb881f10,
pushCI40234072189,attempt1,job121291759845; PRCI40234075915 succeeds too.
Candidate495a7f1a1a3a25c45fd98101fffa9c02e58f3970 / DraftPR15 and baseline1a23239a.
Both28-file snapshots/git blobs and GitHub exact comparison show onlyindex.html
changes. Same reviewed14-package lock (pg8.23.1), Node24.21.0, official pinnedPG16
and fixed dummy local DB. All34 original candidate tests pass with no skips.
Then15 fail-fast checks exercise exact server code through real loopback HTTP and
PG: baseline -> candidate -> baseline, readiness/headers/static routes, unauthenticated
write denial, failed candidate startup with baseline retained, all four CRM tables
preserved across upgrade and rollback including fixture rows added while candidate
runs. No DB restore or migration rollback; no Render routing/zero-downtime claim.
Final fixture counts:leads3/events4/update-dedupe3/reminders2. Workload socket guard
rejects external destinations and unexpected listeners, forces loopback binding;
clean child environments have no actual bot/model/provider/deploy credential.
Hosted runner/source parent has network for public pins/npm. No new dependency,
VPS browser/database, schedule, paid API call or production action.

Archive12612949720,956 bytes,sha256
2e50bef068c70b16ab063608f7bae39e0dd94c1ac102a29d3fe96b125b00ec47,
expires2026-11-24T21:09:04Z. Downloaded ZIP digest and sole report.json digest verified:
7db73ce6ef7dcea143bf7fcebaab3b68ca1e4bd3fe7719d85dc4fd74a3dd0db8.
Proofs attest true local HTTP/data preservation and false actual Render rollback,
production access and publication. This is fixture evidence, not production data.

/nova_release and 🚦 Выпуск NOVA show saved CI evidence, historical Render snapshot
and outstanding requirements. /test_nova_release queues GET-only exact hosted run/
attempt/gate revalidation; it does not deploy/rerun code or refresh Render state.
Own600nova-release-policy.json/activation, exact nova/test_release scope, lease and
snapshot/contract hashes must pass before existing read-only GitHub App authentication.
Reports are immutable per job and typed source-linked memory detects changed evidence.
Plan9 stays active; a successful rehearsal does not approve/consume owner decisions
or enable publication. Live approval/candidate counts must remain unchanged.

Outstanding: review/pin production dependency lock (npm install^pg is not reproducible),
prepare approval-scoped health/auto-deploy policy change, re-read current Render/live/
repo/CI state before any action, verify retained baseline build availability and real
platform rollback compatibility, implement least-privilege exact-version publisher,
and obtain explicit owner approval of the precise publication/configuration scope.
New source/plan changes invalidate older exact-head acceptance until rerun. No
assumption that the available GitHub App has NOVA write/merge or Render permissions.

VPS activation and owner receipt are pending verification in this source commit.
