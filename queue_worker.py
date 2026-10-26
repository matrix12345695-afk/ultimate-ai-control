"""Continuous, bounded operations worker. No arbitrary shell or model calls.

Typed handlers perform HTTPS checks, AST inspection, isolated tests and fixed code recipes.
Development tasks remain blocked with durable owner notifications until isolated AI execution
is actually configured. They are never reported as implemented by the offline planner.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import signal
import sqlite3
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit
import task_queue as queue
import scheduler
import roadmap
import budget_gate
import offline_developer
from artifact_recovery import ArtifactRecoveryBlocked
import metered_provider
import model_broker
import broker_client
import developer_pipeline
import health_incidents
import project_registry
import work_analytics
import readiness_monitor
import evidence_memory
import nova_project_tests
import artifact_prs
import artifact_pr_client
import vps_resources
import nova_ci
import browser_ci
import browser_candidate_ci
import nova_release_ci
import locked_build_ci
import nova_deploy
import nova_recovery_ci
import nova_private_copy_ci
import emergency_control as emergency
import emergency_selftest
from isolated_python import run_bundle, SandboxUnavailable
from sandbox_smoke import FILES as SANDBOX_SMOKE
from owner_notifications import initialize as init_inbox,create as notify
from chat_binding import action as chat_action

ROOT=Path(__file__).resolve().parent
TARGETS=health_incidents.TARGETS
WORKER="operations-1"


class ManagedConnection(sqlite3.Connection):
    def __exit__(self,*args):
        try: return super().__exit__(*args)
        finally: self.close()


def connect(path):
    conn=sqlite3.connect(path,timeout=15,factory=ManagedConnection)
    conn.execute("PRAGMA busy_timeout=15000")
    return conn


def initialize(conn):
    queue.initialize(conn)
    scheduler.initialize(conn)
    roadmap.initialize(conn)
    init_inbox(conn)
    budget_gate.initialize(conn)
    offline_developer.initialize(conn)
    metered_provider.initialize(conn)
    model_broker.initialize(conn)
    health_incidents.initialize(conn)
    evidence_memory.initialize(conn)
    nova_project_tests.initialize(conn)
    artifact_prs.initialize(conn)
    vps_resources.initialize(conn)
    nova_ci.initialize(conn)
    browser_ci.initialize(conn)
    browser_candidate_ci.initialize(conn)
    nova_release_ci.initialize(conn)
    locked_build_ci.initialize(conn)
    nova_deploy.initialize(conn)
    nova_recovery_ci.initialize(conn)
    nova_private_copy_ci.initialize(conn)
    emergency_selftest.initialize(conn)


def send_event(conn,kind,title,reason,event_key,task=None):
    return notify(conn,"ULTIMATE AI CONTROL",kind,title,reason[:500],chat_action(conn)[:500],
                  task_id=str(task) if task else None,event_key=event_key)


def allowed_url(url):
    parsed=urlsplit(url)
    return (parsed.scheme=="https" and parsed.hostname in {"novaweb.uz","www.novaweb.uz"}
            and not parsed.username and not parsed.password and parsed.port in (None,443))


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if not allowed_url(newurl): raise ValueError("redirect destination is not enabled")
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def check_site(payload,opener=None):
    target=payload.get("target")
    if target==readiness_monitor.TARGET: return readiness_monitor.probe(payload,opener)
    if target not in TARGETS: raise ValueError("monitor target not enabled")
    url=TARGETS[target]
    opener=opener or urllib.request.build_opener(SafeRedirect()).open
    try:
        request=urllib.request.Request(url,method="GET",headers={"User-Agent":"ULTIMATE-Availability/4.0","Range":"bytes=0-1023"})
        with opener(request,timeout=12) as response:
            response.read(1024)
            healthy=200<=response.status<400
            detail="HTTP "+str(response.status)
    except urllib.error.HTTPError as exc:
        healthy,detail=False,"HTTP "+str(exc.code)
    except (OSError,ValueError) as exc:
        healthy,detail=False,type(exc).__name__
    return {"target":target,"url":url,"healthy":healthy,"detail":detail}


def inspect_source(payload,root=ROOT):
    if payload.get("target")!="control": raise ValueError("repository not enabled")
    root=Path(root).resolve()
    if "inventory-bot" in root.parts: raise PermissionError("Inventory is protected")
    files=[]
    errors=[]
    # Only first-party .py files and tests; never traverse .env, .git, venv, logs or data.
    paths=list(root.glob("*.py"))+list((root/"tests").glob("*.py"))
    for path in sorted(paths):
        if path.is_symlink() or path.stat().st_size>256000: continue
        if path.resolve().parent not in (root,root/"tests"): continue
        raw=path.read_bytes()
        try: ast.parse(raw,filename=str(path.relative_to(root)))
        except SyntaxError: errors.append(str(path.relative_to(root)))
        files.append({"path":str(path.relative_to(root)),"sha256":hashlib.sha256(raw).hexdigest()})
    if not files: raise ValueError("no source files available")
    digest=hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()
    return {"inspected_files":len(files),"syntax_errors":errors,"source_digest":digest,
            "method":"AST parse and source fingerprints; no test or source code was executed"}


def category(job):
    return 'active' if job['payload'].get('ai_task') or 'artifact_pr' in job['payload'] else ('testing' if job['kind'] in ('test_release','review_change') else 'active')


def record_failed_interval(conn,job,start,tick):
    end=start+max(0.000001,time.monotonic()-tick)
    prior=conn.execute('SELECT MAX(ended_at) FROM agent_work_spans WHERE job_id=? AND attempt=?',(job['id'],job['attempt'])).fetchone()[0]
    begin=max(start,prior or start)
    if begin>=end: return
    try:
        queue.add_work_span(conn,job['id'],job['lease_token'],
                            category(job),
                            begin,end,now=max(time.time(),end))
    except PermissionError:
        pass  # Expired work is never assigned to another worker's lease.


def run_once(path,root=ROOT,site_checker=check_site,repository_inspector=project_registry.inspect_remote):
    with connect(path) as conn:
        evidence_memory.sync(conn)
        emergency.flush_notifications(conn)
        scheduler.tick(conn)
        conn.execute("INSERT INTO agent_worker_status VALUES(?,?,?,?) ON CONFLICT(worker) DO UPDATE SET heartbeat=excluded.heartbeat,state=excluded.state,detail=excluded.detail",(WORKER,time.time(),"idle",""))
        conn.commit()
        job=queue.claim(conn,WORKER,queue.KINDS,lease_seconds=60)
        expired=conn.execute("SELECT id FROM agent_jobs WHERE state='failed' AND last_error='lease_expired' ORDER BY id DESC LIMIT 20").fetchall()
        for ident, in expired:
            send_event(conn,'critical','Исполнитель не завершил задание',
                       f'Задание #{ident} исчерпало попытки после остановки исполнителя. Сохранённые данные оставлены для проверки; автоматического повторного запуска нет.',
                       'job-lease-exhausted-'+str(ident),ident)
    if not job: return None
    start=time.time()
    tick=time.monotonic()
    result=None
    waiting=False
    try:
        with connect(path) as conn: emergency.check_job(conn,job['id'],job['lease_token'])
        if job["kind"]=="check_site": result=site_checker(job["payload"])
        elif job["kind"]=="inspect_repository":
            if job['payload'].get('target')==vps_resources.TARGET:
                vps_resources.scope(job)
                result={'resource_observation':vps_resources.collect(Path(path).parent)}
            elif job['project']=='control' and job['payload']=={'target':'control'}:
                result=inspect_source(job["payload"],root)
            else:
                project_registry.check_scope(job['project'],job['payload'])
                result=repository_inspector(job['project'],job['payload'])
                if not project_registry.valid_result(job['project'],result):
                    raise project_registry.RepositoryScopeError('repository_result_scope_mismatch')
        elif job['kind']=='test_release' and job['payload'].get('target')==emergency_selftest.PROFILE:
            with connect(path) as conn: result=emergency_selftest.save(conn,job,emergency_selftest.acceptance())
        elif job['kind']=='test_release' and job['payload'].get('target')==nova_private_copy_ci.PROFILE:
            nova_private_copy_ci.scope(job)
            result=artifact_pr_client.request(path,job)
        elif job['kind']=='test_release' and job['payload'].get('target')==nova_recovery_ci.PROFILE:
            nova_recovery_ci.scope(job)
            result=artifact_pr_client.request(path,job)
        elif job['kind']=='test_release' and job['payload'].get('target')==nova_deploy.PROFILE:
            nova_deploy.scope(job)
            result=artifact_pr_client.request(path,job)
        elif job['kind']=='test_release' and job['payload'].get('target')==locked_build_ci.PROFILE:
            locked_build_ci.scope(job)
            result=artifact_pr_client.request(path,job)
        elif job['kind']=='test_release' and job['payload'].get('target')==nova_release_ci.PROFILE:
            nova_release_ci.scope(job)
            result=artifact_pr_client.request(path,job)
        elif job['kind']=='test_release' and job['payload'].get('target')==browser_candidate_ci.PROFILE:
            browser_candidate_ci.scope(job)
            result=artifact_pr_client.request(path,job)
        elif job['kind']=='test_release' and job['payload'].get('target')==browser_ci.PROFILE:
            browser_ci.scope(job)
            result=artifact_pr_client.request(path,job)
        elif job['kind']=='test_release' and job['payload'].get('target')==nova_ci.PROFILE:
            nova_ci.scope(job)
            result=artifact_pr_client.request(path,job)
        elif job['kind']=='test_release' and job['payload'].get('target')==nova_project_tests.PROFILE:
            nova_project_tests.check_scope(job)
            with connect(path) as conn:
                result=nova_project_tests.execute(conn,job,Path(path).parent)
        elif job["kind"]=="test_release" and job['payload'].get('target')=='sandbox-smoke':
            policy=Path(path).parent/'sandbox-policy.json'
            report=run_bundle(SANDBOX_SMOKE,policy,timeout=10)
            result={'test_status':report['status'],'backend':report['backend'],'test_elapsed_seconds':report['elapsed_seconds'],
                    'source_digest':report['source_digest'],'output':report['output'][-4000:],'network':False,'writable_tmp':report['writable_tmp']}
        elif job['kind']=='review_change' and 'artifact_pr' in job['payload']:
            result=artifact_pr_client.request(path,job)
            waiting=not result.get('release_check_id')
        elif job["kind"]=="review_change" and job['payload'].get('recipe'):
            with connect(path) as conn:
                result=offline_developer.prepare(conn,job,Path(path).parent/'artifacts',Path(path).parent/'sandbox-policy.json')
            waiting=result['test_status']=='passed'
        elif job['kind']=='review_change' and job['payload'].get('ai_task'):
            try:
                bundle=broker_client.request(path,job)
                result={'source_digest':bundle['source_digest'],'engine':bundle['engine'],
                        'code_draft_created':True,'published':False,'tests_pending':True,
                        'generation_job_id':job['id']}
            except model_broker.BrokerDeferred as exc:
                waiting=True
                result={'blocked':str(exc),'implemented':False,'published':False}
        elif job['kind']=='test_release' and job['payload'].get('target')=='developer-bundle':
            with connect(path) as conn:
                result=developer_pipeline.test_bundle(conn,job,Path(path).parent)
            waiting=result['test_status']=='passed'
        elif job["kind"]=="daily_report":
            with connect(path) as conn:
                result={"report":queue.report(conn,start-86400,start),"budget":budget_gate.summary(conn),
                        "analytics":work_analytics.summary(conn,start-86400,start)}
        else:
            # A free text request is accepted but not falsely marked as implemented.
            waiting=True
            result={"blocked":"isolated_ai_executor_not_configured","task":job["payload"],"implemented":False,
                    "next":"Continue implementing the budgeted provider and isolated developer/tester pipeline"}
        end=start+max(0.000001,time.monotonic()-tick)
        # Record only the measured handler interval. Time waiting in the queue is not work.
        with connect(path) as conn:
            queue.add_work_span(conn,job["id"],job["lease_token"],category(job),start,end,now=max(time.time(),end))
            if result.get('resource_observation'):
                result=vps_resources.complete(conn,job,result['resource_observation'],now=max(time.time(),end))
            elif waiting and result.get('blocked') and roadmap.setting(conn,'provider_setup_deferred')!='true':
                send_event(conn,"decision","Нужен исполнитель для текстовых задач",
                           "Задачи сохранены. Платный провайдер с API-ключом и изолированный AI-разработчик ещё не подключены. Ключ нужно настраивать приватно на VPS. Мониторинг и независимые проверки продолжаются.",
                           "runtime-needs-ai-executor-v4",job["id"])
            elif result.get('release_check_id'):
                send_event(conn,'info','Проверка перед выпуском завершена',
                           f"Отчёт #{result['release_check_id']}. {result['pr_url']}. Commit {result['head_sha']}. CI: {result['ci_state']}. Согласование: {result['approval_state']}. Исполнитель публикации отключён; merge и deploy не выполнялись. /release_checks",
                           'release-check-'+str(job['id']),job['id'])
            elif result.get('artifact_pr_id'):
                send_event(conn,'info' if result['ci_state']=='success' else 'critical',
                           'Draft PR из артефакта проверен' if result['ci_state']=='success' else 'Draft PR требует исправления CI',
                           f"PR #{result['artifact_pr_id']}: {result['pr_url']}. Commit {result['head_sha']}. CI: {result['ci_state']}. Исходный артефакт {result['artifact_id']}. Merge и публикации не было.",
                           'artifact-pr-'+str(result['artifact_pr_id'])+'-'+result['head_sha']+'-'+result['ci_state'],job['id'])
            elif result.get('artifact_id'):
                engine=result.get('engine','deterministic_recipe')
                label='OpenAI через отдельный посредник' if engine=='openai_broker' else ('демонстрация посредника без LLM' if engine=='offline_broker_demo' else 'детерминированный рецепт без LLM')
                send_event(conn,'decision' if result['test_status']=='passed' else 'critical',
                           'Кодовый черновик проверен' if result['test_status']=='passed' else 'Проверка кодового черновика не прошла',
                           f"Артефакт #{result['artifact_id']}, SHA-256 {result['source_digest']}. Тесты: {result['test_status']}. Независимая приёмка: {result.get('independent_acceptance','not_configured')}. Просмотр: /artifact {result['artifact_id']}. Движок: {label}. "+('Восстановлен сохранённый результат; тесты повторно не запускались. ' if result.get('tests_reused') else '')+'Публикации не было.',
                           'artifact-'+str(job['id'])+'-'+result['source_digest'],job['id'])
            elif result.get('emergency_test_id'):
                send_event(conn,'info','Аварийная защита ULTIMATE проверена',
                           '8 сценариев остановки/сброса, блокировки новых допусков и старых согласований прошли на отдельной базе в памяти. Рабочая блокировка не включалась; Inventory не затрагивался. /emergency',
                           'emergency-selftest-'+str(job['id']),job['id'])
            elif result.get('nova_private_copy_ci_id'):
                send_event(conn,'info' if result['test_status']=='passed' else 'critical',
                           'Черновик приватной копии NOVA проверен' if result['test_status']=='passed' else 'Черновик приватной копии не прошёл',
                           result['ci_url']+' · '+('Draft PR17:30 проверок,5003 синтетические заявки/4 таблицы. Шифрование и изолированное восстановление проверены. Реальная копия не получена; на Free нет консоли, нужен согласованный путь запуска и получатель/хранилище. /nova_copy' if result['test_status']=='passed' else 'Шифрование/восстановление не подтверждены. Публикация отключена. /nova_copy'),
                           'nova-private-copy-job-'+str(job['id']),job['id'])
            elif result.get('nova_recovery_ci_id'):
                send_event(conn,'info' if result['test_status']=='passed' else 'critical',
                           'Тест восстановления NOVA проверен' if result['test_status']=='passed' else 'Тест восстановления NOVA не прошёл',
                           result['ci_url']+' · '+('24 проверки PostgreSQL18;5003 синтетические заявки и4 таблицы восстановлены. Реальная копия ещё не подтверждена; срок Free БД19 ноября. /nova_recovery' if result['test_status']=='passed' else 'Восстановление в CI не подтверждено. Публикация отключена. /nova_recovery'),
                           'nova-recovery-job-'+str(job['id']),job['id'])
            elif result.get('nova_deploy_report_id'):
                send_event(conn,'info','План публикации NOVA подготовлен',
                           'Точный коммит, сервис, настройки, CI и срок связаны в одном плане. Симулятор проверил выпуск, условный откат и потерянный ответ. Реальное исполнение отключено: резервная копия, доступная сборка отката, доступ провайдера и согласование ещё не подтверждены. /nova_deploy',
                           'nova-deploy-plan-'+str(job['id']),job['id'])
            elif result.get('locked_build_ci_id'):
                send_event(conn,'info' if result['test_status']=='passed' else 'critical',
                           'Закреплённая сборка NOVA проверена' if result['test_status']=='passed' else 'Закреплённая сборка NOVA не прошла',
                           f"{result['ci_url']}. "+('Draft PR16: Node/pg/14 пакетов закреплены;83 проверки (34 приложение,15 HTTP/PG,34 браузер),15 снимков. Blueprint пока не применён. Публикация отключена. /nova_build' if result['test_status']=='passed' else 'Сборка, тесты и снимки не подтверждены. Публикация отключена. /nova_build'),
                           'locked-build-job-'+str(job['id']),job['id'])
            elif result.get('nova_release_ci_id'):
                send_event(conn,'info' if result['test_status']=='passed' else 'critical',
                           'Репетиция выпуска NOVA проверена' if result['test_status']=='passed' else 'Репетиция NOVA не прошла',
                           f"{result['ci_url']}. "+('34 теста NOVA и15 проверок HTTP/PostgreSQL. Возврат старого кода сохранил тестовые данные новой версии. Это не откат Render. Настройка /health, закрепление зависимостей, доступность сборки и согласование ещё нужны. Публикация отключена. /nova_release' if result['test_status']=='passed' else 'CI не прошёл. Сохранность данных при возврате версии не подтверждена. Публикация отключена. /nova_release'),
                           'nova-release-job-'+str(job['id']),job['id'])
            elif result.get('browser_candidate_id'):
                send_event(conn,'info' if result['test_status']=='passed' else 'critical',
                           'Исправления интерфейса NOVA проверены' if result['test_status']=='passed' else 'Черновик NOVA не прошёл проверки',
                           f"{result['ci_url']}. "+('Draft PR15: подсказки RU/UZ, кнопки44px и положение на мобильном экране. Chromium:34 проверки,15 снимков. API подставной; публикации не было. /nova_candidate' if result['test_status']=='passed' else 'CI не прошёл. Исправления, тесты и снимки не подтверждены. /nova_candidate'),
                           'browser-candidate-job-'+str(job['id']),job['id'])
            elif result.get('browser_ci_id'):
                send_event(conn,'info' if result['test_status']=='passed' else 'critical',
                           'Браузерный CI NOVA сверен' if result['test_status']=='passed' else 'Браузерный CI NOVA не прошёл',
                           f"{result['ci_url']}. "+('Chromium:27 проверок,15 снимков. API подставной, реальных заявок нет. Два замечания: подсказки UZ и размер кнопок языка. /nova_browser' if result['test_status']=='passed' else 'CI не прошёл. Тесты и снимки не подтверждены. /nova_browser'),
                           'browser-ci-job-'+str(job['id']),job['id'])
            elif result.get('nova_ci_id'):
                send_event(conn,'info' if result['test_status']=='passed' else 'critical',
                           'PostgreSQL-тесты NOVA: CI сверен' if result['test_status']=='passed' else 'PostgreSQL-тесты NOVA: CI не прошёл',
                           f"{result['ci_url']}. Версия NOVA {result['revision']}. Тесты: {result['test_status']}, {result['test_counts']}. Исполнение на временном GitHub runner и отдельном PostgreSQL16; VPS сверяет отчёт. Рабочая база и Inventory не изменялись. /nova_pg",
                           'nova-ci-job-'+str(job['id']),job['id'])
            elif result.get('project_test_id'):
                send_event(conn,'info' if result['test_status']=='passed' else 'critical',
                           'Проверки NOVA WEB завершены' if result['test_status']=='passed' else 'Проверки NOVA WEB не прошли',
                           f"Отчёт #{result['project_test_id']}, версия {result['revision']}. Тесты: {result['test_status']}; {result['test_counts']}. PostgreSQL и браузер не проверялись. Исходники, рабочий сайт и Inventory не изменялись.",
                           'project-test-'+str(job['id'])+'-'+result['source_digest'],job['id'])
            elif job["kind"]=="check_site":
                result=health_incidents.complete(conn,job,result,observed_at=end)
            elif job["kind"]=="daily_report":
                metrics=result["report"]
                seconds=sum(row["seconds"] for row in metrics["measured_seconds"] if row["category"] in ("active","testing"))
                send_event(conn,"info","Суточный отчёт ULTIMATE",
                           f"Измеренная работа: {seconds:.1f} сек. Завершено: {metrics['events'].get('succeeded',0)}. Состояния: {metrics['current_states']}. Учтено API: ${result['budget']['accounted_usd']:.4f}. Только реально измеренные интервалы.",
                           "daily-job-"+str(job["id"]),job["id"])
            elif result.get("syntax_errors"):
                send_event(conn,"critical","Ошибки синтаксиса ULTIMATE",str(result["syntax_errors"])[:500],"syntax-job-"+str(job["id"]),job["id"])
            if result.get('test_status') not in (None,'passed'):
                if not result.get('artifact_id') and not result.get('project_test_id') and not result.get('nova_ci_id') and not result.get('browser_ci_id') and not result.get('browser_candidate_id') and not result.get('nova_release_ci_id') and not result.get('locked_build_ci_id'):
                    send_event(conn,'critical','Изолированные тесты не прошли',result['test_status'],
                               'test-failed-'+str(job['id']),job['id'])
                conn.execute('UPDATE agent_jobs SET result=? WHERE id=?',(json.dumps(result),job['id']))
                conn.commit()
                queue.fail(conn,job['id'],job['lease_token'],'isolated_tests_'+result['test_status'],retryable=False)
                return {'id':job['id'],'state':'failed'}
            if result.get('tests_pending'):
                child=queue.finish_with_test(conn,job['id'],job['lease_token'],result,
                      {'target':'developer-bundle','generation_job_id':job['id'],'source_digest':result['source_digest']},
                      event_key='developer-test:'+str(job['id'])+':'+result['source_digest'])
                result['followup_job_id']=child
            elif job['kind']!='check_site' and not result.get('resource_sample_id'):
                queue.finish(conn,job["id"],job["lease_token"],result,awaiting_owner=waiting)
            conn.execute("UPDATE agent_worker_status SET heartbeat=?,state=?,detail=? WHERE worker=?",(time.time(),"waiting_owner" if waiting else "idle",str(job["id"]),WORKER))
            conn.commit()
        return {"id":job["id"],"state":"awaiting_owner" if waiting else "succeeded"}
    except (artifact_pr_client.Pending,artifact_pr_client.Blocked) as exc:
        with connect(path) as conn:
            record_failed_interval(conn,job,start,tick)
            queue.fail(conn,job['id'],job['lease_token'],str(exc),retryable=isinstance(exc,artifact_pr_client.Pending))
            failed=conn.execute('SELECT state FROM agent_jobs WHERE id=?',(job['id'],)).fetchone()[0]=='failed'
            if failed:
                browser_check=job['kind']=='test_release' and job['payload'] in ({'target':browser_ci.PROFILE},{'target':browser_candidate_ci.PROFILE})
                ci_check=job['kind']=='test_release' and job['payload']=={'target':nova_ci.PROFILE}
                rehearsal_check=job['kind']=='test_release' and job['payload']=={'target':nova_release_ci.PROFILE}
                locked_check=job['kind']=='test_release' and job['payload']=={'target':locked_build_ci.PROFILE}
                copy_check=job['kind']=='test_release' and job['payload']=={'target':nova_private_copy_ci.PROFILE}
                recovery_check=job['kind']=='test_release' and job['payload']=={'target':nova_recovery_ci.PROFILE}
                plan_check=job['kind']=='test_release' and job['payload']=={'target':nova_deploy.PROFILE}
                send_event(conn,'critical','Сверка приватной копии остановлена' if copy_check else 'Сверка восстановления остановлена' if recovery_check else 'Проверка плана выпуска остановлена' if plan_check else 'Сверка закреплённой сборки остановлена' if locked_check else 'Сверка репетиции выпуска остановлена' if rehearsal_check else 'Сверка браузерного CI остановлена' if browser_check else 'Сверка PostgreSQL CI остановлена' if ci_check else 'Подготовка Draft PR остановлена',
                           'Требуется проверка доступа, исходной версии или CI. Сохранённый запрос оставлен для сверки; merge и публикации нет.',
                           ('nova-private-copy-stopped-' if copy_check else 'nova-recovery-stopped-' if recovery_check else 'nova-deploy-plan-stopped-' if plan_check else 'locked-build-stopped-' if locked_check else 'nova-release-stopped-' if rehearsal_check else 'browser-ci-stopped-' if browser_check else 'nova-ci-stopped-' if ci_check else 'artifact-pr-stopped-')+str(job['id']),job['id'])
        return {'id':job['id'],'state':'failed' if failed else 'queued'}
    except emergency.Stopped as exc:
        with connect(path) as conn:
            record_failed_interval(conn,job,start,tick)
            queue.finish(conn,job['id'],job['lease_token'],{'blocked':str(exc),'implemented':False,'published':False,'needs_owner_review':True},awaiting_owner=True)
        return {'id':job['id'],'state':'awaiting_owner','error':str(exc)}
    except project_registry.RepositoryScopeError as exc:
        with connect(path) as conn:
            record_failed_interval(conn,job,start,tick)
            queue.fail(conn,job['id'],job['lease_token'],str(exc),retryable=False)
            send_event(conn,'critical','Проверка репозитория остановлена',
                       'Источник не соответствует разрешённому проекту, версии или хешам. Код не запускался; данные других проектов не изменялись.',
                       'repository-scope-'+str(job['id']),job['id'])
        return {'id':job['id'],'state':'failed','error':'RepositoryScopeError'}
    except (SandboxUnavailable,FileNotFoundError,model_broker.BrokerFailed,ArtifactRecoveryBlocked) as exc:
        with connect(path) as conn:
            record_failed_interval(conn,job,start,tick)
            reason=str(exc) if isinstance(exc,(model_broker.BrokerFailed,ArtifactRecoveryBlocked)) else type(exc).__name__
            send_event(conn,'critical','Посредник или изолированный исполнитель остановлен',reason,
                       'sandbox-unavailable-'+str(job['id']),job['id'])
            queue.fail(conn,job['id'],job['lease_token'],type(exc).__name__,retryable=False)
        return {'id':job['id'],'state':'failed','error':type(exc).__name__}
    except Exception as exc:
        with connect(path) as conn:
            record_failed_interval(conn,job,start,tick)
            queue.fail(conn,job["id"],job["lease_token"],type(exc).__name__)
            state=conn.execute('SELECT state FROM agent_jobs WHERE id=?',(job['id'],)).fetchone()[0]
            if state=='failed':
                send_event(conn,'critical','Задача исчерпала попытки',type(exc).__name__,
                           'job-exhausted-'+str(job['id']),job['id'])
        return {"id":job["id"],"state":state,"error":type(exc).__name__}


def apply_limits():
    import resource
    # Keep the worker's soft cap. Only the reviewed Node child raises its own limit
    # to this hard ceiling; the Python sandbox still lowers both limits to320MiB.
    resource.setrlimit(resource.RLIMIT_AS,(384*1024*1024,768*1024*1024))
    resource.setrlimit(resource.RLIMIT_NOFILE,(128,128))
    os.nice(10)


def main():
    import sys
    if sys.argv[1:]!=["--loop"]: raise SystemExit("Usage: queue_worker.py --loop")
    path=Path(os.environ["DB_PATH"]).resolve()
    expected=Path.home()/".ultimate-review-data/live/control.db"
    if path!=expected or not path.is_file(): raise SystemExit("Only the existing ULTIMATE database is enabled")
    apply_limits()
    with connect(path) as conn: initialize(conn)
    stopping=False
    def stop(*args):
        nonlocal stopping
        stopping=True
    def timed_out(*args): raise TimeoutError("job exceeded 30 seconds")
    signal.signal(signal.SIGTERM,stop)
    signal.signal(signal.SIGINT,stop)
    signal.signal(signal.SIGALRM,timed_out)
    while not stopping:
        try:
            signal.alarm(30)
            run_once(path)
        except Exception as exc: print("queue_tick_error="+type(exc).__name__,flush=True)
        finally: signal.alarm(0)
        for _ in range(5):
            if stopping: break
            time.sleep(1)


if __name__=="__main__": main()
