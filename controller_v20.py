"""v2.0 review ledger and CI result verification. No network writes or deployment."""
import re
from datetime import datetime, timezone
from approval import is_authorized
from handoff_v16 import prepare_handoff
from dispatch_v17 import initialize as init_dispatch

SHA=re.compile(r"^[0-9a-f]{40}$")
PR_URL=re.compile(r"^https://github\\.com/matrix12345695-afk/ultimate-ai-control/pull/[1-9][0-9]*$")

def initialize(conn):
    init_dispatch(conn)
    conn.execute("""CREATE TABLE IF NOT EXISTS github_ci_reports(
      request_id INTEGER PRIMARY KEY, head_sha TEXT NOT NULL, pr_url TEXT NOT NULL,
      ci_state TEXT NOT NULL CHECK(ci_state IN ('pending','success','failure')),
      checked_at TEXT NOT NULL)""")

def verify_request(conn, request_id, base_sha):
    package=prepare_handoff(conn,request_id,base_sha)
    row=conn.execute("SELECT approval_id,manifest_json FROM github_change_requests WHERE id=?",(request_id,)).fetchone()
    if not row: raise ValueError("Missing request")
    import json
    if not is_authorized(conn,row[0],request_id,"github_draft_pr","review_only",json.loads(row[1])):
        raise PermissionError("Approval not verified")
    return package

def record_ci(conn, request_id, head_sha, pr_url, results):
    if not SHA.fullmatch(head_sha) or not PR_URL.fullmatch(pr_url):
        raise ValueError("Untrusted PR or SHA")
    receipt=conn.execute("SELECT state,result_ref FROM dispatch_receipts WHERE request_id=?",(request_id,)).fetchone()
    if receipt is None or receipt[0]!="completed" or receipt[1]!=pr_url:
        raise PermissionError("Completed dispatch receipt required")
    if not isinstance(results,list):
        raise ValueError("CI run list required")
    matching=[x for x in results if x.get("head_sha")==head_sha and x.get("name")=="Safe unit tests"]
    if not matching: state="pending"
    elif any(x.get("conclusion")=="failure" for x in matching): state="failure"
    elif any(x.get("status")=="completed" and x.get("conclusion")=="success" for x in matching): state="success"
    else: state="pending"
    conn.execute("""INSERT INTO github_ci_reports VALUES(?,?,?,?,?)
      ON CONFLICT(request_id) DO UPDATE SET
      head_sha=excluded.head_sha,pr_url=excluded.pr_url,ci_state=excluded.ci_state,
      checked_at=excluded.checked_at""",(request_id,head_sha,pr_url,state,datetime.now(timezone.utc).isoformat()))
    conn.commit()
    return state

def telegram_report(request_id,pr_url,head_sha,state):
    if not PR_URL.fullmatch(pr_url) or not SHA.fullmatch(head_sha) or state not in ("pending","success","failure"):
        raise ValueError("Invalid report")
    return ("GitHub review #"+str(request_id)+"\\nDraft PR: "+pr_url+
            "\\nCommit: "+head_sha+"\\nCI: "+state+
            "\\nMerge: disabled. Deploy: owner approval required.")
