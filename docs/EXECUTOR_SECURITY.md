# Legacy Level 2 executor security

The limits below apply to the legacy host subprocess. The separate rootless component-test
runner is described in [ISOLATED_PYTHON_V1.md](ISOLATED_PYTHON_V1.md). It does not enable
legacy commands or allow arbitrary project tests on the host. Namespaces share the host kernel
and are not a virtual machine; broad native/browser/dependency execution remains unsupported.
The initial runner only launches a fixed local unittest command. It accepts no command strings, repository URL, or shell fragments from Telegram.

**Warning:** this Python subprocess is NOT sufficient isolation for AI-generated or untrusted project code. Do not run untrusted code on a machine that has credentials, sensitive data or network access.

A production execution service must first provide:
- Ephemeral per-job container or VM with non-root user
- No production secrets or host filesystem mounts
- Network denied by default, CPU/memory/time/process limits
- Immutable repository SHA and allowlisted test command
- Artifact hashes, audit logs, explicit review and approval for production writes
- Result retention limits and cleanup

Until that infrastructure exists, only run the fixed tests from this trusted repository in GitHub Actions. Never expose a generic Telegram command execution feature.
