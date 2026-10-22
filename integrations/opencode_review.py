"""Optional OpenCode second-agent adapter, DISABLED by default.

Review-only implementation. Do not wire into the production bot until approved.
OpenCode's plan agent is intended to be read-only, but run it inside an
unprivileged, isolated workspace with no production secrets.
"""
import os
import subprocess
from pathlib import Path

MAX_OUTPUT = 12000
ALLOWED_PROJECTS = {"nova", "inventory", "sap", "kinder", "qualisift"}

class AgentUnavailable(RuntimeError):
    pass

def propose(project: str, task: str, workspace: str, *, timeout: int = 90) -> str:
    """Ask OpenCode for a review-only proposal; never execute a shell command."""
    if os.environ.get("UAC_OPENCODE_ENABLED") != "1":
        raise AgentUnavailable("OpenCode integration is disabled")
    if project not in ALLOWED_PROJECTS:
        raise ValueError("Unknown project")
    if not isinstance(task, str) or not 1 <= len(task.strip()) <= 1000:
        raise ValueError("Invalid task")
    if not isinstance(timeout, int) or not 1 <= timeout <= 120:
        raise ValueError("Invalid timeout")
    base = Path(os.environ.get("UAC_OPENCODE_WORKSPACE_ROOT", "/nonexistent")).resolve(strict=True)
    target = Path(workspace).resolve(strict=True)
    if target != base and base not in target.parents:
        raise ValueError("Workspace must be inside approved root")
    if not target.is_dir():
        raise ValueError("Workspace must be a directory")
    executable = os.environ.get("UAC_OPENCODE_BIN", "/usr/local/bin/opencode")
    if not Path(executable).is_file():
        raise AgentUnavailable("OpenCode executable is not installed")
    # Restrict inherited environment: no bot token, GitHub App key, SSH creds,
    # production DB path or other runtime secrets are intentionally forwarded.
    env = {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "HOME": os.environ.get("UAC_OPENCODE_SANDBOX_HOME", "/nonexistent"),
        "XDG_CONFIG_HOME": os.environ.get("UAC_OPENCODE_SANDBOX_HOME", "/nonexistent"),
    }
    # Provider configuration must be provisioned separately in the sandbox.
    proc = subprocess.run(
        [executable, "run", "--agent", "plan",
         "Provide a read-only implementation proposal; do not change files. "
         + "Project: " + project + ". Task: " + task],
        cwd=str(target), env=env, capture_output=True, text=True,
        timeout=timeout, check=False,
    )
    output = (proc.stdout or "")[:MAX_OUTPUT]
    if proc.returncode:
        raise AgentUnavailable("OpenCode plan failed (exit %s)" % proc.returncode)
    return output or "OpenCode returned an empty proposal"
