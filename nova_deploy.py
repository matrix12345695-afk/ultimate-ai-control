"""Non-mutating NOVA publication plan and fixture-only protocol acceptance."""
import hashlib
import json
from pathlib import Path
import time
import locked_build_ci as ci
import artifact_prs as util
import artifact_pr_broker as broker
import task_queue as q
import nova_deploy_machine as machine
import nova_deploy_fixture as simulator

PROFILE='nova-deploy-plan-v1'
HERE=Path(__file__).resolve().parent
OBSERVATION=json.loads((HERE/'nova_deploy_observation.json').read_text())
EXPECTED_SIM={'cases':3,'pass':3,'fail':0,'outcomes':[{'scenario':'success','state':'succeeded','mutations_simulated':2},{'scenario':'rollback','state':'rolled_back','mutations_simulated':3},{'scenario':'ambiguous','state':'ambiguous','mutations_simulated':2}],'provider':'in_memory_fixture','real_Render_calls':0,'production_mutations':0,'published':False}


def definition_digest():
    files={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in
           ('nova_deploy.py','nova_deploy_machine.py','nova_deploy_fixture.py','nova_deploy_observation.json')}
    return util.digest({'files':files,'ci_contract':util.digest(ci.CONTRACT)})


def initialize(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS nova_publication_plans(
      id INTEGER PRIMARY KEY,job_id INTEGER NOT NULL UNIQUE,report TEXT NOT NULL,
      report_sha256 TEXT NOT NULL,created_at REAL NOT NULL)''');conn.commit()


def scope(job):
    if job.get('project')!='nova' or job.get('kind')!='test_release' or job.get('payload')!={'target':PROFILE}: raise broker.Blocked('nova_deploy_scope_denied')


def report_for(evidence,at,sim):
    if not ci.valid(evidence) or evidence['status']!='passed': raise broker.Blocked('locked_source_ci_not_verified')
    if sim!=EXPECTED_SIM or any(type(sim.get(k)) is not int for k in ('cases','pass','fail','real_Render_calls','production_mutations')) or sim.get('published') is not False: raise broker.Blocked('publication_simulator_failed')
    obs=OBSERVATION
    identity=(obs['workspace']==machine.WORKSPACE and obs['service']==machine.SERVICE and
              obs['repository']=='https://github.com/'+machine.REPOSITORY and obs['type']=='web_service' and obs['runtime']=='node' and
              obs['suspended']=='not_suspended' and obs['live']=={'id':machine.BASE_DEPLOY,'commit':machine.BASE,'status':'live'} and
              obs['repo']['full_name']==machine.REPOSITORY and obs['repo']['id']==1426666605 and
              obs['repo']['main']==machine.BASE and obs['repo']['head']==machine.CANDIDATE and obs['repo']['state']=='open' and
              obs['repo']['draft'] is True and obs['repo']['merged'] is False)
    checks={'exact_locked_ci':True,'platform_and_branch_identity':bool(identity),
            'platform_snapshot_fresh':0<=at-obs['observed_at']<=900,
            'ci_observation_fresh':0<=at-evidence['checked_at']<=900,
            'expected_configuration_observed':obs['settings']==machine.BEFORE,
            'no_active_deploy_seen_in_sample':obs['queue_sample']['active_seen'] is False,
            'deploy_queue_fully_verified':obs['queue_sample']['complete'] is True,
            'production_backup_verified':obs['backup_verified'] is True,
            'retained_Render_artifact_verified':obs['retained_build_verified'] is True,
            'provider_publication_access_ready':obs['provider_access_ready'] is True,
            'live_executor_enabled':False,'exact_owner_approval':False}
    blockers=[key for key,value in checks.items() if not value]
    binding={'project':'nova','workspace':machine.WORKSPACE,'service':machine.SERVICE,'repository':machine.REPOSITORY,
             'candidate':machine.CANDIDATE,'base':machine.BASE,'baseline_deploy':machine.BASE_DEPLOY,
             'settings_before':obs['settings'],'settings_proposed':dict(machine.AFTER),
             'lock_sha256':ci.CONTRACT['dependency_lock_sha256'],'ci_run_id':evidence['ci_run_id'],'ci_attempt':evidence['ci_attempt'],
             'ci_harness':evidence['harness_commit'],'ci_contract_sha256':evidence['contract_sha256'],
             'archive_digest':evidence['artifact']['digest'],'snapshot_sha256':util.digest(obs),'expires_at':at+900,
             'conditional_rollback_scope':{'baseline_deploy':machine.BASE_DEPLOY,'no_database_restore':True,'retain_auto_deploy_off':True}}
    return {'schema':PROFILE,'definition_sha256':definition_digest(),'created_at':at,'mode':'dry_run_only',
            'scope':binding,'scope_sha256':util.digest(binding),'ci':evidence,'observation':obs,
            'checks':checks,'blockers':blockers,'plan_state':'blocked','simulation':sim,
            'may_request_approval':False,'publish_allowed':False,'production_mutations':0,'published':False}


def valid(report):
    try:
        return (isinstance(report,dict) and report==report_for(report['ci'],report['created_at'],report['simulation']) and
                type(report['created_at']) in (int,float) and report['created_at']>0 and
                report['publish_allowed'] is False and report['may_request_approval'] is False and report['published'] is False and report['production_mutations']==0 and type(report['production_mutations']) is int)
    except (KeyError,TypeError,ValueError,broker.Blocked): return False


def save(conn,job,report):
    scope(job)
    if not valid(report): raise broker.Blocked('publication_plan_report_changed')
    with q._write(conn):
        now=time.time();owned=q._owned(conn,job['id'],job['lease_token'],now)
        row=conn.execute('SELECT project,kind,payload FROM agent_jobs WHERE id=?',(job['id'],)).fetchone()
        if row[:2]!=('nova','test_release') or json.loads(row[2])!={'target':PROFILE} or not owned[3]<=report['created_at']<=now: raise broker.Blocked('publication_plan_lease_scope_changed')
        old=conn.execute('SELECT id,report,report_sha256 FROM nova_publication_plans WHERE job_id=?',(job['id'],)).fetchone()
        if old:
            prior=json.loads(old[1])
            if not valid(prior) or util.digest(prior)!=old[2]: raise broker.Blocked('saved_publication_plan_changed')
            report=prior;ident=old[0]
        else:
            ident=conn.execute('INSERT INTO nova_publication_plans(job_id,report,report_sha256,created_at) VALUES(?,?,?,?)',(job['id'],util.canonical(report),util.digest(report),now)).lastrowid
    return {'nova_deploy_report_id':ident,'report_sha256':util.digest(report),'plan_state':'blocked',
            'scope_sha256':report['scope_sha256'],'simulation_cases':3,'ci_url':report['ci']['ci_url'],
            'publish_allowed':False,'published':False,'production_mutations':0,'blockers':report['blockers']}


def describe(conn):
    lines=['NOVA WEB · протокол публикации · только проверка',
           'Точная версия: '+machine.CANDIDATE,'Сервис: '+machine.SERVICE]
    row=conn.execute('SELECT id,job_id,report,report_sha256 FROM nova_publication_plans ORDER BY id DESC LIMIT 1').fetchone()
    if row:
        report=json.loads(row[2])
        if not valid(report) or util.digest(report)!=row[3]: lines.append('Основание изменено; нужна новая проверка.')
        else:
            lines.extend([f'План #{row[0]} · /job {row[1]} · выпуск заблокирован',
                          'Отпечаток согласования: '+report['scope_sha256'],
                          'Согласование сейчас не запрашивается: условия ещё не выполнены.',
                          '✅ Симулятор: успешный выпуск, условный откат и потерянный ответ API. Это три фиктивных сценария, без вызовов Render.',
                          'Связанный CI:83 проверки. '+report['ci']['ci_url'],
                          'Снимок платформы: '+report['observation']['observed_utc'],
                          'Осталось: полная проверка очереди платформы, рабочей резервной копии и доступной сборки отката; доступ провайдера; включение проверенного исполнителя и отдельное точное согласование.'])
            if report['scope']['expires_at']<=time.time(): lines.append('Этот план устарел; перед решением нужна новая сверка.')
            if not report['checks']['platform_snapshot_fresh']: lines.append('Снимок Render уже был устаревшим при расчёте; требуется новое чтение платформы.')
            if not report['checks']['platform_and_branch_identity']: lines.append('Сервис, ветка или текущая версия отличаются от проверенной области.')
    else: lines.append('Живой отчёт ещё не сохранён.')
    lines.extend(['Протокол связывает проект/коммит/сервис/настройки/CI/срок. Неизвестный итог записи API запрещает слепой повтор; журнал сохраняется перед запросом.',
                  'Исполнение сейчас доступно только симулятору. Настройки, секреты, БД, Inventory и рабочий сайт эта команда не изменяет.',
                  'Обновить расчёт CI/плана: /test_nova_deploy. Новый снимок Render не получается этой командой автоматически.'])
    return '\n'.join(lines)
