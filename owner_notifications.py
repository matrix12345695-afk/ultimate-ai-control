"""Owner decision inbox: storage only. No Telegram sends or side effects.

A pending decision blocks only its own task; independent tasks can continue.
This module does not implement approval or deployment.
"""
import json
import sqlite3
from datetime import datetime, timezone

KINDS = {"info", "decision", "critical"}
STATES = {"pending", "resolved"}

def initialize(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS owner_notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project TEXT NOT NULL,
        task_id TEXT,
        kind TEXT NOT NULL CHECK(kind IN ('info','decision','critical')),
        title TEXT NOT NULL,
        reason TEXT NOT NULL,
        next_action TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'pending' CHECK(state IN ('pending','resolved')),
        created_at TEXT NOT NULL,
        resolved_at TEXT
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_owner_notifications_state ON owner_notifications(state, id)")
    conn.commit()

def create(conn, project, kind, title, reason, next_action, task_id=None):
    """Store a bounded, human-readable request for the owner."""
    if kind not in KINDS:
        raise ValueError("unknown notification kind")
    values = (project, title, reason, next_action)
    if any(not isinstance(v, str) or not v.strip() or len(v) > 500 for v in values):
        raise ValueError("invalid notification fields")
    if task_id is not None and (not isinstance(task_id, str) or len(task_id) > 100):
        raise ValueError("invalid task id")
    row = conn.execute(
        """INSERT INTO owner_notifications
        (project,task_id,kind,title,reason,next_action,created_at)
        VALUES (?,?,?,?,?,?,?)""",
        (project, task_id, kind, title, reason, next_action,
         datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    return row.lastrowid

def pending(conn, limit=20):
    if not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("invalid limit")
    return conn.execute(
        """SELECT id,project,task_id,kind,title,reason,next_action,created_at
        FROM owner_notifications WHERE state='pending'
        ORDER BY CASE kind WHEN 'critical' THEN 0 WHEN 'decision' THEN 1 ELSE 2 END,
        id ASC LIMIT ?""",
        (limit,),
    ).fetchall()

def resolve(conn, notification_id):
    """Resolve inbox item only; NEVER authorizes a deploy/payment/action."""
    row = conn.execute(
        """UPDATE owner_notifications SET state='resolved',resolved_at=?
        WHERE id=? AND state='pending'""",
        (datetime.now(timezone.utc).isoformat(), notification_id),
    )
    conn.commit()
    return row.rowcount == 1

def format_pending(conn):
    rows = pending(conn)
    if not rows:
        return "Нет запросов, требующих внимания."
    return "\n\n".join(
        f"#{ident} [{kind.upper()}] {project}: {title}\n"
        f"Причина: {reason}\nДействие: {action}"
        for ident, project, task, kind, title, reason, action, created in rows
    )[:3900]
