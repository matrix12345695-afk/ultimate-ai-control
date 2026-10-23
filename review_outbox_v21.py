"""Review notification outbox. No Telegram network calls or credentials.

Trusted worker can atomically claim pending messages for a separately
authenticated Telegram sender. This module never sends or deploys.
"""
import json
from datetime import datetime, timezone
from controller_v20 import telegram_report

def initialize(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS review_outbox (
      request_id INTEGER NOT NULL,
      head_sha TEXT NOT NULL,
      ci_state TEXT NOT NULL,
      body TEXT NOT NULL,
      status TEXT NOT NULL CHECK(status IN ('pending','claimed','sent')),
      created_at TEXT NOT NULL,
      PRIMARY KEY (request_id, head_sha, ci_state)
    )""")

def queue_ci_notification(conn, request_id):
    row=conn.execute("""SELECT request_id,head_sha,pr_url,ci_state
                         FROM github_ci_reports WHERE request_id=?""",(request_id,)).fetchone()
    if row is None: raise ValueError("No verified CI report")
    ident,sha,url,state=row
    body=telegram_report(ident,url,sha,state)
    conn.execute("""INSERT OR IGNORE INTO review_outbox
      (request_id,head_sha,ci_state,body,status,created_at)
      VALUES(?,?,?,?,'pending',?)""",
      (ident,sha,state,body,datetime.now(timezone.utc).isoformat()))
    conn.commit()
    return body

def pending_messages(conn):
    return conn.execute("""SELECT request_id,head_sha,ci_state,body
       FROM review_outbox WHERE status='pending' ORDER BY created_at LIMIT 20""").fetchall()

def claim(conn,request_id,sha,state):
    updated=conn.execute("""UPDATE review_outbox SET status='claimed'
      WHERE request_id=? AND head_sha=? AND ci_state=? AND status='pending'""",
      (request_id,sha,state)).rowcount
    conn.commit()
    return updated==1
