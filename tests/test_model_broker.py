from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import broker_client
import developer_pipeline
import metered_provider as api
import model_broker as broker
import main
import queue_worker
import task_queue as queue
from isolated_python import manifest


class BrokerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.db=self.root/'control.db'
        self.conn=sqlite3.connect(self.db)
        queue_worker.initialize(self.conn)
        self.db.chmod(0o600)
        self.write('broker-policy.json',broker.DEFAULT_POLICY)
        self.write('provider-policy.json',api.DEFAULT_POLICY)
        self.clock=patch.object(api,'datetime')
        clock=self.clock.start();clock.now.return_value=datetime(2026,10,22,12,tzinfo=timezone.utc)

    def tearDown(self):
        self.clock.stop();self.conn.close();self.temp.cleanup()

    def write(self,name,value):
        p=self.root/name;p.write_text(json.dumps(value));p.chmod(0o600);return p

    def job(self,demo=True,task=None,project='control'):
        ident=queue.enqueue(self.conn,project,'review_change',{'ai_task':task or (broker.DEMO_TASK if demo else 'Create a standalone progress component'),'broker_demo':demo})
        job=queue.claim(self.conn,'operations-1',queue.KINDS,lease_seconds=60)
        self.assertEqual(ident,job['id'])
        return job,{'protocol':broker.PROTOCOL,'job_id':ident,'lease_token':job['lease_token']}

    def stage(self):
        job,request=self.job()
        bundle=broker.process(self.conn,self.root,request)
        payload={'target':'developer-bundle','generation_job_id':job['id'],'source_digest':bundle['source_digest']}
        result={'source_digest':bundle['source_digest'],'engine':bundle['engine'],'tests_pending':True}
        child=queue.finish_with_test(self.conn,job['id'],job['lease_token'],result,payload,event_key='test:'+str(job['id']))
        return job,child,bundle

    def enable_fake_provider(self):
        self.write('broker-policy.json',dict(broker.DEFAULT_POLICY,enabled=True,allow_paid=True))
        self.write('provider-policy.json',dict(api.DEFAULT_POLICY,enabled=True))
        key=self.root/'fake.key';key.write_text('sk-test-only-not-real-'+'a'*40);key.chmod(0o600)
        patcher=patch.object(broker,'KEY_PATH',key);patcher.start();self.addCleanup(patcher.stop)
        return key

    def response(self):
        return {'id':'resp_fake_bundle','model':api.DEFAULT_POLICY['model'],'service_tier':'default','status':'completed',
                'usage':{'input_tokens':1000,'output_tokens':500,'total_tokens':1500},
                'output':[{'type':'message','role':'assistant','content':[{'type':'output_text','text':json.dumps({'summary':'Artificial model response for tests only','files':broker.DEMO_FILES})}]}]}

    def test_demo_never_reads_key_or_calls_provider_and_capsule_replays(self):
        job,request=self.job()
        with patch.object(api,'generate',side_effect=AssertionError('paid API forbidden')) as paid:
            first=broker.process(self.conn,self.root,request)
            second=broker.process(self.conn,self.root,request)
            paid.assert_not_called()
        self.assertEqual(first['source_digest'],second['source_digest'])
        self.assertEqual(first['engine'],'offline_broker_demo')
        self.assertEqual(self.conn.execute('SELECT count(*) FROM developer_bundles').fetchone()[0],1)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM provider_costs').fetchone()[0],0)

    def test_unauthorized_foreign_expired_and_paused_jobs_never_read_credentials(self):
        job,request=self.job()
        for changed in ({**request,'lease_token':'wrong'},{**request,'job_id':999},{**request,'endpoint':'https://evil.invalid/'}):
            with self.assertRaises(broker.BrokerFailed): broker.process(self.conn,self.root,changed)
        self.conn.execute("UPDATE agent_jobs SET project='nova' WHERE id=?",(job['id'],));self.conn.commit()
        with self.assertRaises(broker.BrokerFailed): broker.process(self.conn,self.root,request)
        self.conn.execute("UPDATE agent_jobs SET project='control',lease_until=0 WHERE id=?",(job['id'],));self.conn.commit()
        with self.assertRaises(broker.BrokerFailed): broker.process(self.conn,self.root,request)
        self.conn.execute("UPDATE agent_jobs SET lease_until=? WHERE id=?",(__import__('time').time()+60,job['id']));self.conn.commit()
        queue.configure(self.conn,paused=True)
        with self.assertRaises(broker.BrokerDeferred): broker.process(self.conn,self.root,request)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM developer_bundles').fetchone()[0],0)

    def test_disabled_paid_request_and_arbitrary_demo_are_not_implemented(self):
        job,request=self.job(demo=False)
        with patch.object(api,'generate',side_effect=AssertionError('must not send')):
            with self.assertRaisesRegex(broker.BrokerDeferred,'broker_disabled'): broker.process(self.conn,self.root,request)
        self.conn.execute('UPDATE agent_jobs SET payload=? WHERE id=?',(json.dumps({'ai_task':'different task','broker_demo':True}),job['id']));self.conn.commit()
        with self.assertRaisesRegex(broker.BrokerFailed,'unsupported_demo_task'): broker.process(self.conn,self.root,request)

    def test_parser_rejects_traversal_duplicate_fields_empty_tests_and_secrets(self):
        valid={'summary':'draft','files':broker.DEMO_FILES}
        bad=[dict(valid,endpoint='https://evil.invalid/'),{'summary':'draft','files':{'../escape.py':'x','tests/test_x.py':'def test_x(): pass'}},
             {'summary':'draft','files':{'tests/test_x.py':'answer=1'}},
             {'summary':'draft','files':{'tests/test_x.py':'def test_x(: pass'}},
             {'summary':'password=do-not-store','files':broker.DEMO_FILES}]
        for value in bad:
            with self.assertRaises((ValueError,SyntaxError,broker.BrokerFailed)): broker.parse_bundle(json.dumps(value))
        with self.assertRaisesRegex(broker.BrokerFailed,'duplicate_json_key'):
            broker.parse_bundle('{"summary":"first","summary":"second","files":{}}')
        marker=self.root/'must-not-execute'
        files=dict(broker.DEMO_FILES,evil=f"from pathlib import Path; Path({str(marker)!r}).write_text('no')")
        files['untrusted.py']=files.pop('evil')
        broker.parse_bundle(json.dumps({'summary':'draft','files':files}))
        self.assertFalse(marker.exists())

    def test_paid_response_is_metered_without_sending_lease_or_credentials_to_model(self):
        key=self.enable_fake_provider();job,request=self.job(demo=False)
        sent=[]
        def transport(payload,secret,trace):
            self.assertEqual(secret,key.read_text())
            raw=json.dumps(payload)
            self.assertNotIn(request['lease_token'],raw)
            self.assertNotIn(secret,raw)
            self.assertIn('complete source',payload['instructions'])
            self.assertEqual(payload['tools'],[])
            sent.append(trace);return self.response()
        first=broker.process(self.conn,self.root,request,transport=transport)
        self.assertEqual(first['engine'],'openai_broker')
        self.assertEqual(len(sent),1)
        self.assertEqual(self.conn.execute('SELECT actual_microusd FROM provider_costs').fetchone()[0],1250)
        self.assertEqual(broker.process(self.conn,self.root,request,transport=transport)['source_digest'],first['source_digest'])
        self.assertEqual(len(sent),1)

    def test_crash_after_paid_receipt_before_capsule_does_not_send_twice(self):
        self.enable_fake_provider();job,request=self.job(demo=False);sent=[]
        def transport(*args): sent.append(1);return self.response()
        with patch.object(broker,'parse_bundle',side_effect=RuntimeError('simulated process crash')):
            with self.assertRaises(RuntimeError): broker.process(self.conn,self.root,request,transport=transport)
        self.assertEqual(self.conn.execute('SELECT state FROM metered_requests').fetchone()[0],'completed')
        self.assertEqual(self.conn.execute('SELECT count(*) FROM developer_bundles').fetchone()[0],0)
        recovered=broker.process(self.conn,self.root,request,transport=transport)
        self.assertEqual(recovered['engine'],'openai_broker');self.assertEqual(len(sent),1)

    def test_ambiguous_paid_call_freezes_without_automatic_retries(self):
        self.enable_fake_provider();job,request=self.job(demo=False);sent=[]
        def timeout(*args): sent.append(1);raise TimeoutError()
        for _ in range(2):
            with self.assertRaises(broker.BrokerFailed): broker.process(self.conn,self.root,request,transport=timeout)
        self.assertEqual(len(sent),1)
        self.assertEqual(self.conn.execute('SELECT state FROM provider_costs').fetchone()[0],'unknown')
        self.assertEqual(self.conn.execute('SELECT count(*) FROM developer_bundles').fetchone()[0],0)

    def test_atomic_generation_test_link_rolls_back_all_partial_changes(self):
        job,request=self.job();bundle=broker.process(self.conn,self.root,request)
        payload={'target':'developer-bundle','generation_job_id':job['id'],'source_digest':bundle['source_digest']}
        with self.assertRaises(ValueError):
            queue.finish_with_test(self.conn,job['id'],job['lease_token'],{'source_digest':bundle['source_digest'],'oversized':'x'*17000},payload,event_key='atomic')
        self.assertEqual(self.conn.execute('SELECT count(*) FROM agent_jobs').fetchone()[0],1)
        self.assertEqual(self.conn.execute('SELECT state FROM agent_jobs').fetchone()[0],'running')
        with self.assertRaises(PermissionError):
            queue.finish_with_test(self.conn,job['id'],'wrong',{'source_digest':bundle['source_digest']},payload,event_key='atomic')
        child=queue.finish_with_test(self.conn,job['id'],job['lease_token'],{'source_digest':bundle['source_digest']},payload,event_key='atomic')
        saved=json.loads(self.conn.execute('SELECT result FROM agent_jobs WHERE id=?',(job['id'],)).fetchone()[0])
        self.assertEqual(saved['followup_job_id'],child)

    def test_tampered_capsule_is_blocked_before_sandbox_execution(self):
        job,child,bundle=self.stage()
        self.conn.execute('UPDATE developer_bundles SET source_digest=? WHERE job_id=?',('0'*64,job['id']));self.conn.commit()
        with patch.object(developer_pipeline.offline_developer,'prepare_files',side_effect=AssertionError('must not execute')):
            self.assertEqual(queue_worker.run_once(self.db)['state'],'failed')
        self.assertEqual(self.conn.execute('SELECT count(*) FROM code_artifacts').fetchone()[0],0)

    def test_failed_draft_tests_block_owner_ready_state(self):
        job,child,bundle=self.stage()
        original=developer_pipeline.test_bundle
        def failed(files,policy,**kwargs):
            return {'status':'failed','source_digest':manifest(files)[1],'elapsed_seconds':0.1,'backend':'fake-test-only','writable_tmp':False,'output':'FAIL'}
        with patch.object(developer_pipeline,'test_bundle',side_effect=lambda c,j,f:original(c,j,f,runner=failed)):
            result=queue_worker.run_once(self.db)
        self.assertEqual(result['state'],'failed')
        self.assertEqual(self.conn.execute('SELECT test_status FROM code_artifacts').fetchone()[0],'failed')
        self.assertEqual(self.conn.execute('SELECT kind FROM owner_notifications').fetchone()[0],'critical')

    def test_real_subprocess_filters_environment_and_does_not_load_pythonpath(self):
        job,request=self.job()
        attacker=self.root/'pythonpath';attacker.mkdir()
        marker=self.root/'startup-leak'
        (attacker/'sitecustomize.py').write_text(f'open({str(marker)!r},"w").write("bad")')
        original=broker_client.subprocess.Popen;seen=[]
        def launch(*args,**kwargs): seen.append(kwargs['env']);return original(*args,**kwargs)
        with patch.dict(os.environ,{'OPENAI_API_KEY':'test-parent-secret','TELEGRAM_BOT_TOKEN':'test-parent-token','PYTHONPATH':str(attacker)}),patch.object(broker_client.subprocess,'Popen',side_effect=launch):
            bundle=broker_client.request(self.db,job)
        self.assertEqual(bundle['engine'],'offline_broker_demo')
        self.assertFalse(marker.exists())
        self.assertEqual(set(seen[0]),{'HOME','PATH','LANG','PYTHONDONTWRITEBYTECODE'})

    def test_owner_commands_and_disabled_real_job_are_truthful(self):
        with patch.object(main,'DB',self.db):
            self.assertIn('выключена',main.command('/broker4'))
            self.assertIn('только',main.command('/develop inventory Измени код'))
            self.assertIn('сохранено',main.command('/develop control Create a component',source_key='test-command'))
        result=queue_worker.run_once(self.db)
        self.assertEqual(result['state'],'awaiting_owner')
        self.assertEqual(self.conn.execute('SELECT count(*) FROM provider_costs').fetchone()[0],0)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM developer_bundles').fetchone()[0],0)


@unittest.skipUnless(os.getenv('UAC_SANDBOX_TEST_BINARY'),'explicit sandbox integration binary required')
class RealDeveloperPipelineTests(unittest.TestCase):
    def test_real_broker_two_queue_jobs_sandbox_artifact_and_owner_notice(self):
        import shutil
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);db=root/'control.db'
            with queue_worker.connect(db) as conn:
                queue_worker.initialize(conn)
                ident=queue.enqueue(conn,'control','review_change',{'ai_task':broker.DEMO_TASK,'broker_demo':True},event_key='real-demo')
            db.chmod(0o600)
            policy=root/'broker-policy.json';policy.write_text(json.dumps(broker.DEFAULT_POLICY));policy.chmod(0o600)
            binary=Path(os.environ['UAC_SANDBOX_TEST_BINARY']).resolve()
            policy=root/'sandbox-policy.json';policy.write_text(json.dumps({'enabled':True,'backend':'bubblewrap-v1','binary':str(binary),'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest()}));policy.chmod(0o600)
            self.assertEqual(queue_worker.run_once(db)['state'],'succeeded')
            with queue_worker.connect(db) as conn:
                saved=json.loads(conn.execute('SELECT result FROM agent_jobs WHERE id=?',(ident,)).fetchone()[0])
                child=saved['followup_job_id']
                self.assertEqual(conn.execute('SELECT count(*) FROM code_artifacts').fetchone()[0],0)
                self.assertEqual(conn.execute('SELECT count(*) FROM owner_notifications').fetchone()[0],0)
            self.assertEqual(queue_worker.run_once(db),{'id':child,'state':'awaiting_owner'})
            with queue_worker.connect(db) as conn:
                row=conn.execute('SELECT engine,test_status,test_report,path FROM code_artifacts').fetchone()
                self.assertEqual(row[:2],('offline_broker_demo','passed'))
                report=json.loads(row[2]);self.assertIn('Ran 4 tests',report['output'])
                self.assertEqual(report['independent_acceptance']['status'],'passed')
                self.assertIn('Ran 7 tests',report['independent_acceptance']['output'])
                self.assertEqual(report['provenance']['generation_job_id'],ident)
                self.assertEqual(conn.execute('SELECT kind FROM owner_notifications').fetchone()[0],'decision')
                self.assertEqual(conn.execute('SELECT count(*) FROM provider_costs').fetchone()[0],0)
                self.assertEqual(conn.execute('SELECT count(*) FROM agent_work_spans').fetchone()[0],2)
                self.assertEqual((Path(row[3])/'draft_component.py').stat().st_mode & 0o777,0o600)
                self.assertIsNone(queue_worker.run_once(db))


if __name__=='__main__': unittest.main()
