"""Persistent interval schedules; bounded catch-up and idempotent job creation."""
import json
import time
import task_queue as queue
import weekly_reports


def initialize(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS agent_schedules(name TEXT PRIMARY KEY,project TEXT NOT NULL,kind TEXT NOT NULL,
      payload TEXT NOT NULL,interval_seconds INTEGER NOT NULL CHECK(interval_seconds>=60),
      next_due REAL NOT NULL,enabled INTEGER NOT NULL DEFAULT 1);
    CREATE TABLE IF NOT EXISTS agent_worker_status(worker TEXT PRIMARY KEY,heartbeat REAL NOT NULL,state TEXT NOT NULL,detail TEXT);
    CREATE TABLE IF NOT EXISTS agent_health(target TEXT PRIMARY KEY,healthy INTEGER NOT NULL,detail TEXT NOT NULL,checked_at REAL NOT NULL);
    """)
    conn.commit()


def seed(conn,now=None):
    now=time.time() if now is None else now
    report_due=(int(now)//86400)*86400+9*3600
    if report_due<=now: report_due+=86400
    items=[
        ("nova-availability","nova","check_site",{"target":"nova"},900,now),
        ("control-source-audit","control","inspect_repository",{"target":"control"},86400,now),
        ("daily-summary","control","daily_report",{},86400,report_due)
    ]
    for name,project,kind,payload,interval,due in items:
        conn.execute("INSERT OR IGNORE INTO agent_schedules(name,project,kind,payload,interval_seconds,next_due) VALUES(?,?,?,?,?,?)",(name,project,kind,json.dumps(payload,sort_keys=True),interval,due))
    conn.commit()


def tick(conn,now=None):
    now=time.time() if now is None else now
    import emergency_control
    if emergency_control.state(conn)['latched']: return []
    if conn.execute("SELECT paused FROM agent_queue_control WHERE singleton=1").fetchone()[0]: return []
    ids=weekly_reports.tick(conn,now)
    due=conn.execute("SELECT name,project,kind,payload,interval_seconds,next_due FROM agent_schedules WHERE enabled=1 AND next_due<=? AND name<>? ORDER BY next_due LIMIT ?",(now,weekly_reports.NAME,10-len(ids))).fetchall()
    for name,project,kind,payload,interval,scheduled_at in due:
        ident=queue.enqueue(conn,project,kind,json.loads(payload),event_key=f"schedule:{name}:{scheduled_at:.6f}",now=now)
        conn.execute("UPDATE agent_schedules SET next_due=? WHERE name=? AND next_due=?",(now+interval,name,scheduled_at))
        conn.commit()
        ids.append(ident)
    return ids
