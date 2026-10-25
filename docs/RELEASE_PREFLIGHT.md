# Release preflight (read-only)

`/release_check REQUEST_ID` queues a finite leased UAC operation; `/release_checks`
shows the last three durable historical reports. No schedule is added.

The short-lived broker requests contents/pull_requests/actions **read** on only
ultimate-ai-control. Its client rejects non-GET repository calls. Token issuance
itself uses the existing GitHub App token endpoint; no new key or grants are installed.
The operation revalidates the exact artifact source, independent test evidence,
PR identity, open/draft state, two-file diff, base/head refs and latest matching
pull-request CI. Source/report material is checked again after network reads and
under the queue lease/write transaction.

A report binds the observed scope and latest existing candidate, if any. It neither
requests nor decides/consumes an approval. Pending, expired, rejected and scope-
mismatched approval records never count as authorized. Even an exact approval
leaves `publish_allowed=false`: publisher and tested deployment rollback are absent.
The base SHA is only a reference, not proof that deployment rollback works.

Reports bind queue job, exact scope, timestamp and SHA-256. Committed reports are
retained on retry; a new job is needed for a new observation. Evidence memory links
the report and detects changed/missing sources. Reading an old report does not
revalidate GitHub or grant future permission. Repository reads are sequential and
cannot eliminate later remote changes. A future publisher needs immediate new checks,
scoped rollback validation and separate review. No merge/deploy adapter exists here.

Unit fixtures simulate GitHub/owner decisions only in temporary databases. VPS
acceptance must use the existing PR and actual GET responses, save the result and
observe the Telegram receipt while proving approval counts, paid policy and
Inventory's process/source/config metadata remain unchanged.

## Verified deployment, 2026-10-25 UTC

App0621a2d82dd3cacc6702599ef821e83dc7469043 / Draft PR41 is installed only in UAC.
Rollout40162897144 passed404 app tests (including15 real sandbox cases, zero skips
in the sandbox-enabled pass),37 transport tests and restored-copy adversarial checks.
Real job338 re-read PR40 with repository read permissions, saved the successful CI
scope and missing-approval result, delivered Telegram347 and linked evidence memory339.
No production candidate/approval was created or changed. Independent verify40163145833
passed with the same application/processes/report/PR and unchanged Inventory.
The Plan4.0 stage9 remains active; publisher and deployment rollback remain pending.

UAC code rollback action: uac4_release_check_rollback, only while this exact app is
current. It restoresfa0403e73541364aabd358c6fa896be60aaaade6 after draining only UAC,
retains all DB history and cancels only unsupported queued release-check jobs. Existing
owner pauses remain. Older memory readers may require the new version to interpret
release-check references. This UAC code rollback is distinct from the still-unimplemented
rollback for future artifact publication; no live rollback was executed as an acceptance test.
