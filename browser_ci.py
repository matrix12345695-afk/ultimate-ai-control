"""Hosted Chromium frontend evidence with expiring screenshot archive metadata."""
from datetime import datetime
import json
import math
from pathlib import Path
import re
import time
import artifact_prs as util
import artifact_pr_broker as broker
import hosted_ci
import task_queue as q

PROFILE='nova-browser-ci-v1'
CONTRACT=json.loads(Path(__file__).with_name('browser_ci_contract.json').read_text())
REPO='matrix12345695-afk/ultimate-ai-control'


def initialize(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS browser_ci_runs(
      id INTEGER PRIMARY KEY,job_id INTEGER NOT NULL UNIQUE,report TEXT NOT NULL,
      report_sha256 TEXT NOT NULL,created_at REAL NOT NULL)''');conn.commit()


def scope(job):
    if job.get('project')!='nova' or job.get('kind')!='test_release' or job.get('payload')!={'target':PROFILE}: raise broker.Blocked('browser_ci_scope_denied')


def expires(value):
    if not isinstance(value,str): raise ValueError('artifact expiry missing')
    date=datetime.fromisoformat(value.replace('Z','+00:00'))
    if date.tzinfo is None: raise ValueError('artifact expiry timezone missing')
    return date.timestamp()


def observe(client,contract=None):
    CONTRACT=contract if contract is not None else globals()['CONTRACT'];PROFILE=CONTRACT['schema']
    run,job,passed=hosted_ci.inspect(client,CONTRACT)
    artifact=None
    if passed:
        uploads=[step for step in job['steps'] if step.get('name')==CONTRACT.get('upload_step','Upload browser evidence')]
        if len(uploads)!=1 or uploads[0].get('status')!='completed' or uploads[0].get('conclusion')!='success': raise broker.Blocked('browser_artifact_upload_not_verified')
        data=client.call('GET','/actions/runs/'+str(run['id'])+'/artifacts?per_page=100')
        if (not isinstance(data,dict) or type(data.get('total_count')) is not int or not 0<=data['total_count']<=100 or
                not isinstance(data.get('artifacts'),list) or len(data['artifacts'])!=data['total_count']): raise broker.Blocked('browser_artifact_listing_incomplete')
        rows=[row for row in data['artifacts'] if row.get('name')==CONTRACT['artifact_name_prefix']+str(run['run_attempt'])]
        if not rows: raise broker.Pending('browser_artifact_not_visible')
        if len(rows)!=1: raise broker.Blocked('browser_artifact_ambiguous')
        row=rows[0];origin=row.get('workflow_run',{})
        if (type(row.get('id')) is not int or row['id']<=0 or row.get('expired') is not False or
                type(row.get('size_in_bytes')) is not int or not 1000<row['size_in_bytes']<=25*1024**2 or
                not isinstance(row.get('digest'),str) or not re.fullmatch('sha256:[0-9a-f]{64}',row['digest']) or
                origin.get('id')!=run['id'] or origin.get('head_sha')!=CONTRACT['harness_commit'] or
                origin.get('repository_id')!=1429215344 or origin.get('head_repository_id')!=1429215344): raise broker.Blocked('browser_artifact_identity_changed')
        try: future=expires(row.get('expires_at'))>time.time()
        except (ValueError,TypeError,OverflowError): future=False
        if not future: raise broker.Blocked('browser_artifact_expired')
        artifact={'id':row['id'],'name':row['name'],'digest':row['digest'],'size_bytes':row['size_in_bytes'],'expires_at':row['expires_at'],
                  'url':'https://github.com/'+REPO+'/actions/runs/'+str(run['id'])+'/artifacts/'+str(row['id'])}
        final=client.call('GET','/actions/runs/'+str(run['id']))
        if any(final.get(key)!=run.get(key) for key in ('id','run_attempt','head_sha','status','conclusion','event','path')): raise broker.Pending('browser_ci_changed_during_artifact_read')
    return {'schema':PROFILE,'contract_sha256':util.digest(CONTRACT),'repository':REPO,'harness_commit':CONTRACT['harness_commit'],
            'source_revision':CONTRACT['source_revision'],'source_manifest_sha256':CONTRACT['source_manifest_sha256'],
            'dependency_lock_sha256':CONTRACT['dependency_lock_sha256'],'ci_run_id':run['id'],'ci_attempt':run['run_attempt'],'ci_job_id':job['id'],
            'ci_url':'https://github.com/'+REPO+'/actions/runs/'+str(run['id']),'status':'passed' if passed else 'failed',
            'counts':{'tests':CONTRACT['expected_tests'],'pass':CONTRACT['expected_tests'],'fail':0,'errors':0,'skipped':0} if passed else None,
            'counts_source':'exact_commit_required_ci_gate','engine':CONTRACT.get('engine','chromium'),'browser_version':CONTRACT['browser_version'],
            'viewports':CONTRACT['viewports'],'screenshots':15 if passed else None,'advisories':CONTRACT['advisories'] if passed else None,
            'artifact':artifact,'execution_location':'github_hosted_disposable_runner','backend_mocked':CONTRACT.get('backend_mocked',True),'vps_local_execution':False,
            'production_access':False,'physical_device_test':False,'pixel_baseline_test':False,'published':False,'checked_at':time.time()}


def valid(report,contract=None):
    CONTRACT=contract if contract is not None else globals()['CONTRACT'];PROFILE=CONTRACT['schema']
    keys={'schema','contract_sha256','repository','harness_commit','source_revision','source_manifest_sha256','dependency_lock_sha256',
          'ci_run_id','ci_attempt','ci_job_id','ci_url','status','counts','counts_source','engine','browser_version','viewports','screenshots','advisories',
          'artifact','execution_location','backend_mocked','vps_local_execution','production_access','physical_device_test','pixel_baseline_test','published','checked_at'}
    if not isinstance(report,dict) or set(report)!=keys: return False
    expected={'schema':PROFILE,'contract_sha256':util.digest(CONTRACT),'repository':REPO,'harness_commit':CONTRACT['harness_commit'],
              'source_revision':CONTRACT['source_revision'],'source_manifest_sha256':CONTRACT['source_manifest_sha256'],
              'dependency_lock_sha256':CONTRACT['dependency_lock_sha256'],'counts_source':'exact_commit_required_ci_gate',
              'engine':CONTRACT.get('engine','chromium'),'browser_version':CONTRACT['browser_version'],'viewports':CONTRACT['viewports'],'execution_location':'github_hosted_disposable_runner'}
    if any(report.get(k)!=v for k,v in expected.items()): return False
    if report.get('backend_mocked') is not CONTRACT.get('backend_mocked',True) or any(report.get(k) is not False for k in ('vps_local_execution','production_access','physical_device_test','pixel_baseline_test','published')): return False
    if any(type(report[k]) is not int or report[k]<=0 for k in ('ci_run_id','ci_attempt','ci_job_id')): return False
    if report['ci_url']!='https://github.com/'+REPO+'/actions/runs/'+str(report['ci_run_id']): return False
    if type(report['checked_at']) not in (int,float) or not math.isfinite(report['checked_at']) or report['checked_at']<=0: return False
    if report['status']=='failed': return all(report[k] is None for k in ('counts','screenshots','advisories','artifact'))
    if report['status']!='passed' or report['counts']!={'tests':CONTRACT['expected_tests'],'pass':CONTRACT['expected_tests'],'fail':0,'errors':0,'skipped':0} or any(type(x) is not int for x in report['counts'].values()): return False
    if type(report['screenshots']) is not int or report['screenshots']!=15 or report['advisories']!=CONTRACT['advisories']: return False
    a=report['artifact']
    if not isinstance(a,dict) or set(a)!={'id','name','digest','size_bytes','expires_at','url'}: return False
    if (type(a['id']) is not int or a['id']<=0 or a['name']!=CONTRACT['artifact_name_prefix']+str(report['ci_attempt']) or
            not isinstance(a['digest'],str) or not re.fullmatch('sha256:[0-9a-f]{64}',a['digest']) or
            type(a['size_bytes']) is not int or not 1000<a['size_bytes']<=25*1024**2 or
            a['url']!='https://github.com/'+REPO+'/actions/runs/'+str(report['ci_run_id'])+'/artifacts/'+str(a['id'])): return False
    try: return expires(a['expires_at'])>report['checked_at']
    except (ValueError,TypeError,OverflowError): return False


def save(conn,job,report):
    scope(job)
    if not valid(report): raise broker.Blocked('browser_ci_report_contract_changed')
    with q._write(conn):
        now=time.time();owned=q._owned(conn,job['id'],job['lease_token'],now)
        row=conn.execute('SELECT project,kind,payload FROM agent_jobs WHERE id=?',(job['id'],)).fetchone()
        if row[:2]!=('nova','test_release') or json.loads(row[2])!={'target':PROFILE} or not owned[3]<=report['checked_at']<=now: raise broker.Blocked('browser_ci_observation_changed')
        row=conn.execute('SELECT id,report,report_sha256 FROM browser_ci_runs WHERE job_id=?',(job['id'],)).fetchone()
        if row:
            old=json.loads(row[1])
            if not valid(old) or util.digest(old)!=row[2] or {k:v for k,v in old.items() if k!='checked_at'}!={k:v for k,v in report.items() if k!='checked_at'}: raise broker.Blocked('browser_ci_saved_evidence_changed')
            report=old;ident=row[0]
        else:
            ident=conn.execute('INSERT INTO browser_ci_runs(job_id,report,report_sha256,created_at) VALUES(?,?,?,?)',
                               (job['id'],util.canonical(report),util.digest(report),now)).lastrowid
    return {'browser_ci_id':ident,'report_sha256':util.digest(report),'test_status':report['status'],'test_counts':report['counts'],
            'revision':report['source_revision'],'harness_commit':report['harness_commit'],'ci_url':report['ci_url'],
            'ci_run_id':report['ci_run_id'],'ci_attempt':report['ci_attempt'],'artifact_url':report['artifact']['url'] if report['artifact'] else None,
            'screenshots':report['screenshots'],'advisories':report['advisories'],'backend_mocked':CONTRACT.get('backend_mocked',True),'vps_local_execution':False,'published':False}


def describe(conn):
    lines=['NOVA WEB · браузерный GitHub CI','Версия NOVA: '+CONTRACT['source_revision']]
    row=conn.execute('SELECT id,job_id,report,report_sha256 FROM browser_ci_runs ORDER BY id DESC LIMIT 1').fetchone()
    if row:
        report=json.loads(row[2])
        if not valid(report) or util.digest(report)!=row[3]: lines.append('Основание изменено; нужна новая сверка.')
        else:
            lines.extend([f'Отчёт #{row[0]} · /job {row[1]} · {report["status"]}',report['ci_url'],
                          'Chromium '+report['browser_version']+' · 360×800 / 768×1024 / 1440×900',
                          'Тесты по обязательной CI-проверке: '+json.dumps(report['counts'],ensure_ascii=False),
                          'Сверка UTC: '+time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(report['checked_at']))])
            if report['artifact']:
                lines.extend(['15 скриншотов и отчёт: '+report['artifact']['url'],'Хранятся до '+report['artifact']['expires_at']])
                if expires(report['artifact']['expires_at'])<=time.time(): lines.append('Срок хранения архива истёк; прежний отчёт остаётся историей.')
            if report['advisories']: lines.append('Замечания: русские подсказки на UZ-странице; кнопки языка меньше44px. Исправления ещё не опубликованы.')
    else: lines.append('Браузерный CI ещё не сверен на VPS.')
    lines.extend(['Обновить сверку: /test_nova_browser. Запуск на временном GitHub runner, API подставной; реальных заявок нет.',
                  'Это Chromium и размеры экрана, не реальные телефоны, Safari/Firefox, сравнение с эталоном или полный аудит доступности.'])
    return '\n'.join(lines)
