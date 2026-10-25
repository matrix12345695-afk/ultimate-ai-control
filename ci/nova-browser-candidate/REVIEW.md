# NOVA frontend candidate acceptance

Exact candidate: nova-web-agency90f60bdaead95b65857dd0a19a905f43cf8658ef,
Draft PR15, based on1a23239a. Only index.html changes. No merge or publication.

Reuse the existing27 isolated Chromium fixture checks and add7 regression cases:
initial UZ placeholders; reversible RU/UZ switching preserving all entered values
and consent; persisted language and explicit URL override; keyboard focus/Enter;
and both44x44 CSS px targets, bounds and mobile CTA separation at3 viewport sizes.
The7 new cases all fail on the unchanged baseline on local Chromium154.0.8037.57.
Candidate hosted CI must pass34 checks,15 screenshot hashes/dimensions and report
contract with zero known placeholder/target advisories on Chromium151.0.7922.34.
A clean advisory list means only these two known issues are absent, not a full
accessibility, visual, localization, physical-device or production certification.

Dependency/hash/license review remains ci/nova-browser/dependency-review.json and
requirements.txt. Hosted workflow uses the same exact actions, reviewed binary
wheels and Playwright browser revision. No extra dependency or VPS browser.
The browser child receives only clean HOME/PATH/LANG/browser path, two hash-pinned
HTML files and a new output directory. All page API/HTTP/WebSocket is intercepted;
no real lead/backend, deployment credential, model or billing API is used.

The source download, byte pins, gate and workflow are separate from the previous
live baseline contract. Its historical report remains unchanged and continues
to describe the original source and two findings. A candidate pass cannot rewrite
that evidence or enable publication. Archives retain30 days; owner approval and
an independently tested deployment/rollback procedure remain pending.
