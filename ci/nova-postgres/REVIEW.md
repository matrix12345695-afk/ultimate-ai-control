# Disposable NOVA PostgreSQL CI review, 2026-10-25 UTC

NOVA revision1a23239a0a9c7d79905c91505a8741d8350d7e75 has14 test files/34 tests.
The exact28 public files are hashed; no production config, token or database is used.
Tests run serially in separate Node child processes, preserving environment/module
isolation and ensuring the PostgreSQL persistence test precedes restoration checks.
The original tests are not rewritten. The gate rejects skips/incomplete summaries
and independently checks actual PG16 status history and restored operational fields.

The original package requires pg^8.13.3. A separate CI lock resolves pg8.23.1 and
14 registry packages including its dependencies. All have MIT/ISC licenses, SHA512
integrity and no install hooks. npm audit reported zero known advisories at review;
this is not a guarantee of absence of vulnerabilities or a full dependency source audit.
`npm ci --ignore-scripts` runs only on the disposable runner; nothing is installed on VPS.

Official postgres16 Linux/amd64 image is pinned to registry digest
f9d1e581cde3e4c8bc696b07e6f7b7aea1d41014b33a52b27990762daae61beb.
This came from the official tag16 manifest list9e2cf6287f25c3151f4c9421ccce2b17f3e60061c111a29165e0d2cdd9ff0a97.
Docker verifies content addressing. PostgreSQL has the PostgreSQL open-source license;
base-image dependency vulnerability scanning remains outside this limited review.
The container has512MiB/1CPU/64PID limits and192MiB disposable data tmpfs.
It receives only fixed dummy test credentials; the job has repository read permission.

Checkout/setup-node are GitHub's MIT-licensed actions pinned to reviewed commit refs.
Checkout credentials are not persisted. Child tests get a clean HOME/environment,
fixed local test DB URL and no GitHub/Telegram/OpenAI key. The hosted runner itself
has network and writable temporary space; this is a separate profile from the VPS
read-only/no-network sandbox. CI is triggered by relevant code pushes/PRs, not a
scheduled coding automation. No live NOVA or Inventory update is performed.
