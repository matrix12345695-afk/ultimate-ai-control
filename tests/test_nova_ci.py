import copy
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import patch
import artifact_pr_broker as errors
import artifact_prs as util
import evidence_memory as memory
import nova_ci as ci
import nova_ci_broker as broker
import queue_worker
import task_queue as q


class FakeAPI:
    def __init__(self):
        self.read_only=False;self.calls=[]
        self.run={'id':777,'run_attempt':1,'head_sha':ci.CONTRACT['harness_commit'],'event':'push','name':ci.CONTRACT['workflow_name'],
                  'path':ci.CONTRACT['workflow_path'],'repository':{'id':1429215344},'head_repository':{'id':1429215344},'status':'completed','conclusion':'success'}
        self.job={'runner_group_name':'GitHub Actions','labels':['ubuntu-24.04'],'id':888,'run_id':777,'head_sha':ci.CONTRACT['harness_commit'],'name':ci.CONTRACT['workflow_name'],'status':'completed','conclusion':'success',
                  'steps':[{'name':'Run and verify all NOVA tests','status':'completed','conclusion':'success'}]}
        self.final=None;self.total_count=1
    def call(self,method,path,*args,**kwargs):
        assert self.read_only and method=='GET'
        self.calls.append((method,path))
        if path.startswith('/actions/runs?'): return {'workflow_runs':[copy.deepcopy(self.run)]}
        if '/jobs?' in path: return {'total_count':self.total_count,'jobs':[copy.deepcopy(self.job)]}
        return copy.deepcopy(self.final or self.run)


class NovaCITests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.data=Path(self.temp.name);self.path=self.data/'control.db'
        self.conn=sqlite3.connect(self.path);queue_worker.initialize(self.conn)
        ident=q.enqueue(self.conn,'nova','test_release',{'target':ci.PROFILE})
        self.job=q.claim(self.conn,'unit',q.KINDS);self.assertEqual(self.job['id'],ident)
        for name,body in [('nova-ci-policy.json',util.canonical({'enabled':True,'profile':ci.PROFILE,'contract_sha256':util.digest(ci.CONTRACT)})),('review-executor-activation-approved','approved')]:
            p=self.data/name;p.write_text(body);p.chmod(0o600)
        self.api=FakeAPI();self.scopes=[]
    def tearDown(self): self.conn.close();self.temp.cleanup()
    def run_broker(self,issuer=None):
        return broker.run(self.conn,{'job_id':self.job['id'],'lease_token':self.job['lease_token']},self.data,
            client_factory=lambda *args:self.api,token_issuer=issuer or (lambda *args,**kw:self.scopes.append(kw.get('read_only')) or 'fixture'))

    def test_exact_gate_is_read_only_remote_evidence_and_reuses_historical_report(self):
        result=self.run_broker();self.assertEqual(self.scopes,[True]);self.assertEqual(result['test_status'],'passed')
        self.assertFalse(result['vps_local_execution']);self.assertFalse(result['published'])
        self.assertTrue(all(method=='GET' for method,_ in self.api.calls))
        row=self.conn.execute('SELECT report,report_sha256 FROM nova_ci_runs').fetchone();report=json.loads(row[0])
        self.assertTrue(ci.valid(report));self.assertEqual(util.digest(report),row[1]);self.assertEqual(report['counts']['tests'],34)
        self.assertEqual(report['execution_location'],'github_hosted_disposable_runner')
        self.run_broker();self.assertEqual(self.conn.execute('SELECT report FROM nova_ci_runs').fetchone()[0],row[0])
        self.assertEqual(self.conn.execute('SELECT count(*) FROM approvals').fetchone()[0],0)
        self.assertIn('локального запуска БД на VPS нет',ci.describe(self.conn))

    def test_other_revision_workflow_event_or_repository_never_substitutes_for_exact_ci(self):
        for key,value in [('head_sha','a'*40),('path','other.yml'),('event','pull_request'),('repository',{'id':1}),('head_repository',{'id':1}),('name','Other workflow')]:
            with self.subTest(key=key):
                api=FakeAPI();api.read_only=True;api.run[key]=value
                with self.assertRaises(errors.Pending): ci.observe(api)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM nova_ci_runs').fetchone()[0],0)

    def test_pending_failure_missing_gate_and_job_identity_fail_closed(self):
        self.api.run['status']='in_progress'
        with self.assertRaises(errors.Pending): self.run_broker()
        self.api=FakeAPI();self.api.run['conclusion']='failure';self.api.job['conclusion']='failure';self.api.job['steps'][0]['conclusion']='failure'
        result=self.run_broker();self.assertEqual(result['test_status'],'failed');self.assertIsNone(result['test_counts'])
        report=json.loads(self.conn.execute('SELECT report FROM nova_ci_runs').fetchone()[0]);self.assertIsNone(report['postgres_major'])
        self.assertFalse(report['database_restore_verified'])
        for change in ('gate','head','total_count'):
            api=FakeAPI();api.read_only=True
            if change=='gate': api.job['steps']=[]
            elif change=='head': api.job['head_sha']='e'*40
            else: api.total_count=2
            with self.assertRaises(errors.Blocked): ci.observe(api)

    def test_changed_attempt_during_read_is_pending_and_does_not_save_success(self):
        self.api.final=dict(self.api.run,run_attempt=2)
        with self.assertRaises(errors.Pending): self.run_broker()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM nova_ci_runs').fetchone()[0],0)

    def test_policy_scope_or_expired_lease_cannot_read_a_key(self):
        issuer=unittest.mock.Mock()
        policy=self.data/'nova-ci-policy.json';policy.write_text('{}')
        with self.assertRaises(errors.Blocked): self.run_broker(issuer)
        issuer.assert_not_called()
        self.conn.execute('UPDATE agent_jobs SET lease_until=0');self.conn.commit()
        with self.assertRaises(PermissionError): self.run_broker(issuer)
        issuer.assert_not_called()
        with self.assertRaises(errors.Blocked): ci.scope(dict(self.job,project='inventory'))

    def test_contract_source_counts_and_time_tampering_is_denied(self):
        self.api.read_only=True;report=ci.observe(self.api)
        for patch_ in (dict(harness_commit='a'*40),dict(source_revision='a'*40),dict(vps_local_execution=True),dict(counts=dict(report['counts'],skipped=1)),dict(postgres_major=18),dict(checked_at=float('nan'))):
            self.assertFalse(ci.valid(dict(report,**patch_)))
        with self.assertRaises(errors.Blocked): ci.save(self.conn,self.job,dict(report,checked_at=time.time()+1000))

    def test_atomic_save_failure_rolls_back_and_changed_saved_report_is_blocked(self):
        self.conn.execute("CREATE TRIGGER fail_ci_insert BEFORE INSERT ON nova_ci_runs BEGIN SELECT RAISE(FAIL,'copy-only atomic gap'); END");self.conn.commit()
        with self.assertRaises(sqlite3.IntegrityError): self.run_broker()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM nova_ci_runs').fetchone()[0],0)
        self.conn.execute('DROP TRIGGER fail_ci_insert');self.conn.commit();self.run_broker()
        self.conn.execute("UPDATE nova_ci_runs SET report='{}'");self.conn.commit()
        with self.assertRaises(errors.Blocked): self.run_broker()

    def test_evidence_memory_binds_report_and_rejects_modified_source(self):
        result=self.run_broker();q.finish(self.conn,self.job['id'],self.job['lease_token'],result)
        memory.sync(self.conn)
        mid=self.conn.execute("SELECT id FROM project_evidence_memory WHERE event_id IN (SELECT id FROM agent_job_events WHERE job_id=? AND event='succeeded')",(self.job['id'],)).fetchone()[0]
        self.assertIn('nova_ci',memory.detail(self.conn,mid))
        self.assertIn('GitHub CI',memory.summary(self.conn,'nova'))
        self.conn.execute("UPDATE nova_ci_runs SET report='{}'");self.conn.commit()
        self.assertIn('повторной проверки',memory.detail(self.conn,mid))

    def test_worker_persists_actual_broker_result_and_sends_one_honest_notification(self):
        self.conn.execute("UPDATE agent_jobs SET state='queued',lease_token=NULL,lease_until=NULL");self.conn.commit()
        def request(path,job):
            with sqlite3.connect(path) as conn:
                api=FakeAPI();api.read_only=True
                return ci.save(conn,job,ci.observe(api))
        with patch.object(queue_worker.artifact_pr_client,'request',side_effect=request):
            result=queue_worker.run_once(self.path)
        self.assertEqual(result,{'id':self.job['id'],'state':'succeeded'})
        notes=self.conn.execute('SELECT reason FROM owner_notifications').fetchall();self.assertEqual(len(notes),1)
        self.assertIn('VPS сверяет',notes[0][0]);self.assertIn('GitHub runner',notes[0][0])
        self.assertEqual(self.conn.execute('SELECT count(*) FROM provider_costs').fetchone()[0],0)

    def test_hosted_ci_gate_rejects_skips_missing_database_proof_and_wrong_counts(self):
        spec=importlib.util.spec_from_file_location('nova_gate',Path(ci.__file__).parent/'ci/nova-postgres/run.py')
        gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
        text='ok 1 - PostgreSQL CRM survives module reload and records status history\nok 2 - Real PostgreSQL backup is restored into an isolated empty destination\n'
        text+='\n'.join('# '+k+' '+str(v) for k,v in {'tests':34,'pass':34,'fail':0,'cancelled':0,'skipped':0,'todo':0}.items())+'\n'
        self.assertEqual(gate.parse(text)['pass'],34)
        for changed in (text.replace('# skipped 0','# skipped 1'),text.replace('ok 2 -','not ok 2 -'),text.replace('# tests 34','# tests 33')):
            with self.assertRaises(ValueError): gate.parse(changed)

    def test_failed_remote_ci_is_terminal_without_duplicate_generic_alarm(self):
        self.conn.execute("UPDATE agent_jobs SET state='queued',lease_token=NULL,lease_until=NULL");self.conn.commit()
        def request(path,job):
            with sqlite3.connect(path) as conn:
                api=FakeAPI();api.read_only=True
                api.run['conclusion']='failure';api.job['conclusion']='failure';api.job['steps'][0]['conclusion']='failure'
                return ci.save(conn,job,ci.observe(api))
        with patch.object(queue_worker.artifact_pr_client,'request',side_effect=request):
            outcome=queue_worker.run_once(self.path)
        self.assertEqual(outcome,{'id':self.job['id'],'state':'failed'})
        self.assertEqual(self.conn.execute('SELECT count(*) FROM owner_notifications').fetchone()[0],1)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM approvals').fetchone()[0],0)
        self.assertIsNone(json.loads(self.conn.execute('SELECT report FROM nova_ci_runs').fetchone()[0])['counts'])

    def test_self_hosted_or_unknown_runner_cannot_be_labelled_hosted(self):
        for group,labels in [('Other',['ubuntu-24.04']),('GitHub Actions',['self-hosted','ubuntu-24.04']),('GitHub Actions',[])]:
            api=FakeAPI();api.read_only=True;api.job['runner_group_name']=group;api.job['labels']=labels
            with self.assertRaises(errors.Blocked): ci.observe(api)
