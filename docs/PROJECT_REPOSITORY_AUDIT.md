# Project repository evidence, 2026-10-23 UTC

Read-only discovery through the connected GitHub account returned 24 repositories for
`matrix12345695-afk`. This is an inventory of what that connection exposed at that time,
not proof that every project lives in this account. No inspected project was installed,
modified, deployed or granted runtime access by this audit.

| Project | Repository and ID | Observed main commit | Evidence and next gate |
| --- | --- | --- | --- |
| NOVA WEB | matrix12345695-afk/nova-web-agency, 1426666605 | 1a23239a0a9c7d79905c91505a8741d8350d7e75 | package.json names nova-web-agency; `node server.js`, `node --test tests/*.test.js`, dependency pg. Before worker access, audit the pinned server/tests, deployment coupling and allowed read scope. Repository name alone does not prove the installed production version. |
| Kinder Spa Android | matrix12345695-afk/Kinder-Spa-android, 1427568609 | 0ef936334629accfd59ae33987462c3c693d33f9 | Four files only: .gitignore, README.md, SECURITY.md, render.yaml. README identifies Kinder Spa and admin-issued logins, subscriptions and QR anti-replay requirements. It explicitly calls this a scaffold. No Android client/build files or backend source were present in this snapshot. |
| Earlier Kinder candidate | matrix12345695-afk/kinder_spa, 1193473590 | 0b38df105ebdf9a41297194f703f6fc881b6fa5b | Python repository, requirements.txt present. Relationship to the newer Android scaffold and current hosting remains unverified. Do not merge their code, data or business rules based on similar names. |
| ULTIMATE | matrix12345695-afk/ultimate-ai-control, 1429215344 | See PROJECT_STATUS.md for installed feature source | Own isolated runtime and current development only; main is not the deployed feature branch. |
| Inventory Bot | matrix12345695-afk/inventory-bot, 1159200784 | Not a worker target | Protected production. Existing explicitly authorized transport branches are the sole exception; no source, secret, configuration, database or process access is granted to ULTIMATE workers. |

Other projects in the handover are not assigned a repository by guesswork. In particular,
no repository named QualiSift was returned by this account listing. Other spreadsheet or
inventory repositories may be related to SAP/iiko and Mini App work, but that mapping has not
been established. Retain requirements in project memory and research the evidence before
creating a runtime registry or scheduling inspection. No owner action is required merely
because a mapping remains unknown; independent ULTIMATE tasks can continue.

The next stage-7 increment should separate an inspected repository identity from an execution
permission. Pin the exact repository ID/ref, bound fetch size/time, exclude secret/data files,
and avoid running project build/install hooks on the host. Keep per-project scopes explicit
and Inventory denied. Readable GitHub permissions are not publication authorization. This
document is preliminary audit evidence, not a completed multi-project execution feature.
