import copy
from datetime import datetime,timedelta,timezone
import hashlib
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
import browser_ci as ci
import browser_ci_broker as broker
import evidence_memory as memory
import queue_worker
import task_queue as q


class FakeAPI:
    def __init__(self):
        self.read_only=False;self.calls=[];self.final_reads=0;self.rerun_after_artifact=False
        self.run={'id':777,'run_attempt':1,'head_sha':ci.CONTRACT['harness_commit'],'event':'push','name':ci.CONTRACT['workflow_name'],
                  'path':ci.CONTRACT['workflow_path'],'repository':{'id':1429215344},'head_repository':{'id':1429215344},'status':'completed','conclusion':'success'}
        self.job={'id':888,'run_id':777,'head_sha':ci.CONTRACT['harness_commit'],'name':ci.CONTRACT['workflow_name'],'status':'completed','conclusion':'success',
                  'runner_group_name':'GitHub Actions','labels':['ubuntu-24.04'],'steps':[{'name':name,'status':'completed','conclusion':'success'} for name in (ci.CONTRACT['gate_step'],'Upload browser evidence')]}
        self.artifact={'id':555,'name':'nova-browser-evidence-1','expired':False,'size_in_bytes':123456,'digest':'sha256:'+'a'*64,
                       'expires_at':(datetime.now(timezone.utc)+timedelta(days=30)).isoformat(),
                       'workflow_run':{'id':777,'head_sha':ci.CONTRACT['harness_commit'],'repository_id':1429215344,'head_repository_id':1429215344}}
        self.artifacts=[self.artifact];self.total_count=1
    def call(self,method,path,*args,**kwargs):
        assert method=='GET' and self.read_only;self.calls.append((method,path))
        if path.startswith('/actions/runs?'): return {'workflow_runs':[copy.deepcopy(self.run)]}
        if '/jobs?' in path: return {'total_count':1,'jobs':[copy.deepcopy(self.job)]}
        if '/artifacts?' in path: return {'total_count':self.total_count,'artifacts':copy.deepcopy(self.artifacts)}
        self.final_reads+=1
        return dict(self.run,run_attempt=2) if self.rerun_after_artifact and self.final_reads>=2 else copy.deepcopy(self.run)


class BrowserCITests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.data=Path(self.temp.name);self.path=self.data/'control.db'
        self.conn=sqlite3.connect(self.path);queue_worker.initialize(self.conn)
        ident=q.enqueue(self.conn,'nova','test_release',{'target':ci.PROFILE});self.job=q.claim(self.conn,'unit',q.KINDS);self.assertEqual(ident,self.job['id'])
        for name,body in [('browser-ci-policy.json',util.canonical({'enabled':True,'profile':ci.PROFILE,'contract_sha256':util.digest(ci.CONTRACT)})),('review-executor-activation-approved','approved')]:
            p=self.data/name;p.write_text(body);p.chmod(0o600)
        self.api=FakeAPI();self.scopes=[]
    def tearDown(self): self.conn.close();self.temp.cleanup()
    def run_broker(self,issuer=None):
        return broker.run(self.conn,{'job_id':self.job['id'],'lease_token':self.job['lease_token']},self.data,
            client_factory=lambda *args:self.api,token_issuer=issuer or (lambda *args,**kw:self.scopes.append(kw.get('read_only')) or 'fixture'))

    def test_exact_hosted_gate_and_attempt_artifact_are_read_only_and_honest(self):
        result=self.run_broker();self.assertEqual(self.scopes,[True]);self.assertFalse(result['vps_local_execution']);self.assertTrue(result['backend_mocked'])
        self.assertEqual(result['screenshots'],15);self.assertEqual(len(result['advisories']),2)
        self.assertTrue(all(method=='GET' for method,_ in self.api.calls))
        raw,sha=self.conn.execute('SELECT report,report_sha256 FROM browser_ci_runs').fetchone();report=json.loads(raw)
        self.assertTrue(ci.valid(report));self.assertEqual(util.digest(report),sha)
        self.run_broker();self.assertEqual(self.conn.execute('SELECT report FROM browser_ci_runs').fetchone()[0],raw)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM approvals').fetchone()[0],0)
        self.assertIn('реальные телефоны',ci.describe(self.conn))

    def test_missing_expired_wrong_attempt_or_foreign_artifact_cannot_pass(self):
        for change in ('missing','expired','attempt','source','repository','digest','size','ambiguous','partial'):
            api=FakeAPI();api.read_only=True
            if change=='missing': api.artifacts=[];api.total_count=0
            elif change=='expired': api.artifact['expires_at']='2000-01-01T00:00:00Z'
            elif change=='attempt': api.artifact['name']='nova-browser-evidence-2'
            elif change=='source': api.artifact['workflow_run']['head_sha']='e'*40
            elif change=='repository': api.artifact['workflow_run']['repository_id']=1
            elif change=='digest': api.artifact['digest']='unknown'
            elif change=='size': api.artifact['size_in_bytes']=30*1024**2
            elif change=='ambiguous': api.artifacts.append(copy.deepcopy(api.artifact));api.total_count=2
            else: api.total_count=2
            with self.subTest(change=change),self.assertRaises((errors.Blocked,errors.Pending)): ci.observe(api)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM browser_ci_runs').fetchone()[0],0)

    def test_gate_without_upload_or_rerun_during_artifact_read_is_not_success(self):
        self.api.job['steps'].pop()
        with self.assertRaises(errors.Blocked): self.run_broker()
        self.api=FakeAPI();self.api.rerun_after_artifact=True
        with self.assertRaises(errors.Pending): self.run_broker()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM browser_ci_runs').fetchone()[0],0)

    def test_scope_policy_and_expired_lease_are_checked_before_credentials(self):
        issuer=unittest.mock.Mock();(self.data/'browser-ci-policy.json').write_text('{}')
        with self.assertRaises(errors.Blocked): self.run_broker(issuer)
        issuer.assert_not_called()
        self.conn.execute('UPDATE agent_jobs SET lease_until=0');self.conn.commit()
        with self.assertRaises(PermissionError): self.run_broker(issuer)
        issuer.assert_not_called()
        with self.assertRaises(errors.Blocked): ci.scope(dict(self.job,project='inventory'))

    def test_failed_ci_has_no_fabricated_screenshots_counts_or_findings(self):
        self.api.run['conclusion']='failure';self.api.job['conclusion']='failure';self.api.job['steps'][0]['conclusion']='failure'
        result=self.run_broker();self.assertEqual(result['test_status'],'failed')
        report=json.loads(self.conn.execute('SELECT report FROM browser_ci_runs').fetchone()[0])
        for key in ('counts','screenshots','advisories','artifact'): self.assertIsNone(report[key])
        self.assertTrue(ci.valid(report))

    def test_historical_artifact_expiry_is_labelled_without_invalidating_past_fact(self):
        self.run_broker();report=json.loads(self.conn.execute('SELECT report FROM browser_ci_runs').fetchone()[0])
        with patch.object(time,'time',return_value=ci.expires(report['artifact']['expires_at'])+1):
            self.assertTrue(ci.valid(report));self.assertIn('Срок хранения архива истёк',ci.describe(self.conn))

    def test_report_scope_counts_and_archive_tampering_are_rejected(self):
        self.api.read_only=True;report=ci.observe(self.api)
        for change in (dict(vps_local_execution=True),dict(backend_mocked=False),dict(harness_commit='a'*40),dict(screenshots=14),dict(advisories=[]),dict(physical_device_test=True),dict(artifact=dict(report['artifact'],url='https://other.invalid'))):
            self.assertFalse(ci.valid(dict(report,**change)))
        with self.assertRaises(errors.Blocked): ci.save(self.conn,self.job,dict(report,checked_at=time.time()+100))

    def test_atomic_write_failure_and_changed_saved_evidence_fail_closed(self):
        self.conn.execute("CREATE TRIGGER fail_browser BEFORE INSERT ON browser_ci_runs BEGIN SELECT RAISE(FAIL,'copy-only commit gap'); END");self.conn.commit()
        with self.assertRaises(sqlite3.IntegrityError): self.run_broker()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM browser_ci_runs').fetchone()[0],0)
        self.conn.execute('DROP TRIGGER fail_browser');self.conn.commit();self.run_broker()
        self.conn.execute("UPDATE browser_ci_runs SET report='{}'");self.conn.commit()
        with self.assertRaises(errors.Blocked): self.run_broker()

    def test_memory_binds_report_and_detects_changed_archive_evidence(self):
        result=self.run_broker();q.finish(self.conn,self.job['id'],self.job['lease_token'],result);memory.sync(self.conn)
        mid=self.conn.execute("SELECT id FROM project_evidence_memory WHERE event_id IN (SELECT id FROM agent_job_events WHERE job_id=? AND event='succeeded')",(self.job['id'],)).fetchone()[0]
        self.assertIn('browser_ci',memory.detail(self.conn,mid));self.assertIn('скриншотами',memory.summary(self.conn,'nova'))
        self.conn.execute("UPDATE browser_ci_runs SET report='{}'");self.conn.commit();self.assertIn('повторной проверки',memory.detail(self.conn,mid))

    def test_worker_persists_one_notification_and_real_scope_labels(self):
        self.conn.execute("UPDATE agent_jobs SET state='queued',lease_token=NULL,lease_until=NULL");self.conn.commit()
        def request(path,job):
            with sqlite3.connect(path) as conn:
                api=FakeAPI();api.read_only=True;return ci.save(conn,job,ci.observe(api))
        with patch.object(queue_worker.artifact_pr_client,'request',side_effect=request): result=queue_worker.run_once(self.path)
        self.assertEqual(result,{'id':self.job['id'],'state':'succeeded'})
        notes=self.conn.execute('SELECT reason FROM owner_notifications').fetchall();self.assertEqual(len(notes),1)
        self.assertIn('API подставной',notes[0][0]);self.assertIn('Два замечания',notes[0][0])
        self.assertEqual(self.conn.execute('SELECT count(*) FROM provider_costs').fetchone()[0],0)

    def test_pure_screenshot_gate_rejects_missing_images_changed_bytes_and_wrong_coverage(self):
        spec=importlib.util.spec_from_file_location('browser_gate',Path(ci.__file__).parent/'ci/nova-browser/gate.py')
        gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
        folder=self.data/'evidence';folder.mkdir();images=[]
        for name in gate.SHOTS:
            viewport=next(v for v in gate.VIEWPORTS if v in name);width,height=gate.VIEWPORTS[viewport]
            raw=b'\x89PNG\r\n\x1a\n'+b'\0'*8+width.to_bytes(4,'big')+height.to_bytes(4,'big')+b'\0'*1000
            (folder/name).write_bytes(raw);images.append(dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
        report=dict(schema=ci.PROFILE,source_revision=gate.REVISION,source_manifest_sha256='a'*64,engine='chromium',browser_version='151.0.7922.34',playwright_version='1.62.0',
                    counts=dict(tests=27,pass_=27,fail=0,errors=0,skipped=0),viewports=gate.VIEWPORTS,screenshots=images,advisories=gate.ADVISORIES,
                    backend_mocked=True,production_access=False,page_network_intercepted=True,physical_device_test=False,pixel_baseline_test=False,published=False)
        report['counts']['pass']=report['counts'].pop('pass_');(folder/'report.json').write_text(json.dumps(report))
        self.assertTrue(gate.validate(report,'a'*64));gate.files(report,folder)
        for change in (dict(screenshots=images[:-1]),dict(advisories=[]),dict(counts=dict(report['counts'],skipped=1))):
            with self.assertRaises(ValueError): gate.validate(dict(report,**change),'a'*64)
        (folder/images[0]['path']).write_bytes(b'changed')
        with self.assertRaises(ValueError): gate.files(report,folder)
