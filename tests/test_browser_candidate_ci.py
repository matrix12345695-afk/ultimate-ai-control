import copy
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
import browser_candidate_ci as ci
import browser_candidate_broker as broker
import evidence_memory as memory
import queue_worker
import roadmap
import task_queue as q
from test_browser_ci import FakeAPI as BaselineAPI


class FakeAPI(BaselineAPI):
    def __init__(self):
        with patch.object(baseline,'CONTRACT',ci.CONTRACT): super().__init__()
        self.artifact['name']=ci.CONTRACT['artifact_name_prefix']+'1'


class CandidateCITests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.data=Path(self.temp.name);self.path=self.data/'control.db'
        self.conn=sqlite3.connect(self.path);queue_worker.initialize(self.conn)
        q.enqueue(self.conn,'nova','test_release',{'target':ci.PROFILE});self.job=q.claim(self.conn,'candidate-unit',q.KINDS)
        for name,body in [('browser-candidate-policy.json',util.canonical({'enabled':True,'profile':ci.PROFILE,'contract_sha256':util.digest(ci.CONTRACT)})),('review-executor-activation-approved','approved')]:
            p=self.data/name;p.write_text(body);p.chmod(0o600)
        self.api=FakeAPI();self.scopes=[]
    def tearDown(self): self.conn.close();self.temp.cleanup()
    def run_broker(self,issuer=None):
        return broker.run(self.conn,{'job_id':self.job['id'],'lease_token':self.job['lease_token']},self.data,
            client_factory=lambda *args:self.api,token_issuer=issuer or (lambda *args,**kw:self.scopes.append(kw.get('read_only')) or 'fixture'))

    def test_candidate_scope_gate_and_separate_history(self):
        result=self.run_broker();self.assertEqual(self.scopes,[True]);self.assertEqual(result['test_counts']['pass'],34)
        self.assertEqual(result['advisories'],[]);self.assertFalse(result['published']);self.assertFalse(result['vps_local_execution'])
        raw,sha=self.conn.execute('SELECT report,report_sha256 FROM browser_candidate_runs').fetchone();report=json.loads(raw)
        self.assertTrue(ci.valid(report));self.assertFalse(baseline.valid(report));self.assertEqual(util.digest(report),sha)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM browser_ci_runs').fetchone()[0],0)
        self.assertTrue(all(method=='GET' for method,_ in self.api.calls))
        self.run_broker();self.assertEqual(self.conn.execute('SELECT report FROM browser_candidate_runs').fetchone()[0],raw)
        self.assertIn('Сайт не опубликован',ci.describe(self.conn))

    def test_baseline_ci_and_wrong_source_or_archive_cannot_satisfy_candidate(self):
        old=BaselineAPI();old.read_only=True
        with self.assertRaises(errors.Pending): ci.observe(old)
        for change in ('source','name','digest','expired','attempt_race','upload'):
            api=FakeAPI();api.read_only=True
            if change=='source': api.artifact['workflow_run']['head_sha']='a'*40
            elif change=='name': api.artifact['name']='nova-browser-evidence-1'
            elif change=='digest': api.artifact['digest']='unverified'
            elif change=='expired': api.artifact['expires_at']='2000-01-01T00:00:00Z'
            elif change=='attempt_race': api.rerun_after_artifact=True
            else: api.job['steps'].pop()
            with self.subTest(change=change),self.assertRaises((errors.Blocked,errors.Pending)): ci.observe(api)

    def test_report_contract_and_scope_cannot_be_promoted(self):
        self.api.read_only=True;report=ci.observe(self.api)
        for change in (dict(source_revision=baseline.CONTRACT['source_revision']),dict(counts=dict(report['counts'],tests=27,**{'pass':27})),dict(published=True),dict(advisories=['unexpected'])):
            self.assertFalse(ci.valid(dict(report,**change)))
        for change in (dict(project='inventory'),dict(payload={'target':baseline.PROFILE}),dict(payload={'target':ci.PROFILE,'deploy':True})):
            with self.assertRaises(errors.Blocked): ci.scope(dict(self.job,**change))
        with self.assertRaises(errors.Blocked): ci.save(self.conn,self.job,dict(report,checked_at=time.time()+100))

    def test_policy_scope_lease_fail_before_key_access(self):
        issuer=Mock();(self.data/'browser-candidate-policy.json').write_text('{}')
        with self.assertRaises(errors.Blocked): self.run_broker(issuer)
        issuer.assert_not_called()
        self.conn.execute('UPDATE agent_jobs SET lease_until=0');self.conn.commit()
        with self.assertRaises(PermissionError): self.run_broker(issuer)
        issuer.assert_not_called()

    def test_memory_and_plan_require_unchanged_successful_candidate_evidence(self):
        result=self.run_broker();q.finish(self.conn,self.job['id'],self.job['lease_token'],result);memory.sync(self.conn)
        mid=self.conn.execute("SELECT id FROM project_evidence_memory WHERE event_id IN (SELECT id FROM agent_job_events WHERE job_id=? AND event='succeeded')",(self.job['id'],)).fetchone()[0]
        self.assertIn('browser_candidate_ci',memory.detail(self.conn,mid));self.assertIn('34 браузерные проверки',memory.summary(self.conn,'nova'))
        self.assertIn('Выполнено в Draft PR15',roadmap.describe(self.conn));self.assertNotIn('13. Дизайн и браузерное тестирование — ✅ выполнено',roadmap.describe(self.conn))
        self.conn.execute("UPDATE browser_candidate_runs SET report='{}'");self.conn.commit()
        self.assertIn('повторной проверки',memory.detail(self.conn,mid));self.assertNotIn('Выполнено в Draft PR15',roadmap.describe(self.conn))

    def worker(self,failed=False):
        self.conn.execute("UPDATE agent_jobs SET state='queued',lease_token=NULL,lease_until=NULL");self.conn.commit()
        def request(path,job):
            with sqlite3.connect(path) as conn:
                api=FakeAPI();api.read_only=True
                if failed:
                    api.run['conclusion']='failure';api.job['conclusion']='failure';api.job['steps'][0]['conclusion']='failure'
                return ci.save(conn,job,ci.observe(api))
        with patch.object(queue_worker.artifact_pr_client,'request',side_effect=request): return queue_worker.run_once(self.path)

    def test_worker_success_saves_one_honest_notice_no_approval_or_paid_call(self):
        self.assertEqual(self.worker(),{'id':self.job['id'],'state':'succeeded'})
        notes=self.conn.execute('SELECT reason FROM owner_notifications').fetchall();self.assertEqual(len(notes),1)
        self.assertIn('Chromium:34',notes[0][0]);self.assertIn('публикации не было',notes[0][0])
        for table in ('provider_costs','approvals','artifact_release_candidates'):
            self.assertEqual(self.conn.execute('SELECT count(*) FROM '+table).fetchone()[0],0)

    def test_worker_failed_gate_has_no_confirmed_fix_or_duplicate_notification(self):
        self.assertEqual(self.worker(True),{'id':self.job['id'],'state':'failed'})
        notes=self.conn.execute('SELECT reason FROM owner_notifications').fetchall();self.assertEqual(len(notes),1)
        self.assertIn('не подтверждены',notes[0][0]);self.assertNotIn('Chromium:34',notes[0][0])
        report=json.loads(self.conn.execute('SELECT report FROM browser_candidate_runs').fetchone()[0])
        for key in ('counts','screenshots','advisories','artifact'): self.assertIsNone(report[key])
        self.assertNotIn('Выполнено в Draft PR15',roadmap.describe(self.conn))

    def test_transaction_failure_never_leaves_partial_candidate(self):
        self.conn.execute("CREATE TRIGGER fail_candidate BEFORE INSERT ON browser_candidate_runs BEGIN SELECT RAISE(FAIL,'copy-only gap'); END");self.conn.commit()
        with self.assertRaises(sqlite3.IntegrityError): self.run_broker()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM browser_candidate_runs').fetchone()[0],0)
