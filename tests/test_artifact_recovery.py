import json
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch
import artifact_recovery
import offline_developer
import queue_worker
import roadmap
import task_queue as queue
from isolated_python import manifest
from isolated_python import run_bundle


class CrashBeforeArtifactInsert:
    def __init__(self,conn): self.conn=conn
    def execute(self,sql,*args):
        if sql.startswith('INSERT INTO code_artifacts'): raise OSError('artificial crash after durable rename')
        return self.conn.execute(sql,*args)
    def commit(self): return self.conn.commit()


class ArtifactRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.db=self.root/'control.db'
        self.conn=queue_worker.connect(self.db);queue_worker.initialize(self.conn)
        self.job=dict(id=1,attempt=1,project='control',payload=dict(recipe='safe-paths'))
        self.calls=0
    def tearDown(self): self.conn.close();self.temp.cleanup()
    def runner(self,files,policy):
        self.calls+=1
        return dict(status='passed',source_digest=manifest(files)[1],elapsed_seconds=0.1,backend='fake-test-only',writable_tmp=False,output='artificial test fixture')
    def prepare(self,conn=None,job=None,runner=None):
        return offline_developer.prepare(conn or self.conn,job or self.job,self.root/'artifacts','unused',runner=runner or self.runner)
    def published_orphan(self):
        with self.assertRaises(OSError): self.prepare(conn=CrashBeforeArtifactInsert(self.conn))
        self.assertEqual(self.conn.execute('SELECT count(*) FROM code_artifacts').fetchone()[0],0)
        return next((self.root/'artifacts').glob('job-1-attempt-*'))

    def test_crash_after_rename_recovers_same_attempt_then_later_attempt_without_tests(self):
        path=self.published_orphan()
        recovered=self.prepare(runner=Mock(side_effect=AssertionError('tests must not run again')))
        later=self.prepare(job=dict(self.job,attempt=2),runner=Mock(side_effect=AssertionError('tests must not repeat on a new lease')))
        self.assertEqual(recovered['artifact_id'],later['artifact_id'])
        self.assertTrue(later['tests_reused']);self.assertEqual(later['recovered_from_attempt'],1)
        self.assertEqual(self.calls,1)
        self.assertEqual(self.conn.execute('SELECT attempt,path FROM code_artifacts').fetchone(),(1,str(path)))
        self.assertEqual(len(list((self.root/'artifacts').glob('job-*'))),1)

    def test_registered_artifact_is_reused_on_new_attempt_with_original_outcome(self):
        first=self.prepare()
        result=self.prepare(job=dict(self.job,attempt=3),runner=Mock(side_effect=AssertionError()))
        self.assertEqual(result['artifact_id'],first['artifact_id'])
        self.assertEqual(result['test_status'],'passed');self.assertEqual(self.calls,1)

    def test_failed_outcome_remains_failed_on_recovery(self):
        def failed(files,policy): return dict(self.runner(files,policy),status='failed')
        first=self.prepare(runner=failed)
        later=self.prepare(job=dict(self.job,attempt=2),runner=Mock(side_effect=AssertionError()))
        self.assertEqual(first['artifact_id'],later['artifact_id'])
        self.assertEqual(later['test_status'],'failed');self.assertEqual(self.calls,1)

    def test_corrupt_or_missing_orphan_source_never_reruns_tests_or_registers_artifact(self):
        path=self.published_orphan();source=next(path.glob('proposals/*.py'));original=source.read_bytes()
        for change in ('corrupt','missing','public','symlink'):
            if source.is_symlink(): source.unlink()
            source.write_bytes(original);source.chmod(0o600)
            if change=='corrupt': source.write_text('different source')
            elif change=='missing': source.unlink()
            elif change=='public': source.chmod(0o644)
            else:
                outside=self.root/'outside.py';outside.write_bytes(original);outside.chmod(0o600)
                source.unlink();source.symlink_to(outside)
            with self.assertRaises(artifact_recovery.ArtifactRecoveryBlocked):
                self.prepare(job=dict(self.job,attempt=2),runner=Mock(side_effect=AssertionError()))
            if source.exists() or source.is_symlink(): source.unlink()
            self.assertEqual(self.conn.execute('SELECT count(*) FROM code_artifacts').fetchone()[0],0)
        self.assertEqual(self.calls,1)

    def test_foreign_or_missing_identity_and_bad_manifest_refuse_orphan_adoption(self):
        path=self.published_orphan();report=path/'test-report.json';original=json.loads(report.read_text())
        for identity in (None,dict(original['artifact_identity'],job_id=999),dict(original['artifact_identity'],engine='openai_broker')):
            changed=dict(original)
            if identity is None: changed.pop('artifact_identity')
            else: changed['artifact_identity']=identity
            report.write_text(json.dumps(changed))
            with self.assertRaises(artifact_recovery.ArtifactRecoveryBlocked): self.prepare()
        for field in ('backend','output','elapsed_seconds','writable_tmp'):
            changed=dict(original);changed.pop(field);report.write_text(json.dumps(changed))
            with self.assertRaises(artifact_recovery.ArtifactRecoveryBlocked): self.prepare()
            self.assertEqual(self.conn.execute('SELECT count(*) FROM code_artifacts').fetchone()[0],0)
        report.write_text(json.dumps(original));(path/'manifest.json').write_text('[]')
        with self.assertRaisesRegex(artifact_recovery.ArtifactRecoveryBlocked,'manifest changed'): self.prepare()
        self.assertEqual(self.calls,1)

    def test_db_disk_disagreement_and_changed_source_or_engine_do_not_reexecute(self):
        self.prepare()
        self.conn.execute("UPDATE code_artifacts SET test_status='failed'");self.conn.commit()
        with self.assertRaisesRegex(artifact_recovery.ArtifactRecoveryBlocked,'disagree'): self.prepare()
        self.conn.execute("UPDATE code_artifacts SET test_status='passed'");self.conn.commit()
        changed=dict(self.job,payload=dict(recipe='sha-check'))
        with self.assertRaisesRegex(artifact_recovery.ArtifactRecoveryBlocked,'source changed'): self.prepare(job=changed)
        self.assertEqual(self.calls,1)

    def test_unknown_or_future_attempt_directory_is_preserved_and_refused(self):
        root=self.root/'artifacts';root.mkdir(mode=0o700)
        for name in ('job-1-attempt-99','job-1-attempt-4'):
            target=root/name;target.mkdir(mode=0o700)
            with self.assertRaises(artifact_recovery.ArtifactRecoveryBlocked): self.prepare()
            self.assertTrue(target.is_dir());target.rmdir()
        self.assertEqual(self.calls,0)

    def test_worker_recovers_artifact_after_crash_before_queue_completion(self):
        ident=queue.enqueue(self.conn,'control','review_change',dict(recipe='safe-paths'))
        original=offline_developer.prepare
        def prepare(conn,job,*args): return original(conn,job,*args,runner=self.runner)
        with patch.object(offline_developer,'prepare',side_effect=prepare),patch.object(queue,'finish',side_effect=SystemExit('artificial worker exit')):
            with self.assertRaises(SystemExit): queue_worker.run_once(self.db)
        self.assertEqual(self.conn.execute('SELECT state FROM agent_jobs WHERE id=?',(ident,)).fetchone()[0],'running')
        self.conn.execute('UPDATE agent_jobs SET lease_until=0 WHERE id=?',(ident,));self.conn.commit()
        with patch.object(offline_developer,'prepare',side_effect=prepare):
            self.assertEqual(queue_worker.run_once(self.db),dict(id=ident,state='awaiting_owner'))
        result=json.loads(self.conn.execute('SELECT result FROM agent_jobs WHERE id=?',(ident,)).fetchone()[0])
        self.assertTrue(result['tests_reused']);self.assertEqual(self.calls,1)
        self.assertEqual(self.conn.execute('SELECT attempts FROM agent_jobs WHERE id=?',(ident,)).fetchone()[0],2)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM code_artifacts').fetchone()[0],1)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM owner_notifications').fetchone()[0],1)

    def test_owner_deferred_provider_does_not_create_another_key_request(self):
        roadmap.set_setting(self.conn,'provider_setup_deferred','true')
        queue.enqueue(self.conn,'control','plan_change',dict(text='Prepare the next feature'))
        self.assertEqual(queue_worker.run_once(self.db)['state'],'awaiting_owner')
        self.assertEqual(self.conn.execute('SELECT count(*) FROM owner_notifications').fetchone()[0],0)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM provider_costs').fetchone()[0],0)

    def test_expired_last_attempt_is_failed_and_notifies_once_without_retrying(self):
        ident=queue.enqueue(self.conn,'control','review_change',dict(recipe='safe-paths'),max_attempts=1)
        queue.claim(self.conn,'operations-1',queue.KINDS,lease_seconds=60)
        self.conn.execute('UPDATE agent_jobs SET lease_until=0 WHERE id=?',(ident,));self.conn.commit()
        for _ in range(2): self.assertIsNone(queue_worker.run_once(self.db))
        self.assertEqual(self.conn.execute('SELECT state,attempts FROM agent_jobs WHERE id=?',(ident,)).fetchone(),('failed',1))
        self.assertEqual(self.conn.execute('SELECT kind,count(*) FROM owner_notifications').fetchone(),('critical',1))


@unittest.skipUnless(os.getenv('UAC_SANDBOX_TEST_BINARY'),'explicit sandbox integration binary required')
class RealArtifactRecoveryTests(unittest.TestCase):
    def test_real_sandbox_report_recovers_after_rename_without_repeating_tests(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);binary=Path(os.environ['UAC_SANDBOX_TEST_BINARY']).resolve()
            policy=root/'policy.json';policy.write_text(json.dumps(dict(enabled=True,backend='bubblewrap-v1',binary=str(binary),binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest())));policy.chmod(0o600)
            with queue_worker.connect(root/'control.db') as conn:
                queue_worker.initialize(conn)
                job=dict(id=1,attempt=1,project='control',payload=dict(recipe='safe-paths'))
                with self.assertRaises(OSError):
                    offline_developer.prepare(CrashBeforeArtifactInsert(conn),job,root/'artifacts',policy,runner=run_bundle)
                recovered=offline_developer.prepare(conn,dict(job,attempt=2),root/'artifacts',policy,runner=Mock(side_effect=AssertionError('sandbox must not repeat')))
                self.assertTrue(recovered['tests_reused']);self.assertEqual(recovered['backend'],'bubblewrap-v1')
                self.assertEqual(recovered['test_status'],'passed')
                report=json.loads(conn.execute('SELECT test_report FROM code_artifacts').fetchone()[0])
                self.assertIn('Ran 3 tests',report['output'])

