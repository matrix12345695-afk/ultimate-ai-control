"""Exact-commit hosted CI evidence, never represented as VPS-local execution."""
import json
import math
from pathlib import Path
import time
import artifact_prs as util
import artifact_pr_broker as broker
import task_queue as q

PROFILE='nova-postgres-ci-v1'
CONTRACT=json.loads(Path(__file__).with_name('nova_ci_contract.json').read_text())
REPO='matrix12345695-afk/ultimate-ai-control'


def initialize(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS nova_ci_runs(
      id INTEGER PRIMARY KEY,job_id INTEGER NOT NULL UNIQUE,report TEXT NOT NULL,
      report_sha256 TEXT NOT NULL,created_at REAL NOT NULL)''');conn.commit()


def scope(job):
    if job.get('project')!='nova' or job.get('kind')!='test_release' or job.get('payload')!={'target':PROFILE}: raise broker.Blocked('nova_ci_scope_denied')


def observe(client):
    # Client is constrained to this repository and rejects every non-GET request.
    if client.read_only is not True: raise broker.Blocked('nova_ci_requires_read_only')
    head=CONTRACT['harness_commit']
    listing=client.call('GET','/actions/runs?head_sha='+head+'&per_page=20')
    if not isinstance(listing,dict) or not isinstance(listing.get('workflow_runs'),list): raise broker.Blocked('nova_ci_listing_shape')
    matches=[run for run in listing['workflow_runs'] if run.get('head_sha')==head and run.get('event')=='push'
             and run.get('name')==CONTRACT['workflow_name'] and run.get('path','').split('@')[0]==CONTRACT['workflow_path']
             and run.get('repository',{}).get('id')==1429215344 and run.get('head_repository',{}).get('id')==1429215344
             and type(run.get('id')) is int and run['id']>0 and type(run.get('run_attempt')) is int and run['run_attempt']>0]
    if not matches: raise broker.Pending('nova_ci_exact_run_missing')
    run=max(matches,key=lambda row:(row.get('updated_at',''),row['id'],row['run_attempt']))
    if run.get('status')!='completed': raise broker.Pending('nova_ci_not_completed')
    ident=run['id'];attempt=run['run_attempt']
    jobs=client.call('GET',f'/actions/runs/{ident}/attempts/{attempt}/jobs?per_page=100')
    if not isinstance(jobs,dict) or jobs.get('total_count')!=1 or not isinstance(jobs.get('jobs'),list) or len(jobs['jobs'])!=1: raise broker.Blocked('nova_ci_jobs_incomplete')
    job=jobs['jobs'][0]
    if (job.get('name')!=CONTRACT['workflow_name'] or job.get('run_id')!=ident or job.get('head_sha')!=head or
            type(job.get('id')) is not int or job['id']<=0 or job.get('status')!='completed' or
            job.get('runner_group_name')!='GitHub Actions' or 'ubuntu-24.04' not in job.get('labels',[]) or 'self-hosted' in job.get('labels',[])):
        raise broker.Blocked('nova_ci_job_identity_changed')
    steps=job.get('steps')
    if not isinstance(steps,list): raise broker.Blocked('nova_ci_steps_missing')
    gates=[step for step in steps if step.get('name')=='Run and verify all NOVA tests']
    passed=(run.get('conclusion')=='success' and job.get('conclusion')=='success' and len(gates)==1
            and gates[0].get('status')=='completed' and gates[0].get('conclusion')=='success')
    if run.get('conclusion')=='success' and not passed: raise broker.Blocked('nova_ci_success_without_required_gate')
    # Detect a rerun/transition between listing and reading the exact-attempt jobs.
    final=client.call('GET','/actions/runs/'+str(ident))
    if any(final.get(key)!=run.get(key) for key in ('id','run_attempt','head_sha','status','conclusion','event','path')):
        raise broker.Pending('nova_ci_changed_during_observation')
    return {'schema':PROFILE,'contract_sha256':util.digest(CONTRACT),'repository':REPO,
            'harness_commit':head,'source_revision':CONTRACT['source_revision'],
            'source_manifest_sha256':CONTRACT['source_manifest_sha256'],'dependency_lock_sha256':CONTRACT['dependency_lock_sha256'],
            'ci_run_id':ident,'ci_attempt':attempt,'ci_job_id':job['id'],'ci_url':'https://github.com/'+REPO+'/actions/runs/'+str(ident),
            'status':'passed' if passed else 'failed','counts':{'tests':34,'pass':34,'fail':0,'cancelled':0,'skipped':0,'todo':0} if passed else None,
            'counts_source':'exact_commit_required_ci_gate','postgres_major':16 if passed else None,
            'database_persistence_verified':passed,'database_restore_verified':passed,
            'execution_location':'github_hosted_disposable_runner','vps_local_execution':False,
            'production_access':False,'browser_test':False,'published':False,'checked_at':time.time()}


def valid(report):
    keys={'schema','contract_sha256','repository','harness_commit','source_revision','source_manifest_sha256','dependency_lock_sha256',
          'ci_run_id','ci_attempt','ci_job_id','ci_url','status','counts','counts_source','postgres_major',
          'database_persistence_verified','database_restore_verified','execution_location','vps_local_execution','production_access','browser_test','published','checked_at'}
    if not isinstance(report,dict) or set(report)!=keys: return False
    if any(report.get(k)!=v for k,v in {'schema':PROFILE,'contract_sha256':util.digest(CONTRACT),'repository':REPO,
              'harness_commit':CONTRACT['harness_commit'],'source_revision':CONTRACT['source_revision'],
              'source_manifest_sha256':CONTRACT['source_manifest_sha256'],'dependency_lock_sha256':CONTRACT['dependency_lock_sha256'],
              'counts_source':'exact_commit_required_ci_gate','execution_location':'github_hosted_disposable_runner'}.items()): return False
    if any(report.get(k) is not False for k in ('vps_local_execution','production_access','browser_test','published')): return False
    if any(type(report[k]) is not int or report[k]<=0 for k in ('ci_run_id','ci_attempt','ci_job_id')): return False
    if report['ci_url']!='https://github.com/'+REPO+'/actions/runs/'+str(report['ci_run_id']): return False
    if type(report['checked_at']) not in (int,float) or not math.isfinite(report['checked_at']) or report['checked_at']<=0: return False
    passed=report['status']=='passed'
    if passed and (not isinstance(report['counts'],dict) or any(type(x) is not int for x in report['counts'].values())): return False
    if report['status'] not in ('passed','failed'): return False
    return (report['counts']==({'tests':34,'pass':34,'fail':0,'cancelled':0,'skipped':0,'todo':0} if passed else None)
            and report['postgres_major']==(16 if passed else None)
            and report['database_persistence_verified'] is passed and report['database_restore_verified'] is passed)


def save(conn,job,report):
    scope(job)
    if not valid(report): raise broker.Blocked('nova_ci_report_contract_changed')
    with q._write(conn):
        now=time.time();owned=q._owned(conn,job['id'],job['lease_token'],now)
        row=conn.execute('SELECT project,kind,payload FROM agent_jobs WHERE id=?',(job['id'],)).fetchone()
        if row[:2]!=('nova','test_release') or json.loads(row[2])!={'target':PROFILE} or not owned[3]<=report['checked_at']<=now:
            raise broker.Blocked('nova_ci_job_observation_changed')
        row=conn.execute('SELECT id,report,report_sha256 FROM nova_ci_runs WHERE job_id=?',(job['id'],)).fetchone()
        if row:
            previous=json.loads(row[1]);old={k:v for k,v in previous.items() if k!='checked_at'};new={k:v for k,v in report.items() if k!='checked_at'}
            if not valid(previous) or util.digest(previous)!=row[2] or old!=new: raise broker.Blocked('nova_ci_saved_evidence_changed')
            report=previous;ident=row[0]
        else:
            ident=conn.execute('INSERT INTO nova_ci_runs(job_id,report,report_sha256,created_at) VALUES(?,?,?,?)',
                (job['id'],util.canonical(report),util.digest(report),now)).lastrowid
    return {'nova_ci_id':ident,'report_sha256':util.digest(report),'test_status':report['status'],'test_counts':report['counts'],
            'revision':CONTRACT['source_revision'],'harness_commit':CONTRACT['harness_commit'],'ci_url':report['ci_url'],
            'ci_run_id':report['ci_run_id'],'ci_attempt':report['ci_attempt'],'database_integration':report['status']=='passed',
            'vps_local_execution':False,'browser_test':False,'published':False}


def describe(conn):
    lines=['NOVA WEB · PostgreSQL · проверенный GitHub CI','Версия NOVA: '+CONTRACT['source_revision']]
    row=conn.execute('SELECT id,job_id,report,report_sha256 FROM nova_ci_runs ORDER BY id DESC LIMIT 1').fetchone()
    if row:
        report=json.loads(row[2])
        if not valid(report) or util.digest(report)!=row[3]: lines.append('Основание изменено; нужна новая сверка.')
        else:
            lines.extend([f'Отчёт #{row[0]} · /job {row[1]} · {report["status"]}',report['ci_url'],
                          'CI commit: '+report['harness_commit'],
                          'Тесты по обязательному CI-gate: '+json.dumps(report['counts'],ensure_ascii=False),
                          'Сверка UTC: '+time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(report['checked_at']))])
    else: lines.append('Результат CI ещё не сверен на VPS.')
    lines.extend(['Исполнение: временный GitHub runner и отдельный PostgreSQL16. VPS хранит и сверяет результат; локального запуска БД на VPS нет.',
                  'Обновить сверку: /test_nova_pg. Браузер и рабочая база не проверяются; публикация не выполнялась.'])
    return '\n'.join(lines)
