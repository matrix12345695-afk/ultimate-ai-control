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
        if setting(conn,'recipe_acceptance_verified_release'):
            details[5]=(details.get(5,'')+' ✅ Независимая приёмка путей и Git SHA подключена.').strip()
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
        if setting(conn,'work_analytics_verified_release'):
            details[11]=(details.get(11,'')+' ✅ Отчёты за сутки/неделю, ожидание и учёт квитанций проверены.').strip()
    if 'agent_health_incidents' in tables:
        counts=dict(conn.execute('SELECT state,count(*) FROM agent_health_incidents GROUP BY state'))
        if counts: details[6]=(details.get(6,'')+f' Тревог открыто: {counts.get("open",0)}; восстановлений подтверждено: {counts.get("recovered",0)}.').strip()
        if setting(conn,'readiness_verified_release'):
            details[6]=(details.get(6,'')+' ✅ Отдельная проверка API и готовности PostgreSQL подключена.').strip()
    if 'project_memory' in tables:
        count=conn.execute("SELECT count(*) FROM project_memory WHERE project!='policy'").fetchone()[0]
        if count: details[12]=f'✅ Контекстов проектов сохранено: {count}.'
        if setting(conn,'owner_followups_verified_release'):
            details[12]=(details.get(12,'')+' ✅ Список отложенных действий владельца проверен.').strip()
        if 'project_evidence_memory' in tables and setting(conn,'evidence_memory_verified_release'):
            total=conn.execute('SELECT count(*) FROM project_evidence_memory').fetchone()[0]
            details[12]=(details.get(12,'')+f' ✅ История с проверяемыми основаниями подключена: {total} записей.').strip()
    if 'agent_jobs' in tables:
        import project_registry
        registered=project_registry.verified(conn)
        if registered:
            details[7]=f'✅ Репозиториев с проверенными файлами и хешами: {len(registered)}. Доступ только для чтения; исполнение и публикация не включены.'
    if 'project_test_runs' in tables and setting(conn,'nova_tests_verified_release'):
        details[5]=(details.get(5,'')+' ✅ Закреплённые тесты NOVA без PostgreSQL и браузера подключены.').strip()
    if 'artifact_pr_requests' in tables and setting(conn,'artifact_pr_verified_release'):
        count=conn.execute('SELECT count(*) FROM artifact_pr_requests').fetchone()[0]
        details[8]=f'✅ Связанных заявок Draft PR: {count}. Проверка точного diff/CI подключена для двух рецептов ULTIMATE.'
        details[9]='✅ Запрос согласования связывает проект, commit, артефакт и CI. Исполнитель публикации ещё не подключён.'
    if 'artifact_release_checks' in tables and setting(conn,'release_check_verified_release'):
        details[9]=(details.get(9,'')+' ✅ Проверка версии, CI и согласования перед выпуском подключена. /release_checks. Публикация отключена.').strip()
    if 'vps_resource_samples' in tables and setting(conn,'vps_resources_verified_release'):
        details[6]=(details.get(6,'')+' ✅ Память, CPU, диск и inode VPS: замеры и подтверждённые ресурсные тревоги. /vps4.').strip()
    if 'nova_ci_runs' in tables and setting(conn,'nova_ci_verified_release'):
        details[5]=(details.get(5,'')+' ✅ Все34 теста закреплённой NOVA с PostgreSQL16 проходят на временном GitHub runner; VPS сверяет точный CI. /nova_pg.').strip()
    if 'browser_ci_runs' in tables and setting(conn,'browser_ci_verified_release'):
        details[13]=(details.get(13,'')+' ✅ Chromium:27 проверок,3 размера экрана,15 снимков; API подставной. Два замечания сохранены. /nova_browser.').strip()
    if 'browser_candidate_runs' in tables:
        import browser_candidate_ci
        row=conn.execute('SELECT report,report_sha256 FROM browser_candidate_runs ORDER BY id DESC LIMIT 1').fetchone()
        try:
            report=json.loads(row[0]) if row else None
            passed=row and browser_candidate_ci.valid(report) and browser_candidate_ci.util.digest(report)==row[1] and report['status']=='passed'
        except (TypeError,ValueError): passed=False
        if passed:
            details[13]=details.get(13,'')+' ✅ Выполнено в Draft PR15: подсказки RU/UZ, кнопки44px и мобильное положение;34 проверки. Публикация ожидает решения. /nova_candidate.'
    if 'nova_release_ci_runs' in tables:
        import nova_release_ci
        row=conn.execute('SELECT report,report_sha256 FROM nova_release_ci_runs ORDER BY id DESC LIMIT 1').fetchone()
        try:
            report=json.loads(row[0]) if row else None
            passed=row and nova_release_ci.valid(report) and nova_release_ci.util.digest(report)==row[1] and report['status']=='passed'
        except (TypeError,ValueError): passed=False
        if passed:
            details[9]=details.get(9,'')+' ✅ Репетиция HTTP/PG:34+15 проверок, данные сохранены. Откат Render и выпуск ещё не выполнены. /nova_release.'
    return details
