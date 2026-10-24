# Pinned NOVA tests on the VPS

Profile `nova-readonly-node-v1` executes24 tests from10 original test files at
`matrix12345695-afk/nova-web-agency@1a23239a0a9c7d79905c91505a8741d8350d7e75`.
The23 reviewed inputs are pinned by path, length and Git blob ID in nova_test_pins.json.
Their materialized manifest SHA-256 is
`ea67901588811ea194d773e3cc0b0c3248da45003f7be5c3f340be4e6103f7e6`.
The installer fetches only these public bytes into a separate private source cache.
The operations worker verifies every byte before execution, then mounts a fresh read-only bundle.

Selected tests cover attribution, backup serialization, domain boundaries, mocked readiness,
lead durability source assertions, mobile/SEO markup, operations, reminders with a fake sender,
and showcase source links. Five pure modules execute; server.js, crm.js and bot-ui.js are read
as fixtures and are not required as application modules. There is no npm install, pg dependency,
server start, real database, Telegram credential, HTTP call or publication. Excluded test files
are crm, bot-ui, postgres and restore. Static mobile markup checks are not browser/mobile tests.
This subset does not verify the deployed version or replace the separate live readiness probe.

Node is the existing root-owned `/usr/bin/node` (observed v24.21.0); no runtime/package upgrade
is performed. An own NAPI guard is compiled with the existing compiler, from the reviewed
node_thread_guard.c, into a private versioned ULTIMATE tools directory. The binary, guard and
guard source hashes are pinned in an own600 node-policy.json. An upgrade/hash mismatch fails
closed until reviewed again. The stable NAPI interface does not need downloaded Node headers.

Bubblewrap removes host homes, configuration and data, clears environment and capabilities,
uses a PID/network namespace, read-only root/tmp, one CPU,8 CPU seconds,8 wall seconds,
64 descriptors,32MiB JS heap,768MiB whole-process address space, no file growth and bounded output.
V8 uses jitless/single-threaded options and a one-thread pool. The outer seccomp filter permits
only exact pthread flags during trusted Node initialization (clone3 returns ENOSYS for glibc
fallback). Before any project source loads, the mandatory NAPI guard installs a TSYNC filter
denying clone/clone3/fork/vfork across every startup thread. Network and kernel-control calls
remain blocked by the original outer filter. Startup threads are not described as absent.
There is no host fallback or writable scratch.

The queue worker retains its384MiB soft address-space cap; its hard ceiling is768MiB so the
reviewed Node child can set its own bound. Existing Python children still lower both limits
to320MiB. Global queue concurrency stays one. This adds no process supervisor or schedule.

`/test_nova` (or **🧪 NOVA WEB**) queues the exact fixed scope. `/nova_tests` shows the persisted
report. A pass requires exit0, all24 TAP passes and zero skips, failures, cancelled or todo.
Reports bind source, trusted driver, Node/guard hashes and backend. Same-job retry adopts a
matching committed report without rerunning tests. Each result creates one durable owner notice
and a source-linked project-memory observation. Invalid/missing evidence is not called a pass.
Stage5 remains active for broader contracts, PostgreSQL and browser testing.

Local validation:382 source tests including12 original Python sandbox cases and3 Node sandbox
cases (six real Node executions). These prove fixed-source success, failure of deliberately
broken readiness, blocked host files/writes/network/processes/new threads, wall timeout and
output limit. Unit cases verify scope, exact pins, skipped/malformed TAP, persisted recovery,
tamper detection, memory binding, fixed Telegram requests and resource limits. VPS rollout40091932006 and independent verification40092227502 passed. Real queue job197
passed24/24 with no skips, produced source-linked memory197 and Telegram report328; activation
receipt327 is also persisted. All382 source tests (including the15 real sandbox cases) and
33 transport tests passed on the VPS. Backup/restore, replay without another Node execution,
resource limits, original project rules/artifact reports, disabled paid API and unchanged
Inventory were verified. Paths and source-only rollback: [PROJECT_STATUS.md](PROJECT_STATUS.md).
