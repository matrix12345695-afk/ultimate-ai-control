"""v1.4 GitHub change execution gate.

Pure validation and staging only. Production worker cannot write to GitHub.
Actual branch/PR creation must happen via an external reviewed controller
with scoped GitHub credentials, in a non-production environment.
"""
import hashlib
import re
from developer_v13 import prepare

SAFE_PATH=re.compile(r"^(?:docs|tests|proposals)/[a-zA-Z0-9_./-]{1,160}$")
BLOCKED=(".env","credentials","secret","token","../")

def stage(project,task,files):
    proposal=prepare(project,task)
    if not isinstance(files,dict) or not files or len(files)>8:
        raise ValueError("Expected 1-8 files")
    manifests=[]
    for path,content in sorted(files.items()):
        if not isinstance(path,str) or not SAFE_PATH.fullmatch(path) or any(x in path.lower() for x in BLOCKED):
            raise ValueError("Path not allowlisted")
        if not isinstance(content,str) or len(content.encode("utf-8"))>24000:
            raise ValueError("Invalid content size")
        if content.startswith("#!") or "\x00" in content:
            raise ValueError("Executable or binary payload blocked")
        manifests.append({"path":path,"sha256":hashlib.sha256(content.encode()).hexdigest(),"bytes":len(content.encode())})
    proposal.update({
        "files":manifests,
        "status":"AWAITING_REVIEW",
        "github_write_performed":False,
        "ci_executed":False,
        "deploy_performed":False,
    })
    return proposal

def release_ready(manifest, approved, ci_status):
    return bool(approved and ci_status=="success" and manifest.get("status")=="AWAITING_REVIEW"
                and not manifest.get("deploy_performed"))
