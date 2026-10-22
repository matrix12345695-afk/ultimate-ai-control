import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import isolated_python as sandbox
import offline_developer
import queue_worker
from sandbox_smoke import FILES as SMOKE


class BundlePolicyTests(unittest.TestCase):
    def test_reject_traversal_nonpython_secrets_and_oversized_bundle(self):
        for path in ('../escape.py','/tmp/escape.py','tests//x.py','tests/../x.py','.env','tests/test_a.txt'):
            with self.assertRaises(ValueError): sandbox.validate_files({path:'x','tests/test_ok.py':'x'})
        with self.assertRaises(ValueError): sandbox.validate_files({'source.py':'x'})
        with self.assertRaises(ValueError): sandbox.validate_files({'tests/test_big.py':'x'*(sandbox.MAX_BUNDLE_BYTES+1)})

    def test_manifest_is_stable_and_changes_with_source(self):
        one={'tests/test_a.py':'a=1\n','proposals/a.py':'x=2\n'}
        self.assertEqual(sandbox.manifest(one),sandbox.manifest(dict(reversed(list(one.items())))))
        self.assertNotEqual(sandbox.manifest(one)[1],sandbox.manifest({**one,'proposals/a.py':'x=3\n'})[1])

    def test_policy_refuses_world_readable_and_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as name:
            p=Path(name)/'policy.json'
            p.write_text('{}'); p.chmod(0o644)
            with self.assertRaises(sandbox.SandboxUnavailable): sandbox.load_policy(p)
            p.write_text(json.dumps({'enabled':True,'backend':'bubblewrap-v1','binary':'/usr/bin/true','binary_sha256':'bad'})); p.chmod(0o600)
            with self.assertRaises(sandbox.SandboxUnavailable): sandbox.load_policy(p)

    def test_no_unsafe_host_execution_fallback(self):
        with tempfile.TemporaryDirectory() as name:
            with patch.object(sandbox.subprocess,'Popen') as popen:
                with self.assertRaises(FileNotFoundError): sandbox.run_bundle({'tests/test_a.py':'x=1'},Path(name)/'missing')
                popen.assert_not_called()

    def test_offline_artifact_keeps_exact_tested_digest_and_private_files(self):
        with tempfile.TemporaryDirectory() as name:
            conn=sqlite3.connect(':memory:')
            offline_developer.initialize(conn)
            job={'id':1,'attempt':1,'project':'control','payload':{'recipe':'safe-paths'}}
            def runner(files,policy):
                return {'status':'passed','source_digest':sandbox.manifest(files)[1],
                        'elapsed_seconds':0.1,'backend':'bubblewrap-v1','writable_tmp':False,'output':'Ran 3 tests: OK'}
            result=offline_developer.prepare(conn,job,Path(name)/'artifacts','unused',runner=runner)
            self.assertTrue(result['code_draft_created'])
            self.assertFalse(result['published'])
            self.assertEqual(result['engine'],'deterministic_recipe')
            path=Path(conn.execute('SELECT path FROM code_artifacts').fetchone()[0])
            self.assertEqual((path/'test-report.json').stat().st_mode & 0o777,0o600)
            self.assertIn('safe_paths',offline_developer.describe(conn,result['artifact_id']))
            self.assertIn('def safe_review_path',offline_developer.source_preview(conn,result['artifact_id'],1))
            again=offline_developer.prepare(conn,job,Path(name)/'artifacts','unused',runner=lambda *a:self.fail('duplicate execution'))
            self.assertEqual(result['artifact_id'],again['artifact_id'])
            conn.close()

    def test_unrelated_project_or_mismatched_test_digest_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            conn=sqlite3.connect(':memory:')
            offline_developer.initialize(conn)
            job={'id':1,'attempt':1,'project':'inventory','payload':{'recipe':'safe-paths'}}
            with self.assertRaises(PermissionError): offline_developer.prepare(conn,job,name,'unused')
            job['project']='control'
            with self.assertRaises(ValueError): offline_developer.prepare(conn,job,name,'unused',runner=lambda *a:{'source_digest':'bad'})
            conn.close()

    def test_real_test_failure_marks_job_failed_not_success(self):
        import task_queue
        with tempfile.TemporaryDirectory() as name:
            path=Path(name)/'control.db'
            with queue_worker.connect(path) as conn:
                queue_worker.initialize(conn)
                ident=task_queue.enqueue(conn,'control','test_release',{'target':'sandbox-smoke'})
            report={'status':'failed','backend':'fake-test-backend','elapsed_seconds':0.1,'source_digest':'x','output':'failed','writable_tmp':False}
            with patch.object(queue_worker,'run_bundle',return_value=report):
                self.assertEqual(queue_worker.run_once(path)['state'],'failed')
            with queue_worker.connect(path) as conn:
                self.assertEqual(conn.execute('SELECT state FROM agent_jobs WHERE id=?',(ident,)).fetchone()[0],'failed')
                self.assertEqual(conn.execute('SELECT kind FROM owner_notifications').fetchone()[0],'critical')

    def test_exhausted_job_notifies_and_records_failed_work(self):
        import task_queue
        with tempfile.TemporaryDirectory() as name:
            path=Path(name)/'control.db'
            with queue_worker.connect(path) as conn:
                queue_worker.initialize(conn)
                ident=task_queue.enqueue(conn,'control','inspect_repository',{'target':'not-enabled'},max_attempts=1)
            result=queue_worker.run_once(path)
            self.assertEqual(result['state'],'failed')
            with queue_worker.connect(path) as conn:
                self.assertEqual(conn.execute('SELECT count(*) FROM agent_work_spans WHERE job_id=?',(ident,)).fetchone()[0],1)
                self.assertEqual(conn.execute('SELECT kind,title FROM owner_notifications').fetchone(),('critical','Задача исчерпала попытки'))


@unittest.skipUnless(os.getenv('UAC_SANDBOX_TEST_BINARY'),'explicit sandbox integration binary required')
class RealSandboxTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/'policy.json'
        binary=Path(os.environ['UAC_SANDBOX_TEST_BINARY']).resolve()
        self.path.write_text(json.dumps({'enabled':True,'backend':'bubblewrap-v1','binary':str(binary),'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest()}))
        self.path.chmod(0o600)

    def tearDown(self): self.temp.cleanup()

    def run_code(self,source,timeout=10):
        return sandbox.run_bundle({'tests/test_probe.py':source},self.path,timeout=timeout)

    def test_network_host_files_processes_affinity_and_capabilities(self):
        report=sandbox.run_bundle(SMOKE,self.path)
        self.assertEqual(report['status'],'passed',report['output'])

    def test_host_environment_and_canary_do_not_enter(self):
        canary=Path(self.temp.name)/'private-canary'
        canary.write_text('never-export-this')
        code=f'import os,pathlib,unittest\nclass T(unittest.TestCase):\n def test_x(self):\n  self.assertFalse(pathlib.Path({str(canary)!r}).exists())\n  self.assertNotIn("UAC_PRIVATE_CANARY",os.environ)\n'
        with patch.dict(os.environ,{'UAC_PRIVATE_CANARY':'never-export-this'}): report=self.run_code(code)
        self.assertEqual(report['status'],'passed',report['output'])

    def test_memory_bounded_and_threads_denied(self):
        code='''import unittest, threading
class T(unittest.TestCase):
 def test_memory(self):
  with self.assertRaises(MemoryError): bytearray(1024**3)
 def test_threads(self):
  with self.assertRaises(RuntimeError): threading.Thread(target=lambda: None).start()
'''
        report=self.run_code(code)
        self.assertEqual(report['status'],'passed',report['output'])

    def test_sandbox_files_readonly_on_older_backend(self):
        cfg=sandbox.load_policy(self.path)
        if cfg['writable_tmp']: self.skipTest('new backend supports size-limited scratch')
        report=self.run_code('import pathlib,unittest\nclass T(unittest.TestCase):\n def test_write(self):\n  with self.assertRaises(OSError): pathlib.Path("/tmp/forbidden").write_text("x")\n')
        self.assertEqual(report['status'],'passed',report['output'])

    def test_timeout_kills_sandbox(self):
        report=self.run_code('while True: pass\n',timeout=1)
        self.assertEqual(report['status'],'timeout')
        self.assertLess(report['elapsed_seconds'],4)

    def test_output_is_bounded(self):
        report=self.run_code('while True: print("x"*10000,flush=True)\n')
        self.assertEqual(report['status'],'output_limit')
        self.assertLessEqual(len(report['output'].encode()),sandbox.MAX_OUTPUT)

    def test_actual_generated_recipe_passes_in_isolation(self):
        report=sandbox.run_bundle(offline_developer.recipe_files('safe-paths',7),self.path)
        self.assertEqual(report['status'],'passed',report['output'])
        self.assertIn('Ran 3 tests',report['output'])


if __name__=='__main__': unittest.main()
