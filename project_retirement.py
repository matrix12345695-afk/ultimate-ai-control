"""Owner-requested project retirement. Active data is removed; audit history stays.

Activation is an explicit operator migration on the stopped UAC runtime. An empty
ledger preserves old database/test compatibility; no command can clear the ledger.
SQLite guards also cover older writers and reseeding, not just Telegram buttons.
"""
import json
import re
import sqlite3
import time
from datetime import datetime, timezone
from urllib.parse import urlsplit

PROJECTS=('nova','kinder')
ALIASES={'nova':{'nova','nova web','nova-web-agency'},
         'kinder':{'kinder','kinder spa','kinder-spa','kinder_spa','kinder-spa-android'}}
MESSAGE='Этот проект удалён из управления владельцем. Новые задания и проверки отключены.'


def canonical(value):
    value=str(value or '').strip().lower()
    return next((p for p,names in ALIASES.items() if value in names),None)


def enabled(conn):
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='uac_retired_projects'").fetchone():return False
    return bool(conn.execute('SELECT 1 FROM uac_retired_projects LIMIT 1').fetchone())


def retired(conn,project):
    p=canonical(project)
    return bool(p and enabled(conn) and conn.execute('SELECT 1 FROM uac_retired_projects WHERE project=?',(p,)).fetchone())


def matches(project,payload=None):
    if canonical(project):return True
    if isinstance(payload,dict):
        target=str(payload.get('target','')).lower()
        return bool(canonical(payload.get('project')) or canonical(target) or target.startswith(('nova-','nova_','kinder-','kinder_')))
    return False


def require_open(conn,project,payload=None):
    if enabled(conn) and matches(project,payload):raise ValueError(MESSAGE)


def _sql_project(field):
    parts=[]
    for project,names in ALIASES.items():
        values=','.join("'"+x+"'" for x in sorted(names))
        parts.append(f"(EXISTS(SELECT 1 FROM uac_retired_projects WHERE project='{project}') AND lower(trim({field})) IN ({values}))")
    return '('+' OR '.join(parts)+')'


def initialize(conn):
    conn.execute('CREATE TABLE IF NOT EXISTS uac_retired_projects(project TEXT PRIMARY KEY CHECK(project IN (\'nova\',\'kinder\')),retired_at REAL NOT NULL,reason TEXT NOT NULL)')
    conn.execute('CREATE TABLE IF NOT EXISTS uac_project_retirement_events(id INTEGER PRIMARY KEY,at REAL NOT NULL,report TEXT NOT NULL)')
    conn.commit()


def _guards(conn):
    tables={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for table in ('agent_jobs','tasks','proposals','github_change_requests','voice_inputs','owner_notifications','project_memory','agent_schedules'):
        if table not in tables:continue
        condition=_sql_project('NEW.project')
        if table in ('agent_jobs','agent_schedules'):
            condition+=' OR (EXISTS(SELECT 1 FROM uac_retired_projects) AND (json_extract(NEW.payload,\'$.target\') GLOB \'nova[-_]*\' OR json_extract(NEW.payload,\'$.target\') GLOB \'kinder[-_]*\' OR '+_sql_project("json_extract(NEW.payload,'$.project')")+'))'
        result="RAISE(IGNORE)" if table in ('project_memory','agent_schedules') else "RAISE(ABORT,'project_retired_by_owner')"
        conn.execute(f'CREATE TRIGGER IF NOT EXISTS uac_retired_insert_{table} BEFORE INSERT ON {table} WHEN {condition} BEGIN SELECT {result}; END')
        if table=='agent_schedules':
            conn.execute(f"CREATE TRIGGER IF NOT EXISTS uac_retired_schedule_update BEFORE UPDATE ON {table} WHEN ({condition}) AND NEW.enabled=1 BEGIN SELECT RAISE(ABORT,'project_retired_by_owner'); END")
        if table=='agent_jobs':
            conn.execute(f"CREATE TRIGGER IF NOT EXISTS uac_retired_job_resume BEFORE UPDATE OF state ON {table} WHEN ({condition}) AND NEW.state IN ('queued','running','awaiting_owner') BEGIN SELECT RAISE(ABORT,'project_retired_by_owner'); END")


def apply(conn,*,now=None):
    """One transaction, no network/files/processes; caller drains/stops UAC first."""
    initialize(conn)
    now=time.time() if now is None else now
    if conn.in_transaction:raise RuntimeError('independent retirement transaction required')
    conn.execute('BEGIN IMMEDIATE')
    try:
        if conn.execute('SELECT paused FROM agent_queue_control WHERE singleton=1').fetchone()!=(1,):raise RuntimeError('pause UAC before retirement')
        tables={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        jobs=[]
        for ident,project,state,raw in conn.execute('SELECT id,project,state,payload FROM agent_jobs'):
            try:payload=json.loads(raw)
            except (ValueError,TypeError):payload={}
            if matches(project,payload):jobs.append((ident,state))
        if any(state=='running' for _,state in jobs):raise RuntimeError('drain running project jobs first')
        for project in PROJECTS:
            conn.execute('INSERT OR IGNORE INTO uac_retired_projects VALUES(?,?,?)',(project,now,'Explicit owner removal, 31 October2026'))
        counts={'cancelled_jobs':0,'removed_schedules':0,'resolved_requests':0,'removed_contexts':0,'cancelled_voice':0,'revoked_approvals':0}
        for ident,state in jobs:
            if state not in ('queued','awaiting_owner'):continue
            conn.execute("UPDATE agent_jobs SET state='cancelled',lease_token=NULL,lease_until=NULL,updated_at=?,last_error='project_retired_by_owner' WHERE id=?",(now,ident))
            conn.execute("INSERT INTO agent_job_events(job_id,at,event,detail) VALUES(?,?,'cancelled','owner_project_retirement')",(ident,now));counts['cancelled_jobs']+=1
        for table,key in (('agent_schedules','removed_schedules'),('project_memory','removed_contexts'),('repository_head_state',None)):
            if table not in tables:continue
            columns={r[1] for r in conn.execute('PRAGMA table_info('+table+')')}
            if 'project' not in columns:continue
            cur=conn.execute('DELETE FROM '+table+' WHERE '+_sql_project('project'))
            if key:counts[key]=cur.rowcount
        if 'agent_health' in tables:conn.execute("DELETE FROM agent_health WHERE target IN ('nova','kinder')")
        if 'owner_notifications' in tables:
            stamp=datetime.fromtimestamp(now,timezone.utc).isoformat()
            for ident,project,task,key,title,reason,action in conn.execute("SELECT id,project,task_id,event_key,title,reason,next_action FROM owner_notifications WHERE state='pending'").fetchall():
                if canonical(project) or re.search(r'(?i)\bnova\b|\bkinder\b|novaweb\.uz|\bнова\b|\bкиндер\b',' '.join(str(x or '') for x in (task,key,title,reason,action))):
                    conn.execute("UPDATE owner_notifications SET state='resolved',resolved_at=?,delivery_claimed_at=NULL,next_attempt_at=NULL WHERE id=?",(stamp,ident));counts['resolved_requests']+=1
        for table,column,states,target in (('tasks','status',('queued','running','awaiting_owner'),'cancelled'),
                ('proposals','state',('pending','draft','awaiting_review'),'cancelled'),
                ('github_change_requests','status',('awaiting_review','approved'),'cancelled')):
            if table in tables:
                marks=','.join('?' for _ in states)
                conn.execute(f'UPDATE {table} SET {column}=? WHERE {column} IN ({marks}) AND '+_sql_project('project'),(target,*states))
        if 'github_change_requests' in tables and 'approvals' in tables:
            counts['revoked_approvals']=conn.execute("UPDATE approvals SET status='rejected',decided_by='owner_project_retirement',decided_at=? WHERE action='github_draft_pr' AND status IN ('pending','approved') AND id IN (SELECT approval_id FROM github_change_requests WHERE "+_sql_project('project')+')',(datetime.fromtimestamp(now,timezone.utc).isoformat(),)).rowcount
        if 'voice_inputs' in tables:
            counts['cancelled_voice']=conn.execute("UPDATE voice_inputs SET state='rejected',error_code='project_retired_by_owner',transcript=NULL,preview_code=NULL WHERE state IN ('receiving','queued','ready') AND "+_sql_project('project')).rowcount
        conn.execute("UPDATE uac_settings SET value='control',updated_at=? WHERE key='active_project' AND "+_sql_project('value'),(now,))
        conn.execute("UPDATE uac_settings SET value='disabled',updated_at=? WHERE key='repo_head_gate'",(now,))
        conn.execute("UPDATE uac_roadmap SET title='Новый коммерческий AI-продукт',state='planned',acceptance='Reviewed working product, documented package and owner-approved sale',evidence='Previous commercial project retired by owner; new AI operator direction approved',updated_at=? WHERE id=16",(now,))
        _guards(conn)
        conn.execute('INSERT INTO uac_project_retirement_events(at,report) VALUES(?,?)',(now,json.dumps(counts,sort_keys=True)))
        conn.commit();return counts
    except BaseException:conn.rollback();raise


def filtered(conn,text):
    if not enabled(conn) or not isinstance(text,str):return text
    text=re.sub(r'(?i)\b(nova|kinder)\b','control',text) if text.startswith('Usage:') else text
    lines=[line for line in text.splitlines() if not re.search(r'(?i)nova|kinder|нова|киндер',line)]
    return '\n'.join(lines) or 'Активных записей нет. /projects4'


def before_command(conn,text):
    if not enabled(conn):return None
    parts=text.split();op=parts[0].split('@')[0].lower() if parts else ''
    if op.startswith(('/nova','/test_nova')) or any(canonical(p) for p in parts[1:3]):return MESSAGE
    if op in ('/projects','/projects4','/memory') and len(parts)==1:
        rows=conn.execute("SELECT project FROM project_memory WHERE project!='policy' ORDER BY project").fetchall()
        return 'Активные проекты ULTIMATE\n'+'\n'.join(p for p, in rows if not retired(conn,p))
    if op in ('/repo_heads','/repo_check','/repo_head'):
        return 'Внешние репозитории не подключены. Старые проекты удалены из управления.'
    if op in ('/check','/readiness4','/monitor4'):
        return 'Активные цели проверки сайтов не настроены. /projects4'
    return None


def denied_url(conn,url):
    if not enabled(conn):return False
    host=urlsplit(url).hostname or ''
    return host in ('novaweb.uz','www.novaweb.uz','novaweb-agency.onrender.com')
