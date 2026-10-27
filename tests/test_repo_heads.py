import copy
import concurrent.futures
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import patch
import urllib.error
import emergency_control as emergency
import evidence_memory as memory
import main
import owner_notifications as inbox
import project_registry as registry
import queue_worker
import repo_heads as heads
import roadmap
import scheduler
import task_queue as q


class Response(io.BytesIO):
    def __init__(self,value,url):super().__init__(json.dumps(value).encode());self.url=url;self.status=200;self.headers={}
    def geturl(self):return self.url

class RepositoryHeadTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'control.db'
        self.conn=queue_worker.connect(self.path);queue_worker.initialize(self.conn)
        self.seen=[]
        roadmap.set_setting(self.conn,"repo_head_gate","enabled")
    def tearDown(self):self.conn.close();self.temp.cleanup()
    def opener(self,request,timeout):
        self.seen.append((request.full_url,request.get_method(),dict(request.header_items())))
        config=registry.REPOSITORIES['kinder' if 'Kinder-Spa-android' in request.full_url else 'nova']
        if '/git/ref/' in request.full_url:value={'ref':'refs/heads/main','object':{'type':'commit','sha':config['revision']}}
        else:value={'id':config['repository_id'],'full_name':registry.OWNER+'/'+config['repository'],'private':False,'fork':False,'default_branch':'main','owner':{'login':registry.OWNER,'id':registry.OWNER_ID}}
        return Response(value,request.full_url)
    def job(self,project='nova'):
        ident=q.enqueue(self.conn,project,'inspect_repository',heads.payload(project),max_attempts=1)
        job=q.claim(self.conn,'fixture-head-'+str(ident),q.KINDS)
        self.assertEqual(ident,job['id']);return job
    def complete(self,*,project='nova',head=None,status='observed',error=None,stamp=None):
        job=self.job(project);report=heads.observe(job,opener=self.opener)
        if head:report['head_sha']=head
        if status!='observed':report.update(status=status,error_code=error,head_sha=None)
        if stamp is not None:report['observed_at']=stamp
        result=heads.complete(self.conn,job,report);return job,report,result

    def test_only_two_fixed_get_endpoints_and_no_credentials_code_or_tests(self):
        job=self.job();report=heads.observe(job,opener=self.opener)
        self.assertTrue(heads.valid(report,'nova'));self.assertEqual(report['head_sha'],registry.REPOSITORIES['nova']['revision'])
        self.assertEqual(len(self.seen),2)
        self.assertTrue(all(method=='GET' and url.startswith('https://api.github.com/repos/matrix12345695-afk/nova-web-agency') for url,method,headers in self.seen))
        self.assertFalse(any('Authorization' in headers for url,method,headers in self.seen))
        self.assertFalse(report['tests_executed']);self.assertFalse(report['code_executed']);self.assertFalse(report['published'])

    def test_inventory_unknown_project_and_arbitrary_payload_are_denied_before_network(self):
        for project in ('inventory','inventory-mini-app','control','foreign'):
            with self.assertRaises(registry.RepositoryScopeError):heads.observe({'project':project,'kind':'inspect_repository','payload':{'target':heads.PROFILE}},opener=self.opener)
        job=self.job();job['payload']['url']='https://foreign.invalid'
        with self.assertRaises(registry.RepositoryScopeError):heads.observe(job,opener=self.opener)
        self.assertEqual(self.seen,[])

    def test_identity_visibility_branch_and_ref_changes_fail_closed(self):
        for key,value in (('id',0),('private',True),('fork',True),('default_branch','other'),('full_name','foreign/repo'),('owner',{'login':registry.OWNER,'id':True})):
            def changed(request,timeout):
                response=self.opener(request,timeout);data=json.loads(response.getvalue());data[key]=value;return Response(data,request.full_url)
            report=heads.observe({'project':'nova','kind':'inspect_repository','payload':heads.payload('nova')},opener=changed)
            self.assertEqual(report['status'],'scope_denied');self.assertIsNone(report['head_sha'])
        def changed_ref(request,timeout):
            response=self.opener(request,timeout)
            if '/git/ref/' in request.full_url:return Response({'ref':'refs/tags/main','object':{'type':'tag','sha':'a'*40}},request.full_url)
            return response
        self.assertEqual(heads.observe(self.job(),opener=changed_ref)['error_code'],'ref')

    def test_network_errors_are_bounded_sanitized_and_never_become_a_healthy_snapshot(self):
        def failed(*args,**kwargs):raise OSError('https://example.invalid/private-fixture-value')
        report=heads.observe(self.job(),opener=failed)
        self.assertEqual(report['status'],'unavailable');self.assertEqual(report['error_code'],'network')
        self.assertNotIn('private-fixture-value',json.dumps(report))
        for value in (None,True,float('nan'),'today'):
            self.assertFalse(heads.valid(dict(report,observed_at=value),'nova'))
        with self.assertRaises(heads.ReadError):heads.NoRedirect().redirect_request(None,None,None,None,None,None)

    def test_body_and_deadline_checks_reject_oversized_slow_or_retargeted_responses(self):
        def oversized(request,timeout):return Response({'data':'x'*70000},request.full_url)
        self.assertEqual(heads.observe({'project':'nova','kind':'inspect_repository','payload':heads.payload('nova')},opener=oversized)['error_code'],'oversize')
        def retargeted(request,timeout):return Response({},'https://foreign.invalid/')
        self.assertEqual(heads.observe({'project':'nova','kind':'inspect_repository','payload':heads.payload('nova')},opener=retargeted)['status'],'scope_denied')
        with patch.object(heads.time,'monotonic',side_effect=[0,0,13]):
            self.assertEqual(heads.observe({'project':'nova','kind':'inspect_repository','payload':heads.payload('nova')},opener=self.opener)['error_code'],'deadline')

    def test_manual_buckets_and_explicit_schedules_respect_existing_owner_disable(self):
        first=heads.enqueue(self.conn,'nova',now=100);self.assertEqual(first,heads.enqueue(self.conn,'nova',now=200))
        self.assertNotEqual(first,heads.enqueue(self.conn,'nova',now=1000))
        scheduler.seed(self.conn,now=0);prior=self.conn.execute('SELECT * FROM agent_schedules ORDER BY name').fetchall()
        heads.seed(self.conn,now=100);self.conn.execute('UPDATE agent_schedules SET enabled=0 WHERE name=?',(heads.schedule_name('nova'),));self.conn.commit()
        heads.seed(self.conn,now=200)
        self.assertEqual(self.conn.execute('SELECT enabled,next_due FROM agent_schedules WHERE name=?',(heads.schedule_name('nova'),)).fetchone(),(0,21700))
        self.assertEqual(prior,self.conn.execute("SELECT * FROM agent_schedules WHERE name NOT LIKE 'repo-head-%' ORDER BY name").fetchall())

    def test_periodic_tick_pause_emergency_and_restart_are_idempotent(self):
        heads.seed(self.conn,now=100);q.configure(self.conn,paused=True)
        self.assertEqual(scheduler.tick(self.conn,now=22000),[])
        q.configure(self.conn,paused=False);ids=scheduler.tick(self.conn,now=22000)
        self.assertEqual(len(ids),2);self.assertEqual(scheduler.tick(self.conn,now=22000),[])
        self.assertEqual(len(scheduler.tick(self.conn,now=1000000)),2)
        emergency.stop(self.conn);self.assertEqual(scheduler.tick(self.conn,now=2000000),[])

    def test_unknown_schedule_is_never_overwritten(self):
        heads.seed(self.conn,now=100);self.conn.execute('UPDATE agent_schedules SET payload=? WHERE name=?',('{}',heads.schedule_name('nova')));self.conn.commit()
        with self.assertRaises(ValueError):heads.seed(self.conn,now=1000)
        self.assertEqual(self.conn.execute('SELECT payload FROM agent_schedules WHERE name=?',(heads.schedule_name('nova'),)).fetchone()[0],'{}')

    def test_disabled_gate_blocks_manual_and_schedule_admission_without_changing_other_work(self):
        heads.seed(self.conn,now=100);roadmap.set_setting(self.conn,'repo_head_gate','disabled')
        with self.assertRaises(registry.RepositoryScopeError):heads.enqueue(self.conn,'nova')
        self.assertEqual(scheduler.tick(self.conn,now=22000),[])
        self.assertEqual(self.conn.execute('SELECT count(*) FROM agent_jobs').fetchone()[0],0)
        q.enqueue(self.conn,'control','daily_report',{});self.assertEqual(queue_worker.run_once(self.path)['state'],'succeeded')

    def test_scheduled_admission_and_next_due_share_the_same_transaction(self):
        heads.seed(self.conn,now=100);before=self.conn.execute('SELECT * FROM agent_schedules ORDER BY name').fetchall()
        with patch.object(q,'_event',side_effect=sqlite3.OperationalError('fixture fault')):
            with self.assertRaises(sqlite3.OperationalError):heads.tick(self.conn,22000)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM agent_jobs').fetchone()[0],0)
        self.assertEqual(before,self.conn.execute('SELECT * FROM agent_schedules ORDER BY name').fetchall())

    def test_invalid_schedule_alerts_once_and_preserves_independent_target(self):
        heads.seed(self.conn,now=100);self.conn.execute('UPDATE agent_schedules SET payload=? WHERE name=?',('{}',heads.schedule_name('nova')));self.conn.commit()
        self.assertEqual(len(heads.tick(self.conn,22000)),1)
        self.assertEqual(heads.tick(self.conn,22000),[])
        self.assertEqual(self.conn.execute("SELECT count(*) FROM owner_notifications WHERE event_key='repo-head-schedule-invalid:nova'").fetchone()[0],1)

    def test_matching_initial_head_is_quiet_new_heads_notify_once_and_pins_remain(self):
        baseline=copy.deepcopy(registry.REPOSITORIES)
        self.complete();self.assertEqual(self.conn.execute('SELECT count(*) FROM owner_notifications').fetchone()[0],0)
        self.complete(head='a'*40);self.complete(head='a'*40)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM owner_notifications').fetchone()[0],1)
        self.complete(head='b'*40)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM owner_notifications').fetchone()[0],2)
        self.assertEqual(registry.REPOSITORIES,baseline)
        self.assertIn('прежние тесты его не подтверждают',heads.describe(self.conn))

    def test_scope_critical_survives_network_errors_and_only_its_own_recovery_resolves_it(self):
        other=inbox.create(self.conn,'other','decision','unrelated fixture','reason','action',event_key='other-fixture')
        self.complete(status='scope_denied',error='identity');critical=self.conn.execute("SELECT id FROM owner_notifications WHERE kind='critical'").fetchone()[0]
        self.complete(status='unavailable',error='network');self.complete(status='unavailable',error='http_403')
        self.assertEqual(self.conn.execute('SELECT state FROM owner_notifications WHERE id=?',(critical,)).fetchone()[0],'pending')
        self.complete()
        self.assertEqual(self.conn.execute('SELECT state FROM owner_notifications WHERE id=?',(critical,)).fetchone()[0],'resolved')
        self.assertEqual(self.conn.execute('SELECT state FROM owner_notifications WHERE id=?',(other,)).fetchone()[0],'pending')

    def test_snapshot_job_event_and_notice_rollback_atomically(self):
        job=self.job();report=heads.observe(job,opener=self.opener);report['head_sha']='a'*40
        with patch.object(q,'_event',side_effect=sqlite3.OperationalError('fixture fault')):
            with self.assertRaises(sqlite3.OperationalError):heads.complete(self.conn,job,report)
        for table in ('repository_head_runs','repository_head_state','owner_notifications'):
            self.assertEqual(self.conn.execute('SELECT count(*) FROM '+table).fetchone()[0],0)
        self.assertEqual(self.conn.execute('SELECT state FROM agent_jobs WHERE id=?',(job['id'],)).fetchone()[0],'running')

    def test_lease_epoch_and_report_tampering_cannot_complete(self):
        job=self.job();report=heads.observe(job,opener=self.opener)
        with self.assertRaises(PermissionError):heads.complete(self.conn,dict(job,lease_token='foreign'),report)
        for key,value in (('baseline_sha','a'*40),('tests_executed',True),('credential_used',True),('head_sha','not-a-commit')):
            with self.assertRaises(ValueError):heads.complete(self.conn,job,dict(report,**{key:value}))
        emergency.stop(self.conn)
        with self.assertRaises(emergency.Stopped):heads.complete(self.conn,job,report)

    def test_late_observation_is_retained_without_replacing_latest_or_notifying(self):
        old=self.job();old_report=heads.observe(old,opener=self.opener)
        q.configure(self.conn,concurrency=2);new=self.job();new_report=heads.observe(new,opener=self.opener);new_report['head_sha']='a'*40
        heads.complete(self.conn,new,new_report);heads.complete(self.conn,old,old_report)
        result=json.loads(self.conn.execute('SELECT result FROM agent_jobs WHERE id=?',(old['id'],)).fetchone()[0])
        self.assertTrue(result['superseded']);self.assertEqual(heads.latest(self.conn,'nova')[0]['head_sha'],'a'*40)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM owner_notifications').fetchone()[0],1)

    def test_failed_read_is_a_failed_job_with_immutable_evidence_and_independent_work_continues(self):
        job,report,result=self.complete(status='unavailable',error='network')
        self.assertEqual(self.conn.execute('SELECT state FROM agent_jobs WHERE id=?',(job['id'],)).fetchone()[0],'failed')
        self.assertEqual(heads.record(self.conn,result['repo_head_id'])[0],report)
        with self.assertRaises(sqlite3.IntegrityError):self.conn.execute('DELETE FROM repository_head_runs')
        self.conn.rollback();ident=q.enqueue(self.conn,'control','daily_report',{})
        self.assertEqual(queue_worker.run_once(self.path)['id'],ident)

    def test_memory_and_views_are_read_only_and_detect_mutated_source_results(self):
        job,report,result=self.complete();heads.seed(self.conn)
        while memory.sync(self.conn)['scanned']:pass
        mid=self.conn.execute('SELECT id FROM project_evidence_memory').fetchone()[0]
        self.assertIn('repo_head',memory.detail(self.conn,mid))
        before=self.conn.total_changes;heads.describe(self.conn);heads.latest(self.conn,'nova')
        self.assertEqual(before,self.conn.total_changes)
        self.conn.execute('UPDATE agent_jobs SET result=? WHERE id=?',('{}',job['id']));self.conn.commit()
        self.assertIn('повторной проверки',memory.detail(self.conn,mid));self.assertIn('требуют проверки',heads.describe(self.conn))

    def test_worker_commits_one_result_and_failed_status_is_not_success(self):
        ident=heads.enqueue(self.conn,'nova')
        with patch.object(heads,'observe',side_effect=lambda job:heads_observe(job,self.opener)):
            self.assertEqual(queue_worker.run_once(self.path),{'id':ident,'state':'succeeded'})
        ident=heads.enqueue(self.conn,'kinder')
        def failed(job):
            report=heads_observe(job,self.opener);report.update(status='unavailable',error_code='network',head_sha=None);return report
        with patch.object(heads,'observe',side_effect=failed):self.assertEqual(queue_worker.run_once(self.path),{'id':ident,'state':'failed'})
        self.assertEqual(self.conn.execute('SELECT count(*) FROM provider_costs').fetchone()[0],0)

    def test_corrupt_report_does_not_stall_memory_cursor_or_independent_jobs(self):
        job,report,result=self.complete()
        self.conn.execute('UPDATE agent_jobs SET result=? WHERE id=?',(json.dumps(dict(result,report_sha256='a'*64)),job['id']));self.conn.commit()
        while memory.sync(self.conn)['scanned']:pass
        ident=q.enqueue(self.conn,'control','daily_report',{});self.assertEqual(queue_worker.run_once(self.path)['id'],ident)
        for invalid in (True,[],0,2**64):
            with self.assertRaises(ValueError):heads.record(self.conn,invalid)

    def test_commands_and_partial_plan_keep_production_and_test_claims_separate(self):
        self.complete();roadmap.mark(self.conn,7,'active','more project scopes needed')
        with patch.object(main,'DB',self.path):
            self.assertIn('Контроль main GitHub',main.command('/roadmap'));self.assertIn('7. Несколько проектов — в работе',main.command('/roadmap'))
            self.assertIn('опубликованная версия проверяется отдельно',main.command('/repo_heads'))
            self.assertIn('Inventory исключён',main.command('/repo_head inventory'))
            self.assertIn('в очереди',main.command('/repo_head kinder'))
        self.assertIn('устарел',heads.describe(self.conn,now=time.time()+heads.FRESH+10))

# Preserve the real implementation while patching the worker's dependency.
_original_observe=heads.observe
def heads_observe(job,opener):return _original_observe(job,opener=opener)

if __name__=='__main__':unittest.main()
