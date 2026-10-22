"""Persist exact GitHub change requests and immutable review payloads.

Approval records do not execute actions or grant production deployment.
"""
import json
from approval import request_approval, is_authorized
from execution_gate import stage

def initialize(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS github_change_requests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project TEXT NOT NULL, task TEXT NOT NULL,
        manifest_json TEXT NOT NULL, approval_id TEXT NOT NULL UNIQUE,
        status TEXT NOT NULL DEFAULT 'awaiting_review'
    )""")

def create_request(conn, project, task, files):
    manifest=stage(project,task,files)
    conn.execute("INSERT INTO github_change_requests(project,task,manifest_json,approval_id) VALUES(?,?,?,'temporary')",
                 (project,task,json.dumps(manifest,sort_keys=True)))
    task_id=conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    approval_id=request_approval(conn,task_id,"github_draft_pr","review_only",manifest,ttl_minutes=60)
    conn.execute("UPDATE github_change_requests SET approval_id=? WHERE id=?",(approval_id,task_id))
    conn.commit()
    return task_id,approval_id,manifest

def describe(conn, task_id):
    row=conn.execute("SELECT project,manifest_json,approval_id,status FROM github_change_requests WHERE id=?",(task_id,)).fetchone()
    if row is None: return "Заявка не найдена."
    project,raw,approval,status=row
    data=json.loads(raw)
    details=", ".join(f["path"]+" ("+f["sha256"][:12]+")" for f in data["files"])
    permitted=is_authorized(conn,approval,task_id,"github_draft_pr","review_only",data)
    return (f"Заявка #{task_id} • {project}\n"
            f"Ветка: {data['proposed_branch']}\n"
            f"Файлы SHA-256: {details}\n"
            f"Одобрение: {approval}\n"
            f"Готово к передаче на ручную проверку: {'да' if permitted else 'нет'}\n"
            "Создание ветки и PR этой командой НЕ выполняется.")
