"""Local-only emergency acceptance. All stop/reset actions target :memory: only."""
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import time
import approval
import emergency_control as control
import owner_notifications as inbox
import task_queue as q
import artifact_prs as util
PROFILE='emergency-control-v1'


def initialize(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS emergency_selftest_runs(
      id INTEGER PRIMARY KEY,job_id INTEGER NOT NULL UNIQUE,report TEXT NOT NULL,
      report_sha256 TEXT NOT NULL,created_at REAL NOT NULL)''');conn.commit()


def implementation_digest():
    root=Path(__file__).resolve().parent
    return util.digest({name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in
                        ('emergency_control.py','emergency_selftest.py','task_queue.py','approval.py','artifact_pr_broker.py','metered_provider.py')})


def acceptance():
    checks={}
    def check(name,condition):
        if not condition: raise AssertionError('emergency_selftest_'+name)
        checks[name]=True
    with sqlite3.connect(':memory:') as conn:
        q.initialize(conn);inbox.initialize(conn);approval.init_approvals(conn)
        ident=q.enqueue(conn,'control','test_release',{'target':'fixture'});job=q.claim(conn,'fixture-only',q.KINDS)
        aid=approval.request_approval(conn,1,'publish_exact_version','production',{'fixture':True});approval.decide(conn,aid,'fixture-owner','fixture-owner',True)
        stopped=control.stop(conn,source_key='fixture-stop-1');control.stop(conn,source_key='fixture-stop-1')
        check('latched_and_deduplicated',stopped['latched'] and conn.execute("SELECT count(*) FROM owner_notifications WHERE kind='critical'").fetchone()[0]==1)
        q.enqueue(conn,'control','test_release',{'target':'next-fixture'})
        check('no_new_claims',q.claim(conn,'next',q.KINDS) is None)
        try: q.configure(conn,paused=False)
        except control.Stopped: rejected=True
        else: rejected=False
        check('ordinary_resume_blocked',rejected)
        try: control.admit(conn,'github_draft_write','fixture',job_id=job['id'],lease_token=job['lease_token'])
        except control.Stopped: rejected=True
        else: rejected=False
        check('new_mutation_admission_blocked',rejected and not conn.execute('SELECT count(*) FROM uac_action_admissions').fetchone()[0])
        try: control.reset(conn,1)
        except control.Stopped as exc: rejected=str(exc)=='emergency_jobs_still_running'
        else: rejected=False
        check('running_jobs_must_drain',rejected)
        q.finish(conn,ident,job['lease_token'],{'fixture':True});control.reset(conn,1,source_key='fixture-reset-1')
        current=control.state(conn);paused=conn.execute('SELECT paused FROM agent_queue_control').fetchone()[0]
        check('separate_reset_and_resume',not current['latched'] and current['epoch']==2 and paused==1)
        check('old_approval_stays_invalid',not approval.is_authorized(conn,aid,1,'publish_exact_version','production',{'fixture':True}))
        control.stop(conn,source_key='fixture-stop-1')
        q.configure(conn,paused=False);fresh=q.claim(conn,'fixture-fresh',q.KINDS)
        check('replayed_old_stop_is_not_reexecuted',not control.state(conn)['latched'] and fresh and conn.execute('SELECT control_epoch FROM agent_jobs WHERE id=?',(fresh['id'],)).fetchone()[0]==2)
    return {'schema':PROFILE,'checks':checks,'counts':{'tests':8,'pass':8,'fail':0},
            'implementation_sha256':implementation_digest(),'checked_at':time.time(),
            'execution':'isolated_in_memory_database','network_calls':0,'live_control_changed':False,
            'service_signals':0,'paid_calls':0,'published':False}


CHECKS={'latched_and_deduplicated','no_new_claims','ordinary_resume_blocked','new_mutation_admission_blocked',
        'running_jobs_must_drain','separate_reset_and_resume','old_approval_stays_invalid','replayed_old_stop_is_not_reexecuted'}


def valid(report):
    try:
        return (isinstance(report,dict) and set(report)=={'schema','checks','counts','implementation_sha256','checked_at','execution','network_calls','live_control_changed','service_signals','paid_calls','published'}
                and report['schema']==PROFILE and isinstance(report['checks'],dict) and set(report['checks'])==CHECKS and all(v is True for v in report['checks'].values())
                and report['counts']=={'tests':8,'pass':8,'fail':0} and all(type(v) is int for v in report['counts'].values())
                and isinstance(report['implementation_sha256'],str) and re.fullmatch('[0-9a-f]{64}',report['implementation_sha256']) is not None
                and type(report['checked_at']) in (int,float) and 0<report['checked_at']<float('inf')
                and report['execution']=='isolated_in_memory_database' and report['live_control_changed'] is False and report['published'] is False
                and all(type(report[k]) is int and report[k]==0 for k in ('network_calls','service_signals','paid_calls')))
    except (KeyError,TypeError,ValueError): return False


def save(conn,job,report):
    if job.get('project')!='control' or job.get('kind')!='test_release' or job.get('payload')!={'target':PROFILE}: raise PermissionError('emergency_selftest_scope')
    if not valid(report): raise ValueError('emergency_selftest_evidence')
    with q._write(conn):
        now=time.time();owned=q._owned(conn,job['id'],job['lease_token'],now)
        row=conn.execute('SELECT project,kind,payload FROM agent_jobs WHERE id=?',(job['id'],)).fetchone()
        if row[:2]!=('control','test_release') or json.loads(row[2])!={'target':PROFILE} or not owned[3]<=report['checked_at']<=now: raise PermissionError('emergency_selftest_job_changed')
        old=conn.execute('SELECT id,report,report_sha256 FROM emergency_selftest_runs WHERE job_id=?',(job['id'],)).fetchone()
        if old:
            report=json.loads(old[1])
            if not valid(report) or util.digest(report)!=old[2]: raise ValueError('emergency_selftest_saved_evidence_changed')
            ident=old[0]
        else: ident=conn.execute('INSERT INTO emergency_selftest_runs(job_id,report,report_sha256,created_at) VALUES(?,?,?,?)',(job['id'],util.canonical(report),util.digest(report),now)).lastrowid
    return {'emergency_test_id':ident,'report_sha256':util.digest(report),'test_status':'passed','test_counts':report['counts'],
            'live_control_changed':False,'network_calls':0,'published':False}


def describe(conn):
    lines=[control.describe(conn)]
    row=conn.execute('SELECT id,job_id,report,report_sha256 FROM emergency_selftest_runs ORDER BY id DESC LIMIT 1').fetchone()
    if row:
        report=json.loads(row[2])
        if valid(report) and util.digest(report)==row[3]:
            lines.append(f'Проверка #{row[0]} · /job {row[1]}:8 сценариев на отдельной базе в памяти, без изменения рабочей блокировки и сетевых вызовов.')
            if report['implementation_sha256']!=implementation_digest(): lines.append('Код после проверки менялся; повтори /emergency_test.')
        else: lines.append('Сохранённая проверка изменилась; нужна повторная сверка.')
    lines.append('Проверить механизм отдельно от рабочей очереди: /emergency_test. Проверка не нажимает аварийную кнопку на VPS.')
    return '\n'.join(lines)
