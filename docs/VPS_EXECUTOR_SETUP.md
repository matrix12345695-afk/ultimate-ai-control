# ULTIMATE AI CONTROL: isolated VPS preparation

Status: **configuration template only**, NOT a deployed or running executor.
Target host: existing Ubuntu 22.04 VPS. Render production v1.8 unchanged.

Known IDs:
- GitHub App ID: 5424384
- Installation ID: 174076314
- Repository: matrix12345695-afk/ultimate-ai-control

## Operating model
1. Use a separate Linux user `ultimate-review` with no sudo permissions.
2. Use a dedicated directory under `/opt/ultimate-review` and application state under `/var/lib/ultimate-review`.
3. Keep the downloaded PEM key only on the VPS in a root-owned protected path, such as `/etc/ultimate-review/app-key.pem` (mode 0600).
4. Never paste the key into chats, issues, pull requests, git history or test output.
5. An isolated credential broker must issue time-limited GitHub App installation tokens, scoped to the single repository.
6. Set `REVIEW_EXECUTOR_ENABLED=false` until live GitHub permissions, approval transfer and Telegram delivery are independently verified.
7. No merge, deployment or AI API privileges are permitted.
8. Protect `main` via GitHub branch rules; app permissions alone cannot constrain branches or individual file paths.
9. Do not install or start this template unit as the operational executor. It currently runs tests only. A proper authenticated runner and transport must be implemented and audited first.

## Remaining gates
- Confirm actual installation permissions through GitHub using the new App identity.
- Provision isolated token issuance without exposing key material to the Telegram worker.
- Solve secure, authenticated approval handoff from Render SQLite to VPS.
- Verify exact immutable approved files, base SHA, created Draft PR and CI outcome.
- Verify Telegram owner chat ID and live delivery receipt.
- Run fault tests for timeouts and restart recovery.
- Obtain separate owner approval for any Render production release.
