# Project repository discovery

Read-only connector inventory, 2026-10-22 UTC. Discovery is not deployment permission.

| Project | Discovered repository | Observed evidence | Access posture |
| --- | --- | --- | --- |
| ULTIMATE | matrix12345695-afk/ultimate-ai-control | Live operations runtime, source commits and tests recorded separately | Isolated authorized ULTIMATE development |
| NOVA WEB | matrix12345695-afk/nova-web-agency | Main 1a23239a0a9c7d79905c91505a8741d8350d7e75; Node server, pg, Render blueprint, tests and domain runbook | Read-only inspection now; publication requires owner decision |
| Kinder Spa | matrix12345695-afk/Kinder-Spa-android | Main 0ef936334629accfd59ae33987462c3c693d33f9; README, SECURITY.md, render.yaml, .gitignore only; no Android implementation yet | Specification scaffold, preserve approved business rules |
| Older Kinder code | matrix12345695-afk/kinder_spa | Main 0b38df105ebdf9a41297194f703f6fc881b6fa5b; Telegram handlers and Sheets service | Distinct older codebase; do not assume it is the Android app |
| Inventory | matrix12345695-afk/inventory-bot | Existing protected production project | No application changes, no worker checkout or execution; isolated transport branches only |
| Inventory Mini App | matrix12345695-afk/safia-inventory-web is a name candidate | Similar name alone does not prove the requested app or deployment boundary | Do not enable worker access until identity/boundaries are verified |
| QualiSift | No match in available repository-name search | Actual repository is still unidentified | Ask for its location when integration starts; do not guess another SaaS repository |
| SAP/iiko, iiko Loader Pro, SAP MB51 | No confirmed repository mapping in current discovery | Requirements imported into project memory | Verify source/artifacts before implementation; Windows automation is unavailable on this Ubuntu host |

NOVA's migration runbook describes a Free Render PostgreSQL expiry of 2026-11-19, based on
2026-10-20 documentation. This is a historical runbook statement, not current billing/runtime
verification. No hosting plan, payment, database connection or domain setting was changed.
