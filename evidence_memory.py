"""Append-only, source-linked observations of committed work; never instructions/approval.

Only typed facts are copied. Task text, error details, test output, tokens, source files
and private URLs stay out of this index. Hashes detect changed/missing journal evidence;
they do not authenticate a database against an administrator who can rewrite it.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import math
import re
import time
import task_queue as queue
import project_registry
import acceptance_checks

EVENTS = {'succeeded','awaiting_owner','failed','cancelled','retry_scheduled','lease_expired'}
PAGE_SIZE = 5
STATES = {'succeeded':'задание завершено','awaiting_owner':'ожидает решения; выполнение не подтверждено',
          'failed':'ошибка','cancelled':'отменено','retry_scheduled':'назначен повтор',
          'lease_expired':'истекла аренда исполнителя'}
SOURCE_STATES = {'passed','failed','timeout','output_limit'}


def initialize(conn):
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS project_evidence_memory(
      id INTEGER PRIMARY KEY,project TEXT NOT NULL,event_id INTEGER NOT NULL UNIQUE,
      observed_at REAL NOT NULL,recorded_at REAL NOT NULL,fact TEXT NOT NULL,
      reference TEXT NOT NULL,source_sha256 TEXT NOT NULL,entry_sha256 TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS project_evidence_page ON project_evidence_memory(project,id DESC);
    CREATE TABLE IF NOT EXISTS project_evidence_cursor(
      singleton INTEGER PRIMARY KEY CHECK(singleton=1),event_id INTEGER NOT NULL);
    INSERT OR IGNORE INTO project_evidence_cursor VALUES(1,0);
    CREATE TRIGGER IF NOT EXISTS project_evidence_no_update BEFORE UPDATE ON project_evidence_memory
      BEGIN SELECT RAISE(ABORT,'project evidence is append-only'); END;
    CREATE TRIGGER IF NOT EXISTS project_evidence_no_delete BEFORE DELETE ON project_evidence_memory
      BEGIN SELECT RAISE(ABORT,'project evidence is append-only'); END;
    ''')
    conn.commit()


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def decode(raw):
    if not isinstance(raw,str) or len(raw.encode())>256000: return None
    try:
        value=json.loads(raw)
        return value if isinstance(value,dict) else None
    except (ValueError,RecursionError): return None


def sha(value):
    return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None


def evidence(conn,reference):
    """Re-read only explicitly referenced SQLite rows, never files or network sources."""
    if (not isinstance(reference,dict) or set(reference)-{'event_id','job_id','artifact_id','project_test_id','artifact_pr_id','release_check_id','resource_sample_id','result'}
            or type(reference.get('event_id')) is not int or type(reference.get('job_id')) is not int):
        raise ValueError('invalid memory reference')
    event=conn.execute('SELECT id,job_id,at,event,detail FROM agent_job_events WHERE id=?',
                       (reference['event_id'],)).fetchone()
    job=conn.execute('SELECT id,project,kind,payload FROM agent_jobs WHERE id=?',
                     (reference['job_id'],)).fetchone()
    if not event or not job or event[1]!=job[0] or job[1] not in queue.PROJECTS:
        raise ValueError('memory source absent or out of scope')
    source={'event':event,'job':job}
    if 'artifact_id' in reference:
        if type(reference['artifact_id']) is not int: raise ValueError('invalid artifact reference')
        artifact=conn.execute('''SELECT id,job_id,attempt,project,engine,source_digest,manifest,
            test_status,test_report,created_at FROM code_artifacts WHERE id=?''',
            (reference['artifact_id'],)).fetchone()
        if not artifact or artifact[1]!=job[0] or artifact[3]!=job[1]:
            raise ValueError('artifact belongs to another job or project')
        source['artifact']=artifact
    if 'project_test_id' in reference:
        if type(reference['project_test_id']) is not int: raise ValueError('invalid project test reference')
        run=conn.execute('''SELECT id,job_id,attempt,project,profile,revision,source_digest,report,report_sha256,created_at
            FROM project_test_runs WHERE id=?''',(reference['project_test_id'],)).fetchone()
        if not run or run[1]!=job[0] or run[3]!=job[1]: raise ValueError('project test belongs to another job or project')
        source['project_test']=run
    if 'artifact_pr_id' in reference:
        import artifact_prs
        identity,remote,_=artifact_prs.record(conn,reference['artifact_pr_id'])
        payload=decode(job[3])
        if job[1]!='control' or not payload or payload.get('artifact_pr')!=identity['artifact_id']:
            raise ValueError('PR belongs to another job or project')
        source['artifact_pr']={'identity':identity,'remote':{k:v for k,v in remote.items() if k!='checked_at'}}
    if 'release_check_id' in reference:
        row=conn.execute('SELECT job_id,report,report_sha256 FROM artifact_release_checks WHERE id=?',(reference['release_check_id'],)).fetchone()
        import artifact_prs
        if not row or row[0]!=job[0] or job[1]!='control' or artifact_prs.digest(json.loads(row[1]))!=row[2]:
            raise ValueError('release check belongs to another job or changed')
        source['release_check']=row
    if 'resource_sample_id' in reference:
        import vps_resources
        row=conn.execute('SELECT job_id,sample,report,report_sha256 FROM vps_resource_samples WHERE id=?',(reference['resource_sample_id'],)).fetchone()
        if not row or row[0]!=job[0] or job[1]!='control' or vps_resources.digest(json.loads(row[2]))!=row[3]:
            raise ValueError('resource sample source changed or outside scope')
        source['resource_sample']=row
    if reference.get('result') is True:
        source['result']=conn.execute('SELECT result FROM agent_jobs WHERE id=?',(job[0],)).fetchone()[0]
    elif 'result' in reference:
        raise ValueError('invalid result reference')
    return source


def observation(conn,event):
    event_id,job_id,at,transition,_=event
    if transition not in EVENTS or type(at) not in (int,float) or not math.isfinite(at): return None
    job=conn.execute('SELECT project,kind,state,payload,result FROM agent_jobs WHERE id=?',(job_id,)).fetchone()
    if not job or job[0] not in queue.PROJECTS or job[1] not in queue.KINDS: return None
    project,kind,state,payload,raw=job
    reference={'event_id':event_id,'job_id':job_id}
    fact={'event':transition,'job_kind':kind}
    # Current results can substantiate this event only while it is the matching terminal
    # observation. Historical transitions remain history without borrowing a later result.
    if state==transition and transition in {'succeeded','awaiting_owner','failed'}:
        result=decode(raw)
        if result and kind in {'review_change','test_release'} and project=='control':
            ident=result.get('artifact_id')
            if type(ident) is int and ident>0:
                row=conn.execute('''SELECT job_id,project,source_digest,test_status,test_report,engine
                    FROM code_artifacts WHERE id=?''',(ident,)).fetchone()
                report=decode(row[4]) if row else None
                if (row and row[:2]==(job_id,project) and sha(row[2]) and report and
                        result.get('source_digest')==row[2]==report.get('source_digest') and
                        row[3] in SOURCE_STATES and result.get('test_status')==row[3]==report.get('status') and
                        row[5] in {'deterministic_recipe','offline_broker_demo','openai_broker'}):
                    artifact={'id':ident,'source_digest':row[2],'test_status':row[3],
                              'engine':row[5],'publication_verified':False}
                    checks=report.get('independent_acceptance')
                    if isinstance(checks,dict) and checks.get('status') in SOURCE_STATES|{'not_run'}:
                        profile=checks.get('profile')
                        try: expected=acceptance_checks.harness_sha256(profile)
                        except (ValueError,KeyError,TypeError): expected=None
                        if (expected and checks.get('harness_sha256')==expected and
                                checks.get('candidate_source_digest')==row[2]):
                            artifact['independent_acceptance']={
                                'profile':profile,'harness_sha256':expected,'status':checks['status']}
                    fact['artifact']=artifact
                    reference.update(artifact_id=ident,result=True)
        if result and kind=='inspect_repository' and state=='succeeded':
            try: project_registry.check_scope(project,decode(payload))
            except project_registry.RepositoryScopeError: pass
            else:
                if project_registry.valid_result(project,result):
                    fact['repository']={key:result[key] for key in
                        ('revision','source_digest','code_executed','tests_executed','published')}
                    reference['result']=True
        if result and kind=='test_release' and project=='nova' and type(result.get('project_test_id')) is int:
            import nova_project_tests as tests
            ident=result['project_test_id']
            row=conn.execute('''SELECT job_id,project,source_digest,report,report_sha256 FROM project_test_runs WHERE id=?''',(ident,)).fetchone()
            report=decode(row[3]) if row else None
            if (row and row[:2]==(job_id,project) and report and
                    result.get('source_digest')==row[2] and tests.valid_report(report,row[2]) and
                    result.get('test_status')==report['status'] and hashlib.sha256(row[3].encode()).hexdigest()==row[4]):
                fact['project_test']={key:report[key] for key in
                    ('profile','revision','source_digest','test_counts','database_integration','browser_test','published')}
                reference.update(project_test_id=ident,result=True)
        if result and kind=='review_change' and project=='control' and type(result.get('artifact_pr_id')) is int:
            import artifact_prs
            identity,remote,_=artifact_prs.record(conn,result['artifact_pr_id'])
            if (remote.get('verified') is True and result.get('head_sha')==remote.get('head_sha') and
                    result.get('ci_state')==remote.get('ci_state') and result.get('source_digest')==identity['source_digest']):
                fact['artifact_pr']={key:result[key] for key in ('pr_url','head_sha','base_sha','source_digest','ci_state','published')}
                reference.update(artifact_pr_id=result['artifact_pr_id'],result=True)
        if result and kind=='review_change' and project=='control' and type(result.get('release_check_id')) is int:
            import artifact_prs
            row=conn.execute('SELECT job_id,report,report_sha256 FROM artifact_release_checks WHERE id=?',(result['release_check_id'],)).fetchone()
            if row and row[0]==job_id and artifact_prs.digest(json.loads(row[1]))==row[2]==result.get('report_sha256'):
                report=json.loads(row[1])
                if report.get('publish_allowed') is False:
                    fact['release_check']={'head_sha':report['scope']['head_sha'],'approval_state':report['approval_state'],'published':False}
                    reference.update(release_check_id=result['release_check_id'],result=True)
        if result and kind=='inspect_repository' and project=='control' and type(result.get('resource_sample_id')) is int:
            import vps_resources
            row=conn.execute('SELECT job_id,report,report_sha256 FROM vps_resource_samples WHERE id=?',(result['resource_sample_id'],)).fetchone()
            if row and row[0]==job_id and vps_resources.digest(json.loads(row[1]))==row[2]==result.get('report_sha256'):
                report=json.loads(row[1])
                fact['resource_sample']={'observed_at':report['observed_at'],'grades':report['grades'],'read_only':True}
                reference.update(resource_sample_id=result['resource_sample_id'],result=True)
    return project,at,fact,reference


def sync(conn,limit=80):
    """Bounded catch-up from committed events; cursor and append commit or roll back together.

    The operations worker calls this even while paused. It neither executes the remembered
    task nor creates retries, notifications or schedules. An interrupted batch is replayable.
    """
    if type(limit) is not int or not 1<=limit<=200: raise ValueError('invalid memory batch size')
    scanned=added=0
    with queue._write(conn):
        cursor=conn.execute('SELECT event_id FROM project_evidence_cursor WHERE singleton=1').fetchone()[0]
        rows=conn.execute('SELECT id,job_id,at,event,detail FROM agent_job_events WHERE id>? ORDER BY id LIMIT ?',
                          (cursor,limit)).fetchall()
        for event in rows:
            scanned+=1
            item=observation(conn,event)
            if item:
                project,at,fact,reference=item
                fingerprint=digest(evidence(conn,reference))
                entry=digest([project,at,fact,reference,fingerprint])
                added+=conn.execute('''INSERT OR IGNORE INTO project_evidence_memory(
                    project,event_id,observed_at,recorded_at,fact,reference,source_sha256,entry_sha256)
                    VALUES(?,?,?,?,?,?,?,?)''',
                    (project,event[0],at,time.time(),canonical(fact),canonical(reference),fingerprint,entry)).rowcount
            cursor=event[0]
        conn.execute('UPDATE project_evidence_cursor SET event_id=? WHERE singleton=1',(cursor,))
    return {'scanned':scanned,'added':added,'cursor':cursor}


@contextmanager
def snapshot(conn):
    conn.execute('SAVEPOINT memory_read')
    try: yield
    except Exception:
        conn.execute('ROLLBACK TO memory_read')
        raise
    finally: conn.execute('RELEASE memory_read')


def checked(conn,row):
    ident,project,at,raw,ref,source_hash,entry_hash=row
    try:
        fact,reference=decode(raw),decode(ref)
        if (not fact or not reference or digest([project,at,fact,reference,source_hash])!=entry_hash
                or digest(evidence(conn,reference))!=source_hash): return None
        return fact,reference
    except (ValueError,TypeError,KeyError,RecursionError): return None


def project_name(conn,project):
    if not isinstance(project,str) or not conn.execute('SELECT 1 FROM project_memory WHERE project=? AND project!=?',(project,'policy')).fetchone():
        raise ValueError('Память проекта не найдена.')


def summary(conn,project,page=1):
    project_name(conn,project)
    if type(page) is not int or not 1<=page<=1000000: raise ValueError('Нужна допустимая страница.')
    with snapshot(conn):
        total=conn.execute('SELECT count(*) FROM project_evidence_memory WHERE project=?',(project,)).fetchone()[0]
        pages=max(1,(total+PAGE_SIZE-1)//PAGE_SIZE)
        if page>pages: return f'Такой страницы нет. Страниц: {pages}.'
        cursor=conn.execute('SELECT event_id FROM project_evidence_cursor WHERE singleton=1').fetchone()[0]
        tail=conn.execute('SELECT COALESCE(max(id),0) FROM agent_job_events').fetchone()[0]
        lines=[f'📚 История проекта {project} · {page}/{pages}',
               f'Сохранено наблюдений: {total}. Журнал обработан до события {cursor}/{tail}.']
        rows=conn.execute('''SELECT id,project,observed_at,fact,reference,source_sha256,entry_sha256
            FROM project_evidence_memory WHERE project=? ORDER BY id DESC LIMIT ? OFFSET ?''',
            (project,PAGE_SIZE,(page-1)*PAGE_SIZE)).fetchall()
        for row in rows:
            proof=checked(conn,row)
            if proof is None:
                lines.append(f'\n#{row[0]} · источник изменён или отсутствует; нужна повторная проверка.')
                continue
            fact,reference=proof
            stamp=datetime.fromtimestamp(row[2],timezone.utc).strftime('%d.%m %H:%M UTC')
            lines.append(f'\n#{row[0]} · {stamp} · /job {reference["job_id"]}: '+STATES[fact['event']])
            if fact.get('artifact'):
                artifact=fact['artifact']
                lines.append(f'Черновик #{artifact["id"]}: тесты {artifact["test_status"]}; публикация не подтверждена.')
            if fact.get('repository'): lines.append('Файлы закреплённой версии прочитаны; код и тесты не запускались.')
            if fact.get('project_test'): lines.append('Выполнен выбранный набор тестов Node; PostgreSQL и браузер не проверялись. /nova_tests')
            if fact.get('resource_sample'): lines.append('Сохранён замер ресурсов VPS; история не подтверждает текущее состояние. /vps4')
            if fact.get('release_check'): lines.append('Проверка перед выпуском сохранена; это исторический отчёт, публикация отключена. /release_checks')
            if fact.get('artifact_pr'): lines.append('Draft PR сверён с артефактом и точным CI; публикации нет. /artifact_prs')
            lines.append(f'Основание: событие {reference["event_id"]}. /memory_item {row[0]}')
        if not rows: lines.append('Наблюдений пока нет. Исходные требования: /memory '+project)
        if page<pages: lines.append(f'\nДальше: /memory_log {project} {page+1}')
        lines.append('\nЭто история наблюдений, не разрешение повторять действия или публиковать. Бизнес-правила не переписываются.')
        return '\n'.join(lines)


def detail(conn,ident):
    if type(ident) is not int or not 1<=ident<=9223372036854775807: raise ValueError('Нужен положительный номер.')
    with snapshot(conn):
        row=conn.execute('''SELECT id,project,observed_at,fact,reference,source_sha256,entry_sha256
            FROM project_evidence_memory WHERE id=?''',(ident,)).fetchone()
        if not row: return 'Запись памяти не найдена.'
        proof=checked(conn,row)
        if proof is None: return 'Источник записи изменён или отсутствует. Факт требует повторной проверки; прежняя запись сохранена.'
        fact,reference=proof
        current=conn.execute('SELECT state FROM agent_jobs WHERE id=?',(reference['job_id'],)).fetchone()[0]
        return (f'Память #{ident} · {row[1]}\nИсторическое наблюдение: '+STATES[fact['event']]
                +f'\nТекущее состояние задачи: {current}\n/job {reference["job_id"]} · событие {reference["event_id"]}'
                +'\n'+json.dumps(fact,ensure_ascii=False,indent=2)
                +'\nSHA-256 основания: '+row[5]
                +'\nСверено с журналом SQLite. Исходные файлы сейчас не перечитывались. Запись не разрешает публикацию, оплату или повторное исполнение.')
