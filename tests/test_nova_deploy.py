import json
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import Mock,patch
import artifact_pr_broker as errors
import artifact_prs as util
import nova_deploy as plan
import nova_deploy_broker as broker
import nova_deploy_fixture as fixture
import evidence_memory as memory
import queue_worker
import roadmap
import task_queue as q
from test_locked_build_ci import FakeAPI


class PublicationPlanTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.data=Path(self.temp.name);self.path=self.data/'control.db'
        self.conn=sqlite3.connect(self.path);queue_worker.initialize(self.conn)
        q.enqueue(self.conn,'nova','test_release',{'target':plan.PROFILE});self.job=q.claim(self.conn,'plan-unit',q.KINDS)
        for name,body in [('nova-deploy-plan-policy.json',util.canonical({'enabled':True,'profile':plan.PROFILE,'mode':'dry_run_only','definition_sha256':plan.definition_digest()})),('review-executor-activation-approved','approved')]:
            p=self.data/name;p.write_text(body);p.chmod(0o600)
        self.api=FakeAPI();self.scopes=[]
    def tearDown(self): self.conn.close();self.temp.cleanup()
    def run_broker(self,issuer=None):
        return broker.run(self.conn,{'job_id':self.job['id'],'lease_token':self.job['lease_token']},self.data,
            client_factory=lambda *a:self.api,token_issuer=issuer or (lambda *a,**kw:self.scopes.append(kw.get('read_only')) or 'fixture'))
    def test_actual_read_only_ci_and_simulation_create_only_a_blocked_plan(self):
        result=self.run_broker();self.assertEqual(self.scopes,[True]);self.assertEqual(result['plan_state'],'blocked');self.assertFalse(result['publish_allowed'])
        raw,sha=self.conn.execute('SELECT report,report_sha256 FROM nova_publication_plans').fetchone();report=json.loads(raw)
        self.assertTrue(plan.valid(report));self.assertEqual(util.digest(report),sha);self.assertEqual(report['simulation']['cases'],3)
        self.assertEqual(report['production_mutations'],0);self.assertFalse(report['may_request_approval'])
        self.assertIn('production_backup_verified',report['blockers']);self.assertIn('retained_Render_artifact_verified',report['blockers'])
        self.assertTrue(all(method=='GET' for method,_ in self.api.calls))
        self.run_broker();self.assertEqual(self.conn.execute('SELECT report FROM nova_publication_plans').fetchone()[0],raw)
        for table in ('approvals','artifact_release_candidates','provider_costs'):
            self.assertEqual(self.conn.execute('SELECT count(*) FROM '+table).fetchone()[0],0)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM sqlite_master WHERE name='nova_deploy_simulations'").fetchone()[0],0)
    def test_scope_disabled_policy_and_stale_lease_fail_before_credentials(self):
        issuer=Mock();(self.data/'nova-deploy-plan-policy.json').write_text('{}')
        with self.assertRaises(errors.Blocked): self.run_broker(issuer)
        issuer.assert_not_called();self.conn.execute('UPDATE agent_jobs SET lease_until=0');self.conn.commit()
        with self.assertRaises(PermissionError): self.run_broker(issuer)
        issuer.assert_not_called()
        for change in (dict(project='inventory'),dict(payload={'target':plan.PROFILE,'execute':True}),dict(kind='review_change')):
            with self.assertRaises(errors.Blocked): plan.scope(dict(self.job,**change))
    def test_snapshot_age_or_different_branch_is_reported_as_blocked_not_approval_ready(self):
        self.api.read_only=True;evidence=plan.ci.observe(self.api);at=time.time()
        with patch.object(plan,'OBSERVATION',dict(plan.OBSERVATION,observed_at=at-901)):
            report=plan.report_for(evidence,at,fixture.acceptance());self.assertFalse(report['checks']['platform_snapshot_fresh']);self.assertFalse(report['may_request_approval'])
        changed=dict(plan.OBSERVATION,repo=dict(plan.OBSERVATION['repo'],head='f'*40))
        with patch.object(plan,'OBSERVATION',changed):
            report=plan.report_for(evidence,at,fixture.acceptance());self.assertFalse(report['checks']['platform_and_branch_identity'])
    def test_tampered_scope_evidence_simulation_or_permission_is_rejected(self):
        self.run_broker();report=json.loads(self.conn.execute('SELECT report FROM nova_publication_plans').fetchone()[0])
        for change in (dict(publish_allowed=True),dict(may_request_approval=True),dict(mode='execute'),dict(blockers=[]),dict(scope_sha256='a'*64),dict(simulation=dict(report['simulation'],real_Render_calls=1))):
            self.assertFalse(plan.valid(dict(report,**change)))
        self.conn.execute("UPDATE nova_publication_plans SET report='{}'");self.conn.commit()
        with self.assertRaises(errors.Blocked): self.run_broker()
    def test_failed_ci_does_not_produce_publication_plan_or_simulated_pass(self):
        self.api.run['conclusion']='failure';self.api.job['conclusion']='failure';self.api.job['steps'][0]['conclusion']='failure'
        with self.assertRaises(errors.Blocked): self.run_broker()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM nova_publication_plans').fetchone()[0],0)
    def test_memory_plan_and_expiry_revalidate_source_without_completing_publication(self):
        result=self.run_broker();q.finish(self.conn,self.job['id'],self.job['lease_token'],result);memory.sync(self.conn)
        mid=self.conn.execute("SELECT id FROM project_evidence_memory WHERE event_id IN (SELECT id FROM agent_job_events WHERE job_id=? AND event='succeeded')",(self.job['id'],)).fetchone()[0]
        self.assertIn('nova_deploy',memory.detail(self.conn,mid));self.assertIn('три фиктивных сценария',memory.summary(self.conn,'nova'))
        self.assertIn('Протокол/симулятор выпуска проверен',roadmap.describe(self.conn));self.assertNotIn('9. Согласование публикаций — ✅ выполнено',roadmap.describe(self.conn))
        report=json.loads(self.conn.execute('SELECT report FROM nova_publication_plans').fetchone()[0])
        with patch.object(time,'time',return_value=report['scope']['expires_at']+1): self.assertIn('план устарел',plan.describe(self.conn))
        self.conn.execute("UPDATE nova_publication_plans SET report='{}'");self.conn.commit()
        self.assertIn('повторной проверки',memory.detail(self.conn,mid));self.assertNotIn('Протокол/симулятор выпуска проверен',roadmap.describe(self.conn))
    def test_worker_persists_one_plan_notice_without_approving_anything(self):
        self.conn.execute("UPDATE agent_jobs SET state='queued',lease_token=NULL,lease_until=NULL");self.conn.commit()
        def request(path,job):
            with sqlite3.connect(path) as conn:
                api=FakeAPI();api.read_only=True
                report=plan.report_for(plan.ci.observe(api),time.time(),fixture.acceptance())
                return plan.save(conn,job,report)
        with patch.object(queue_worker.artifact_pr_client,'request',side_effect=request): self.assertEqual(queue_worker.run_once(self.path),{'id':self.job['id'],'state':'succeeded'})
        notes=self.conn.execute('SELECT title,reason FROM owner_notifications').fetchall();self.assertEqual(len(notes),1)
        self.assertIn('Реальное исполнение отключено',notes[0][1]);self.assertEqual(self.conn.execute('SELECT count(*) FROM approvals').fetchone()[0],0)
    def test_failed_plan_uses_own_alarm(self):
        self.conn.execute("UPDATE agent_jobs SET state='queued',lease_token=NULL,lease_until=NULL");self.conn.commit()
        with patch.object(queue_worker.artifact_pr_client,'request',side_effect=errors.Blocked('publication_plan_policy_disabled')):
            self.assertEqual(queue_worker.run_once(self.path),{'id':self.job['id'],'state':'failed'})
        self.assertEqual(self.conn.execute('SELECT title,event_key FROM owner_notifications').fetchall(),[('Проверка плана выпуска остановлена','nova-deploy-plan-stopped-'+str(self.job['id']))])
    def test_report_commit_gap_leaves_no_plan_or_live_approval(self):
        self.conn.execute("CREATE TRIGGER deny_plan BEFORE INSERT ON nova_publication_plans BEGIN SELECT RAISE(FAIL,'copy-only gap'); END");self.conn.commit()
        with self.assertRaises(sqlite3.IntegrityError): self.run_broker()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM nova_publication_plans').fetchone()[0],0)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM approvals').fetchone()[0],0)
