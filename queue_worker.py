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
from isolated_python import run_bundle, SandboxUnavailable
from sandbox_smoke import FILES as SANDBOX_SMOKE
from owner_notifications import initialize as init_inbox,create as notify
from chat_binding import action as chat_action

ROOT=Path(__file__).resolve().parent
TARGETS={"nova":"https://novaweb.uz/"}
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


def record_failed_interval(conn,job,start,tick):
    end=start+max(0.000001,time.monotonic()-tick)
    prior=conn.execute('SELECT MAX(ended_at) FROM agent_work_spans WHERE job_id=? AND attempt=?',(job['id'],job['attempt'])).fetchone()[0]
    begin=max(start,prior or start)
    if begin>=end: return
    try:
        queue.add_work_span(conn,job['id'],job['lease_token'],
                            'testing' if job['kind'] in ('test_release','review_change') else 'active',
                            begin,end,now=max(time.time(),end))
    except PermissionError:
        pass  # Expired work is never assigned to another worker's lease.


def run_once(path,root=ROOT,site_checker=check_site):
    with connect(path) as conn:
        scheduler.tick(conn)
        conn.execute("INSERT INTO agent_worker_status VALUES(?,?,?,?) ON CONFLICT(worker) DO UPDATE SET heartbeat=excluded.heartbeat,state=excluded.state,detail=excluded.detail",(WORKER,time.time(),"idle",""))
        conn.commit()
        job=queue.claim(conn,WORKER,queue.KINDS,lease_seconds=60)
    if not job: return None
    start=time.time()
    tick=time.monotonic()
    result=None
    waiting=False
    try:
        if job["kind"]=="check_site": result=site_checker(job["payload"])
        elif job["kind"]=="inspect_repository": result=inspect_source(job["payload"],root)
        elif job["kind"]=="test_release" and job['payload'].get('target')=='sandbox-smoke':
            policy=Path(path).parent/'sandbox-policy.json'
            report=run_bundle(SANDBOX_SMOKE,policy,timeout=10)
            result={'test_status':report['status'],'backend':report['backend'],'test_elapsed_seconds':report['elapsed_seconds'],
                    'source_digest':report['source_digest'],'output':report['output'][-4000:],'network':False,'writable_tmp':report['writable_tmp']}
        elif job["kind"]=="review_change" and job['payload'].get('recipe'):
            with connect(path) as conn:
                result=offline_developer.prepare(conn,job,Path(path).parent/'artifacts',Path(path).parent/'sandbox-policy.json')
            waiting=result['test_status']=='passed'
        elif job["kind"]=="daily_report":
            with connect(path) as conn:
                result={"report":queue.report(conn,start-86400,start),"budget":budget_gate.summary(conn)}
        else:
            # A free text request is accepted but not falsely marked as implemented.
            waiting=True
            result={"blocked":"isolated_ai_executor_not_configured","task":job["payload"],"implemented":False,
                    "next":"Continue implementing the budgeted provider and isolated developer/tester pipeline"}
        end=start+max(0.000001,time.monotonic()-tick)
        # Record only the measured handler interval. Time waiting in the queue is not work.
        with connect(path) as conn:
            category='testing' if job['kind'] in ('test_release','review_change') else 'active'
            queue.add_work_span(conn,job["id"],job["lease_token"],category,start,end,now=max(time.time(),end))
            if waiting and result.get('blocked'):
                send_event(conn,"decision","Нужен исполнитель для текстовых задач",
                           "Задачи сохранены. Платный провайдер с API-ключом и изолированный AI-разработчик ещё не подключены. Ключ нужно настраивать приватно на VPS. Мониторинг и независимые проверки продолжаются.",
                           "runtime-needs-ai-executor-v4",job["id"])
            elif result.get('artifact_id'):
                send_event(conn,'decision' if result['test_status']=='passed' else 'critical',
                           'Кодовый черновик проверен' if result['test_status']=='passed' else 'Проверка кодового черновика не прошла',
                           f"Артефакт #{result['artifact_id']}, SHA-256 {result['source_digest']}. Тесты: {result['test_status']}. Просмотр: /artifact {result['artifact_id']}. Движок: детерминированный рецепт без LLM. Исходники и отчёт сохранены; публикации не было.",
                           'artifact-'+str(job['id'])+'-'+result['source_digest'],job['id'])
            elif job["kind"]=="check_site":
                old=conn.execute("SELECT healthy FROM agent_health WHERE target=?",(result["target"],)).fetchone()
                if (old is None and not result["healthy"]) or (old and bool(old[0])!=result["healthy"]):
                    send_event(conn,"info" if result["healthy"] else "critical","Состояние NOVA WEB изменилось",
                               result["url"]+": "+result["detail"],"health-job-"+str(job["id"]),job["id"])
                conn.execute("INSERT INTO agent_health VALUES(?,?,?,?) ON CONFLICT(target) DO UPDATE SET healthy=excluded.healthy,detail=excluded.detail,checked_at=excluded.checked_at",(result["target"],int(result["healthy"]),result["detail"],time.time()))
                conn.commit()
            elif job["kind"]=="daily_report":
                metrics=result["report"]
                seconds=sum(row["seconds"] for row in metrics["measured_seconds"] if row["category"] in ("active","testing"))
                send_event(conn,"info","Суточный отчёт ULTIMATE",
                           f"Измеренная работа: {seconds:.1f} сек. Завершено: {metrics['events'].get('succeeded',0)}. Состояния: {metrics['current_states']}. Учтено API: ${result['budget']['accounted_usd']:.4f}. Только реально измеренные интервалы.",
                           "daily-job-"+str(job["id"]),job["id"])
            elif result.get("syntax_errors"):
                send_event(conn,"critical","Ошибки синтаксиса ULTIMATE",str(result["syntax_errors"])[:500],"syntax-job-"+str(job["id"]),job["id"])
            if result.get('test_status') not in (None,'passed'):
                if not result.get('artifact_id'):
                    send_event(conn,'critical','Изолированные тесты не прошли',result['test_status'],
                               'test-failed-'+str(job['id']),job['id'])
                conn.execute('UPDATE agent_jobs SET result=? WHERE id=?',(json.dumps(result),job['id']))
                conn.commit()
                queue.fail(conn,job['id'],job['lease_token'],'isolated_tests_'+result['test_status'],retryable=False)
                return {'id':job['id'],'state':'failed'}
            queue.finish(conn,job["id"],job["lease_token"],result,awaiting_owner=waiting)
            conn.execute("UPDATE agent_worker_status SET heartbeat=?,state=?,detail=? WHERE worker=?",(time.time(),"waiting_owner" if waiting else "idle",str(job["id"]),WORKER))
            conn.commit()
        return {"id":job["id"],"state":"awaiting_owner" if waiting else "succeeded"}
    except (SandboxUnavailable,FileNotFoundError) as exc:
        with connect(path) as conn:
            record_failed_interval(conn,job,start,tick)
            send_event(conn,'critical','Изолированный исполнитель недоступен',type(exc).__name__,
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
    resource.setrlimit(resource.RLIMIT_AS,(384*1024*1024,384*1024*1024))
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
