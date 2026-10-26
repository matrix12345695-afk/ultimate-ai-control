"""Exact-commit hosted CI evidence, never represented as VPS-local execution."""
import json
import math
from pathlib import Path
import time
import artifact_prs as util
import artifact_pr_broker as broker
import task_queue as q

PROFILE='nova-recovery-ci-v1'
CONTRACT=json.loads(Path(__file__).with_name('nova_recovery_contract.json').read_text())
REPO='matrix12345695-afk/ultimate-ai-control'


def initialize(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS nova_recovery_ci_runs(
      id INTEGER PRIMARY KEY,job_id INTEGER NOT NULL UNIQUE,report TEXT NOT NULL,
      report_sha256 TEXT NOT NULL,created_at REAL NOT NULL)''');conn.commit()


def scope(job):
    if job.get('project')!='nova' or job.get('kind')!='test_release' or job.get('payload')!={'target':PROFILE}: raise broker.Blocked('nova_ci_scope_denied')


def observe(client):
    import hosted_ci
    run,job,passed=hosted_ci.inspect(client,CONTRACT)
    artifact=None
    if passed:
        uploads=[step for step in job['steps'] if step.get('name')==CONTRACT['upload_step']]
        if len(uploads)!=1 or uploads[0].get('status')!='completed' or uploads[0].get('conclusion')!='success': raise broker.Blocked('recovery_artifact_upload_not_verified')
        data=client.call('GET','/actions/runs/'+str(run['id'])+'/artifacts?per_page=100')
        if not isinstance(data,dict) or type(data.get('total_count')) is not int or not 0<=data['total_count']<=100 or not isinstance(data.get('artifacts'),list) or len(data['artifacts'])!=data['total_count']: raise broker.Blocked('recovery_archive_listing_incomplete')
        rows=[row for row in data['artifacts'] if row.get('name')==CONTRACT['artifact_name_prefix']+str(run['run_attempt'])]
        if not rows: raise broker.Pending('recovery_archive_not_visible')
        if len(rows)!=1: raise broker.Blocked('recovery_archive_ambiguous')
        row=rows[0];origin=row.get('workflow_run',{})
        artifact={'id':row.get('id'),'name':row.get('name'),'digest':row.get('digest'),'size_bytes':row.get('size_in_bytes'),'expires_at':row.get('expires_at'),'url':'https://github.com/'+REPO+'/actions/runs/'+str(run['id'])+'/artifacts/'+str(row.get('id'))}
        if (not artifact_valid(artifact,run['id'],run['run_attempt']) or row.get('expired') is not False or origin.get('id')!=run['id'] or origin.get('head_sha')!=CONTRACT['harness_commit'] or origin.get('repository_id')!=1429215344 or origin.get('head_repository_id')!=1429215344): raise broker.Blocked('recovery_archive_identity_changed')
        if expires(artifact['expires_at'])<=time.time(): raise broker.Blocked('recovery_archive_expired')
        final=client.call('GET','/actions/runs/'+str(run['id']))
        if any(final.get(k)!=run.get(k) for k in ('id','run_attempt','head_sha','status','conclusion','event','path')): raise broker.Pending('recovery_ci_changed_during_archive_read')
    return report_for(run['id'],run['run_attempt'],job['id'],passed,artifact,time.time())


def artifact_valid(item,run,attempt):
    import re
    try:
        return (isinstance(item,dict) and set(item)=={'id','name','digest','size_bytes','expires_at','url'} and type(item['id']) is int and item['id']>0 and item['name']==CONTRACT['artifact_name_prefix']+str(attempt) and isinstance(item['digest'],str) and re.fullmatch('sha256:[0-9a-f]{64}',item['digest']) is not None and type(item['size_bytes']) is int and 500<item['size_bytes']<=128*1024 and expires(item['expires_at'])>0 and item['url']=='https://github.com/'+REPO+'/actions/runs/'+str(run)+'/artifacts/'+str(item['id']))
    except (ValueError,TypeError,KeyError,OverflowError): return False


def expires(value):
    from datetime import datetime
    if not isinstance(value,str): raise ValueError('expiry_missing')
    date=datetime.fromisoformat(value.replace('Z','+00:00'))
    if date.tzinfo is None: raise ValueError('expiry_timezone_missing')
    return date.timestamp()


SNAPSHOT=json.loads(Path(__file__).with_name('nova_recovery_snapshot.json').read_text())


def report_for(run,attempt,job,passed,artifact,at):
    if util.digest(SNAPSHOT)!=CONTRACT['platform_snapshot_sha256']: raise ValueError('recovery_platform_snapshot_changed')
    return {'schema':PROFILE,'contract_sha256':util.digest(CONTRACT),'repository':REPO,'harness_commit':CONTRACT['harness_commit'],'source_revision':CONTRACT['source_revision'],'source_manifest_sha256':CONTRACT['source_manifest_sha256'],'dependency_lock_sha256':CONTRACT['dependency_lock_sha256'],'ci_run_id':run,'ci_attempt':attempt,'ci_job_id':job,'ci_url':'https://github.com/'+REPO+'/actions/runs/'+str(run),'status':'passed' if passed else 'failed','counts':{'tests':24,'pass':24,'fail':0,'errors':0,'skipped':0} if passed else None,'counts_source':'exact_commit_required_ci_gate','postgres_major':18 if passed else None,'fixture_restore_verified':passed,'fixture_leads':5003 if passed else None,'legacy_export_limit':5000 if passed else None,'all_four_tables_preserved':passed,'archive':artifact,'platform_snapshot':SNAPSHOT,'platform_snapshot_sha256':util.digest(SNAPSHOT),'execution_location':'github_hosted_disposable_runner','production_access':False,'production_backup_verified':False,'Render_rollback_eligible':False,'Render_rollback_executed':False,'publish_allowed':False,'vps_local_execution':False,'published':False,'checked_at':at}


def valid(report):
    try:
        if not isinstance(report,dict) or report['status'] not in ('passed','failed'): return False
        passed=report['status']=='passed'
        if type(report['checked_at']) not in (int,float) or not math.isfinite(report['checked_at']) or report['checked_at']<=0: return False
        if any(type(report[k]) is not int or report[k]<=0 for k in ('ci_run_id','ci_attempt','ci_job_id')): return False
        if passed and (not artifact_valid(report['archive'],report['ci_run_id'],report['ci_attempt']) or any(type(v) is not int for v in report['counts'].values())): return False
        if not passed and report['archive'] is not None: return False
        if any(report[k] is not False for k in ('production_access','production_backup_verified','Render_rollback_eligible','Render_rollback_executed','publish_allowed','vps_local_execution','published')): return False
        if report['fixture_restore_verified'] is not passed or report['all_four_tables_preserved'] is not passed: return False
        return report==report_for(report['ci_run_id'],report['ci_attempt'],report['ci_job_id'],passed,report['archive'],report['checked_at'])
    except (KeyError,TypeError,ValueError): return False


def save(conn,job,report):
    scope(job)
    if not valid(report): raise broker.Blocked('nova_ci_report_contract_changed')
    with q._write(conn):
        now=time.time();owned=q._owned(conn,job['id'],job['lease_token'],now)
        row=conn.execute('SELECT project,kind,payload FROM agent_jobs WHERE id=?',(job['id'],)).fetchone()
        if row[:2]!=('nova','test_release') or json.loads(row[2])!={'target':PROFILE} or not owned[3]<=report['checked_at']<=now:
            raise broker.Blocked('nova_ci_job_observation_changed')
        row=conn.execute('SELECT id,report,report_sha256 FROM nova_recovery_ci_runs WHERE job_id=?',(job['id'],)).fetchone()
        if row:
            previous=json.loads(row[1]);old={k:v for k,v in previous.items() if k!='checked_at'};new={k:v for k,v in report.items() if k!='checked_at'}
            if not valid(previous) or util.digest(previous)!=row[2] or old!=new: raise broker.Blocked('nova_ci_saved_evidence_changed')
            report=previous;ident=row[0]
        else:
            ident=conn.execute('INSERT INTO nova_recovery_ci_runs(job_id,report,report_sha256,created_at) VALUES(?,?,?,?)',
                (job['id'],util.canonical(report),util.digest(report),now)).lastrowid
    return {'nova_recovery_ci_id':ident,'report_sha256':util.digest(report),'test_status':report['status'],'test_counts':report['counts'],'revision':CONTRACT['source_revision'],'ci_url':report['ci_url'],'ci_run_id':report['ci_run_id'],'ci_attempt':report['ci_attempt'],'artifact_url':report['archive']['url'] if report['archive'] else None,'fixture_restore_verified':report['fixture_restore_verified'],'production_backup_verified':False,'published':False,'vps_local_execution':False}


def describe(conn):
    lines=['NOVA WEB · восстановление PostgreSQL18 · тестовая проверка',
           'Версия: '+CONTRACT['source_revision']]
    row=conn.execute('SELECT id,job_id,report,report_sha256 FROM nova_recovery_ci_runs ORDER BY id DESC LIMIT 1').fetchone()
    if row:
        report=json.loads(row[2])
        if not valid(report) or util.digest(report)!=row[3]: lines.append('Основание изменено; нужна новая сверка.')
        else:
            lines.extend([f'Отчёт #{row[0]} · /job {row[1]} · {report["status"]}',report['ci_url']])
            if report['status']=='passed':
                lines.extend(['✅24 проверки: полный дамп схемы приложения и восстановление5003 синтетических заявок, всех4 таблиц, ID/sequence, ограничений и служебных записей. Экспорт из согласованного read-only snapshot.',
                              'Проверено ограничение старого /backup: не более5000 заявок; JSON не заменяет дамп всей схемы.',report['archive']['url']])
                if expires(report['archive']['expires_at'])<=time.time(): lines.append('Архив истёк; отчёт исторический.')
    else: lines.append('CI восстановления ещё не сверен на VPS.')
    lines.extend(['Снимок Render '+SNAPSHOT['observed_utc']+': '+SNAPSHOT['database_name']+', Free, PostgreSQL18, срок до19.11.2026 08:40 UTC.',
                  'У бесплатного тарифа нет управляемого PITR/экспортов. Подключённый SQL-инструмент заблокирован пустым внешним allowlist; доступ не расширялся.',
                  'База указана в старом runbook NOVA; текущее подключение приложения без чтения секрета не подтверждено.',
                  'Реальная приватная копия/её восстановление и доступность сборки отката Render ещё НЕ подтверждены. Публикация отключена.',
                  'Дампы не загружаются в GitHub: архив CI содержит только синтетические счётчики/хеши и публичные source pins.',
                  'Обновить только CI-сверку: /test_nova_recovery. Новый снимок Render автоматически не получается. /owner_later'])
    return '\n'.join(lines)
