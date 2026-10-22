"""Read-only diagnostics. No credentials, no production writes."""
import sqlite3
from datetime import datetime, timezone

def snapshot(conn: sqlite3.Connection, ai_enabled=False):
    tasks=dict(conn.execute("SELECT status,COUNT(*) FROM tasks GROUP BY status").fetchall())
    proposals=conn.execute("SELECT COUNT(*) FROM proposals").fetchone()[0]
    approvals=conn.execute("SELECT COUNT(*) FROM approvals WHERE status='pending'").fetchone()[0]
    return {"checked_at":datetime.now(timezone.utc).isoformat(),
            "tasks":tasks,"proposals":proposals,"pending_approvals":approvals,
            "ai_enabled":bool(ai_enabled),"production_writes_enabled":False}

def format_snapshot(data):
    counts=", ".join(f"{k}: {v}" for k,v in sorted(data["tasks"].items())) or "нет"
    return ("📊 Диагностика ULTIMATE AI CONTROL\n"
            f"Задачи: {counts}\n"
            f"Черновики: {data['proposals']}\n"
            f"Ожидают согласования: {data['pending_approvals']}\n"
            f"AI-модель: {'включена' if data['ai_enabled'] else 'отключена'}\n"
            "Изменения рабочих систем: запрещены без подтверждения")
