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
    names={"planned":"запланировано","active":"в работе","blocked":"есть препятствие","done":"✅ выполнено"}
    details=completed_work(conn)
    lines=['ULTIMATE 4.0 · план']
    for ident,title,state in conn.execute('SELECT id,title,state FROM uac_roadmap ORDER BY id'):
        lines.append(f'{ident}. {title} — {names.get(state,state)}')
        if ident in details: lines.append('   '+details[ident])
    lines.append('\nСтатусы работ обновляются из журнала при открытии плана. Готовая часть не завершает весь этап.')
    return '\n'.join(lines)


def completed_work(conn):
    """Read persisted outcomes, without promoting a partial roadmap stage to done.

    This is a live projection of the queue/artifact journal, so a committed job completion
    needs no second write or fragile synchronization hook. No API/model inference is used.
    """
    tables={row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    details={}
    if 'owner_notifications' in tables:
        count=conn.execute('SELECT count(*) FROM owner_notifications WHERE delivered_at IS NOT NULL AND telegram_message_id IS NOT NULL').fetchone()[0]
        if count: details[1]=f'✅ Доставлено уведомлений: {count}.'
    if 'code_artifacts' in tables:
        total,passed=conn.execute("SELECT count(*),COALESCE(sum(test_status='passed'),0) FROM code_artifacts").fetchone()
        if total: details[4]=f'✅ Сохранено кодовых черновиков: {total}.'
        if passed: details[5]=f'✅ Черновиков с пройденными тестами: {passed}.'
        independently_checked=0
        for raw, in conn.execute("SELECT test_report FROM code_artifacts WHERE test_status='passed'"):
            try: checks=json.loads(raw).get('independent_acceptance',{})
            except (TypeError,ValueError,AttributeError): continue
            if isinstance(checks,dict) and checks.get('status')=='passed': independently_checked+=1
        if independently_checked: details[5]+=f' Независимую приёмку прошли: {independently_checked}.'
    if 'agent_jobs' in tables:
        counts={(kind,state):count for kind,state,count in conn.execute('SELECT kind,state,count(*) FROM agent_jobs GROUP BY kind,state')}
        complete=sum(count for (kind,state),count in counts.items() if state=='succeeded')
        pending=sum(count for (kind,state),count in counts.items() if state=='awaiting_owner')
        details[2]=f'✅ Выполнено заданий: {complete}. Ожидают решения: {pending}.'
        if setting(conn,'artifact_recovery_verified_release'):
            details[2]+=' ✅ Восстановление сохранённых результатов проверено.'
        checks=counts.get(('check_site','succeeded'),0)
        if checks: details[6]=f'✅ Выполнено проверок доступности: {checks}.'
        reports=counts.get(('daily_report','succeeded'),0)
        if reports: details[11]=f'✅ Сформировано суточных отчётов: {reports}.'
        last=conn.execute('SELECT id,kind,state,result FROM agent_jobs ORDER BY updated_at DESC,id DESC LIMIT 1').fetchone()
        if last:
            ident,kind,state,raw=last
            labels={'succeeded':'выполнено','awaiting_owner':'ожидает решения','failed':'ошибка','cancelled':'отменено','running':'выполняется','queued':'в очереди'}
            label=labels.get(state,state)
            try: result=json.loads(raw) if raw else {}
            except (TypeError,ValueError): result={}
            if not isinstance(result,dict): result={}
            if state=='awaiting_owner' and result.get('artifact_id') and result.get('test_status')=='passed':
                label='тесты выполнены; ожидает согласования'
            elif result.get('blocked'):
                label='заблокировано; ожидает решения'
            stage={'check_site':6,'inspect_repository':6,'review_change':4,'test_release':5,'daily_report':11}.get(kind)
            if stage:
                details[stage]=(details.get(stage,'')+' '+f'Последняя работа #{ident}: {label}.').strip()
    if 'agent_work_spans' in tables:
        count=conn.execute('SELECT count(*) FROM agent_work_spans').fetchone()[0]
        if count: details[11]=(details.get(11,'')+f' ✅ Записано интервалов работы: {count}.').strip()
    if 'agent_health_incidents' in tables:
        counts=dict(conn.execute('SELECT state,count(*) FROM agent_health_incidents GROUP BY state'))
        if counts: details[6]=(details.get(6,'')+f' Тревог открыто: {counts.get("open",0)}; восстановлений подтверждено: {counts.get("recovered",0)}.').strip()
    if 'project_memory' in tables:
        count=conn.execute("SELECT count(*) FROM project_memory WHERE project!='policy'").fetchone()[0]
        if count: details[12]=f'✅ Контекстов проектов сохранено: {count}.'
    return details
