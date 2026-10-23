"""Post-write Draft PR attestation, used by an isolated trusted runner.

Read-only verification. Missing fields fail closed; no merges or deployments.
"""
import re
from controller_v20 import PR_URL,SHA

def verify_draft_pr(pr,expected_repo,expected_branch,expected_base,expected_head):
    if expected_repo!="matrix12345695-afk/ultimate-ai-control":
        raise PermissionError("Repository not allowed")
    if not isinstance(pr,dict) or not PR_URL.fullmatch(str(pr.get("url",""))):
        raise ValueError("Invalid PR URL")
    if pr.get("draft") is not True or pr.get("merged") is not False:
        raise ValueError("Not a safe draft")
    if pr.get("head")!=expected_branch or pr.get("head_sha")!=expected_head:
        raise ValueError("Head mismatch")
    if pr.get("base")!="main" or pr.get("base_sha")!=expected_base:
        raise ValueError("Base mismatch")
    if not SHA.fullmatch(expected_head) or not SHA.fullmatch(expected_base):
        raise ValueError("Invalid commit")
    if pr.get("head_repo_full_name")!=expected_repo:
        raise ValueError("Wrong head repository")
    return {"url":pr["url"],"head_sha":expected_head,"verified":True}

def reconciliation_required(conn,request_id):
    row=conn.execute("SELECT state,result_ref FROM dispatch_receipts WHERE request_id=?",(request_id,)).fetchone()
    if row is None: return False
    return row[0]=="reserved"
