"""Read-only recovery inspection for incomplete GitHub review dispatches.

Never retries, reuses approvals, changes receipts or writes to GitHub.
"""
from pr_attestation_v25 import verify_draft_pr

REPO="matrix12345695-afk/ultimate-ai-control"

def inspect_reserved(conn,request_id,fetch_branch,fetch_pr):
    row=conn.execute("SELECT state,base_sha,result_ref FROM dispatch_receipts WHERE request_id=?",(request_id,)).fetchone()
    if row is None: return {"status":"not_dispatched"}
    state,base_sha,result_ref=row
    if state!="reserved": return {"status":state,"result_ref":result_ref}
    request=conn.execute("SELECT manifest_json FROM github_change_requests WHERE id=?",(request_id,)).fetchone()
    if request is None: raise ValueError("Unknown request")
    import json
    manifest=json.loads(request[0])
    branch=manifest["proposed_branch"]
    remote=fetch_branch(REPO,branch)
    if remote is None:
        return {"status":"manual_review","reason":"Reserved request with no confirmed branch"}
    head_sha=remote.get("sha") if isinstance(remote,dict) else None
    if not isinstance(head_sha,str) or len(head_sha)!=40:
        return {"status":"manual_review","reason":"Cannot verify branch head"}
    pr=fetch_pr(REPO,branch)
    if pr is None:
        return {"status":"manual_review","reason":"Branch exists; PR not confirmed","head_sha":head_sha}
    try:
        attestation=verify_draft_pr(pr,REPO,branch,base_sha,head_sha)
    except (ValueError,PermissionError):
        return {"status":"manual_review","reason":"PR does not match approved base and branch"}
    return {"status":"verified_needs_operator","pr":attestation["url"],"head_sha":head_sha}
