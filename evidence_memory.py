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
    if (not isinstance(reference,dict) or set(reference)-{'event_id','job_id','artifact_id','project_test_id','artifact_pr_id','release_check_id','resource_sample_id','nova_ci_id','browser_ci_id','browser_candidate_id','nova_release_ci_id','locked_build_ci_id','nova_deploy_report_id','nova_recovery_ci_id','nova_private_copy_ci_id','emergency_test_id','voice_local_id','voice_flow_id','voice_input_id','weekly_report_id','result'}
            or type(reference.get('event_id')) is not int or type(reference.get('job_id')) is not int):
        raise ValueError('invalid memory reference')
    event=conn.execute('SELECT id,job_id,at,event,detail FROM agent_job_events WHERE id=?',
                       (reference['event_id'],)).fetchone()
    job=conn.execute('SELECT id,project,kind,payload FROM agent_jobs WHERE id=?',
                     (reference['job_id'],)).fetchone()
    if not event or not job or event[1]!=job[0] or job[1] not in queue.PROJECTS:
        raise ValueError('memory source absent or out of scope')
    source={'event':event,'job':job}
    if 'weekly_report_id' in reference:
        import weekly_reports
        end=reference['weekly_report_id']
        snapshot,weekly_sha,notice=weekly_reports.record(conn,end)
        record=conn.execute('SELECT job_id FROM weekly_analytics_reports WHERE period_end=?',(end,)).fetchone()
        if record!=(job[0],) or job[1]!='control' or job[2]!='daily_report':raise ValueError('weekly report belongs to another job')
        source['weekly_report']={'snapshot':snapshot,'sha256':weekly_sha,'notification_id':notice}
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
    if 'nova_ci_id' in reference:
        import nova_ci
        row=conn.execute('SELECT job_id,report,report_sha256 FROM nova_ci_runs WHERE id=?',(reference['nova_ci_id'],)).fetchone()
        if not row or row[0]!=job[0] or job[1]!='nova' or not nova_ci.valid(json.loads(row[1])) or nova_ci.util.digest(json.loads(row[1]))!=row[2]:
            raise ValueError('NOVA CI evidence changed or outside scope')
        source['nova_ci']=row
    if 'browser_ci_id' in reference:
        import browser_ci
        row=conn.execute('SELECT job_id,report,report_sha256 FROM browser_ci_runs WHERE id=?',(reference['browser_ci_id'],)).fetchone()
        if not row or row[0]!=job[0] or job[1]!='nova' or not browser_ci.valid(json.loads(row[1])) or browser_ci.util.digest(json.loads(row[1]))!=row[2]:
            raise ValueError('Browser CI evidence changed or outside scope')
        source['browser_ci']=row
    if 'browser_candidate_id' in reference:
        import browser_candidate_ci
        row=conn.execute('SELECT job_id,report,report_sha256 FROM browser_candidate_runs WHERE id=?',(reference['browser_candidate_id'],)).fetchone()
        if not row or row[0]!=job[0] or job[1]!='nova' or not browser_candidate_ci.valid(json.loads(row[1])) or browser_candidate_ci.util.digest(json.loads(row[1]))!=row[2]:
            raise ValueError('Browser CI evidence changed or outside scope')
        source['browser_candidate_ci']=row
    if 'locked_build_ci_id' in reference:
        import locked_build_ci
        row=conn.execute('SELECT job_id,report,report_sha256 FROM locked_build_ci_runs WHERE id=?',(reference['locked_build_ci_id'],)).fetchone()
        if not row or row[0]!=job[0] or job[1]!='nova' or not locked_build_ci.valid(json.loads(row[1])) or locked_build_ci.util.digest(json.loads(row[1]))!=row[2]:
            raise ValueError('Browser CI evidence changed or outside scope')
        source['locked_build_ci']=row
    if 'nova_release_ci_id' in reference:
        import nova_release_ci
        row=conn.execute('SELECT job_id,report,report_sha256 FROM nova_release_ci_runs WHERE id=?',(reference['nova_release_ci_id'],)).fetchone()
        if not row or row[0]!=job[0] or job[1]!='nova' or not nova_release_ci.valid(json.loads(row[1])) or nova_release_ci.util.digest(json.loads(row[1]))!=row[2]:
            raise ValueError('Browser CI evidence changed or outside scope')
        source['nova_release_ci']=row
    if 'voice_flow_id' in reference:
        import voice_flow_test
        row=conn.execute('SELECT job_id,report,report_sha256 FROM voice_flow_runs WHERE id=?',(reference['voice_flow_id'],)).fetchone()
        if not row or row[0]!=job[0] or job[1]!='control' or not voice_flow_test.valid(json.loads(row[1])) or voice_flow_test.local_voice.util.digest(json.loads(row[1]))!=row[2]:raise ValueError('voice flow evidence changed')
        source['voice_flow']=row
    if 'voice_input_id' in reference:
        import voice_native
        row=conn.execute('SELECT job_id,receipt,receipt_sha256 FROM voice_inputs WHERE id=?',(reference['voice_input_id'],)).fetchone()
        if not row or row[0]!=job[0] or job[1]!='control' or not voice_native.valid_receipt(json.loads(row[1])) or __import__('artifact_prs').digest(json.loads(row[1]))!=row[2]:raise ValueError('voice recognition evidence changed')
        source['voice_input']=row
    if 'voice_local_id' in reference:
        import local_voice
        row=conn.execute('SELECT job_id,report,report_sha256 FROM voice_local_runs WHERE id=?',(reference['voice_local_id'],)).fetchone()
        if not row or row[0]!=job[0] or job[1]!='control' or not local_voice.valid(json.loads(row[1])) or local_voice.util.digest(json.loads(row[1]))!=row[2]: raise ValueError('local voice evidence changed')
        source['local_voice']=row
    if 'emergency_test_id' in reference:
        import emergency_selftest
        row=conn.execute('SELECT job_id,report,report_sha256 FROM emergency_selftest_runs WHERE id=?',(reference['emergency_test_id'],)).fetchone()
        if not row or row[0]!=job[0] or job[1]!='control' or not emergency_selftest.valid(json.loads(row[1])) or emergency_selftest.util.digest(json.loads(row[1]))!=row[2]: raise ValueError('emergency selftest evidence changed')
        source['emergency_selftest']=row
    if 'nova_private_copy_ci_id' in reference:
        import nova_private_copy_ci
        row=conn.execute('SELECT job_id,report,report_sha256 FROM nova_private_copy_ci_runs WHERE id=?',(reference['nova_private_copy_ci_id'],)).fetchone()
        if not row or row[0]!=job[0] or job[1]!='nova' or not nova_private_copy_ci.valid(json.loads(row[1])) or nova_private_copy_ci.util.digest(json.loads(row[1]))!=row[2]:
            raise ValueError('private copy evidence changed or outside scope')
        source['nova_private_copy_ci']=row
    if 'nova_recovery_ci_id' in reference:
        import nova_recovery_ci
        row=conn.execute('SELECT job_id,report,report_sha256 FROM nova_recovery_ci_runs WHERE id=?',(reference['nova_recovery_ci_id'],)).fetchone()
        if not row or row[0]!=job[0] or job[1]!='nova' or not nova_recovery_ci.valid(json.loads(row[1])) or nova_recovery_ci.util.digest(json.loads(row[1]))!=row[2]:
            raise ValueError('recovery evidence changed or outside scope')
        source['nova_recovery_ci']=row
    if 'nova_deploy_report_id' in reference:
        import nova_deploy
        row=conn.execute('SELECT job_id,report,report_sha256 FROM nova_publication_plans WHERE id=?',(reference['nova_deploy_report_id'],)).fetchone()
        if not row or row[0]!=job[0] or job[1]!='nova' or not nova_deploy.valid(json.loads(row[1])) or nova_deploy.util.digest(json.loads(row[1]))!=row[2]:
            raise ValueError('publication plan changed or outside scope')
        source['nova_deploy']=row
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
        if result and kind=='daily_report' and project=='control' and type(result.get('weekly_report_id')) is int:
            import weekly_reports
            end=result['weekly_report_id']
            snapshot,weekly_sha,notice=weekly_reports.record(conn,end)
            row=conn.execute('SELECT job_id FROM weekly_analytics_reports WHERE period_end=?',(end,)).fetchone()
            if row==(job_id,) and result.get('report_sha256')==weekly_sha:
                fact['weekly_report']={'since':snapshot['since'],'until':snapshot['until'],'timezone':snapshot['timezone'],
                    'work_seconds':snapshot['analytics']['work_seconds'],'published':False}
                reference.update(weekly_report_id=end,result=True)
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
        if result and kind=='test_release' and project=='nova' and type(result.get('nova_ci_id')) is int:
            import nova_ci
            row=conn.execute('SELECT job_id,report,report_sha256 FROM nova_ci_runs WHERE id=?',(result['nova_ci_id'],)).fetchone()
            if row and row[0]==job_id and nova_ci.valid(json.loads(row[1])) and nova_ci.util.digest(json.loads(row[1]))==row[2]==result.get('report_sha256'):
                report=json.loads(row[1])
                fact['nova_ci']={key:report[key] for key in ('ci_url','harness_commit','source_revision','status','execution_location','vps_local_execution')}
                reference.update(nova_ci_id=result['nova_ci_id'],result=True)
        if result and kind=='test_release' and project=='nova' and type(result.get('browser_ci_id')) is int:
            import browser_ci
            row=conn.execute('SELECT job_id,report,report_sha256 FROM browser_ci_runs WHERE id=?',(result['browser_ci_id'],)).fetchone()
            if row and row[0]==job_id and browser_ci.valid(json.loads(row[1])) and browser_ci.util.digest(json.loads(row[1]))==row[2]==result.get('report_sha256'):
                report=json.loads(row[1])
                fact['browser_ci']={key:report[key] for key in ('ci_url','harness_commit','source_revision','status','screenshots','advisories','backend_mocked','vps_local_execution')}
                reference.update(browser_ci_id=result['browser_ci_id'],result=True)
        if result and kind=='test_release' and project=='nova' and type(result.get('browser_candidate_id')) is int:
            import browser_candidate_ci
            row=conn.execute('SELECT job_id,report,report_sha256 FROM browser_candidate_runs WHERE id=?',(result['browser_candidate_id'],)).fetchone()
            if row and row[0]==job_id and browser_candidate_ci.valid(json.loads(row[1])) and browser_candidate_ci.util.digest(json.loads(row[1]))==row[2]==result.get('report_sha256'):
                report=json.loads(row[1])
                fact['browser_candidate_ci']={key:report[key] for key in ('ci_url','harness_commit','source_revision','status','screenshots','advisories','backend_mocked','vps_local_execution')}
                reference.update(browser_candidate_id=result['browser_candidate_id'],result=True)
        if result and kind=='test_release' and project=='nova' and type(result.get('locked_build_ci_id')) is int:
            import locked_build_ci
            row=conn.execute('SELECT job_id,report,report_sha256 FROM locked_build_ci_runs WHERE id=?',(result['locked_build_ci_id'],)).fetchone()
            if row and row[0]==job_id and locked_build_ci.valid(json.loads(row[1])) and locked_build_ci.util.digest(json.loads(row[1]))==row[2]==result.get('report_sha256'):
                report=json.loads(row[1])
                fact['locked_build_ci']={key:report[key] for key in ('ci_url','harness_commit','source_revision','status','counts','dependency_lock_sha256','screenshots','advisories','backend_mocked','vps_local_execution')}
                reference.update(locked_build_ci_id=result['locked_build_ci_id'],result=True)
        if result and kind=='test_release' and project=='nova' and type(result.get('nova_release_ci_id')) is int:
            import nova_release_ci
            row=conn.execute('SELECT job_id,report,report_sha256 FROM nova_release_ci_runs WHERE id=?',(result['nova_release_ci_id'],)).fetchone()
            if row and row[0]==job_id and nova_release_ci.valid(json.loads(row[1])) and nova_release_ci.util.digest(json.loads(row[1]))==row[2]==result.get('report_sha256'):
                report=json.loads(row[1])
                fact['nova_release_ci']={key:report[key] for key in ('ci_url','harness_commit','candidate_revision','status','nova_test_counts','rehearsal_counts','rollback_data_preservation_verified','Render_rollback_executed','publish_allowed','blockers')}
                reference.update(nova_release_ci_id=result['nova_release_ci_id'],result=True)
        if result and kind=='test_release' and project=='control' and type(result.get('voice_flow_id')) is int:
            import voice_flow_test
            row=conn.execute('SELECT job_id,report,report_sha256 FROM voice_flow_runs WHERE id=?',(result['voice_flow_id'],)).fetchone()
            if row and row[0]==job_id and voice_flow_test.valid(json.loads(row[1])) and voice_flow_test.local_voice.util.digest(json.loads(row[1]))==row[2]==result.get('report_sha256'):
                report=json.loads(row[1]);fact['voice_flow']={k:report[k] for k in ('counts','real_native_case_count','synthetic_state_case_count','telegram_roundtrip_verified','owner_confirmation_real','live_inbox_changed')}
                reference.update(voice_flow_id=result['voice_flow_id'],result=True)
        if result and kind=='plan_change' and project=='control' and type(result.get('voice_input_id')) is int and result.get('voice_recognition')=='transcribed':
            import voice_native
            row=conn.execute('SELECT job_id,receipt,receipt_sha256 FROM voice_inputs WHERE id=?',(result['voice_input_id'],)).fetchone()
            if row and row[0]==job_id and voice_native.valid_receipt(json.loads(row[1])) and __import__('artifact_prs').digest(json.loads(row[1]))==row[2]==result.get('receipt_sha256'):
                receipt=json.loads(row[1]);fact['voice_input']={k:receipt[k] for k in ('audio_sha256','transcript_sha256','language','decoded_seconds','recognize_seconds','model_sha256','network','paid_calls')}
                reference.update(voice_input_id=result['voice_input_id'],result=True)
        if result and kind=='test_release' and project=='control' and type(result.get('voice_local_id')) is int:
            import local_voice
            row=conn.execute('SELECT job_id,report,report_sha256 FROM voice_local_runs WHERE id=?',(result['voice_local_id'],)).fetchone()
            if row and row[0]==job_id and local_voice.valid(json.loads(row[1])) and local_voice.util.digest(json.loads(row[1]))==row[2]==result.get('report_sha256'):
                report=json.loads(row[1]);fact['local_voice']={k:report[k] for k in ('counts','fixture_language','fixture_seconds','recognize_seconds','model_sha256','contract_sha256','owner_voice_enabled')}
                reference.update(voice_local_id=result['voice_local_id'],result=True)
        if result and kind=='test_release' and project=='control' and type(result.get('emergency_test_id')) is int:
            import emergency_selftest
            row=conn.execute('SELECT job_id,report,report_sha256 FROM emergency_selftest_runs WHERE id=?',(result['emergency_test_id'],)).fetchone()
            if row and row[0]==job_id and emergency_selftest.valid(json.loads(row[1])) and emergency_selftest.util.digest(json.loads(row[1]))==row[2]==result.get('report_sha256'):
                report=json.loads(row[1]);fact['emergency_selftest']={k:report[k] for k in ('counts','implementation_sha256','live_control_changed','network_calls','service_signals','paid_calls')}
                reference.update(emergency_test_id=result['emergency_test_id'],result=True)
        if result and kind=='test_release' and project=='nova' and type(result.get('nova_private_copy_ci_id')) is int:
            import nova_private_copy_ci
            row=conn.execute('SELECT job_id,report,report_sha256 FROM nova_private_copy_ci_runs WHERE id=?',(result['nova_private_copy_ci_id'],)).fetchone()
            if row and row[0]==job_id and nova_private_copy_ci.valid(json.loads(row[1])) and nova_private_copy_ci.util.digest(json.loads(row[1]))==row[2]==result.get('report_sha256'):
                report=json.loads(row[1]);fact['nova_private_copy_ci']={key:report[key] for key in ('ci_url','harness_commit','source_revision','status','encrypted_fixture_verified','fixture_leads','production_backup_verified','production_key_generated','durable_retention_verified','Render_execution_path_available','published')}
                reference.update(nova_private_copy_ci_id=result['nova_private_copy_ci_id'],result=True)
        if result and kind=='test_release' and project=='nova' and type(result.get('nova_recovery_ci_id')) is int:
            import nova_recovery_ci
            row=conn.execute('SELECT job_id,report,report_sha256 FROM nova_recovery_ci_runs WHERE id=?',(result['nova_recovery_ci_id'],)).fetchone()
            if row and row[0]==job_id and nova_recovery_ci.valid(json.loads(row[1])) and nova_recovery_ci.util.digest(json.loads(row[1]))==row[2]==result.get('report_sha256'):
                report=json.loads(row[1]);fact['nova_recovery_ci']={key:report[key] for key in ('ci_url','harness_commit','source_revision','status','fixture_restore_verified','fixture_leads','production_backup_verified','Render_rollback_eligible','published')}
                reference.update(nova_recovery_ci_id=result['nova_recovery_ci_id'],result=True)
        if result and kind=='test_release' and project=='nova' and type(result.get('nova_deploy_report_id')) is int:
            import nova_deploy
            row=conn.execute('SELECT job_id,report,report_sha256 FROM nova_publication_plans WHERE id=?',(result['nova_deploy_report_id'],)).fetchone()
            if row and row[0]==job_id and nova_deploy.valid(json.loads(row[1])) and nova_deploy.util.digest(json.loads(row[1]))==row[2]==result.get('report_sha256'):
                report=json.loads(row[1]);fact['nova_deploy']={key:report[key] for key in ('mode','scope_sha256','plan_state','checks','blockers','publish_allowed','production_mutations')}
                reference.update(nova_deploy_report_id=result['nova_deploy_report_id'],result=True)
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
            if fact.get('voice_flow'):lines.append('Нативный звук и8 синтетических сценариев приёма/подтверждения проверены; реальный входящий цикл ещё требует проверки владельцем. /voice4')
            if fact.get('voice_input'):lines.append('Голосовое распознано локально; текст не включён в память. Подтверждение задачи хранится отдельно. /voice_inbox')
            if fact.get('local_voice'): lines.append('Исторический пилот:3 проверки публичной английской записи OGG/Opus; без входящего сообщения владельца. /voice4')
            if fact.get('emergency_selftest'): lines.append('8 сценариев аварийной защиты прошли на отдельной базе; рабочая блокировка не менялась. /emergency')
            if fact.get('nova_private_copy_ci'): lines.append('Draft17:30 проверок шифрованной копии и восстановления фиктивных данных; рабочая копия не получена. /nova_copy' if fact['nova_private_copy_ci']['status']=='passed' else 'Черновик шифрованной копии не прошёл CI. /nova_copy')
            if fact.get('nova_recovery_ci'): lines.append('PostgreSQL18:24 проверки восстановления5003 фиктивных заявок/4 таблиц; реальная копия ещё не проверена. /nova_recovery')
            if fact.get('nova_deploy'): lines.append('Подготовлен точный план публикации; симулятор и три фиктивных сценария. Реальное исполнение отключено. /nova_deploy')
            if fact.get('locked_build_ci'): lines.append('Сверена закреплённая сборка:83 проверки и15 снимков; Blueprint не применён, публикация отключена. /nova_build')
            if fact.get('nova_release_ci'): lines.append('Сверена репетиция HTTP/PG и сохранности тестовых данных; откат Render не выполнялся, публикация отключена. /nova_release')
            if fact.get('browser_candidate_ci'): lines.append('Сверен исправленный черновик NOVA;34 браузерные проверки, публикации нет. /nova_candidate')
            if fact.get('browser_ci'): lines.append('Сверен браузерный CI со скриншотами и замечаниями; API подставной, исполнение на GitHub. /nova_browser')
            if fact.get('nova_ci'): lines.append('Сверен точный GitHub CI с PostgreSQL; это не локальное исполнение на VPS. /nova_pg')
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
