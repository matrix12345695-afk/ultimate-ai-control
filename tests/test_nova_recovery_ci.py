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
import nova_recovery_ci as ci
import nova_recovery_broker as broker
import evidence_memory as memory
import queue_worker
import roadmap
import task_queue as q
from test_browser_ci import FakeAPI as BaselineAPI

class FakeAPI(BaselineAPI):
    def __init__(self):
        with patch.object(baseline,'CONTRACT',ci.CONTRACT): super().__init__()
        self.artifact['name']=ci.CONTRACT['artifact_name_prefix']+'1';self.artifact['size_in_bytes']=8000
        self.job['steps'][1]['name']=ci.CONTRACT['upload_step']

class RecoveryCITests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.data=Path(self.temp.name);self.path=self.data/'control.db'
        self.conn=sqlite3.connect(self.path);queue_worker.initialize(self.conn)
        q.enqueue(self.conn,'nova','test_release',{'target':ci.PROFILE});self.job=q.claim(self.conn,'recovery-unit',q.KINDS)
        for name,body in [('nova-recovery-ci-policy.json',util.canonical({'enabled':True,'profile':ci.PROFILE,'contract_sha256':util.digest(ci.CONTRACT)})),('review-executor-activation-approved','approved')]:
            p=self.data/name;p.write_text(body);p.chmod(0o600)
        self.api=FakeAPI();self.scopes=[]
    def tearDown(self): self.conn.close();self.temp.cleanup()
    def run_broker(self,issuer=None):
        return broker.run(self.conn,{'job_id':self.job['id'],'lease_token':self.job['lease_token']},self.data,client_factory=lambda *a:self.api,token_issuer=issuer or (lambda *a,**kw:self.scopes.append(kw.get('read_only')) or 'fixture'))
    def test_exact_read_only_ci_and_historical_metadata_do_not_mean_live_backup(self):
        result=self.run_broker();self.assertEqual(self.scopes,[True]);self.assertEqual(result['test_counts']['pass'],24)
        raw,sha=self.conn.execute('SELECT report,report_sha256 FROM nova_recovery_ci_runs').fetchone();report=json.loads(raw)
        self.assertTrue(ci.valid(report));self.assertEqual(util.digest(report),sha);self.assertEqual(report['postgres_major'],18);self.assertEqual(report['fixture_leads'],5003)
        self.assertEqual(report['legacy_export_limit'],5000);self.assertFalse(report['production_backup_verified']);self.assertFalse(report['Render_rollback_eligible'])
        self.assertTrue(all(method=='GET' for method,_ in self.api.calls));self.run_broker();self.assertEqual(self.conn.execute('SELECT report FROM nova_recovery_ci_runs').fetchone()[0],raw)
        for table in ('nova_publication_plans','locked_build_ci_runs','approvals','provider_costs','artifact_release_candidates'):
            self.assertEqual(self.conn.execute('SELECT count(*) FROM '+table).fetchone()[0],0)
    def test_wrong_harness_upload_archive_and_rerun_are_denied(self):
        old=BaselineAPI();old.read_only=True
        with self.assertRaises(errors.Pending): ci.observe(old)
        for change in ('upload','artifact','attempt','source','digest','expiry','dump_size','duplicate'):
            api=FakeAPI();api.read_only=True
            if change=='upload': api.job['steps'][1]['name']='Upload browser evidence'
            elif change=='artifact': api.artifact['name']='nova-locked-build-1'
            elif change=='attempt': api.rerun_after_artifact=True
            elif change=='source': api.artifact['workflow_run']['head_sha']='a'*40
            elif change=='digest': api.artifact['digest']='unknown'
            elif change=='expiry': api.artifact['expires_at']='2000-01-01T00:00:00Z'
            elif change=='dump_size': api.artifact['size_in_bytes']=200000
            else: api.artifacts.append(dict(api.artifact));api.total_count=2
            with self.subTest(change=change),self.assertRaises((errors.Blocked,errors.Pending)): ci.observe(api)
    def test_scope_policy_and_lease_before_credentials(self):
        issuer=Mock();(self.data/'nova-recovery-ci-policy.json').write_text('{}')
        with self.assertRaises(errors.Blocked): self.run_broker(issuer)
        issuer.assert_not_called();self.conn.execute('UPDATE agent_jobs SET lease_until=0');self.conn.commit()
        with self.assertRaises(PermissionError): self.run_broker(issuer)
        issuer.assert_not_called()
        for change in (dict(project='inventory'),dict(payload={'target':ci.PROFILE,'export_live':True}),dict(kind='review_change')):
            with self.assertRaises(errors.Blocked): ci.scope(dict(self.job,**change))
    def test_counts_snapshot_archive_and_production_status_cannot_be_forged(self):
        self.api.read_only=True;report=ci.observe(self.api)
        for change in (dict(counts=dict(report['counts'],tests=23)),dict(postgres_major=16),dict(production_backup_verified=True),dict(Render_rollback_eligible=True),dict(publish_allowed=True),dict(fixture_leads=5000),dict(platform_snapshot_sha256='a'*64),dict(archive=dict(report['archive'],digest='unknown'))):
            self.assertFalse(ci.valid(dict(report,**change)))
        with self.assertRaises(errors.Blocked): ci.save(self.conn,self.job,dict(report,checked_at=time.time()+100))
        self.run_broker();self.conn.execute("UPDATE nova_recovery_ci_runs SET report='{}'");self.conn.commit()
        with self.assertRaises(errors.Blocked): self.run_broker()
    def test_typed_memory_and_plan_remain_partial_and_validate_source(self):
        result=self.run_broker();q.finish(self.conn,self.job['id'],self.job['lease_token'],result);memory.sync(self.conn)
        mid=self.conn.execute("SELECT id FROM project_evidence_memory WHERE event_id IN (SELECT id FROM agent_job_events WHERE job_id=? AND event='succeeded')",(self.job['id'],)).fetchone()[0]
        self.assertIn('nova_recovery_ci',memory.detail(self.conn,mid));self.assertIn('24 проверки',memory.summary(self.conn,'nova'))
        self.assertIn('PG18: восстановлены5003',roadmap.describe(self.conn));self.assertNotIn('9. Согласование публикаций — ✅ выполнено',roadmap.describe(self.conn))
        self.assertIn('19.11.2026',ci.describe(self.conn));self.assertIn('НЕ подтверждены',ci.describe(self.conn))
        self.conn.execute("UPDATE nova_recovery_ci_runs SET report='{}'");self.conn.commit()
        self.assertIn('повторной проверки',memory.detail(self.conn,mid));self.assertNotIn('PG18: восстановлены5003',roadmap.describe(self.conn))
    def worker(self,failed=False):
        self.conn.execute("UPDATE agent_jobs SET state='queued',lease_token=NULL,lease_until=NULL");self.conn.commit()
        def request(path,job):
            with sqlite3.connect(path) as conn:
                api=FakeAPI();api.read_only=True
                if failed: api.run['conclusion']='failure';api.job['conclusion']='failure';api.job['steps'][0]['conclusion']='failure'
                return ci.save(conn,job,ci.observe(api))
        with patch.object(queue_worker.artifact_pr_client,'request',side_effect=request): return queue_worker.run_once(self.path)
    def test_success_notice_is_fixture_only_and_no_approval_or_paid_call(self):
        self.assertEqual(self.worker(),{'id':self.job['id'],'state':'succeeded'})
        notes=self.conn.execute('SELECT reason FROM owner_notifications').fetchall();self.assertEqual(len(notes),1);self.assertIn('синтетические',notes[0][0]);self.assertIn('Реальная копия ещё не подтверждена',notes[0][0])
        for table in ('provider_costs','approvals','artifact_release_candidates'): self.assertEqual(self.conn.execute('SELECT count(*) FROM '+table).fetchone()[0],0)
    def test_failed_ci_never_claims_recovery_verified(self):
        self.assertEqual(self.worker(True),{'id':self.job['id'],'state':'failed'})
        report=json.loads(self.conn.execute('SELECT report FROM nova_recovery_ci_runs').fetchone()[0]);self.assertIsNone(report['counts']);self.assertIsNone(report['archive']);self.assertFalse(report['fixture_restore_verified'])
        self.assertNotIn('PG18: восстановлены5003',roadmap.describe(self.conn))
    def test_blocked_scope_gets_own_alarm(self):
        self.conn.execute("UPDATE agent_jobs SET state='queued',lease_token=NULL,lease_until=NULL");self.conn.commit()
        with patch.object(queue_worker.artifact_pr_client,'request',side_effect=errors.Blocked('nova_recovery_policy_disabled')): self.assertEqual(queue_worker.run_once(self.path),{'id':self.job['id'],'state':'failed'})
        self.assertEqual(self.conn.execute('SELECT title,event_key FROM owner_notifications').fetchall(),[('Сверка восстановления остановлена','nova-recovery-stopped-'+str(self.job['id']))])
    def test_report_insert_failure_keeps_no_partial_success(self):
        self.conn.execute("CREATE TRIGGER deny_recovery BEFORE INSERT ON nova_recovery_ci_runs BEGIN SELECT RAISE(FAIL,'copy-only gap'); END");self.conn.commit()
        with self.assertRaises(sqlite3.IntegrityError): self.run_broker()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM nova_recovery_ci_runs').fetchone()[0],0)
