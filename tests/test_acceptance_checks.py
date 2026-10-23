import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
from unittest.mock import patch
import acceptance_checks as acceptance
from isolated_python import manifest,run_bundle
import model_broker as broker
import offline_developer
import developer_pipeline
import queue_worker
import task_queue as queue


def report(files,status='passed'):
    return dict(status=status,source_digest=manifest(files)[1],elapsed_seconds=0.01,
                backend='fake-test-only',writable_tmp=False,output='artificial runner fixture')


class AcceptanceChecksTests(unittest.TestCase):
    def test_candidate_tests_and_shadow_modules_never_enter_acceptance_bundle(self):
        files=dict(broker.DEMO_FILES)
        files['unittest.py']='raise RuntimeError("candidate shadow module")'
        files['tests/test_owner_acceptance.py']='raise RuntimeError("candidate tests")'
        calls=[]
        def runner(bundle,policy,**kwargs): calls.append((bundle,kwargs));return report(bundle)
        result=acceptance.check(files,'unused',acceptance.PROFILE,runner=runner)
        self.assertEqual(result['status'],'passed')
        self.assertEqual(set(calls[0][0]),{'draft_component.py','tests/test_owner_acceptance.py'})
        self.assertEqual(calls[0][0]['tests/test_owner_acceptance.py'],acceptance.TESTS)
        self.assertEqual(calls[0][1],{'timeout':8})
        self.assertEqual(result['candidate_source_digest'],manifest(files)[1])
        self.assertEqual(result['harness_sha256'],hashlib.sha256(acceptance.TESTS.encode()).hexdigest())

    def test_side_effects_imports_decorators_recursion_and_unknown_profiles_never_run(self):
        bad=['import os\ndef bounded_percent(done,total): return 0',
             '@type\ndef bounded_percent(done,total): return 0',
             'def bounded_percent(done,total): return bounded_percent(done,total)',
             'def bounded_percent(done,total):\n type.__class__=int\n return 0',
             'def bounded_percent(done,total=0): return 0',
             'def bounded_percent(done,total): return __import__("os")',
             'def bounded_percent(done,total):\n while True: pass']
        runner=Mock(side_effect=AssertionError('unreviewed code must not run'))
        for source in bad:
            result=acceptance.check(dict(broker.DEMO_FILES,**{'draft_component.py':source}),'unused',acceptance.PROFILE,runner=runner)
            self.assertEqual(result['status'],'failed')
        with self.assertRaises(ValueError): acceptance.check(broker.DEMO_FILES,'unused','other-profile',runner=runner)
        runner.assert_not_called()

    def test_acceptance_report_must_match_its_exact_source_and_harness(self):
        def wrong(files,policy,**kwargs): return dict(report(files),source_digest='0'*64)
        with self.assertRaisesRegex(ValueError,'digest_mismatch'):
            acceptance.check(broker.DEMO_FILES,'unused',acceptance.PROFILE,runner=wrong)

    def test_failed_or_timed_out_acceptance_blocks_passed_artifact_and_replay_is_bound(self):
        for status in ('failed','timeout'):
            with tempfile.TemporaryDirectory() as name:
                root=Path(name)
                with queue_worker.connect(root/'control.db') as conn:
                    queue_worker.initialize(conn)
                    job=dict(id=1,attempt=1,project='control')
                    calls=[]
                    def runner(files,policy,**kwargs):
                        calls.append(files)
                        return report(files,'passed' if len(calls)==1 else status)
                    result=offline_developer.prepare_files(conn,job,root/'artifacts',root/'policy',broker.DEMO_FILES,
                        engine='offline_broker_demo',runner=runner,acceptance_profile=acceptance.PROFILE)
                    self.assertEqual(result['test_status'],'failed')
                    saved=json.loads(conn.execute('SELECT test_report FROM code_artifacts').fetchone()[0])
                    self.assertEqual(saved['candidate_test_status'],'passed')
                    self.assertEqual(saved['independent_acceptance']['status'],status)
                    replay=offline_developer.prepare_files(conn,job,root/'artifacts',root/'policy',broker.DEMO_FILES,
                        engine='offline_broker_demo',runner=Mock(side_effect=AssertionError()),acceptance_profile=acceptance.PROFILE)
                    self.assertEqual(replay['test_status'],'failed')
                    with self.assertRaisesRegex(ValueError,'contract changed'):
                        offline_developer.prepare_files(conn,job,root/'artifacts',root/'policy',broker.DEMO_FILES,engine='offline_broker_demo')
                    saved['independent_acceptance']['harness_sha256']='0'*64
                    conn.execute('UPDATE code_artifacts SET test_report=?',(json.dumps(saved),));conn.commit()
                    with self.assertRaisesRegex(ValueError,'harness changed'):
                        offline_developer.prepare_files(conn,job,root/'artifacts',root/'policy',broker.DEMO_FILES,
                            engine='offline_broker_demo',acceptance_profile=acceptance.PROFILE)

    def test_general_model_bundle_never_infers_demo_contract(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name)
            with queue_worker.connect(root/'control.db') as conn:
                queue_worker.initialize(conn);job=dict(id=1,attempt=1,project='control')
                result=offline_developer.prepare_files(conn,job,root/'artifacts',root/'policy',broker.DEMO_FILES,engine='openai_broker',runner=lambda f,p:report(f))
                self.assertEqual(result['independent_acceptance'],'not_configured')
                with self.assertRaises(ValueError):
                    offline_developer.prepare_files(conn,job,root/'artifacts',root/'policy',broker.DEMO_FILES,engine='openai_broker',acceptance_profile=acceptance.PROFILE)

    def test_worker_marks_failed_acceptance_as_failed_and_not_owner_ready(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);db=root/'control.db'
            policy=root/'broker-policy.json';policy.write_text(json.dumps(broker.DEFAULT_POLICY));policy.chmod(0o600)
            with queue_worker.connect(db) as conn:
                queue_worker.initialize(conn)
                parent=queue.enqueue(conn,'control','review_change',dict(ai_task=broker.DEMO_TASK,broker_demo=True))
                job=queue.claim(conn,'operations-1',queue.KINDS,lease_seconds=60)
                bundle=broker.process(conn,root,dict(protocol=broker.PROTOCOL,job_id=parent,lease_token=job['lease_token']))
                child=queue.finish_with_test(conn,parent,job['lease_token'],dict(source_digest=bundle['source_digest']),
                    dict(target='developer-bundle',generation_job_id=parent,source_digest=bundle['source_digest']),event_key='acceptance-test')
            original=developer_pipeline.test_bundle;calls=[]
            def runner(files,policy,**kwargs):
                calls.append(1);return report(files,'passed' if len(calls)==1 else 'failed')
            with patch.object(developer_pipeline,'test_bundle',side_effect=lambda c,j,f:original(c,j,f,runner=runner)):
                self.assertEqual(queue_worker.run_once(db),dict(id=child,state='failed'))
            with queue_worker.connect(db) as conn:
                self.assertEqual(conn.execute('SELECT kind FROM owner_notifications').fetchone()[0],'critical')
                self.assertEqual(conn.execute('SELECT test_status FROM code_artifacts').fetchone()[0],'failed')
                self.assertEqual(conn.execute('SELECT count(*) FROM provider_costs').fetchone()[0],0)


@unittest.skipUnless(os.getenv('UAC_SANDBOX_TEST_BINARY'),'explicit sandbox integration binary required')
class RealAcceptanceTests(unittest.TestCase):
    def test_real_acceptance_passes_correct_code_and_rejects_lying_tests_and_mutants(self):
        with tempfile.TemporaryDirectory() as name:
            binary=Path(os.environ['UAC_SANDBOX_TEST_BINARY']).resolve()
            policy=Path(name)/'policy.json';policy.write_text(json.dumps(dict(enabled=True,backend='bubblewrap-v1',binary=str(binary),binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest())));policy.chmod(0o600)
            correct=acceptance.check(broker.DEMO_FILES,policy,acceptance.PROFILE)
            self.assertEqual(correct['status'],'passed',correct.get('output'))
            self.assertIn('Ran 7 tests',correct['output'])
            original=broker.DEMO_FILES['draft_component.py']
            mutants=['def bounded_percent(done,total): return 0\n',
                     original.replace('return min(100, (done * 100) // total)','return (done * 100) // total'),
                     original.replace('(done * 100) // total','((done * 100) + total - 1) // total')]
            lying_tests='''import unittest
unittest.TestCase.assertEqual=lambda *args,**kwargs: None
class LyingTests(unittest.TestCase):
    def test_false_positive(self): self.assertEqual(1,999)
'''
            for source in mutants:
                files={'draft_component.py':source,'tests/test_candidate.py':lying_tests}
                self.assertEqual(run_bundle(files,policy,timeout=8)['status'],'passed')
                independent=acceptance.check(files,policy,acceptance.PROFILE)
                self.assertEqual(independent['status'],'failed',independent.get('output'))
                self.assertIn('FAILED',independent['output'])

