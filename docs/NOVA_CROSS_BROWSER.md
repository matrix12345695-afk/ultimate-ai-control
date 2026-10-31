# NOVA: three-engine frontend acceptance

Status31 October2026: source prepared; hosted acceptance pending.
This continues ULTIMATE/NOVA after Kinder Spa was moved to its separate chat.

The new ci/nova-cross-browser harness fixes NOVA Draft PR17 at
9df2a1c9fcc35e83f1a2fe35bee2480afac3254f. Its two HTML files are byte-identical
to the previously reviewed PR15 frontend fixes; no NOVA branch is changed.
The three separate GitHub-hosted jobs run the same34 existing frontend checks
on Chromium151.0.7922.34, Firefox153.0 and WebKit26.5 from Playwright1.62.0.
That will be102 engine/case executions, not102 unique functional cases.

Each engine must produce34 passes, no skips/errors/failures,15 screenshot
hashes with validated dimensions, and a report bound to the exact source,
GitHub harness revision and nine harness-file hashes. The eight local contract
tests reject wrong engines/versions/source, failures/skips, promoted live/device
claims, incomplete manifests and modified/missing/extra/symlink screenshots.
Local fixture tests do not establish actual browser acceptance.

RU/UZ placeholders and persistence, keyboard navigation,44px targets and
360x800/768x1024/1440x900 layouts are tested, along with showroom filtering,
required fields, duplicate submit, mocked API success/failure and disabled intake.
All page networking is intercepted. There is no real lead, production backend,
database, Telegram/model key or deployment credential in the browser process.

Firefox omits Playwright's unsupported mobile-emulation option and records
mobile_emulation=false; responsive viewport/touch checks still run. WebKit is
the Playwright engine, not Safari/iOS device certification. No physical device,
pixel comparison or comprehensive accessibility/localization audit is claimed.

The baseline and candidate Chromium contracts/reports remain separate. The base
browser suite still defaults to Chromium; optional engine choice is exercised
only by the new harness. No runtime broker/commands/admission/memory integration
is installed. The VPS Telegram plan cannot yet show this new hosted evidence;
this GitHub checkpoint records source progress only. Stage13 stays active.

Review: [scope, dependencies and acceptance gates](../ci/nova-cross-browser/REVIEW.md).
Workflow: .github/workflows/nova-cross-browser.yml, contents-read only, no persisted
checkout credential, existing hash-pinned packages/actions, separate30-day archives.
No new cost approval, model setup, scheduler, Render publication, VPS installation,
Inventory access or Kinder work is introduced.
