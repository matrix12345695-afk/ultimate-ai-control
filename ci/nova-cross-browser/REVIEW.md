# NOVA cross-browser frontend acceptance

This is hosted CI, not a VPS runtime feature or a publication adapter.
Owner moved Kinder Spa to a separate chat; this increment concerns NOVA/UAC only.
NOVA Draft PR17/source9df2a1c9fcc35e83f1a2fe35bee2480afac3254f is fixed.
Its index.html/showcase.html sizes and Git blob IDs match the reviewed PR15
candidate exactly. No NOVA source or branch is changed by these checks.

Run the existing34 frontend cases separately on the three browser engines
shipped by the already hashed Playwright1.62.0 dependency:
Chromium151.0.7922.34/revision1234; Firefox153.0/revision1538;
WebKit26.5/revision2336 on Ubuntu24.04. No new package or version is introduced.
Existing wheel/hash/license review remains ci/nova-browser/dependency-review.json.
This is Playwright's patched WebKit, not the shipping Safari application.
Firefox tests360x800/768x1024/1440x900 responsive viewports and touch input;
it has no Playwright mobile emulation, and its report explicitly records false.
No engine stands for a real iPhone, Android handset or complete accessibility audit.

The unchanged cases cover RU/UZ placeholders/persistence, keyboard language
selection/navigation,44px controls, responsive main/showcase layouts, filtering,
required fields, duplicate submission, mocked success/errors/network failures
and disabled intake. Fifteen PNGs per engine are hash/size/dimension checked.
There is no pixel comparison. Known findings must remain empty; this is not a
general accessibility or localization certificate. Tests must not be weakened
to accommodate a genuine browser regression.

Source acquisition allows only two fixed raw GitHub HTML URLs and verifies byte
counts/Git blob hashes. The child gets a clean HOME, PATH/LANG and browser path,
no deployment/App/Telegram/model/database secret. Every page HTTP/API/WebSocket
request is intercepted; fixture POSTs never reach a real customer backend.
No PG/server is launched. The imported PG harness contributes only its bounded
subprocess utility. Network acquisition and child execution have finite deadlines.
Each report binds source manifest, harness Git revision and nine harness files,
engine/version, exact34 passes with zero skips, screenshots and explicit scope flags.
Unexpected/missing/tampered screenshots fail validation. Workflow uploads separate
30-day engine archives, including failure evidence when available. Matrix jobs
do not cancel one another. Contents permission is read-only; checkout does not
persist credentials; dependency installs retain the reviewed hashes/action pins.

The original Chromium baseline and candidate contracts remain separate and keep
their historical source/version/report evidence. The base class defaults to the
same Chromium configuration; engine selection is a class attribute used only by
this new suite. Firefox omits unsupported is_mobile, rather than skipping mobile
viewport tests. This CI does not change runtime policies, queue admission,
source pins, approvals, schedules, budgets, memory rows or Telegram Plan states.
Provider setup stays deferred; Inventory and Kinder are untouched.

Acceptance requires all three exact-engine hosted jobs, their report contracts
and downloaded artifact contents to pass. A local unit/synthetic contract pass
alone cannot establish cross-browser acceptance. A later reviewed runtime adapter
is required before Plan4.0 can display this new evidence; this change does not
pretend the installed VPS already reads a new contract.
