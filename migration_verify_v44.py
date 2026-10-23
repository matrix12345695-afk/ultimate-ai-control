"""Offline migration verification for a stopped Telegram dispatcher.

Never replaces the destination DB automatically. Review results before cutover.
"""
import hashlib
import sqlite3
from pathlib import Path

def inspect_database(path):
    path=Path(path)
    if not path.is_file() or path.stat().st_size==0:
        raise ValueError("Database file missing or empty")
    uri=path.resolve().as_uri()+"?mode=ro"
    with sqlite3.connect(uri,uri=True) as conn:
        if conn.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
            raise ValueError("SQLite integrity check failed")
        tables={row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        required={"tasks","approvals","github_change_requests"}
        if not required.issubset(tables):
            raise ValueError("Missing production tables: "+",".join(sorted(required-tables)))
        counts={table:conn.execute('SELECT COUNT(*) FROM "'+table+'"').fetchone()[0] for table in sorted(required)}
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    return {"sha256":digest,"tables":sorted(tables),"counts":counts}
