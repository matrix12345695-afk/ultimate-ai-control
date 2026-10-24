import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import acceptance_checks
import evidence_memory as memory
import main
import project_registry
import queue_worker
import roadmap
import task_queue as q


class EvidenceMemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/'control.db'
        self.conn=sqlite3.connect(self.path)
        queue_worker.initialize(self.conn)

    def tearDown(self):
        self.conn.close();self.temp.cleanup()

    def finished(self,project='control',result=None,waiting=False):
        ident=q.enqueue(self.conn,project,'plan_change',{'text':'private task text'},now=100)
        job=q.claim(self.conn,'copy-worker',q.KINDS,now=101)
        self.assertEqual(ident,job['id'])
        q.finish(self.conn,ident,job['lease_token'],result or {'implemented':False},awaiting_owner=waiting,now=102)
        return ident

    def records(self):
        return self.conn.execute('SELECT * FROM project_evidence_memory ORDER BY id').fetchall()

    def test_restart_backfill_is_idempotent_scoped_and_does_not_copy_sensitive_details(self):
        job=self.finished(result={'secret':'sk-private-test-only','implemented':False},waiting=True)
        first=memory.sync(self.conn,1)
        self.assertEqual(first['scanned'],1);self.assertEqual(first['added'],0)
        while memory.sync(self.conn,1)['scanned']: pass
        before=self.records()
        queue_worker.initialize(self.conn)
        self.assertEqual(memory.sync(self.conn)['added'],0)
        self.assertEqual(before,self.records())
        stored=str(before)
        self.assertNotIn('private task text',stored);self.assertNotIn('sk-private',stored)
        self.assertIn(f'/job {job}',memory.summary(self.conn,'control'))
        self.assertIn('ожидает решения',memory.detail(self.conn,before[0][0]))
        self.assertIn('Сохранено наблюдений: 0',memory.summary(self.conn,'nova'))
        self.assertIn('Сохранено наблюдений: 0',memory.summary(self.conn,'inventory'))

    def test_failed_retry_and_expired_lease_are_not_success_or_unmeasured_work(self):
        ident=q.enqueue(self.conn,'control','review_change',{},now=100,max_attempts=2)
        job=q.claim(self.conn,'copy',q.KINDS,now=101,lease_seconds=5)
        q.fail(self.conn,ident,job['lease_token'],'SECRET error detail',now=102)
        job=q.claim(self.conn,'copy',q.KINDS,now=162,lease_seconds=5)
        q.claim(self.conn,'next',q.KINDS,now=168)
        memory.sync(self.conn)
        text=memory.summary(self.conn,'control')
        self.assertIn('назначен повтор',text);self.assertIn('истекла аренда',text)
        self.assertNotIn('задание завершено',text);self.assertNotIn('SECRET',str(self.records()))

    def test_transaction_failure_rolls_back_entries_and_cursor_and_leaves_business_rules(self):
        self.finished()
        context=self.conn.execute('SELECT * FROM project_memory ORDER BY project').fetchall()
        cursor=self.conn.execute('SELECT * FROM project_evidence_cursor').fetchall()
        with patch.object(memory,'evidence',side_effect=RuntimeError('injected crash')):
            with self.assertRaises(RuntimeError): memory.sync(self.conn)
        self.assertEqual(self.records(),[])
        self.assertEqual(cursor,self.conn.execute('SELECT * FROM project_evidence_cursor').fetchall())
        self.assertEqual(memory.sync(self.conn)['added'],1)
        self.assertEqual(context,self.conn.execute('SELECT * FROM project_memory ORDER BY project').fetchall())
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute('DELETE FROM project_evidence_memory')
        self.conn.rollback()
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("UPDATE project_evidence_memory SET fact='{}'")
        self.conn.rollback()

    def test_changed_or_missing_sources_invalidate_observation_without_rewriting_history(self):
        job=self.finished();memory.sync(self.conn)
        original=self.records()
        event=self.conn.execute("SELECT id FROM agent_job_events WHERE event='succeeded'").fetchone()[0]
        self.conn.execute('UPDATE agent_job_events SET detail=? WHERE id=?',('changed',event));self.conn.commit()
        self.assertIn('источник изменён',memory.summary(self.conn,'control'))
        self.assertIn('повторной проверки',memory.detail(self.conn,original[0][0]))
        self.assertEqual(original,self.records())
        self.conn.execute('DELETE FROM agent_jobs WHERE id=?',(job,));self.conn.commit()
        self.assertIn('источник изменён',memory.summary(self.conn,'control'))

    def test_cancelled_later_job_preserves_historical_fact_but_shows_current_state(self):
        job=self.finished(waiting=True);memory.sync(self.conn)
        ident=self.records()[0][0]
        q.cancel(self.conn,job,now=103);memory.sync(self.conn)
        detail=memory.detail(self.conn,ident)
        self.assertIn('Историческое наблюдение: ожидает решения',detail)
        self.assertIn('Текущее состояние задачи: cancelled',detail)
        self.assertEqual(len(self.records()),2)

    def test_pagination_commands_are_read_only_and_incomplete_catchup_is_visible(self):
        for _ in range(7): self.finished()
        memory.sync(self.conn,10)
        self.assertIn('/21',memory.summary(self.conn,'control'))
        while memory.sync(self.conn)['scanned']: pass
        before=self.conn.total_changes
        with patch.object(main,'DB',self.path):
            first=main.command('/memory_log control')
            second=main.command('/memory_log control 2')
            self.assertIn('1/2',first);self.assertIn('2/2',second)
            self.assertIn('/memory_log control',main.command('/memory control'))
            self.assertIn('Память проекта не найдена',main.command('/memory_log unknown'))
            self.assertIn('Отклонено',main.command('/memory_log control 2 extra'))
            self.assertIn('Отклонено',main.command('/memory_item 01'))
            self.assertIn('1/2',main.command('🧾 История проектов'))
        self.conn.execute("UPDATE uac_settings SET value='nova' WHERE key='active_project'")
        memory.summary(self.conn,'control')
        self.assertEqual(self.conn.total_changes,before+1)
        self.assertTrue(self.conn.in_transaction)
        self.conn.rollback()
        with self.assertRaises(ValueError): memory.sync(self.conn,0)

    def test_worker_catches_up_even_when_paused_without_rerunning_task(self):
        job=self.finished()
        q.configure(self.conn,paused=True)
        with patch.object(queue_worker,'inspect_source',side_effect=AssertionError('must not execute')):
            self.assertIsNone(queue_worker.run_once(self.path))
        self.assertEqual(len(self.records()),1)
        self.assertEqual(self.conn.execute('SELECT attempts FROM agent_jobs WHERE id=?',(job,)).fetchone()[0],1)

    def test_artifact_hash_test_profile_and_job_identity_are_bound(self):
        job=q.enqueue(self.conn,'control','review_change',{'recipe':'safe-paths'},now=100)
        claimed=q.claim(self.conn,'copy',q.KINDS,now=101)
        profile='review-path-v1';source='b'*64
        report={'source_digest':source,'status':'passed','output':'sensitive output',
                'independent_acceptance':{'profile':profile,'status':'passed','candidate_source_digest':source,
                                          'harness_sha256':acceptance_checks.harness_sha256(profile)}}
        artifact=self.conn.execute('''INSERT INTO code_artifacts(job_id,attempt,project,engine,source_digest,
            manifest,test_status,test_report,path,created_at) VALUES(?,1,'control','deterministic_recipe',?,
            '[]','passed',?,'not-opened',102)''',(job,source,json.dumps(report))).lastrowid
        self.conn.commit()
        q.finish(self.conn,job,claimed['lease_token'],dict(artifact_id=artifact,source_digest=source,test_status='passed'),awaiting_owner=True,now=103)
        memory.sync(self.conn)
        ident=self.records()[0][0];detail=memory.detail(self.conn,ident)
        self.assertIn(profile,detail);self.assertIn(source,detail)
        self.assertNotIn('sensitive output',str(self.records()))
        self.assertIn('публикация не подтверждена',memory.summary(self.conn,'control'))
        self.conn.execute("UPDATE code_artifacts SET test_status='failed' WHERE id=?",(artifact,));self.conn.commit()
        self.assertIn('повторной проверки',memory.detail(self.conn,ident))

    def test_cross_project_artifact_cannot_be_promoted_and_protected_jobs_are_excluded(self):
        first=self.finished()
        self.conn.execute("UPDATE agent_jobs SET project='inventory' WHERE id=?",(first,));self.conn.commit()
        memory.sync(self.conn)
        self.assertEqual(self.records(),[])
        second=self.finished()
        self.conn.execute("UPDATE agent_jobs SET kind='review_change',result=? WHERE id=?",
                          (json.dumps(dict(artifact_id=999,source_digest='a'*64,test_status='passed')),second));self.conn.commit()
        memory.sync(self.conn)
        self.assertNotIn('artifact',str(self.records()))

    def test_repository_observation_does_not_claim_test_execution_or_publication(self):
        scope=project_registry.REPOSITORIES['kinder']
        files=[{'path':path,'bytes':size,'git_blob':blob,'sha256':'a'*64} for path,size,blob in scope['files']]
        result=dict(method=project_registry.METHOD,project='kinder',repository=project_registry.OWNER+'/'+scope['repository'],
                    repository_id=scope['repository_id'],revision=scope['revision'],files=files,
                    source_digest=project_registry._digest(files),code_executed=False,tests_executed=False,published=False,complete_project_audit=False)
        ident=q.enqueue(self.conn,'kinder','inspect_repository',{'target':'kinder','source':project_registry.METHOD},now=100)
        job=q.claim(self.conn,'copy',q.KINDS,now=101)
        q.finish(self.conn,ident,job['lease_token'],result,now=102)
        memory.sync(self.conn)
        self.assertIn('код и тесты не запускались',memory.summary(self.conn,'kinder'))
        self.assertIn(scope['revision'],memory.detail(self.conn,self.records()[0][0]))
        self.assertNotIn('repository',memory.summary(self.conn,'control'))
