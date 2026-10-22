"""Persist reviewed v3.1 autofix evidence, not executable changes.

Approvals created here have an isolated action and are NEVER consumed by the
GitHub draft PR worker. The real executor will require a separate integration
and security review. Only the admin's Telegram dispatcher can call this code.
"""
import json
import sqlite3
from approval import request_approval
from behavior_review_v34 import evidence, review_message

ACTION = "autofix_evidence_review_only"
ENVIRONMENT = "review_only"
FIXTURES = {
    "newline": ("answer = 42", "missing-final-newline"),
    "whitespace": ("answer = 42   \n", "trim-trailing-whitespace"),
}
PATH = "proposals/review_example.py"


def initialize(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS autofix_evidence_v35 (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       report_json TEXT NOT NULL,
       digest TEXT NOT NULL,
       approval_id TEXT NOT NULL UNIQUE,
       status TEXT NOT NULL DEFAULT 'pending'
    )""")


def create(conn, kind):
    if kind not in FIXTURES:
        raise ValueError("Unsupported fixture kind")
    source, rule = FIXTURES[kind]
    report = evidence(PATH, source, rule)
    payload = json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    initialize(conn)
    cursor = conn.execute(
        "INSERT INTO autofix_evidence_v35(report_json,digest,approval_id) VALUES(?,?,'pending-' || lower(hex(randomblob(12))))",
        (payload, report["evidence_sha256"]),
    )
    ident = cursor.lastrowid
    approval = request_approval(conn, ident, ACTION, ENVIRONMENT, report, ttl_minutes=60)
    conn.execute("UPDATE autofix_evidence_v35 SET approval_id=? WHERE id=?", (approval, ident))
    conn.commit()
    return ident, approval, report


def describe(conn, ident):
    initialize(conn)
    row = conn.execute(
        """SELECT r.report_json,r.digest,r.approval_id,a.status,a.action,a.environment
           FROM autofix_evidence_v35 AS r
           LEFT JOIN approvals AS a ON r.approval_id=a.id
           WHERE r.id=?""",
        (ident,),
    ).fetchone()
    if row is None:
        return "Отчёт не найден."
    payload,digest,approval,state,action,environment=row
    report=json.loads(payload)
    if digest!=report.get("evidence_sha256") or action!=ACTION or environment!=ENVIRONMENT:
        return "Отчёт изменён или неверно связан. Одобрение недействительно."
    from approval import canonical_digest
    expected=conn.execute(
        "SELECT artifact_sha256 FROM approvals WHERE id=?", (approval,)
    ).fetchone()
    if expected is None or expected[0]!=canonical_digest(report):
        return "Содержимое отчёта не совпадает с одобрением."
    return (f"Пакет исправления #{ident}\n"+review_message(report)+
            f"\nСостояние: {state}\nОдобрение: {approval}\n"+
            "Команда /approve <approval_id> подтверждает только отчёт. "+
            "GitHub PR не создаётся.")
