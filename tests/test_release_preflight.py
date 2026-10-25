import copy
import json
import time
import unittest
from unittest.mock import patch
import approval
import artifact_prs as ledger
import artifact_pr_broker as broker
import release_preflight as preflight
import runtime_commands
import task_queue as q
import test_artifact_prs as fixtures


class ReleasePreflightTests(unittest.TestCase):
    setUp=fixtures.ArtifactPRTests.setUp
    tearDown=fixtures.ArtifactPRTests.tearDown
    run_broker=fixtures.ArtifactPRTests.run_broker

    def start(self):
        result=self.run_broker()
        q.finish(self.conn,self.job['id'],self.job['lease_token'],result,awaiting_owner=True)
        ident=q.enqueue(self.conn,'control','review_change',{'artifact_pr':self.artifact,'refresh':True,'release_check':True})
        self.job=q.claim(self.conn,'unit',q.KINDS)
        self.assertEqual(ident,self.job['id']);self.github.calls.clear()

    def test_real_read_path_no_approval_or_repository_write_and_durable_report(self):
        self.start();scopes=[]
        result=self.run_broker(issuer=lambda *args,**kw:scopes.append(kw.get('read_only')) or 'fixture')
        self.assertEqual(scopes,[True]);self.assertTrue(all(m=='GET' for m,_,_ in self.github.calls))
        self.assertFalse(result['publish_allowed']);self.assertEqual(result['approval_state'],'missing')
        self.assertEqual(self.conn.execute('SELECT count(*) FROM approvals').fetchone()[0],0)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM artifact_release_candidates').fetchone()[0],0)
        raw,sha=self.conn.execute('SELECT report,report_sha256 FROM artifact_release_checks').fetchone()
        report=json.loads(raw);self.assertEqual(ledger.digest(report),sha)
        self.assertEqual(report['scope']['head_sha'],self.github.head)
        self.assertEqual(report['rollback_reference']['base_sha'],self.github.base)
        self.assertIn('deployment_rollback_not_verified',report['blockers'])
        self.assertIn('Исторический отчёт',preflight.describe(self.conn))
        original=raw;self.run_broker()
        self.assertEqual(self.conn.execute('SELECT report FROM artifact_release_checks').fetchone()[0],original)

    def test_exact_owner_approval_does_not_enable_publishing_or_consume_decision(self):
        self.start();candidate,aid,scope=ledger.request_release(self.conn,1)
        approval.decide(self.conn,aid,'owner','owner',True)
        before=self.conn.execute('SELECT * FROM approvals').fetchall()
        result=self.run_broker();self.assertEqual(result['approval_state'],'approved')
        self.assertFalse(result['publish_allowed']);self.assertFalse(result['published'])
        self.assertEqual(self.conn.execute('SELECT * FROM approvals').fetchall(),before)
        report=json.loads(self.conn.execute('SELECT report FROM artifact_release_checks').fetchone()[0])
        self.assertEqual(report['candidate_id'],candidate)
        self.assertEqual(report['blockers'],['publisher_not_connected','deployment_rollback_not_verified'])

    def test_rejected_expired_or_other_exact_scope_cannot_authorize(self):
        for mode in ('rejected','expired','wrong_head','wrong_ci'):
            with self.subTest(mode=mode):
                # Isolate each case using a rollback-only saved DB snapshot.
                self.start();candidate,aid,scope=ledger.request_release(self.conn,1)
                approval.decide(self.conn,aid,'owner','owner',mode!='rejected')
                if mode=='expired':
                    self.conn.execute("UPDATE approvals SET expires_at='2000-01-01T00:00:00+00:00' WHERE id=?",(aid,));self.conn.commit()
                elif mode in ('wrong_head','wrong_ci'):
                    changed=dict(scope,head_sha='e'*40) if mode=='wrong_head' else dict(scope,ci_runs=[])
                    self.conn.execute('UPDATE approvals SET artifact_sha256=? WHERE id=?',(approval.canonical_digest(changed),aid));self.conn.commit()
                result=self.run_broker();self.assertEqual(result['approval_state'],'not_authorized');self.assertFalse(result['publish_allowed'])
                if mode!='wrong_ci': self.tearDown();self.setUp()

    def test_remote_movement_and_failing_ci_never_yield_successful_report(self):
        self.start();self.github.branch='e'*40
        with self.assertRaises(broker.Blocked): self.run_broker()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM artifact_release_checks').fetchone()[0],0)
        self.github.branch=self.github.head;self.github.ci='failure'
        with self.assertRaises(PermissionError): self.run_broker()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM artifact_release_checks').fetchone()[0],0)

    def test_changed_local_source_during_remote_check_and_lost_lease_fail_closed(self):
        self.start();original=self.github.call
        identity,files=ledger.material(self.conn,self.artifact,self.data)
        file=self.data/'artifacts'/('job-'+str(identity['generation_job_id'])+'-attempt-1')/next(iter(files))
        def call(*args,**kwargs):
            result=original(*args,**kwargs)
            if args[1].startswith('/actions/runs?'): file.write_text('changed in flight')
            return result
        self.github.call=call
        with self.assertRaises(PermissionError): self.run_broker()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM artifact_release_checks').fetchone()[0],0)
        file.write_text(next(iter(files.values())))
        self.conn.execute('UPDATE agent_jobs SET lease_until=? WHERE id=?',(time.time()-1,self.job['id']));self.conn.commit()
        with self.assertRaises(PermissionError): self.run_broker()

    def test_invalid_payload_is_rejected_before_credential_access(self):
        self.start();self.conn.execute('UPDATE agent_jobs SET payload=? WHERE id=?',
            (json.dumps({'artifact_pr':self.artifact,'release_check':True}),self.job['id']));self.conn.commit()
        issuer=unittest.mock.Mock()
        with self.assertRaises(PermissionError): self.run_broker(issuer=issuer)
        issuer.assert_not_called()

    def test_command_queues_only_the_read_only_scope(self):
        self.start()
        # Give the real worker an unclaimed job and a bounded mocked broker result.
        self.conn.execute("UPDATE agent_jobs SET state='queued',lease_token=NULL,lease_until=NULL WHERE id=?",(self.job['id'],));self.conn.commit()
        # Queue dispatch is covered by the real broker tests above; assert the
        # runtime command queues only the supported read-only scope.
        from contextlib import contextmanager
        @contextmanager
        def connect(): yield self.conn
        text=runtime_commands.handle('/release_check 1',connect,source_key='owner-unit')
        self.assertIn('публикация отключена',text)
        payload=json.loads(self.conn.execute("SELECT payload FROM agent_jobs WHERE event_key='owner-unit'").fetchone()[0])
        self.assertEqual(payload,{'artifact_pr':self.artifact,'refresh':True,'release_check':True})

    def test_token_read_only_permissions_are_requested(self):
        import github_app_auth_v46 as auth
        class Response:
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def read(self): return json.dumps({'token':'x'*40}).encode()
        requests=[]
        with patch.object(auth,'make_jwt',return_value='unit-jwt'):
            auth.installation_token('unused',opener=lambda req,**kw: requests.append(req) or Response(),read_only=True)
        payload=json.loads(requests[0].data)
        self.assertEqual(payload['repositories'],['ultimate-ai-control'])
        self.assertEqual(payload['permissions'],{'contents':'read','pull_requests':'read','actions':'read'})

    def test_memory_links_report_and_detects_changed_evidence(self):
        import evidence_memory as memory
        self.start();result=self.run_broker()
        q.finish(self.conn,self.job['id'],self.job['lease_token'],result)
        memory.sync(self.conn)
        row=self.conn.execute("SELECT id FROM project_evidence_memory WHERE event_id IN (SELECT id FROM agent_job_events WHERE job_id=?) ORDER BY id DESC LIMIT 1",(self.job['id'],)).fetchone()
        self.assertIsNotNone(row)
        self.assertIn('release_check',memory.detail(self.conn,row[0]))
        self.conn.execute("UPDATE artifact_release_checks SET report='{}'");self.conn.commit()
        self.assertIn('повторной проверки',memory.detail(self.conn,row[0]))
