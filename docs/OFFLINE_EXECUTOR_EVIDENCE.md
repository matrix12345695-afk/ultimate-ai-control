# Rootless component executor: evidence and limitations

Observed 2026-10-22 UTC. Application candidate:
`b5d9888aa2d15fb1a91ffd5968ddae26992b52ee`, draft PR #25.

## Verified preparation

The existing VPS permits unprivileged user namespaces; its Docker socket is inaccessible.
No Docker groups, permissions, daemons, OS packages or independent services were changed.
Ubuntu bubblewrap 0.6.1-1ubuntu0.3 was extracted into ULTIMATE private tools. Package SHA-256:
`706763714e5d19fc7ab2572a6418506e3a4a5d5960e99309707b58117e6b40cb`.
Executable SHA-256:
`bf6cf3d4456665f5d80c14eb79a76e0ce87b39a0883e614a161658b4ec33492c`.
The package's license/copyright documentation is retained beside the binary.

The first VPS preflight caught unsupported thread creation before activation. The first
candidate was not deployed. The runner now explicitly denies every clone variant and threads;
this is part of its supported single-threaded contract. No global task limit was raised.

All 255 tests passed locally using the exact Ubuntu binary, including seven real sandbox
integration tests. Both deterministic recipes (safe-paths and sha-check) passed actual isolated
unit tests locally. VPS preflight also passed all 255 tests with zero skipped, and 11 transport
checks passed. Backup restoration and commands against the restored SQLite copy passed.
Preflight: https://github.com/matrix12345695-afk/inventory-bot/actions/runs/39854814682
GitHub CI: https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/39854779234

## Boundaries

This increment runs bounded pure Python tests and existing deterministic code recipes. It
is not a general AI developer, full project/browser test environment, or a virtual machine.
No network, credentials, production directories, file writes, threads or subprocess creation
are available inside this version. It shares the host kernel. Test reports and source hashes
are retained independently; a passing draft never triggers a merge or publication.

The $30 ledger remains installed and paid calls remain disabled. General AI coding still
needs a metered provider, private key configuration and reviewed model pricing. ChatGPT Plus
does not supply that API key. The current ChatGPT URL is still unavailable, so there is no
return-link button for this conversation yet; automatic ChatGPT message ingestion is absent.

## Activation

Live deployment verification is recorded below only after a real queued pilot and its
Telegram API receipt have been checked. API acceptance is not proof the owner read a message.

The first activation completed a real sandbox smoke job (six boundary tests) and created
artifact #1 with three passing tests. Telegram accepted its decision notification as message
154. The installer then checked the lower-priority information receipt too early and safely
rolled back ULTIMATE code, retaining database and artifact history. The transport wait was
corrected to require both receipts; retries reuse the original artifact rather than duplicate it.
This also exercised the actual rollback path: Inventory was never signalled or modified.

A later preflight exposed a shared-UID resource problem before activation: RLIMIT_NPROC counts
other services' threads as well. A read-only diagnostic observed 123 owner threads, close to
128. The final runner leaves the inherited UID-wide task limit unchanged and blocks all process
and thread creation inside the sandbox with seccomp. It retains the memory/CPU/time/output
bounds. No global limit or independent service was changed.

## Verified live activation at 21:17 UTC

- Installed application: `b5d9888aa2d15fb1a91ffd5968ddae26992b52ee`.
- Runtime: `/home/maksim/.ultimate-review-runtime`.
- Database: `/home/maksim/.ultimate-review-data/live/control.db`.
- Policy: `/home/maksim/.ultimate-review-data/live/sandbox-policy.json`, mode 0600.
- Supervisors: existing UAC dispatcher cron/flock/restart loop and UAC scheduler loop; no systemd unit.
- Worker PID at verification: 674334; sole Telegram dispatcher PID: 674676.
- Full VPS suite: 255 tests, zero skipped; transport suite: 11 tests. GitHub CI also passed.
- Actual queued sandbox boundary job passed six tests in a fresh namespace.
- Actual queued deterministic safe-paths draft: artifact #2, three isolated tests passed.
- Artifact SHA-256: `4c30840532e8d1f6cd551f0b6123b9c97194a9ac644d3d35b6ff28c28bf06cef`.
- The artifact remains awaiting owner review; source and report files were hash/permission checked.
- Telegram accepted draft notification 157 and activation information 158; both receipts persisted.
- /sandbox, /artifact 2 and /artifact_code 2 1 were exercised against the live database.
- Daily sandbox self-test schedule added; 15-minute NOVA checks and daily source/report schedules remain.
- Existing measured work intervals and job history retained. NOVA remained HTTP 200.
- Inventory PID remained 67760 with matching source fingerprints and configuration metadata.
- API/model calls: zero. Production publications: none.

Deployment: https://github.com/matrix12345695-afk/inventory-bot/actions/runs/39855843817
CI: https://github.com/matrix12345695-afk/ultimate-ai-control/actions/runs/39855835975
Verified backup/restore:
`/home/maksim/.ultimate-review-data/backups/before-uac4-1792703788251235368.sqlite3`.

## Rollback

The reviewed, pinned transport action `uac4_executor_rollback` accepts only this exact release
and its recorded prior release `b6d2d201c995637f89ba67be4208d4c5048cc1f1`. It disables only
the new UAC sandbox self-test schedule, restores prior UAC code/policy and restarts only the
exact UAC worker/dispatcher under their existing supervisors. Database additions, task history,
artifacts and receipts are retained. It never restores a stale backup over new live task data
and never signals Inventory. Restore the tested backup only as a separate reviewed disaster
recovery operation, not as a routine code rollback.

## Next gates

Complete a priced provider transport and usage reconciliation while keeping it disabled until
private owner key configuration exists. Then connect general code generation to this bounded
component executor and expand supported test/dependency environments under separate policies.
Exact-version release approval, authenticated GitHub credential brokerage, speech recognition,
full browser/design automation and project-specific integrations remain incomplete. A finished
operations increment is not reported as completion of all 16 roadmap stages.

Independent verification after Actions cleanup succeeded at 21:19 UTC with the same worker
and dispatcher PIDs, source digest and both Telegram receipts:
https://github.com/matrix12345695-afk/inventory-bot/actions/runs/39856193908.
