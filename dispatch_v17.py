"""One-time dispatch receipts for externally reviewed GitHub draft PR work.

Only a receipt is reserved here. No network write, GitHub token or worker run.
"""
import json
import sqlite3
from datetime import datetime,timezone
from handoff_v16 import prepare_handoff

def initialize(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS dispatch_receipts (
        request_id INTEGER PRIMARY KEY,
        handoff_sha256 TEXT NOT NULL UNIQUE,
        base_sha TEXT NOT NULL,
        state TEXT NOT NULL CHECK(state IN ('reserved','completed','failed')),
        reserved_at TEXT NOT NULL,
        result_ref TEXT
    )""")

def reserve_once(conn, request_id, base_sha):
    """Atomic single-use reservation. Fail closed for repeated submissions."""
    package=prepare_handoff(conn,request_id,base_sha)
    now=datetime.now(timezone.utc).isoformat()
    try:
        conn.execute("BEGIN IMMEDIATE")
        row=conn.execute("SELECT state FROM dispatch_receipts WHERE request_id=?",(request_id,)).fetchone()
        if row is not None:
            raise ValueError("Already reserved; manual reconciliation required")
        conn.execute("INSERT INTO dispatch_receipts VALUES (?,?,?,?,?,NULL)",
                     (request_id,package["handoff_sha256"],base_sha,"reserved",now))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return package

def record_result(conn,request_id,handoff_sha256,result_ref,success):
    if not isinstance(result_ref,str) or not result_ref.startswith("https://github.com/") or len(result_ref)>300:
        raise ValueError("Invalid result reference")
    state="completed" if success else "failed"
    changed=conn.execute("UPDATE dispatch_receipts SET state=?,result_ref=? WHERE request_id=? AND handoff_sha256=? AND state='reserved'",
                         (state,result_ref,request_id,handoff_sha256)).rowcount
    if changed!=1:
        conn.rollback()
        raise ValueError("Receipt missing or already completed")
    conn.commit()
    return state
