# NOVA: three-engine frontend acceptance

Status31 October2026: bounded hosted acceptance DONE, Draft UAC PR63.
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

## Verified hosted result

Harness7e882be68a343c50443c70772ee247a31998c362 passes push41190426541
and PR41190428897 on first attempts. All three engines pass34/34, no skips,
errors or failures:102 engine/case executions of34 functional cases. Chromium
jobs124505924876/124505931241; Firefox124505924632/124505931405;
WebKit124505924754/124505931391 (push/PR respectively).

Downloaded push archives: Chromium13038781975, Firefox13037629599,
WebKit13038881380. Published archive digests, exact harness/source revision,
all nine harness-file hashes and45 PNG hashes/dimensions/complete file sets
were independently validated. Full IDs, hashes and scope flags are recorded
in [the receipt](evidence/NOVA_CROSS_BROWSER_20261031.json). Archives expire
30 November2026; this receipt is historical, not perpetual artifact availability.

All ten checks on the exact source commit succeed: new cross-browser, original
Chromium, candidate Chromium, locked build and safe units on both push and PR.
Local offline suite682 tests passes with18 existing host-dependent skips;
the eight new mutation/file-contract cases execute successfully. No sandbox
coverage is inferred from those skips. Original Chromium findings remain
historical; its contract and the candidate contract still pass unchanged.

The three full-page UZ mobile screenshots were also viewed. They show remaining
Russian text in the mobile CTA, FAQ and some supporting copy. These are known
uncovered localization work, not a failed placeholder/target regression or proof
of complete RU/UZ quality. Next: prepare exact draft translations with tests,
preserve user-entered values and submit behavior, and keep publication separate.

This documentation receipt adds no runtime adapter, installation or Telegram
plan update. Stage13 remains active for broader acceptance and live integration.
