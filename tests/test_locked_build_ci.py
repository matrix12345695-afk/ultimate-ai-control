import json
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import Mock,patch
import artifact_pr_broker as errors
import artifact_prs as util
import browser_ci as baseline
import locked_build_ci as ci
import locked_build_broker as broker
import evidence_memory as memory
import queue_worker
import roadmap
import task_queue as q
from test_browser_ci import FakeAPI as BaselineAPI


class FakeAPI(BaselineAPI):
    def __init__(self):
        with patch.object(baseline,'CONTRACT',ci.CONTRACT): super().__init__()
        self.artifact['name']=ci.CONTRACT['artifact_name_prefix']+'1'
        self.job['steps'][1]['name']=ci.CONTRACT['upload_step']


class LockedBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.data=Path(self.temp.name);self.path=self.data/'control.db'
        self.conn=sqlite3.connect(self.path);queue_worker.initialize(self.conn)
        q.enqueue(self.conn,'nova','test_release',{'target':ci.PROFILE});self.job=q.claim(self.conn,'locked-unit',q.KINDS)
        for name,body in [('nova-locked-build-policy.json',util.canonical({'enabled':True,'profile':ci.PROFILE,'contract_sha256':util.digest(ci.CONTRACT)})),('review-executor-activation-approved','approved')]:
            p=self.data/name;p.write_text(body);p.chmod(0o600)
        self.api=FakeAPI();self.scopes=[]
    def tearDown(self): self.conn.close();self.temp.cleanup()
    def run_broker(self,issuer=None):
        return broker.run(self.conn,{'job_id':self.job['id'],'lease_token':self.job['lease_token']},self.data,
            client_factory=lambda *args:self.api,token_issuer=issuer or (lambda *args,**kw:self.scopes.append(kw.get('read_only')) or 'fixture'))
    def test_combined_exact_ci_is_read_only_without_relabeling83_as_browser_only(self):
        result=self.run_broker();self.assertEqual(self.scopes,[True]);self.assertEqual(result['test_counts']['pass'],83)
        raw,sha=self.conn.execute('SELECT report,report_sha256 FROM locked_build_ci_runs').fetchone();report=json.loads(raw)
        self.assertTrue(ci.valid(report));self.assertFalse(baseline.valid(report));self.assertEqual(util.digest(report),sha)
        self.assertEqual(report['engine'],'node_postgres_chromium');self.assertFalse(report['backend_mocked'])
        text=ci.describe(self.conn);self.assertIn('34 теста приложения',text);self.assertIn('34 Chromium',text);self.assertIn('предложение',text)
        self.assertTrue(all(method=='GET' for method,_ in self.api.calls));self.run_broker()
        self.assertEqual(self.conn.execute('SELECT report FROM locked_build_ci_runs').fetchone()[0],raw)
        for table in ('browser_ci_runs','browser_candidate_runs','nova_release_ci_runs'):
            self.assertEqual(self.conn.execute('SELECT count(*) FROM '+table).fetchone()[0],0)
    def test_other_profile_or_unverified_archive_does_not_satisfy_build(self):
        old=BaselineAPI();old.read_only=True
        with self.assertRaises(errors.Pending): ci.observe(old)
        for change in ('upload','artifact','attempt','source','digest','expiry'):
            api=FakeAPI();api.read_only=True
            if change=='upload': api.job['steps'][1]['name']='Upload browser evidence'
            elif change=='artifact': api.artifact['name']='nova-browser-candidate-1'
            elif change=='attempt': api.rerun_after_artifact=True
            elif change=='source': api.artifact['workflow_run']['head_sha']='a'*40
            elif change=='digest': api.artifact['digest']='unknown'
            else: api.artifact['expires_at']='2000-01-01T00:00:00Z'
            with self.subTest(change=change),self.assertRaises((errors.Blocked,errors.Pending)): ci.observe(api)
    def test_scope_policy_and_lease_checked_before_credentials(self):
        issuer=Mock();(self.data/'nova-locked-build-policy.json').write_text('{}')
        with self.assertRaises(errors.Blocked): self.run_broker(issuer)
        issuer.assert_not_called();self.conn.execute('UPDATE agent_jobs SET lease_until=0');self.conn.commit()
        with self.assertRaises(PermissionError): self.run_broker(issuer)
        issuer.assert_not_called()
        for change in (dict(project='inventory'),dict(payload={'target':ci.PROFILE,'publish':True}),dict(kind='review_change')):
            with self.assertRaises(errors.Blocked): ci.scope(dict(self.job,**change))
    def test_counts_engine_lock_and_publication_cannot_be_forged(self):
        self.api.read_only=True;report=ci.observe(self.api)
        for change in (dict(counts=dict(report['counts'],tests=34,**{'pass':34})),dict(engine='chromium'),dict(backend_mocked=True),dict(dependency_lock_sha256='a'*64),dict(published=True),dict(advisories=['unknown'])):
            self.assertFalse(ci.valid(dict(report,**change)))
        with self.assertRaises(errors.Blocked): ci.save(self.conn,self.job,dict(report,checked_at=time.time()+100))
        self.run_broker();self.conn.execute("UPDATE locked_build_ci_runs SET report='{}'");self.conn.commit()
        with self.assertRaises(errors.Blocked): self.run_broker()
    def test_memory_and_plan_bind_new_version_without_finishing_publication(self):
        result=self.run_broker();q.finish(self.conn,self.job['id'],self.job['lease_token'],result);memory.sync(self.conn)
        mid=self.conn.execute("SELECT id FROM project_evidence_memory WHERE event_id IN (SELECT id FROM agent_job_events WHERE job_id=? AND event='succeeded')",(self.job['id'],)).fetchone()[0]
        self.assertIn('locked_build_ci',memory.detail(self.conn,mid));self.assertIn('83 проверки',memory.summary(self.conn,'nova'))
        self.assertIn('Draft PR16: версии/сборка закреплены',roadmap.describe(self.conn));self.assertNotIn('9. Согласование публикаций — ✅ выполнено',roadmap.describe(self.conn))
        self.conn.execute("UPDATE locked_build_ci_runs SET report='{}'");self.conn.commit()
        self.assertIn('повторной проверки',memory.detail(self.conn,mid));self.assertNotIn('Draft PR16: версии/сборка закреплены',roadmap.describe(self.conn))
    def worker(self,failed=False):
        self.conn.execute("UPDATE agent_jobs SET state='queued',lease_token=NULL,lease_until=NULL");self.conn.commit()
        def request(path,job):
            with sqlite3.connect(path) as conn:
                api=FakeAPI();api.read_only=True
                if failed: api.run['conclusion']='failure';api.job['conclusion']='failure';api.job['steps'][0]['conclusion']='failure'
                return ci.save(conn,job,ci.observe(api))
        with patch.object(queue_worker.artifact_pr_client,'request',side_effect=request): return queue_worker.run_once(self.path)
    def test_worker_success_is_one_notice_no_approval_or_paid_call(self):
        self.assertEqual(self.worker(),{'id':self.job['id'],'state':'succeeded'})
        notes=self.conn.execute('SELECT reason FROM owner_notifications').fetchall();self.assertEqual(len(notes),1)
        self.assertIn('83 проверки (34 приложение,15 HTTP/PG,34 браузер)',notes[0][0]);self.assertIn('Blueprint пока не применён',notes[0][0])
        for table in ('provider_costs','approvals','artifact_release_candidates'):
            self.assertEqual(self.conn.execute('SELECT count(*) FROM '+table).fetchone()[0],0)
    def test_failed_build_has_no_success_counts_or_duplicate_alarm(self):
        self.assertEqual(self.worker(True),{'id':self.job['id'],'state':'failed'})
        notes=self.conn.execute('SELECT reason FROM owner_notifications').fetchall();self.assertEqual(len(notes),1);self.assertIn('не подтверждены',notes[0][0])
        report=json.loads(self.conn.execute('SELECT report FROM locked_build_ci_runs').fetchone()[0]);self.assertIsNone(report['counts']);self.assertIsNone(report['artifact'])
        self.assertNotIn('Draft PR16: версии/сборка закреплены',roadmap.describe(self.conn))
    def test_blocked_build_uses_its_own_alarm(self):
        self.conn.execute("UPDATE agent_jobs SET state='queued',lease_token=NULL,lease_until=NULL");self.conn.commit()
        with patch.object(queue_worker.artifact_pr_client,'request',side_effect=errors.Blocked('locked_build_policy_disabled')):
            self.assertEqual(queue_worker.run_once(self.path),{'id':self.job['id'],'state':'failed'})
        self.assertEqual(self.conn.execute('SELECT title,event_key FROM owner_notifications').fetchall(),[('Сверка закреплённой сборки остановлена','locked-build-stopped-'+str(self.job['id']))])
    def test_report_insert_failure_never_leaves_partial_success(self):
        self.conn.execute("CREATE TRIGGER fail_locked BEFORE INSERT ON locked_build_ci_runs BEGIN SELECT RAISE(FAIL,'copy-only gap'); END");self.conn.commit()
        with self.assertRaises(sqlite3.IntegrityError): self.run_broker()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM locked_build_ci_runs').fetchone()[0],0)
