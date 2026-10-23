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
    initialize_delivery(conn)

def create(conn, project, kind, title, reason, next_action, task_id=None, event_key=None, *, commit=True):
    """Store a bounded, human-readable request for the owner."""
    if kind not in KINDS:
        raise ValueError("unknown notification kind")
    if type(commit) is not bool or (not commit and not conn.in_transaction):
        raise ValueError('notification transaction required')
    values = (project, title, reason, next_action)
    if any(not isinstance(v, str) or not v.strip() or len(v) > 500 for v in values):
        raise ValueError("invalid notification fields")
    if task_id is not None and (not isinstance(task_id, str) or len(task_id) > 100):
        raise ValueError("invalid task id")
    if event_key is not None:
        if not isinstance(event_key, str) or not event_key or len(event_key) > 200:
            raise ValueError("invalid event key")
        existing = conn.execute("SELECT id FROM owner_notifications WHERE event_key=?", (event_key,)).fetchone()
        if existing:
            return existing[0]
    row = conn.execute(
        """INSERT INTO owner_notifications
        (project,task_id,kind,title,reason,next_action,created_at,event_key)
        VALUES (?,?,?,?,?,?,?,?) ON CONFLICT DO NOTHING""",
        (project, task_id, kind, title, reason, next_action,
         datetime.now(timezone.utc).isoformat(), event_key),
    )
    if commit: conn.commit()
    if not row.rowcount and event_key is not None:
        return conn.execute("SELECT id FROM owner_notifications WHERE event_key=?", (event_key,)).fetchone()[0]
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

def initialize_delivery(conn):
    """Backward-compatible delivery fields; no network I/O."""
    columns = {row[1] for row in conn.execute("PRAGMA table_info(owner_notifications)")}
    for name, definition in (
        ("delivered_at", "TEXT"),
        ("delivery_claimed_at", "TEXT"),
        ("delivery_attempts", "INTEGER NOT NULL DEFAULT 0"),
        ("event_key", "TEXT"),
        ("next_attempt_at", "TEXT"),
        ("delivery_failed_at", "TEXT"),
        ("delivery_error", "TEXT"),
        ("telegram_message_id", "INTEGER"),
    ):
        if name not in columns:
            conn.execute(f"ALTER TABLE owner_notifications ADD COLUMN {name} {definition}")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS owner_notification_event ON owner_notifications(event_key) WHERE event_key IS NOT NULL")
    conn.commit()

def claim_delivery(conn, now=None, stale_seconds=300):
    """Claim one message. Reclaim after crash; duplicates remain possible on network ambiguity."""
    from datetime import timedelta
    now = now or datetime.now(timezone.utc)
    stale = (now - timedelta(seconds=stale_seconds)).isoformat()
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute(
            """SELECT id,project,kind,title,reason,next_action FROM owner_notifications
            WHERE delivered_at IS NULL AND state='pending'
            AND delivery_failed_at IS NULL AND delivery_attempts < 8
            AND (next_attempt_at IS NULL OR next_attempt_at <= ?)
            AND (delivery_claimed_at IS NULL OR delivery_claimed_at < ?)
            ORDER BY CASE kind WHEN 'critical' THEN 0 WHEN 'decision' THEN 1 ELSE 2 END, id
            LIMIT 1""", (now.isoformat(), stale)
        ).fetchone()
        if row:
            conn.execute(
                """UPDATE owner_notifications SET delivery_claimed_at=?,
                delivery_attempts=delivery_attempts+1 WHERE id=?""",
                (now.isoformat(), row[0])
            )
        conn.commit()
        return row
    except Exception:
        conn.rollback()
        raise

def mark_delivered(conn, notification_id, at=None, message_id=None):
    at = at or datetime.now(timezone.utc).isoformat()
    conn.execute(
        "UPDATE owner_notifications SET delivered_at=?,telegram_message_id=?,delivery_claimed_at=NULL,delivery_error=NULL WHERE id=? AND delivered_at IS NULL",
        (at, message_id, notification_id)
    )
    conn.commit()

def release_delivery(conn, notification_id, error="temporary", retry_after=None, permanent=False, now=None):
    from datetime import timedelta
    now = now or datetime.now(timezone.utc)
    attempts = conn.execute("SELECT delivery_attempts FROM owner_notifications WHERE id=?", (notification_id,)).fetchone()
    if not attempts:
        return
    delay = max(30, min(86400, retry_after or 30 * 2 ** min(attempts[0], 10)))
    failed_at = now.isoformat() if permanent or attempts[0] >= 8 else None
    conn.execute(
        "UPDATE owner_notifications SET delivery_claimed_at=NULL,next_attempt_at=?,delivery_failed_at=?,delivery_error=? WHERE id=? AND delivered_at IS NULL",
        ((now + timedelta(seconds=delay)).isoformat(), failed_at, str(error)[:80], notification_id)
    )
    conn.commit()

def format_delivery(row):
    ident, project, kind, title, reason, action = row
    return (f"🔔 ULTIMATE AI CONTROL · {kind.upper()}\n"
            f"Проект: {project}\nТема: {title}\n"
            f"Причина: {reason}\nЧто сделать: {action}\n"
            f"Запрос #{ident} · /owner_inbox")

