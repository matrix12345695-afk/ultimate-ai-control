#!/usr/bin/env bash
# One-time STAGING installer for Ubuntu 22.04. No keys, external traffic,
# service activation, repository merge, or Render deployment.
set -Eeuo pipefail
if [[ "${EUID}" -ne 0 ]]; then echo "Run with sudo/root" >&2; exit 1; fi
command -v git >/dev/null || { echo "git missing" >&2; exit 1; }
command -v python3 >/dev/null || { echo "python3 missing" >&2; exit 1; }
id ultimate-review >/dev/null 2>&1 || useradd --system --home /var/lib/ultimate-review --shell /usr/sbin/nologin ultimate-review
install -d -o ultimate-review -g ultimate-review -m 0700 /var/lib/ultimate-review
install -d -o root -g root -m 0700 /etc/ultimate-review
if [[ -e /opt/ultimate-review ]]; then
  echo "Existing /opt/ultimate-review left unchanged. Inspect manually." >&2
  exit 2
fi
git clone --single-branch --branch feature/v20-ci-audit-control \
  https://github.com/matrix12345695-afk/ultimate-ai-control.git /opt/ultimate-review
cd /opt/ultimate-review
python3 -m venv .venv
.venv/bin/python -m compileall -q .
.venv/bin/python -m unittest discover -s tests -q
chown -R root:root /opt/ultimate-review
chmod -R go-w /opt/ultimate-review
echo "STAGING ONLY: tests complete. No service started. No GitHub App key installed."
