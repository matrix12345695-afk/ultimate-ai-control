"""Content-bound Draft PR ledger for two independently tested ULTIMATE recipes.

No credentials, GitHub calls, merge or deployment. New requests never overwrite
active source; the only exportable bytes are the two reviewed recipe files.
"""
import hashlib
import json
from pathlib import Path
import re
import time
import acceptance_checks
import approval
import artifact_recovery as private
import offline_developer
import task_queue as q

REPO='matrix12345695-afk/ultimate-ai-control'
METHOD='artifact-pr-v1'


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)


def digest(value): return hashlib.sha256(canonical(value).encode()).hexdigest()


def initialize(conn):
    approval.init_approvals(conn)
    conn.execute('''CREATE TABLE IF NOT EXISTS artifact_pr_requests(
        id INTEGER PRIMARY KEY,job_id INTEGER NOT NULL UNIQUE,artifact_id INTEGER NOT NULL UNIQUE,
        identity TEXT NOT NULL,identity_sha256 TEXT NOT NULL,remote TEXT NOT NULL DEFAULT '{}',
        created_at REAL NOT NULL,updated_at REAL NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS artifact_release_candidates(
        id INTEGER PRIMARY KEY,request_id INTEGER NOT NULL,scope TEXT NOT NULL,
        scope_sha256 TEXT NOT NULL,approval_id TEXT NOT NULL UNIQUE,created_at REAL NOT NULL)''')
    conn.execute('CREATE INDEX IF NOT EXISTS artifact_release_scope ON artifact_release_candidates(scope_sha256)')
    conn.commit()


def material(conn,ident,data):
    if type(ident) is not int or ident<=0: raise ValueError('invalid artifact number')
    row=conn.execute('''SELECT job_id,attempt,project,engine,source_digest,manifest,test_status,test_report,path
        FROM code_artifacts WHERE id=?''',(ident,)).fetchone()
    if not row or row[2:4]!=('control','deterministic_recipe') or row[6]!='passed':
        raise PermissionError('only independently tested ULTIMATE recipe artifacts may be exported')
    job_id,attempt,_,_,source_digest,raw_manifest,_,raw_report,path=row
    job=conn.execute('SELECT project,kind,payload,state FROM agent_jobs WHERE id=?',(job_id,)).fetchone()
    if not job or job[:2]!=('control','review_change') or job[3] not in ('awaiting_owner','succeeded'):
        raise PermissionError('artifact generation has not completed')
    payload=json.loads(job[2]);recipe=payload.get('recipe') if isinstance(payload,dict) else None
    if recipe not in acceptance_checks.RECIPE_PROFILES: raise PermissionError('recipe not enabled')
    files=offline_developer.recipe_files(recipe,job_id)
    entries,expected=offline_developer.manifest(files)
    profile=acceptance_checks.RECIPE_PROFILES[recipe]
    report=json.loads(raw_report);checks=report.get('independent_acceptance',{})
    if (source_digest!=expected or json.loads(raw_manifest)!=entries or
            report.get('source_digest')!=expected or report.get('status')!='passed' or
            report.get('candidate_test_status')!='passed' or checks.get('status')!='passed' or
            checks.get('profile')!=profile or checks.get('candidate_source_digest')!=expected or
            checks.get('harness_sha256')!=acceptance_checks.harness_sha256(profile)):
        raise PermissionError('artifact test or acceptance evidence changed')
    root=Path(data)/'artifacts'/('job-'+str(job_id)+'-attempt-'+str(attempt))
    if Path(path)!=root: raise PermissionError('artifact path outside own data directory')
    private.private_directory(root)
    for name,body in files.items():
        p=root/name
        for parent in p.parents:
            if parent==root: break
            private.private_directory(parent)
        if private.private_read(p,len(body.encode()))!=body.encode(): raise PermissionError('artifact source bytes changed')
    if json.loads(private.private_read(root/'manifest.json',64000))!=entries or json.loads(private.private_read(root/'test-report.json',256000))!=report:
        raise PermissionError('artifact files and report disagree')
    identity={'schema':METHOD,'project':'control','repository':REPO,'artifact_id':ident,
              'generation_job_id':job_id,'recipe':recipe,'source_digest':expected,'files':entries,
              'report_sha256':hashlib.sha256(raw_report.encode()).hexdigest(),
              'acceptance_profile':profile,'harness_sha256':checks['harness_sha256'],
              'base_ref':'main','branch':'ai-review/artifact-'+str(ident)+'-'+expected[:16],
              'draft':True,'merge_allowed':False,'deploy_allowed':False}
    return identity,files


def prepare(conn,job,data):
    payload=job.get('payload')
    refresh=isinstance(payload,dict) and payload.get('refresh') is True
    if (job.get('project')!='control' or job.get('kind')!='review_change' or not isinstance(payload,dict)
            or set(payload)!=({'artifact_pr','refresh'} if refresh else {'artifact_pr'})):
        raise PermissionError('artifact PR scope not enabled')
    identity,files=material(conn,payload['artifact_pr'],data)
    with q._write(conn):
        q._owned(conn,job['id'],job['lease_token'],time.time())
        row=conn.execute('SELECT id,job_id,identity,identity_sha256 FROM artifact_pr_requests WHERE artifact_id=?',
                         (payload['artifact_pr'],)).fetchone()
        if row:
            if (row[1]!=job['id'] and not refresh) or row[2]!=canonical(identity) or row[3]!=digest(identity):
                raise PermissionError('artifact PR identity changed; reconciliation required')
            return row[0],identity,files
        if refresh: raise PermissionError('cannot refresh a missing PR request')
        today=int(time.time())//86400*86400
        if conn.execute('SELECT count(*) FROM artifact_pr_requests WHERE created_at>=?',(today,)).fetchone()[0]>=3:
            raise PermissionError('daily draft limit reached')
        ident=conn.execute('''INSERT INTO artifact_pr_requests(job_id,artifact_id,identity,identity_sha256,created_at,updated_at)
            VALUES(?,?,?,?,?,?)''',(job['id'],payload['artifact_pr'],canonical(identity),digest(identity),time.time(),time.time())).lastrowid
        q._event(conn,job['id'],time.time(),'artifact_pr_prepared',str(ident))
        return ident,identity,files


def save_remote(conn,job,ident,remote):
    allowed={'base_sha','base_tree','tree_sha','head_sha','pr_number','pr_url','ci_state','ci_runs','checked_at','verified','commit_date'}
    if not isinstance(remote,dict) or set(remote)-allowed: raise ValueError('invalid PR state')
    with q._write(conn):
        q._owned(conn,job['id'],job['lease_token'],time.time())
        row=conn.execute('SELECT artifact_id,job_id FROM artifact_pr_requests WHERE id=?',(ident,)).fetchone()
        if not row or row[0]!=job['payload'].get('artifact_pr') or (row[1]!=job['id'] and job['payload'].get('refresh') is not True):
            raise PermissionError('PR lease mismatch')
        conn.execute('UPDATE artifact_pr_requests SET remote=?,updated_at=? WHERE id=?',
                     (canonical(remote),time.time(),ident))


def record(conn,ident):
    row=conn.execute('SELECT job_id,artifact_id,identity,identity_sha256,remote,created_at FROM artifact_pr_requests WHERE id=?',(ident,)).fetchone()
    if not row: raise ValueError('PR request not found')
    identity=json.loads(row[2]);remote=json.loads(row[4])
    if digest(identity)!=row[3] or identity.get('repository')!=REPO or identity.get('project')!='control':
        raise PermissionError('PR identity integrity check failed')
    return identity,remote,row


def release_scope(identity,remote):
    if (remote.get('verified') is not True or remote.get('ci_state')!='success' or
            type(remote.get('checked_at')) not in (int,float) or not 0<=time.time()-remote['checked_at']<=900):
        raise PermissionError('fresh exact-head CI verification required')
    return {'action':'publish_exact_version','project':identity['project'],'repository':REPO,
            'request_source_digest':digest(identity),'artifact_sha256':identity['source_digest'],
            'test_report_sha256':identity['report_sha256'],'pr_url':remote['pr_url'],
            'base_sha':remote['base_sha'],'head_sha':remote['head_sha'],'ci_runs':remote['ci_runs']}


def request_release(conn,ident):
    with q._write(conn):
        identity,remote,_=record(conn,ident);scope=release_scope(identity,remote);sha=digest(scope)
        from datetime import datetime,timezone
        existing=conn.execute('''SELECT c.id,c.approval_id FROM artifact_release_candidates c
            JOIN approvals a ON a.id=c.approval_id WHERE c.scope_sha256=?
            AND a.status IN ('pending','approved') AND a.expires_at>? ORDER BY c.id DESC LIMIT 1''',
            (sha,datetime.now(timezone.utc).isoformat())).fetchone()
        if existing: return existing[0],existing[1],scope
        # Reuse owner-authenticated approval primitives atomically; no decision is made here.
        aid=approval.request_approval(conn,ident,'publish_exact_version','production',scope,ttl_minutes=60,commit=False)
        cur=conn.execute('INSERT INTO artifact_release_candidates(request_id,scope,scope_sha256,approval_id,created_at) VALUES(?,?,?,?,?)',
                         (ident,canonical(scope),sha,aid,time.time()))
        return cur.lastrowid,aid,scope


def release_authorized(conn,candidate_id,observed_scope):
    row=conn.execute('SELECT request_id,scope,scope_sha256,approval_id FROM artifact_release_candidates WHERE id=?',(candidate_id,)).fetchone()
    if not row or digest(observed_scope)!=row[2] or canonical(observed_scope)!=row[1]: return False
    try:
        identity,remote,_=record(conn,row[0])
        if digest(release_scope(identity,remote))!=row[2]: return False
    except (ValueError,PermissionError): return False
    return approval.is_authorized(conn,row[3],row[0],'publish_exact_version','production',observed_scope)


def describe(conn,ident=None):
    if ident is None:
        rows=conn.execute('SELECT id,artifact_id,remote FROM artifact_pr_requests ORDER BY id DESC LIMIT 6').fetchall()
        return '📝 Черновики из проверенных артефактов\n'+('\n'.join(f'#{i} · артефакт {a} · /artifact_pr_status {i}' for i,a,_ in rows) or 'Заявок пока нет.')+'\nСоздать: /artifact_pr <артефакт>. Только два разрешённых рецепта ULTIMATE. Merge и deploy не выполняются.'
    identity,remote,_=record(conn,ident)
    return (f'Черновик #{ident} · control · артефакт {identity["artifact_id"]}\n'
            +'Источник SHA-256: '+identity['source_digest']+'\n'
            +'PR: '+remote.get('pr_url','ещё не создан')+'\n'
            +'Commit: '+remote.get('head_sha','ещё не зафиксирован')+'\nCI: '+remote.get('ci_state','pending')
            +'\nПубликация не выполнялась. Согласование конкретной версии: /artifact_release '+str(ident)
            +'\nДаже одобрение сохраняет только разрешение; исполнитель публикации ещё не подключён.')
