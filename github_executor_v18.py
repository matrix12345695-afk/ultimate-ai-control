"""V1.8 credential-isolated Draft PR executor adapter.

Called only by a separate trusted runner, never by the Render Telegram worker.
The caller supplies a narrow GitHub client and independently verified approved
handoff. This adapter has no merge or deployment operation.
"""
import re
from handoff_v16 import verify_material

REPO=re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
BRANCH=re.compile(r"^ai-review/[a-z0-9-]{1,90}$")

def draft_pr(client,repo,package,files,actual_base_sha,approved=False):
    if approved is not True:
        raise PermissionError("External approval verification required")
    if not REPO.fullmatch(repo) or not BRANCH.fullmatch(package.get("branch","")):
        raise ValueError("Invalid destination")
    if not verify_material(package,files,actual_base_sha):
        raise ValueError("Manifest or base commit mismatch")
    # The client must obtain current default branch SHA from GitHub. No stale writes.
    remote_base=client.get_base_sha(repo)
    if remote_base!=actual_base_sha:
        raise ValueError("Base branch changed")
    branch=package["branch"]
    if client.branch_exists(repo,branch):
        raise ValueError("Branch exists: refuse replay")
    client.create_branch(repo,branch,remote_base)
    # Exact hash-verified files only, never generated or interpreted by this adapter.
    for path,content in sorted(files.items()):
        client.create_file(repo,branch,path,content)
    sha=client.get_branch_sha(repo,branch)
    if not re.fullmatch(r"[0-9a-f]{40}",sha):
        raise ValueError("Unexpected head SHA")
    url=client.create_draft_pr(repo,branch,remote_base,sha,
        "Draft: approved controlled change",
        "Review only. No automatic merge or deployment.")
    return {"url":url,"head_sha":sha,"base_sha":remote_base,"branch":branch,"status":"draft_review"}
