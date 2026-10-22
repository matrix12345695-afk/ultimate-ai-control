"""Immutable, fail-closed handoff for an OUT-OF-PROCESS GitHub executor.

This module has no GitHub credentials, network writes, or deployment capability.
It will only issue an approved, hash-bound description of an operation.
"""
import hashlib
import json
import re
from approval import is_authorized, canonical_digest

HEX40=re.compile(r"^[0-9a-f]{40}$")
HEX64=re.compile(r"^[0-9a-f]{64}$")

def prepare_handoff(conn, request_id, base_sha):
    if not isinstance(base_sha,str) or not HEX40.fullmatch(base_sha):
        raise ValueError("A full 40-character base commit SHA is required")
    row=conn.execute("SELECT project,manifest_json,approval_id,status FROM github_change_requests WHERE id=?",(request_id,)).fetchone()
    if row is None:
        raise ValueError("Request not found")
    project,encoded,approval_id,state=row
    if state!="awaiting_review":
        raise ValueError("Request already processed")
    manifest=json.loads(encoded)
    if not is_authorized(conn,approval_id,request_id,"github_draft_pr","review_only",manifest):
        raise PermissionError("Missing, invalid or expired content-bound approval")
    paths=manifest.get("files",[])
    if not paths or not all(HEX64.fullmatch(f.get("sha256","")) for f in paths):
        raise ValueError("Invalid manifest")
    package={
        "schema":"github-review-handoff-v1",
        "request_id":request_id,
        "project":project,
        "branch":manifest["proposed_branch"],
        "base_sha":base_sha,
        "files":[{"path":x["path"],"sha256":x["sha256"],"bytes":x["bytes"]} for x in paths],
        "manifest_digest":canonical_digest(manifest),
        "approval_id":approval_id,
        "mode":"DRAFT_PR_ONLY",
        "merge_allowed":False,
        "deploy_allowed":False,
        "execution_performed":False,
    }
    package["handoff_sha256"]=canonical_digest(package)
    return package

def verify_material(package, files, actual_base_sha):
    if actual_base_sha!=package.get("base_sha"):
        return False
    if package.get("mode")!="DRAFT_PR_ONLY" or package.get("merge_allowed") is not False or package.get("deploy_allowed") is not False:
        return False
    if not isinstance(files,dict):
        return False
    expected=package.get("files",[])
    if set(files)!={item["path"] for item in expected}:
        return False
    for item in expected:
        value=files[item["path"]]
        if not isinstance(value,str) or len(value.encode())!=item["bytes"]:
            return False
        if hashlib.sha256(value.encode()).hexdigest()!=item["sha256"]:
            return False
    return True
