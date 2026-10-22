"""Level 2 Telegram control commands. No deployments or code execution."""
from datetime import datetime, timezone
from approval import init_approvals, decide

def initialize(conn):
    fields={row[1] for row in conn.execute("PRAGMA table_info(tasks)")}
    if "status" not in fields:
        conn.execute("ALTER TABLE tasks ADD COLUMN status TEXT NOT NULL DEFAULT 'queued'")
    conn.execute("CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY, at TEXT, action TEXT, detail TEXT)")
    init_approvals(conn)
    conn.commit()

def record(conn, action, detail):
    conn.execute("INSERT INTO audit(at,action,detail) VALUES(?,?,?)",
                 (datetime.now(timezone.utc).isoformat(),action,detail[:500]))

def handle(text, connect, admin):
    parts=text.split(maxsplit=2)
    op=parts[0].split("@")[0].lower()
    if op not in ("/approvals","/approve","/reject","/taskstatus","/cancel","/audit"):
        return None
    with connect() as conn:
        initialize(conn)
        if op=="/approvals":
            rows=conn.execute("SELECT id,task_id,action,environment,status FROM approvals ORDER BY requested_at DESC LIMIT 10").fetchall()
            return "\n".join(f"{r[0]} | task {r[1]} | {r[2]} @ {r[3]} | {r[4]}" for r in rows) or "No approval requests."
        if op in ("/approve","/reject"):
            if len(parts)<2: return f"Usage: {op} <approval_id>"
            try:
                result=decide(conn,parts[1],admin,admin,op=="/approve")
                record(conn,"approval",f"{parts[1]} -> {result}")
                conn.commit()
                return f"Recorded: {result}. This DOES NOT deploy anything."
            except (ValueError,PermissionError) as ex:
                return f"Refused: {ex}"
        if op=="/audit":
            rows=conn.execute("SELECT at,action,detail FROM audit ORDER BY id DESC LIMIT 10").fetchall()
            return "\n".join(f"{r[0][:16]} {r[1]} {r[2]}" for r in rows) or "Audit log empty."
        if len(parts)<2 or not parts[1].isdigit():
            return f"Usage: {op} <task_id>"
        task=int(parts[1])
        if op=="/taskstatus":
            row=conn.execute("SELECT id,project,description,status FROM tasks WHERE id=?",(task,)).fetchone()
            return f"#{row[0]} [{row[3]}] {row[1]}: {row[2]}" if row else "Task not found."
        changed=conn.execute("UPDATE tasks SET status='cancelled' WHERE id=? AND status='queued'",(task,)).rowcount
        if changed: record(conn,"cancel",str(task))
        conn.commit()
        return "Task cancelled." if changed else "Task missing or not queued."
