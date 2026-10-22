"""One-time handoff to an external, separately authenticated GitHub executor.

No network access, GitHub credentials, code execution, merges or deployment.
"""
import hashlib
import json
import re
from approval import is_authorized
from execution_gate import stage

SHA=re.compile(r"^[0-9a-f]{40}$")

def claim(conn, request_id, files, base_sha):
    if not isinstance(base_sha,str) or not SHA.fullmatch(base_sha):
        raise ValueError("A fixed 40-character base commit SHA is required")
    row=conn.execute("SELECT project,task,manifest_json,approval_id,status FROM github_change_requests WHERE id=?",(request_id,)).fetchone()
    if not row:
        raise ValueError("Unknown request")
    project,task,raw,approval,status=row
    if status!="awaiting_review":
        raise ValueError("Request already claimed or closed")
    saved=json.loads(raw)
    fresh=stage(project,task,files)
    if fresh!=saved:
        raise ValueError("File content differs from approved hashes")
    if not is_authorized(conn,approval,request_id,"github_draft_pr","review_only",saved):
        raise PermissionError("Exact manifest not approved or approval expired")
    # Atomically consume approval before creating a handoff.
    changed=conn.execute("UPDATE github_change_requests SET status='handed_off' WHERE id=? AND status='awaiting_review'",(request_id,)).rowcount
    if changed!=1:
        raise ValueError("Request already consumed")
    conn.commit()
    return {"request_id":request_id,"project":project,"branch":saved["proposed_branch"],
            "base_commit_sha":base_sha,"files":saved["files"],
            "sha256":hashlib.sha256(json.dumps(saved,sort_keys=True).encode()).hexdigest(),
            "status":"HANDOFF_ONLY","github_writes":False,"deploy":False}

def handoff_text(packet):
    return ("🔐 Передача заявки #"+str(packet["request_id"])+" подготовлена\n"
            +"Базовый коммит: "+packet["base_commit_sha"]+"\n"
            +"Ветка: "+packet["branch"]+"\n"
            +"Передача одноразовая. Ветка/PR ещё не созданы.")
