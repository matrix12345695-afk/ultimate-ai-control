# NOVA interface fixes: candidate, not publication

Prepared NOVA Draft PR15, exact head495a7f1a1a3a25c45fd98101fffa9c02e58f3970,
base1a23239a0a9c7d79905c91505a8741d8350d7e75. Only index.html changes:
RU/UZ name/contact placeholders restore when switching back without touching values;
language controls at least44x44px plus keyboard outline; mobile header backdrop-filter
is removed below761px so fixed language controls use viewport bounds instead of
appearing partly offscreen. Desktop blur, form/API/business logic remain unchanged.
No main merge, Render deployment, owner approval or real lead was performed.

All7 new browser regression cases fail on the baseline. First candidate90f60bda
passed6 but failed the unchanged mobile bounds test (y=-20); source495a7f1 fixes it
(y=678 at360x800). Local development Chromium154.0.8037.57 passes34/34,0 skips.
Hosted exact harness8bd210e3acefe36b92b2f55ff8d0a8135bd83bd6 push40229505378
and PR40229509407 pass34/34 on Chromium151.0.7922.34 / Playwright1.62.0,15 PNGs,
3 viewport sizes, no known placeholder/target advisories. Real NOVA PR CI40229463007
also succeeds. APIs are fixtures: no real client/server or physical-device/full
localization/accessibility/pixel acceptance is claimed.

Archive12612513627,12840836 bytes,
sha256:2c17578aff9305de3576d7c7839d2bde26f6f00895e83ba6fa7a18c7fd2570fc,
expires2026-11-24T20:11:41Z. CI report file SHA256:
fa5cf16ee1aa1f85a2e19aaab5e54e3c51a6803c32c9b943919d7f3eb039b5a5.

The separate candidate contract/table/broker cannot satisfy or overwrite baseline
browser evidence. /test_nova_candidate rechecks the exact hosted run/attempt/gate
and archive using a repository-read-only App token; /nova_candidate and the new
🎨 Черновик NOVA button show immutable historical evidence and expiry. Credentials
are accessed only after exact nova/test_release payload, live lease and own600
browser-candidate-policy.json/activation checks. No new credential, dependency,
VPS browser, schedule, publisher or increase of budget. Model-key setup is deferred.
Memory binds candidate report/hash/job and detects changed evidence. Plan13 stays
active; completed Draft work appears only from a valid successful saved candidate
report, separate from pending owner decision and production publication. Original
source findings remain historical facts under /nova_browser.

Local447 app tests pass including15 real Python/Node sandbox cases,0 skips with
explicit reviewed local sandbox policies. VPS activation and receipt independently verified below.

## Verified VPS activation,2026-10-25 UTC

Appa03e1cfd22b8e807a2afa41ea6a92d6b578c3141, UAC Draft PR45 stacked on44.
Rollout40229896025 passed46 transport tests and447 app tests: default pass skipped15
host-dependent cases; full sandbox-enabled pass exercised all15 real Python/Node
cases with zero skips. Exact-app Safe unit tests40229722955/40229726534 and candidate
browser checks40229722962/40229726573 also succeeded.

Actual own GitHub App GET-only authentication/CI/archive gate and restored-copy
pending/tampered-report probes passed. Live queue job623 saved candidate report SHA256
82a45d58430d27a9b433238fcd803bfba095162c17f749886daf63989c2c85ca.
Telegram accepted activation363 and result364; typed evidence memory624 binds it.
Independent verify40230295351 at20:20 UTC repeated the exact source/harness/run/attempt,
archive ID/digest/expiry, report/receipt/memory, commands and partial Plan13.
Baseline browser report/findings, original PG/local Node checks, resource/health,
recipe, PR and approval preflight also reverified without changing historical evidence.

Sole dispatcher874510 and one credential-free operations worker verified; Inventory
PID67760/source/configuration metadata unchanged. API calls/holds/spend0, provider
setup still deferred. No approval or release candidate was created. Read-only HTTP
GET of https://novaweb.uz/ returned200,35735 bytes, git blob
00d76b471b3675ab052bbe30526fb0f2e350ac42, matching the original index.html; NOVA main
still1a23239a. Thus these fixes are completed in the Draft, not published.

Backup: /home/maksim/.ultimate-review-data/backups/before-uac4-1792959430844990896.sqlite3.
Pinned transport05a49fa2d3fe051b02eac6d5f039b168ef1d7852; bridge verify request
4ac79a151f271be9cd481506d1e4891120cdfa81. UAC-only rollback action
uac4_browser_candidate_rollback requires this exact installed app, drains only UAC,
restores3fa30fefac0e8dc878f849283b253c9e52d67318 and cancels only unsupported queued
nova-browser-candidate-v1 checks. It preserves owner pauses, additive report/policy/
delivery/history/typed references, budgets and external services. Older code needs
the newer reader for candidate references. No DB restore or live rollback executed.
This rollback is for UAC code, not a tested NOVA deployment rollback. Next: prepare
and independently verify the NOVA publication/rollback path and exact owner approval;
no publication until those requirements are met.
