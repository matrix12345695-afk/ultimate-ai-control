# NOVA browser profile review, 2026-10-25 UTC

The profile uses two exact HTML files from NOVA1a23239a. All CSS/JavaScript are inline.
It runs27 real Chromium checks for four pages at360x800,768x1024 and1440x900 CSS
viewports, RU/UZ main-page language persistence, internal navigation/keyboard,
no horizontal overflow in key content, demo filters/selection, required inputs,
single submission, error/retry state and disabled order intake. Fifteen PNGs and a
hash manifest/report are uploaded as a per-attempt artifact with30-day retention.
A successful gate also requires the exact known advisory list rather than hiding it.

Playwright1.62.0 and its three transitive Python packages are binary-wheel/hash pinned.
Versions/licenses/SHA256/bytes and PyPI advisory counts are in dependency-review.json.
Licenses are Apache-2.0, MIT and/or PSF-2.0. The current PyPI responses reported no
known advisories; this is not a full dependency/native/browser vulnerability audit.
The wheel selects Chromium revision1234/version151.0.7922.34 through Microsoft's
Playwright CDN. Chromium is BSD-style/third-party licensed; upstream browser download
relies on official pinned revision and TLS rather than a separately reviewed binary hash.
Checkout/setup-python/upload-artifact are GitHub actions pinned to MIT-licensed commits.

This runs only on a disposable GitHub-hosted VM, not the VPS. Setup may install OS
browser dependencies there. Browser child HOME/environment contains no production,
Telegram, OpenAI or GitHub credential; checkout credentials are not persisted. Source
pages are rendered on a virtual HTTPS origin using route fulfillment. Page HTTP and
WebSocket attempts are intercepted, external page requests fail, service workers are
blocked, and API replies are fixture data. No actual lead is submitted. The browser
process/runner itself has network for setup and is not a network-isolated VPS capsule.

The local development probe used preinstalled Chromium154 and passed27 checks, but
only the hosted bundled151 version is accepted as this CI profile. Screenshots are
rendering evidence, not an approved design, pixel baseline comparison or full WCAG,
real-device, Safari/Firefox, backend/API or live-production acceptance. Reduced motion
and disabled animations/transitions/caret make evidence more stable.

Two observed advisories remain on the pinned source: UZ form placeholders retain
Russian; language buttons have targets below44 CSS px. The tester/design stages remain
active and these findings are preserved for follow-up. No production update is made.
