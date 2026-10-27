"""Read-only public GitHub main-ref observations; pins/tests/production never advance here."""
from datetime import datetime,timezone,timedelta
import hashlib
import json
import math
import re
import time
import urllib.error
import urllib.request
import emergency_control as emergency
import owner_notifications as inbox
import project_registry as registry
import task_queue as q
import roadmap

PROFILE='repository-head-v1'
INTERVAL=21600
FRESH=2*INTERVAL
ERRORS={'http_403','http_404','http_429','http_other','network','deadline','invalid_json','oversize','response','identity','ref'}

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
def digest(value):return hashlib.sha256(canonical(value).encode()).hexdigest()
def sha(value):return isinstance(value,str) and re.fullmatch('[0-9a-f]{40}',value) is not None

def initialize(conn):
    conn.executescript('''CREATE TABLE IF NOT EXISTS repository_head_runs(
      id INTEGER PRIMARY KEY,job_id INTEGER NOT NULL UNIQUE,project TEXT NOT NULL,report TEXT NOT NULL,
      report_sha256 TEXT NOT NULL,created_at REAL NOT NULL);
    CREATE TABLE IF NOT EXISTS repository_head_state(
      project TEXT PRIMARY KEY,run_id INTEGER NOT NULL,observed_at REAL NOT NULL,signature TEXT NOT NULL,
      generation INTEGER NOT NULL,notice_id INTEGER);
    CREATE TRIGGER IF NOT EXISTS repository_head_no_update BEFORE UPDATE ON repository_head_runs
      BEGIN SELECT RAISE(ABORT,'repository observations are immutable'); END;
    CREATE TRIGGER IF NOT EXISTS repository_head_no_delete BEFORE DELETE ON repository_head_runs
      BEGIN SELECT RAISE(ABORT,'repository observations are immutable'); END;''');conn.commit()


def payload(project):
    if project not in registry.REPOSITORIES:raise registry.RepositoryScopeError('repository head scope denied; Inventory protected')
    return {'target':PROFILE,'project':project}

def scope(job):
    project=job.get('project')
    if job.get('kind')!='inspect_repository' or job.get('payload')!=payload(project):raise registry.RepositoryScopeError('repository head job scope denied')
    return project,registry.REPOSITORIES[project]

def schedule_name(project):payload(project);return 'repo-head-'+project+'-v1'

def seed(conn,*,now=None):
    now=q._now(now)
    with q._write(conn):
        require_enabled(conn)
        for project in registry.REPOSITORIES:
            raw=q._json(payload(project));name=schedule_name(project)
            conn.execute('INSERT OR IGNORE INTO agent_schedules VALUES(?,?,?,?,?,?,1)',(name,project,'inspect_repository',raw,INTERVAL,now+INTERVAL))
            row=conn.execute('SELECT project,kind,payload,interval_seconds FROM agent_schedules WHERE name=?',(name,)).fetchone()
            if row!=(project,'inspect_repository',raw,INTERVAL):raise ValueError('unknown repository head schedule; no override')

def require_enabled(conn):
    if roadmap.setting(conn,'repo_head_gate','disabled')!='enabled':raise registry.RepositoryScopeError('repository head admission disabled')

def _enqueue(conn,project,key,now):
    raw=q._json(payload(project));old=conn.execute('SELECT id,project,kind,payload FROM agent_jobs WHERE event_key=?',(key,)).fetchone()
    if old:
        if old[1:]!=(project,'inspect_repository',raw):raise ValueError('repository head event conflict')
        return old[0]
    ident=conn.execute("INSERT INTO agent_jobs(project,kind,payload,event_key,priority,max_attempts,created_at,available_at,updated_at) VALUES(?,'inspect_repository',?,?,50,1,?,?,?)",(project,raw,key,now,now,now)).lastrowid
    q._event(conn,ident,now,'queued');return ident

def enqueue(conn,project,*,now=None):
    payload(project);now=q._now(now)
    with q._write(conn):
        require_enabled(conn);return _enqueue(conn,project,f'repo-head-manual:{project}:{int(now//900)}',now)

def tick(conn,now):
    now=q._now(now);ids=[]
    with q._write(conn):
        if roadmap.setting(conn,'repo_head_gate','disabled')!='enabled' or emergency.state(conn)['latched'] or conn.execute('SELECT paused FROM agent_queue_control').fetchone()[0]:return []
        for project in registry.REPOSITORIES:
            name=schedule_name(project);row=conn.execute('SELECT project,kind,payload,interval_seconds,next_due,enabled FROM agent_schedules WHERE name=?',(name,)).fetchone()
            if not row or row[5]==0:continue
            if (row[:4]!=(project,'inspect_repository',q._json(payload(project)),INTERVAL) or row[5]!=1 or type(row[4]) not in (int,float) or not math.isfinite(row[4])):
                inbox.create(conn,'ULTIMATE AI CONTROL','critical','Расписание GitHub требует проверки',project+': определение проверки main не совпало с разрешённым. Остальные задания продолжаются.','/repo_heads. Определение не перезаписано.',event_key='repo-head-schedule-invalid:'+project,commit=False);continue
            if row[4]>now:continue
            ids.append(_enqueue(conn,project,f'repo-head-schedule:{project}:{row[4]:.6f}',now))
            conn.execute('UPDATE agent_schedules SET next_due=? WHERE name=?',(now+INTERVAL,name))
    return ids


class ReadError(RuntimeError):
    def __init__(self,code,denied=False):self.code=code;self.denied=denied

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise ReadError('response',True)

def read_json(url,limit,deadline,opener):
    remaining=deadline-time.monotonic()
    if remaining<=0:raise ReadError('deadline')
    request=urllib.request.Request(url,method='GET',headers={'User-Agent':'ULTIMATE-Repository-Head/4.0','Accept':'application/vnd.github+json','Accept-Encoding':'identity'})
    try:
        with opener(request,timeout=min(3,remaining)) as response:
            if response.status!=200 or response.geturl()!=url or response.headers.get('Content-Encoding','identity').lower()!='identity':raise ReadError('response',True)
            raw=bytearray()
            while True:
                if time.monotonic()>deadline:raise ReadError('deadline')
                chunk=response.read1(min(8192,limit+1-len(raw)))
                if not chunk:break
                raw.extend(chunk)
                if len(raw)>limit:raise ReadError('oversize')
    except urllib.error.HTTPError as exc:raise ReadError('http_'+str(exc.code) if exc.code in (403,404,429) else 'http_other') from None
    except ReadError:raise
    except (OSError,ValueError):raise ReadError('network') from None
    if time.monotonic()>deadline:raise ReadError('deadline')
    try:
        value=json.loads(raw)
        if not isinstance(value,dict):raise ValueError('object needed')
        return value
    except (ValueError,UnicodeError,RecursionError):raise ReadError('invalid_json') from None


def observe(job,*,opener=None,clock=time.time):
    project,config=scope(job);root='https://api.github.com/repos/'+registry.OWNER+'/'+config['repository']
    opener=opener or urllib.request.build_opener(NoRedirect()).open
    report={'schema':PROFILE,'project':project,'repository':registry.OWNER+'/'+config['repository'],'repository_id':config['repository_id'],
            'ref':'refs/heads/main','baseline_sha':config['revision'],'head_sha':None,'status':'unavailable','error_code':None,
            'observed_at':None,'code_executed':False,'tests_executed':False,'published':False,'credential_used':False}
    try:
        deadline=time.monotonic()+12;metadata=read_json(root,65536,deadline,opener)
        owner=metadata.get('owner')
        if (type(metadata.get('id')) is not int or metadata['id']!=config['repository_id'] or metadata.get('full_name')!=report['repository']
            or metadata.get('private') is not False or metadata.get('fork') is not False or metadata.get('default_branch')!='main'
            or not isinstance(owner,dict) or owner.get('login')!=registry.OWNER or type(owner.get('id')) is not int or owner['id']!=registry.OWNER_ID):raise ReadError('identity',True)
        ref=read_json(root+'/git/ref/heads/main',8192,deadline,opener);obj=ref.get('object')
        if ref.get('ref')!='refs/heads/main' or not isinstance(obj,dict) or obj.get('type')!='commit' or not sha(obj.get('sha')):raise ReadError('ref',True)
        report.update(head_sha=obj['sha'],status='observed')
    except ReadError as exc:report.update(status='scope_denied' if exc.denied else 'unavailable',error_code=exc.code)
    report['observed_at']=q._now(clock());return report


def valid(report,project):
    try:
        config=registry.REPOSITORIES[project]
        if set(report)!={'schema','project','repository','repository_id','ref','baseline_sha','head_sha','status','error_code','observed_at','code_executed','tests_executed','published','credential_used'}:return False
        if (report['schema']!=PROFILE or report['project']!=project or report['repository']!=registry.OWNER+'/'+config['repository']
            or type(report['repository_id']) is not int or report['repository_id']!=config['repository_id'] or report['ref']!='refs/heads/main' or report['baseline_sha']!=config['revision']
            or any(report[k] is not False for k in ('code_executed','tests_executed','published','credential_used'))):return False
        if type(report['observed_at']) not in (int,float):return False
        q._now(report['observed_at'])
        if report['status']=='observed':return sha(report['head_sha']) and report['error_code'] is None
        return report['status'] in ('scope_denied','unavailable') and report['head_sha'] is None and report['error_code'] in ERRORS
    except (KeyError,TypeError,ValueError):return False


def complete(conn,job,report,*,now=None):
    project,_=scope(job);now=q._now(now)
    if not valid(report,project):raise ValueError('invalid repository head report')
    with q._write(conn):
        owned=q._owned(conn,job['id'],job['lease_token'],now);emergency.check_job(conn,job['id'],job['lease_token'])
        stored=conn.execute('SELECT project,kind,payload FROM agent_jobs WHERE id=?',(job['id'],)).fetchone()
        if stored!=(project,'inspect_repository',q._json(payload(project))) or not owned[3]<=report['observed_at']<=now:raise ValueError('repository head identity/time changed')
        hashed=digest(report);ident=conn.execute('INSERT INTO repository_head_runs(job_id,project,report,report_sha256,created_at) VALUES(?,?,?,?,?)',(job['id'],project,canonical(report),hashed,now)).lastrowid
        old=conn.execute('SELECT run_id,observed_at,signature,generation,notice_id FROM repository_head_state WHERE project=?',(project,)).fetchone()
        superseded=bool(old and old[1]>report['observed_at']);signature=report['status']+(':'+report['head_sha'] if report['status']=='observed' else '')
        if not superseded:
            generation=(old[3] if old else 0)+int(not old or old[2]!=signature);notice=old[4] if old else None
            changed=not old or old[2]!=signature;drift=report['status']=='observed' and report['head_sha']!=report['baseline_sha']
            recovery=bool(old and not old[2].startswith('observed:') and report['status']=='observed')
            if changed and (drift or report['status']!='observed' or old):
                kind='critical' if report['status']=='scope_denied' else 'info'
                title='GitHub: область доступа изменилась' if kind=='critical' else ('GitHub: чтение восстановлено' if recovery else 'GitHub: версия или доступ изменились')
                reason=(project+': '+(f"main {report['head_sha']}. "+('Новая версия ещё не проверена ULTIMATE.' if drift else 'main совпадает с закреплённой версией.') if report['status']=='observed' else 'Текущая версия неизвестна: '+report['error_code']+'.'))
                notice=inbox.create(conn,'ULTIMATE AI CONTROL',kind,title,reason,'/repo_heads — сохранённые снимки. Проверенные версии не изменены; тесты и публикации выполняются отдельно.',task_id=str(job['id']),event_key=f'repo-head:{project}:{generation}',commit=False)
            if report['status']=='observed':
                # Close only this monitor's proven scope incidents, even through intervening network errors.
                incidents=conn.execute("SELECT n.id,n.event_key,r.id FROM owner_notifications n JOIN repository_head_runs r ON n.task_id=CAST(r.job_id AS TEXT) WHERE r.project=? AND n.project='ULTIMATE AI CONTROL' AND n.kind='critical' AND n.title='GitHub: область доступа изменилась' AND n.state='pending' AND n.event_key LIKE ? ORDER BY n.id LIMIT 100",(project,'repo-head:'+project+':%')).fetchall()
                for note,key,run in incidents:
                    try:prior,_=record(conn,run)
                    except (ValueError,TypeError,KeyError):continue
                    if prior['status']=='scope_denied' and re.fullmatch('repo-head:'+project+':[1-9][0-9]*',key):
                        conn.execute("UPDATE owner_notifications SET state='resolved',resolved_at=? WHERE id=? AND event_key=? AND kind='critical' AND state='pending'",(datetime.fromtimestamp(now,timezone.utc).isoformat(),note,key))
            conn.execute('INSERT INTO repository_head_state VALUES(?,?,?,?,?,?) ON CONFLICT(project) DO UPDATE SET run_id=excluded.run_id,observed_at=excluded.observed_at,signature=excluded.signature,generation=excluded.generation,notice_id=excluded.notice_id',(project,ident,report['observed_at'],signature,generation,notice))
        state='succeeded' if report['status']=='observed' else 'failed'
        result={'repo_head_id':ident,'report_sha256':hashed,'repo_head_status':report['status'],'superseded':superseded,'published':False}
        conn.execute('UPDATE agent_jobs SET state=?,result=?,worker=NULL,lease_token=NULL,lease_until=NULL,updated_at=?,last_error=? WHERE id=?',(state,q._json(result),now,None if state=='succeeded' else 'repository_head_'+report['error_code'],job['id']))
        q._event(conn,job['id'],now,state,'repository branch metadata only');return result


def record(conn,ident):
    if type(ident) is not int or not 1<=ident<=9223372036854775807:raise ValueError('invalid repository observation ID')
    row=conn.execute('SELECT job_id,project,report,report_sha256 FROM repository_head_runs WHERE id=?',(ident,)).fetchone()
    if not row:raise ValueError('repository head report absent')
    report=json.loads(row[2]);job=conn.execute('SELECT project,kind,payload,state,result FROM agent_jobs WHERE id=?',(row[0],)).fetchone()
    if not valid(report,row[1]) or digest(report)!=row[3] or not job or job[:3]!=(row[1],'inspect_repository',q._json(payload(row[1]))):raise ValueError('repository head evidence changed')
    result=json.loads(job[4]);expected='succeeded' if report['status']=='observed' else 'failed'
    if (not isinstance(result,dict) or set(result)!={'repo_head_id','report_sha256','repo_head_status','superseded','published'} or job[3]!=expected or result.get('repo_head_id')!=ident or result.get('report_sha256')!=row[3] or result.get('repo_head_status')!=report['status'] or result.get('published') is not False or type(result.get('superseded')) is not bool):raise ValueError('repository head job result changed')
    return report,row[3]


def latest(conn,project):
    payload(project);row=conn.execute('SELECT run_id FROM repository_head_state WHERE project=?',(project,)).fetchone()
    return record(conn,row[0]) if row else None


def describe(conn,*,now=None):
    now=q._now(now);lines=['📁 Версии проектов в GitHub','Периодическая проверка main: раз в6 часов.']
    for project in registry.REPOSITORIES:
        lines.append('\n'+project+':')
        try:proof=latest(conn,project)
        except (ValueError,TypeError,KeyError):lines.append('Сохранённые основания требуют проверки.');continue
        if not proof:lines.append('Наблюдения ещё нет.');continue
        report,_=proof;age=now-report['observed_at']
        stamp=datetime.fromtimestamp(report['observed_at'],timezone(timedelta(hours=5))).strftime('%d.%m %H:%M Ташкент')
        lines.append('Снимок: '+stamp+(' · устарел' if not 0<=age<=FRESH else ''))
        if report['status']=='observed':
            lines.append('main: '+report['head_sha'])
            lines.append('Совпадает с закреплённой версией.' if report['head_sha']==report['baseline_sha'] else 'Есть новый коммит; прежние тесты его не подтверждают.')
        else:lines.append('Версия сейчас не подтверждена: '+report['error_code']+'.')
        lines.append('/repo_head '+project)
    lines.extend(['\nЭто состояние GitHub; опубликованная версия проверяется отдельно. Тесты, файлы проекта и закреплённые версии эта проверка не меняет. Inventory исключён.'])
    return '\n'.join(lines)
