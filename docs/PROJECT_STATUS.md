# ULTIMATE AI CONTROL 4.0 — current checkpoint

Updated 2026-10-23 UTC. This is the resume point for later owner-authorized development. Historical
deployment records retain their original observations; this file identifies the latest state.

## Installed state

Application: `c541aaec14f5bb5b03417bd00cce037471ddd0ac`, draft
[PR #32](https://github.com/matrix12345695-afk/ultimate-ai-control/pull/32), stacked on PR #31.
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

Prepared increment: [pinned project registry](PROJECT_REGISTRY.md), restricted public source
reads for NOVA and Kinder, verified identities/commits/file hashes and journal-backed project
status. Local real GETs matched all six allowlisted files. VPS rollout is pending; reading
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
| 5. Tester | Network-free tests and independent seven-test demo contract live; custom contracts and wider stacks pending. |
| 6. Monitoring | NOVA availability, scoped incident recovery and local source inspections live; functional/API checks and more verified targets pending. |
| 7. Multiple projects | Memory imported and initial read-only repository audit recorded; runtime identities/scopes and execution still pending. |
| 8. Draft PRs | Private artifacts and human-created draft PRs exist; autonomous scoped patch-to-PR flow pending. |
| 9. Publication approval | Required by policy; authenticated project/version/digest approval and rollback gates pending. |
| 10. Voice | Pending transcription choice, budget accounting and task confirmation. |
| 11. Analytics | Measured work spans and basic reports exist; full agent/project costs and waiting-time analysis pending. |
| 12. Memory | Project rules/decisions and owner follow-up view persisted; broader evidence-linked lifecycle/retrieval pending. |
| 13. Design/browser | Pending isolated browser execution and visual/mobile acceptance. |
| 14. Open source | Initial research exists; choose only after license/security/dependency/resource review. |
| 15. Autonomous cycle | Operations run on VPS; general development, approvals/recovery and measured end-to-end acceptance pending. |
| 16. NOVA commerce | Requirements retained; no NOVA production changes authorized by this checkpoint. |

Initial [repository audit](PROJECT_REPOSITORY_AUDIT.md) found the NOVA Node.js project and
the four-file Kinder Android scaffold, separately from an older Python Kinder candidate.
No inspected project was modified, installed, deployed or granted worker access. Unknown
project mappings remain unassigned; Inventory remains denied. Stage 7 is not complete.

Next priority: reviewed repository identities/read scopes, custom acceptance contracts,
memory and monitoring without
model access. [Private model setup](PRIVATE_MODEL_SETUP.md) is explicitly deferred by the owner.
After the owner resumes it, a single bounded real generation → exact-bundle tests → owner
notification with an actual financial receipt will be required. Artificial-response tests
must never be represented as actual model access.

## Boundaries and rollback

Never modify/restart Inventory code, configuration, data, tokens or services. Use only isolated
ULTIMATE actions through the pinned transport, never the standard Inventory deploy. Never
raise the $30 ceiling, buy services, disclose secrets or publish another project without its
owner's specific approval. A model answer or a passed artifact does not authorize publication.

Current UAC rollback: `uac4_followups_rollback`, with the recorded old app
`8a955c038c0b710e252f063adbc005059e631acb` and state
`.ultimate-review-data/live/uac4-owner-followups-rollout.json`. It validates exact current code
and recorded version transition, restores only UAC code, restarts only its worker/dispatcher and
retains the task journal, incident history, valid resolutions, artifacts and the owner's API deferral. No policy/credential change is part of this update or
rollback. Do not replace live accounting/history with an older backup. Reassess this rollback
gate after any later activation or policy change.
