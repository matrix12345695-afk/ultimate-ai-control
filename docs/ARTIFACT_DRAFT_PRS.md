# Draft PRs from independently tested recipes

This adapter exports only control-project deterministic safe-paths/sha-check artifacts.
It re-derives the two exact reviewed files from the original job, verifies private on-disk
source/manifest/report against SQLite, and requires passed own tests and a matching passed
independent profile/harness. Other projects, model bundles, changed/partial/uncommitted artifacts,
unknown destinations, overwrites and active application files are denied.

`/artifact_pr ARTIFACT_ID` creates one idempotent queue request per artifact. The short-lived
credential broker reuses the existing owner-provisioned GitHub App and activation marker. It
issues a temporary token restricted to ultimate-ai-control contents/pull_requests write and
actions read. No new credential is provisioned. The queue process and all candidate sandboxes
receive no GitHub token/key. Same Linux-user trusted code is not a separate OS secret boundary;
untrusted code remains in the previously tested no-home sandbox.

The new own600 policy permits only draft-only exports for the two recipes. At most three new
requests per UTC day are prepared. Repository/owner IDs and public non-fork status are checked.
Only new ai-review/artifact-* refs may be created. The exact main base is frozen. Existing
destination paths, moved bases/heads, wrong PR repository, non-draft/closed/merged PR or a diff
other than the exact two added blobs blocks verification. There is no merge, delete, force
update, release or deploy API. Current base-branch protection could not be read with the chat
connector; protection is not claimed from this adapter's own constraints.

Tree and commit objects are content-addressed; author/committer date is frozen before network
writes. Durable progress is bound to the current job lease. A timeout resumes from saved state,
and uncertain PR creation is reconciled using the one deterministic branch, including closed
PRs. A closed/conflicting object is never silently reopened/overwritten. Branch/PR creation
cannot provide absolute exactly-once network delivery; reconciliation prevents automatic
duplicate PR creation in the supported scope. API deadlines and finite queue retries remain.

Only exact-head pull_request runs of .github/workflows/tests.yml / Safe unit tests from the
same repository count. The latest updated run/attempt determines CI, including failures and
cancelled runs. Pending CI retries the same queue request without another PR. No passed CI is
inferred from local artifact tests. `/artifact_pr_refresh REQUEST_ID` performs only GET requests
and revokes verified status until a fresh check succeeds. `/artifact_prs` lists requests and
`/artifact_pr_status REQUEST_ID` shows source, head, PR and CI. Terminal PR results enter the
owner outbox and evidence-linked memory. No new daemon/schedule is created.

`/artifact_release REQUEST_ID` explicitly creates a pending owner approval only after a
successful exact-head check no older than15 minutes. Its immutable scope binds project,
repository, PR, base/head SHA, artifact/report digests and CI run IDs/attempts. Existing
owner-authenticated /approve and /reject record the decision for60 minutes. Candidate+approval
are created in one transaction; repeat requests for the same scope reuse them. An approval
does not execute anything. A future publisher must re-fetch GitHub immediately before acting,
recompute observed scope, check freshness and authorization, and enforce separate deployment,
environment and rollback gates. The publisher itself is not implemented or enabled here.
No live approval is made by a rollout or test. Stage8 and9 remain partial beyond these parts.

Validation:394 local source tests, including15 real Python/Node sandbox cases;12 added tests
cover uncertain creation/replay, source integrity, scope, lease/policy, latest CI, drift,
GET-only refresh, exact approval binding/expiry, atomic rollback and memory provenance.
Actual VPS/App access, PR CI and Telegram delivery are recorded in PROJECT_STATUS.md after
server verification; unit fake responses alone never establish live GitHub access.
