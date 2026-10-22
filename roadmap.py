"""Evidence-based roadmap and persistent project context; no model-generated progress."""
import json
from pathlib import Path
import time

STAGES = [
    (1,"Уведомления владельцу",[],"Persisted Telegram receipt, retries and live inbox"),
    (2,"Планировщик и очередь",[1],"Persistent jobs, leases, recovery, safe pause and independent execution"),
    (3,"AI и бюджет $30",[2],"Approved provider configuration, atomic reservations, usage and cost reconciliation"),
    (4,"Агент-разработчик",[2,3],"Real isolated changes with file evidence and draft PR"),
    (5,"Агент-тестировщик",[2],"Isolated tests, required checks and failure evidence"),
    (6,"Мониторинг сайтов и приложений",[1,2],"Scheduled availability checks and transition notifications"),
    (7,"Несколько проектов",[2],"Verified repository registry and separate project permissions"),
    (8,"Черновики и Pull Request",[4,5],"Reviewed patch, commit digest, draft PR and exact-head checks"),
    (9,"Согласование публикаций",[8],"Authenticated Telegram approval scoped to one project/version/digest"),
    (10,"Голосовое управление",[2,3],"Voice download, budgeted transcription, confirmation of interpreted task"),
    (11,"Рабочее время и аналитика",[2],"Measured intervals, failures, costs, daily and weekly reports"),
    (12,"Память проектов",[2],"Persisted business rules and evidence-linked decisions"),
    (13,"Дизайн и браузерное тестирование",[4,5],"Mobile screenshots, accessible UI and regression checks"),
    (14,"Проверенные open-source компоненты",[5],"License, dependency, security and resource audit before integration"),
    (15,"Полный автономный цикл",[3,4,5,7,8,9,11,12],"Continuous useful work, recovery, resource limits and owner-controlled publication"),
    (16,"NOVA WEB как коммерческая платформа",[7,8,9],"Leads, order pipeline, customer-site production and analytics")
]


def initialize(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS uac_roadmap(id INTEGER PRIMARY KEY,title TEXT NOT NULL,dependencies TEXT NOT NULL,
      acceptance TEXT NOT NULL,state TEXT NOT NULL DEFAULT 'planned',evidence TEXT,updated_at REAL NOT NULL);
    CREATE TABLE IF NOT EXISTS project_memory(project TEXT PRIMARY KEY,content TEXT NOT NULL,source TEXT NOT NULL,updated_at REAL NOT NULL);
    CREATE TABLE IF NOT EXISTS uac_settings(key TEXT PRIMARY KEY,value TEXT NOT NULL,updated_at REAL NOT NULL);
    """)
    now=time.time()
    for ident,title,deps,acceptance in STAGES:
        conn.execute("INSERT OR IGNORE INTO uac_roadmap(id,title,dependencies,acceptance,updated_at) VALUES(?,?,?,?,?)",(ident,title,json.dumps(deps),acceptance,now))
    doc=json.loads(Path(__file__).with_name("project_memory.json").read_text())
    for project,content in {"policy":doc["policy"],**doc["projects"]}.items():
        conn.execute("INSERT OR IGNORE INTO project_memory VALUES(?,?,?,?)",(project,json.dumps(content,ensure_ascii=False),doc["source"],now))
    conn.execute("INSERT OR IGNORE INTO uac_settings VALUES('active_project','control',?)",(now,))
    conn.commit()


def setting(conn,key,default=None):
    row=conn.execute("SELECT value FROM uac_settings WHERE key=?",(key,)).fetchone()
    return row[0] if row else default


def set_setting(conn,key,value):
    conn.execute("INSERT INTO uac_settings VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at",(key,value,time.time()))
    conn.commit()


def mark(conn,ident,state,evidence):
    if state not in {"planned","active","blocked","done"} or not isinstance(evidence,str) or not evidence.strip():
        raise ValueError("state/evidence required")
    if conn.execute("UPDATE uac_roadmap SET state=?,evidence=?,updated_at=? WHERE id=?",(state,evidence[:4000],time.time(),ident)).rowcount != 1:
        raise ValueError("unknown stage")
    conn.commit()


def describe(conn):
    names={"planned":"запланировано","active":"в работе","blocked":"есть препятствие","done":"проверено"}
    return "ULTIMATE 4.0 · план\n"+"\n".join(f"{ident}. {title} — {names.get(state,state)}" for ident,title,state in conn.execute("SELECT id,title,state FROM uac_roadmap ORDER BY id"))
