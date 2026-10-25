"""Read-only hosted release rehearsal and historical Render audit; no publisher."""
import json
import math
from pathlib import Path
import time
import artifact_prs as util
import artifact_pr_broker as broker
import hosted_ci
import task_queue as q

PROFILE='nova-release-rehearsal-v1'
CONTRACT=json.loads(Path(__file__).with_name('nova_release_contract.json').read_text())
SNAPSHOT=json.loads(Path(__file__).with_name('nova_render_snapshot.json').read_text())
REPO='matrix12345695-afk/ultimate-ai-control'
BLOCKERS=['http_health_check_not_configured','main_commit_triggers_auto_deploy',
          'retained_Render_artifact_eligibility_unverified','Render_platform_rollback_not_executed',
          'current_Render_state_revalidation_required','exact_NOVA_owner_approval_required',
          'publication_adapter_not_enabled','production_dependency_lock_unpinned']


def initialize(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS nova_release_ci_runs(
      id INTEGER PRIMARY KEY,job_id INTEGER NOT NULL UNIQUE,report TEXT NOT NULL,
      report_sha256 TEXT NOT NULL,created_at REAL NOT NULL)''');conn.commit()


def scope(job):
    if job.get('project')!='nova' or job.get('kind')!='test_release' or job.get('payload')!={'target':PROFILE}: raise broker.Blocked('nova_release_scope_denied')


def snapshot_valid():
    return (util.digest(SNAPSHOT)==CONTRACT['render_snapshot_sha256'] and SNAPSHOT['workspace_id']=='tea-d52kjcur433s73ca9810'
            and SNAPSHOT['service_id']=='srv-dbbhm5k9v7es73f9kf10' and SNAPSHOT['repository']=='https://github.com/matrix12345695-afk/nova-web-agency'
            and SNAPSHOT['live_commit']==CONTRACT['base_revision'] and SNAPSHOT['health_check_path']==''
            and SNAPSHOT['auto_deploy']=='commit' and SNAPSHOT['settings_changed'] is False and SNAPSHOT['retained_build_available'] is None)


def observe(client):
    if not snapshot_valid(): raise broker.Blocked('nova_release_snapshot_changed')
    run,job,passed=hosted_ci.inspect(client,CONTRACT)
    return {'schema':PROFILE,'contract_sha256':util.digest(CONTRACT),'repository':REPO,
            'harness_commit':CONTRACT['harness_commit'],'base_revision':CONTRACT['base_revision'],
            'candidate_revision':CONTRACT['candidate_revision'],'source_manifest_sha256':CONTRACT['source_manifest_sha256'],
            'dependency_lock_sha256':CONTRACT['dependency_lock_sha256'],'render_snapshot_sha256':util.digest(SNAPSHOT),
            'render_snapshot_observed_at':SNAPSHOT['observed_at'],'ci_run_id':run['id'],'ci_attempt':run['run_attempt'],'ci_job_id':job['id'],
            'ci_url':'https://github.com/'+REPO+'/actions/runs/'+str(run['id']),'status':'passed' if passed else 'failed',
            'nova_test_counts':{'tests':34,'pass':34,'fail':0,'cancelled':0,'skipped':0,'todo':0} if passed else None,
            'rehearsal_counts':{'tests':15,'pass':15,'fail':0,'errors':0,'skipped':0} if passed else None,
            'counts_source':'exact_commit_required_ci_gate','postgres_major':16 if passed else None,
            'real_loopback_http_verified':passed,'upgrade_data_preservation_verified':passed,
            'rollback_data_preservation_verified':passed,'candidate_era_fixture_preserved':passed,'failed_candidate_not_promoted':passed,
            'execution_location':'github_hosted_disposable_runner','vps_local_execution':False,
            'Render_rollback_executed':False,'Render_artifact_eligibility_verified':False,'database_restored':False,
            'production_access':False,'owner_approval_created':False,'publish_allowed':False,'merged':False,'published':False,
            'blockers':BLOCKERS[:],'checked_at':time.time()}


def valid(report):
    if not isinstance(report,dict) or not snapshot_valid(): return False
    fixed={'schema':PROFILE,'contract_sha256':util.digest(CONTRACT),'repository':REPO,'harness_commit':CONTRACT['harness_commit'],
           'base_revision':CONTRACT['base_revision'],'candidate_revision':CONTRACT['candidate_revision'],
           'source_manifest_sha256':CONTRACT['source_manifest_sha256'],'dependency_lock_sha256':CONTRACT['dependency_lock_sha256'],
           'render_snapshot_sha256':util.digest(SNAPSHOT),'render_snapshot_observed_at':SNAPSHOT['observed_at'],
           'counts_source':'exact_commit_required_ci_gate','execution_location':'github_hosted_disposable_runner','blockers':BLOCKERS}
    booleans=('real_loopback_http_verified','upgrade_data_preservation_verified','rollback_data_preservation_verified','candidate_era_fixture_preserved','failed_candidate_not_promoted')
    prohibited=('vps_local_execution','Render_rollback_executed','Render_artifact_eligibility_verified','database_restored','production_access','owner_approval_created','publish_allowed','merged','published')
    if set(report)!=set(fixed)|set(booleans)|set(prohibited)|{'ci_run_id','ci_attempt','ci_job_id','ci_url','status','nova_test_counts','rehearsal_counts','postgres_major','checked_at'}: return False
    if any(report[k]!=v for k,v in fixed.items()) or any(report[k] is not False for k in prohibited): return False
    if any(type(report[k]) is not int or report[k]<=0 for k in ('ci_run_id','ci_attempt','ci_job_id')): return False
    if report['ci_url']!='https://github.com/'+REPO+'/actions/runs/'+str(report['ci_run_id']): return False
    if type(report['checked_at']) not in (int,float) or not math.isfinite(report['checked_at']) or report['checked_at']<=0: return False
    passed=report['status']=='passed'
    if report['status'] not in ('passed','failed') or any(report[k] is not passed for k in booleans): return False
    if passed and any(not isinstance(report[k],dict) or any(type(v) is not int for v in report[k].values()) for k in ('nova_test_counts','rehearsal_counts')): return False
    return (report['nova_test_counts']==({'tests':34,'pass':34,'fail':0,'cancelled':0,'skipped':0,'todo':0} if passed else None)
            and report['rehearsal_counts']==({'tests':15,'pass':15,'fail':0,'errors':0,'skipped':0} if passed else None)
            and type(report['postgres_major']) is (int if passed else type(None)) and report['postgres_major']==(16 if passed else None))


def save(conn,job,report):
    scope(job)
    if not valid(report): raise broker.Blocked('nova_release_report_contract_changed')
    with q._write(conn):
        now=time.time();owned=q._owned(conn,job['id'],job['lease_token'],now)
        row=conn.execute('SELECT project,kind,payload FROM agent_jobs WHERE id=?',(job['id'],)).fetchone()
        if row[:2]!=('nova','test_release') or json.loads(row[2])!={'target':PROFILE} or not owned[3]<=report['checked_at']<=now: raise broker.Blocked('nova_release_observation_changed')
        row=conn.execute('SELECT id,report,report_sha256 FROM nova_release_ci_runs WHERE job_id=?',(job['id'],)).fetchone()
        if row:
            old=json.loads(row[1])
            if not valid(old) or util.digest(old)!=row[2] or {k:v for k,v in old.items() if k!='checked_at'}!={k:v for k,v in report.items() if k!='checked_at'}: raise broker.Blocked('nova_release_saved_evidence_changed')
            report=old;ident=row[0]
        else:
            ident=conn.execute('INSERT INTO nova_release_ci_runs(job_id,report,report_sha256,created_at) VALUES(?,?,?,?)',
                               (job['id'],util.canonical(report),util.digest(report),now)).lastrowid
    return {'nova_release_ci_id':ident,'report_sha256':util.digest(report),'test_status':report['status'],
            'nova_test_counts':report['nova_test_counts'],'rehearsal_counts':report['rehearsal_counts'],
            'revision':report['candidate_revision'],'harness_commit':report['harness_commit'],'ci_url':report['ci_url'],
            'ci_run_id':report['ci_run_id'],'ci_attempt':report['ci_attempt'],'publish_allowed':False,'published':False,
            'Render_rollback_executed':False,'vps_local_execution':False,'blockers':report['blockers']}


def describe(conn):
    lines=['NOVA WEB · подготовка выпуска · публикация отключена',
           'Черновик: '+CONTRACT['candidate_revision'],
           'https://github.com/matrix12345695-afk/nova-web-agency/pull/15']
    row=conn.execute('SELECT id,job_id,report,report_sha256 FROM nova_release_ci_runs ORDER BY id DESC LIMIT 1').fetchone()
    if row:
        report=json.loads(row[2])
        if not valid(report) or util.digest(report)!=row[3]: lines.append('Основание изменено; нужна новая сверка.')
        else:
            lines.extend([f'Отчёт #{row[0]} · /job {row[1]} · {report["status"]}',report['ci_url'],
                          'Сверка CI UTC: '+time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(report['checked_at']))])
            if report['status']=='passed': lines.append('✅ Выполнено:34 теста NOVA и15 проверок перехода старая → новая → старая версия через настоящий локальный HTTP и PostgreSQL16. Все четыре таблицы и тестовые записи новой версии сохранились без восстановления БД.')
            else: lines.append('Репетиция не прошла; переход и сохранность данных не подтверждены.')
    else: lines.append('Репетиция ещё не сверена на VPS.')
    lines.extend(['Render: исторический снимок '+SNAPSHOT['observed_at']+'. Перед выпуском требуется новое чтение платформы.',
                  'Сервис '+SNAPSHOT['service_id']+'; текущий на момент снимка deploy '+SNAPSHOT['live_deploy_id']+'.',
                  'Осталось: настроить HTTP /health (сейчас только порт); учесть автопубликацию main; закрепить зависимости; проверить доступность старой сборки и фактический откат Render; подготовить исполнителя и получить согласование точной версии.',
                  'Репетиция на GitHub не выполняла откат Render. Только фиктивные данные, без реальных заявок и доступа к рабочей БД.',
                  'Обновить сверку CI: /test_nova_release. Состояние Render на VPS автоматически не обновляется.'])
    return '\n'.join(lines)
