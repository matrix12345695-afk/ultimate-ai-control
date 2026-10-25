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
import nova_release_ci as ci
import nova_release_broker as broker
import evidence_memory as memory
import queue_worker
import roadmap
import task_queue as q
from test_browser_ci import FakeAPI as BaselineAPI


class FakeAPI(BaselineAPI):
    def __init__(self):
        with patch.object(baseline,'CONTRACT',ci.CONTRACT): super().__init__()


class ReleaseCITests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.data=Path(self.temp.name);self.path=self.data/'control.db'
        self.conn=sqlite3.connect(self.path);queue_worker.initialize(self.conn)
        q.enqueue(self.conn,'nova','test_release',{'target':ci.PROFILE});self.job=q.claim(self.conn,'release-unit',q.KINDS)
        for name,body in [('nova-release-policy.json',util.canonical({'enabled':True,'profile':ci.PROFILE,'contract_sha256':util.digest(ci.CONTRACT)})),('review-executor-activation-approved','approved')]:
            p=self.data/name;p.write_text(body);p.chmod(0o600)
        self.api=FakeAPI();self.scopes=[]
    def tearDown(self): self.conn.close();self.temp.cleanup()
    def run_broker(self,issuer=None):
        return broker.run(self.conn,{'job_id':self.job['id'],'lease_token':self.job['lease_token']},self.data,
            client_factory=lambda *args:self.api,token_issuer=issuer or (lambda *args,**kw:self.scopes.append(kw.get('read_only')) or 'fixture'))

    def test_exact_read_only_ci_does_not_authorize_or_claim_render_rollback(self):
        result=self.run_broker();self.assertEqual(self.scopes,[True]);self.assertEqual(result['nova_test_counts']['pass'],34)
        self.assertEqual(result['rehearsal_counts']['pass'],15);self.assertFalse(result['publish_allowed']);self.assertFalse(result['Render_rollback_executed'])
        raw,sha=self.conn.execute('SELECT report,report_sha256 FROM nova_release_ci_runs').fetchone();report=json.loads(raw)
        self.assertTrue(ci.valid(report));self.assertTrue(report['candidate_era_fixture_preserved']);self.assertEqual(util.digest(report),sha)
        self.assertIn('http_health_check_not_configured',report['blockers']);self.assertIn('production_dependency_lock_unpinned',report['blockers'])
        self.assertTrue(all(method=='GET' for method,_ in self.api.calls))
        self.run_broker();self.assertEqual(self.conn.execute('SELECT report FROM nova_release_ci_runs').fetchone()[0],raw)
        self.assertIn('исторический снимок',ci.describe(self.conn));self.assertIn('Состояние Render на VPS автоматически не обновляется',ci.describe(self.conn))

    def test_wrong_profile_gate_and_rerun_cannot_satisfy_rehearsal(self):
        for change in ('source','workflow','gate','attempt','hosted'):
            api=FakeAPI();api.read_only=True
            if change=='source': api.run['head_sha']='a'*40
            elif change=='workflow': api.run['path']='other.yml'
            elif change=='gate': api.job['steps'][0]['name']='Other gate'
            elif change=='attempt': api.run['run_attempt']=2
            else: api.job['runner_group_name']='Production'
            if change=='attempt':
                oldcall=api.call
                api.call=lambda method,path,*a,**kw: dict(api.run,run_attempt=3) if path=='/actions/runs/777' else oldcall(method,path,*a,**kw)
            with self.subTest(change=change),self.assertRaises((errors.Blocked,errors.Pending)): ci.observe(api)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM nova_release_ci_runs').fetchone()[0],0)

    def test_snapshot_scope_policy_and_lease_checked_before_credentials(self):
        issuer=Mock()
        with patch.object(ci,'SNAPSHOT',dict(ci.SNAPSHOT,workspace_id='other')):
            with self.assertRaises(errors.Blocked): self.run_broker(issuer)
        issuer.assert_not_called()
        (self.data/'nova-release-policy.json').write_text('{}')
        with self.assertRaises(errors.Blocked): self.run_broker(issuer)
        issuer.assert_not_called()
        self.conn.execute('UPDATE agent_jobs SET lease_until=0');self.conn.commit()
        with self.assertRaises(PermissionError): self.run_broker(issuer)
        issuer.assert_not_called()
        for change in (dict(project='inventory'),dict(payload={'target':ci.PROFILE,'publish':True}),dict(kind='review_change')):
            with self.assertRaises(errors.Blocked): ci.scope(dict(self.job,**change))

    def test_historical_report_cannot_promote_a_rehearsal_to_production_permission(self):
        self.api.read_only=True;report=ci.observe(self.api)
        for change in (dict(publish_allowed=True),dict(Render_rollback_executed=True),dict(owner_approval_created=True),dict(blockers=[]),dict(render_snapshot_sha256='a'*64),dict(base_revision='a'*40),dict(rehearsal_counts=dict(report['rehearsal_counts'],skipped=1))):
            self.assertFalse(ci.valid(dict(report,**change)))
        with self.assertRaises(errors.Blocked): ci.save(self.conn,self.job,dict(report,checked_at=time.time()+100))
        self.run_broker();self.conn.execute("UPDATE nova_release_ci_runs SET report='{}'");self.conn.commit()
        with self.assertRaises(errors.Blocked): self.run_broker()

    def test_memory_and_partial_plan_revalidate_the_saved_report(self):
        result=self.run_broker();q.finish(self.conn,self.job['id'],self.job['lease_token'],result);memory.sync(self.conn)
        mid=self.conn.execute("SELECT id FROM project_evidence_memory WHERE event_id IN (SELECT id FROM agent_job_events WHERE job_id=? AND event='succeeded')",(self.job['id'],)).fetchone()[0]
        self.assertIn('nova_release_ci',memory.detail(self.conn,mid));self.assertIn('откат Render не выполнялся',memory.summary(self.conn,'nova'))
        self.assertIn('Репетиция HTTP/PG:34+15',roadmap.describe(self.conn));self.assertNotIn('9. Согласование публикаций — ✅ выполнено',roadmap.describe(self.conn))
        self.conn.execute("UPDATE nova_release_ci_runs SET report='{}'");self.conn.commit()
        self.assertIn('повторной проверки',memory.detail(self.conn,mid));self.assertNotIn('Репетиция HTTP/PG:34+15',roadmap.describe(self.conn))

    def worker(self,failed=False):
        self.conn.execute("UPDATE agent_jobs SET state='queued',lease_token=NULL,lease_until=NULL");self.conn.commit()
        def request(path,job):
            with sqlite3.connect(path) as conn:
                api=FakeAPI();api.read_only=True
                if failed:
                    api.run['conclusion']='failure';api.job['conclusion']='failure';api.job['steps'][0]['conclusion']='failure'
                return ci.save(conn,job,ci.observe(api))
        with patch.object(queue_worker.artifact_pr_client,'request',side_effect=request): return queue_worker.run_once(self.path)

    def test_worker_persists_one_honest_notice_no_owner_decision_or_spend(self):
        self.assertEqual(self.worker(),{'id':self.job['id'],'state':'succeeded'})
        notes=self.conn.execute('SELECT reason FROM owner_notifications').fetchall();self.assertEqual(len(notes),1)
        self.assertIn('Это не откат Render',notes[0][0]);self.assertIn('Публикация отключена',notes[0][0])
        for table in ('provider_costs','approvals','artifact_release_candidates'):
            self.assertEqual(self.conn.execute('SELECT count(*) FROM '+table).fetchone()[0],0)

    def test_failure_never_claims_preserved_data_or_sends_duplicate_alarm(self):
        self.assertEqual(self.worker(True),{'id':self.job['id'],'state':'failed'})
        notes=self.conn.execute('SELECT reason FROM owner_notifications').fetchall();self.assertEqual(len(notes),1)
        self.assertIn('не подтверждена',notes[0][0]);self.assertNotIn('15 проверок',notes[0][0])
        report=json.loads(self.conn.execute('SELECT report FROM nova_release_ci_runs').fetchone()[0]);self.assertTrue(ci.valid(report))
        self.assertIsNone(report['rehearsal_counts']);self.assertFalse(report['rollback_data_preservation_verified'])
        self.assertNotIn('Репетиция HTTP/PG:34+15',roadmap.describe(self.conn))

    def test_atomic_report_failure_never_creates_partial_evidence(self):
        self.conn.execute("CREATE TRIGGER fail_release BEFORE INSERT ON nova_release_ci_runs BEGIN SELECT RAISE(FAIL,'copy-only gap'); END");self.conn.commit()
        with self.assertRaises(sqlite3.IntegrityError): self.run_broker()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM nova_release_ci_runs').fetchone()[0],0)

    def test_blocked_observation_uses_its_own_alarm_without_success_evidence(self):
        self.conn.execute("UPDATE agent_jobs SET state='queued',lease_token=NULL,lease_until=NULL");self.conn.commit()
        with patch.object(queue_worker.artifact_pr_client,'request',side_effect=errors.Blocked('nova_release_snapshot_changed')):
            self.assertEqual(queue_worker.run_once(self.path),{'id':self.job['id'],'state':'failed'})
        notes=self.conn.execute('SELECT title,event_key FROM owner_notifications').fetchall()
        self.assertEqual(notes,[('Сверка репетиции выпуска остановлена','nova-release-stopped-'+str(self.job['id']))])
        self.assertEqual(self.conn.execute('SELECT count(*) FROM nova_release_ci_runs').fetchone()[0],0)
