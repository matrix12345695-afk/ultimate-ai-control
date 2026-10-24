"""Approval primitives for future execution adapters. No actions are executed here."""
import hashlib
import json
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

def canonical_digest(payload: dict) -> str:
    serialized=json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",",":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

def init_approvals(conn: sqlite3.Connection):
    conn.execute("""CREATE TABLE IF NOT EXISTS approvals (
        id TEXT PRIMARY KEY, task_id INTEGER NOT NULL, action TEXT NOT NULL,
        environment TEXT NOT NULL, artifact_sha256 TEXT NOT NULL,
        status TEXT NOT NULL, expires_at TEXT NOT NULL,
        requested_at TEXT NOT NULL, decided_by TEXT, decided_at TEXT
    )""")
    conn.commit()

def request_approval(conn, task_id:int, action:str, environment:str, payload:dict, ttl_minutes=30, *, commit=True):
    if type(commit) is not bool or (not commit and not conn.in_transaction):
        raise ValueError('approval transaction required')
    if not action or not environment or ttl_minutes<=0:
        raise ValueError("invalid approval request")
    now=datetime.now(timezone.utc)
    req_id=secrets.token_urlsafe(18)
    conn.execute("INSERT INTO approvals VALUES (?,?,?,?,?,?,?,?,?,?)",
                 (req_id,task_id,action,environment,canonical_digest(payload),
                  "pending",(now+timedelta(minutes=ttl_minutes)).isoformat(),
                  now.isoformat(),None,None))
    if commit: conn.commit()
    return req_id

def decide(conn, request_id:str, approver_id:str, allowed_admin_id:str, approve:bool):
    if not allowed_admin_id or approver_id != allowed_admin_id:
        raise PermissionError("not an administrator")
    row=conn.execute("SELECT status,expires_at FROM approvals WHERE id=?",(request_id,)).fetchone()
    if not row or row[0]!="pending":
        raise ValueError("approval missing or already decided")
    if datetime.now(timezone.utc)>=datetime.fromisoformat(row[1]):
        raise ValueError("approval expired")
    status="approved" if approve else "rejected"
    conn.execute("UPDATE approvals SET status=?,decided_by=?,decided_at=? WHERE id=? AND status='pending'",
                 (status,approver_id,datetime.now(timezone.utc).isoformat(),request_id))
    conn.commit()
    return status

def is_authorized(conn, request_id:str, task_id:int, action:str, environment:str, payload:dict) -> bool:
    row=conn.execute("SELECT task_id,action,environment,artifact_sha256,status,expires_at FROM approvals WHERE id=?",
                     (request_id,)).fetchone()
    return bool(row and row[0]==task_id and row[1]==action and row[2]==environment
                and row[3]==canonical_digest(payload) and row[4]=="approved"
                and datetime.now(timezone.utc)<datetime.fromisoformat(row[5]))
