# Rootless Python test executor v1

The host capability probe found no access to Docker. No Docker privileges, groups, services or
production containers were changed. Linux user namespaces are available, so a pinned Ubuntu
Bubblewrap 0.6.1-1ubuntu0.3 package is extracted only into ULTIMATE's private tools directory.
The package hash is checked against the Ubuntu package index and executable bytes are pinned.
No OS package installation scripts run. The package copyright/license files remain beside it.

The runner accepts a bounded dictionary of Python source files with test_*.py tests. It creates
a fresh read-only source tree, uses new user/mount/PID/IPC/network namespaces, drops capabilities,
clears the environment and supplies only the Python runtime/libraries. Production directories,
host home directories, private configuration, databases and sockets are absent.

A seccomp filter denies network calls, fork/vfork, process clone, new namespaces, mounting,
ptrace, cross-process memory access and CPU affinity changes. All clone variants and thread creation are denied. This initial runner is single-threaded and
uses one address space and one CPU.
Limits: 320 MiB address space, 15 CPU seconds, 20 seconds wall time, 64 descriptors, no core dump,
bounded file size and a 256000-byte output budget with a retained 64000-byte tail.
Timeout/output overflow kills only the dedicated sandbox process group. No host fallback exists.

Ubuntu's pinned 0.6.1 utility lacks size-limited tmpfs support. Therefore this backend has a
read-only /tmp and read-only root, not an unlimited writable temporary filesystem. It supports
pure Python component tests and in-memory state; tests requiring file writes, threads or child processes
must fail or remain unsupported. This is not yet a complete application/browser test platform.
Newer verified Bubblewrap builds may use a bounded 32 MiB scratch mount instead.

The offline developer uses two pre-existing deterministic recipes: safe paths and Git SHA
validation. It is not an LLM and does not claim general software development. Source manifests,
hashes, test receipts and code are preserved in immutable per-job-attempt directories, with a
100-directory retention ceiling. Failed tests block success. A passing draft awaits owner review;
the worker never merges or publishes it and does not bypass existing GitHub approval gates.

Telegram: /sandbox, /selftest, /recipe safe-paths, /recipe sha-check, /artifact <id>,
/artifact_code <id> [file_index]. Scheduled boundary self-tests use real execution and measured
testing intervals; missing measurements are never invented. The generic model executor and
priced provider remain disabled pending later implementation/configuration.
