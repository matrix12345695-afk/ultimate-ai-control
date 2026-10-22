"""V0.8 local controls: cost reservations and non-executing change proposals."""
import hashlib, json, os, sqlite3, uuid
from datetime import datetime, timezone

def setup(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS ai_usage (
      id TEXT PRIMARY KEY, month TEXT NOT NULL, reserved_cents INTEGER NOT NULL,
      state TEXT NOT NULL, created_at TEXT NOT NULL)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS proposals (
      id TEXT PRIMARY KEY, project TEXT NOT NULL, task TEXT NOT NULL,
      plan TEXT NOT NULL, digest TEXT NOT NULL, state TEXT NOT NULL,
      created_at TEXT NOT NULL)""")
    conn.commit()

def reserve(conn, maximum_cents, request_cents):
    """Local conservative reservation, NOT an API-provider billing limit."""
    if not isinstance(maximum_cents,int) or maximum_cents<0 or not isinstance(request_cents,int) or request_cents<=0:
        raise ValueError("invalid budget")
    month=datetime.now(timezone.utc).strftime("%Y-%m")
    conn.execute("BEGIN IMMEDIATE")
    try:
        spent=conn.execute("SELECT COALESCE(SUM(reserved_cents),0) FROM ai_usage WHERE month=?",(month,)).fetchone()[0]
        if spent+request_cents>maximum_cents:
            conn.rollback()
            return None
        request_id=uuid.uuid4().hex
        conn.execute("INSERT INTO ai_usage VALUES (?,?,?,?,?)",
                     (request_id,month,request_cents,"reserved",datetime.now(timezone.utc).isoformat()))
        conn.commit()
        return request_id
    except Exception:
        conn.rollback()
        raise

def budget_status(conn, maximum_cents):
    month=datetime.now(timezone.utc).strftime("%Y-%m")
    reserved=conn.execute("SELECT COALESCE(SUM(reserved_cents),0) FROM ai_usage WHERE month=?",(month,)).fetchone()[0]
    return f"Local reservation limit: {maximum_cents} cents; reserved: {reserved} cents; remaining: {max(0,maximum_cents-reserved)} cents. Not provider billing data."

def save_proposal(conn, project, task, plan):
    if not project or not task or not plan: raise ValueError("empty proposal")
    digest=hashlib.sha256(plan.encode("utf-8")).hexdigest()
    proposal_id=uuid.uuid4().hex[:12]
    conn.execute("INSERT INTO proposals VALUES (?,?,?,?,?,?,?)",
                 (proposal_id,project,task[:1000],plan[:10000],digest,"draft",datetime.now(timezone.utc).isoformat()))
    conn.commit()
    return proposal_id

def list_proposals(conn):
    rows=conn.execute("SELECT id,project,state,substr(task,1,70) FROM proposals ORDER BY created_at DESC LIMIT 10").fetchall()
    return "\n".join(f"{i} [{state}] {project}: {task}" for i,project,state,task in rows) or "No proposals."

def proposal_detail(conn, id):
    row=conn.execute("SELECT project,task,plan,digest,state FROM proposals WHERE id=?",(id,)).fetchone()
    if not row: return "Proposal not found."
    return f"Project: {row[0]}\nTask: {row[1]}\nState: {row[4]}\nSHA256: {row[3]}\nPlan:\n{row[2]}"[:3800]
