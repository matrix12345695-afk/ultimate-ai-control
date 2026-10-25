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

VPS activation is verified below; later documentation records independent verification.

## Verified VPS activation,2026-10-25 UTC

Installed app9d0360570284a7c18b39246af4cad1632dc2fb94 / Draft PR46 stacked on45.
Rollout40234805546 passed49 transport tests and456 app tests. First default pass
skipped15 host-dependent cases; full sandbox-enabled pass exercised all15 real
Python/Node cases with zero skips. Exact-app Safe unit CI40234688758/40234692431
and same-profile PR rehearsal40234692424 succeeded. Actual existing GitHub App
read-only authentication verified the pinned CI before activation. Restored-copy
pending/report-tamper and evidence invalidation probes changed only the copy.

Live queue job646 saved report SHA256
 e27459e3ca6de628c5932f4456765868456f20066dadf9d2cdb9ace47127f3b6.
Telegram accepted activation369/result370; typed evidence memory647 binds it.
Plan9 remains active and shows its completed34+15-check rehearsal component.
Commands/menu, own600policy, archived snapshot hash and all outstanding publication
blockers verified. No owner approval or release candidate created. Prior browser,
PG, local Node, resource/health, recipe, memory and PR/preflight evidence also reverified.
Sole dispatcher940092 and one credential-free operations worker verified;
Inventory67760/source/config metadata unchanged; paid calls/holds/spend0 and model
setup still deferred. No new schedule, production dependency, Render credential,
provider permission, platform configuration, NOVA code or live deployment changed.

Backup/home/maksim/.ultimate-review-data/backups/before-uac4-1792963174109785797.sqlite3.
Transportd328806b2d42f1802e3f5b61916519afd8765133. Version-gated UAC rollback
uac4_nova_release_rollback drains only UAC, restoresa03e1cfd, cancels only unsupported
queued nova-release-rehearsal-v1 checks with audit and restores only its own pause.
It keeps owner pauses, archived snapshot/policy/report/history/receipts/typed refs,
accounting and external services. Older readers need the newer code for rehearsal
references. State:.ultimate-review-data/live/uac4-nova-release-rollout.json.
No database restore or live rollback was performed. This is UAC code rollback,
not an executed Render rollback.

A non-executable exact-service publication proposal is saved in
[NOVA_PUBLICATION_PLAN.json](NOVA_PUBLICATION_PLAN.json), including current baseline,
reviewed candidate/HTML blobs, proposed/health and auto-deploy settings, fresh-source
acceptance/backup/access prerequisites, exact approval scope and post-deploy/conditional
rollback criteria. It does not issue API calls or approve any setting/version.
Pinning production dependencies requires a new candidate revision and acceptance;
current495a7f1a proof cannot silently authorize a later source revision.

Independent verify40235182107 at21:22 UTC repeated the same real CI run/attempt,
source/contract/snapshot/report hashes, receipt370, memory647, source9d036057 and
partial Plan9. Dispatcher940092 remained sole, Inventory/source/config stayed
unchanged and paid policy remained disabled. Control-room Render GETs at21:22 UTC
still showed the same live deploydep-dbchlhqvcj2c738paun0/baseline1a23239a, health
path empty and auto-deploycommit; no newer deploy. GitHub main stayed1a23239a and
public homepage GET200 again matched original35735-byte blob00d76b47. This later
observation is separately documented; VPS snapshot remains the explicitly historical
21:08:45 UTC read and is not silently replaced with a supposed live Render feed.
