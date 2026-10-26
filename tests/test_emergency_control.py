"""Fault and race tests use disposable DBs, fixture credentials and fake transports."""
import json
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

import approval
import artifact_pr_broker as broker
import emergency_control as control
import emergency_selftest as selftest
import evidence_memory as memory
import owner_notifications as inbox
import queue_worker
import runtime_commands
import scheduler
import task_queue as q
import test_artifact_prs as artifact_fixtures
import test_metered_provider as provider_fixtures


class EmergencyControlTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'control.db'
        self.conn=sqlite3.connect(self.path);queue_worker.initialize(self.conn)

    def tearDown(self): self.conn.close();self.temp.cleanup()

    def job(self):
        q.enqueue(self.conn,'control','test_release',{'target':'fixture'})
        return q.claim(self.conn,'fixture',q.KINDS)

    def approved(self):
        ident=approval.request_approval(self.conn,1,'publish','production',{'sha':'fixture'})
        approval.decide(self.conn,ident,'owner','owner',True);return ident

    def authorized(self,ident): return approval.is_authorized(self.conn,ident,1,'publish','production',{'sha':'fixture'})

    def test_restart_and_initializer_preserve_stop(self):
        control.stop(self.conn,source_key='stop');self.conn.close()
        self.conn=sqlite3.connect(self.path);queue_worker.initialize(self.conn)
        self.assertTrue(control.state(self.conn)['latched']);self.assertIsNone(q.claim(self.conn,'x',q.KINDS))

    def test_missing_control_row_is_not_recreated(self):
        self.conn.execute('DELETE FROM uac_emergency_control');self.conn.commit()
        with self.assertRaises(control.Stopped): queue_worker.initialize(self.conn)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM uac_emergency_control').fetchone()[0],0)

    def test_migrating_legacy_queue_and_approval_binds_zero(self):
        conn=sqlite3.connect(':memory:');q.initialize(conn);approval.init_approvals(conn)
        job=q.enqueue(conn,'control','test_release',{'target':'fixture'})
        aid=approval.request_approval(conn,job,'publish','production',{})
        conn.execute('ALTER TABLE agent_jobs DROP COLUMN control_epoch')
        for table in ('approval_control_epochs','uac_emergency_control'): conn.execute('DROP TABLE '+table)
        conn.commit();q.initialize(conn);approval.init_approvals(conn)
        self.assertEqual(conn.execute('SELECT control_epoch FROM agent_jobs').fetchone()[0],0)
        self.assertEqual(conn.execute('SELECT epoch FROM approval_control_epochs WHERE approval_id=?',(aid,)).fetchone()[0],0)
        self.assertEqual(control.state(conn)['epoch'],0);conn.close()

    def test_stop_deduplicates_and_replays_without_reactivation(self):
        control.stop(self.conn,source_key='a');control.stop(self.conn,source_key='b')
        self.assertEqual(self.conn.execute('SELECT count(*) FROM uac_control_events').fetchone()[0],1)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM owner_notifications WHERE kind='critical'").fetchone()[0],1)
        control.reset(self.conn,1,source_key='reset');control.stop(self.conn,source_key='a')
        self.assertFalse(control.state(self.conn)['latched']);self.assertEqual(control.state(self.conn)['epoch'],2)

    def test_old_reset_replay_cannot_clear_new_stop(self):
        control.stop(self.conn);control.reset(self.conn,1,source_key='reset')
        control.stop(self.conn);control.reset(self.conn,1,source_key='reset')
        self.assertTrue(control.state(self.conn)['latched']);self.assertEqual(control.state(self.conn)['epoch'],3)

    def test_conflicting_source_key_and_stale_reset_fail_closed(self):
        control.stop(self.conn,source_key='same')
        with self.assertRaises(ValueError): control.reset(self.conn,1,source_key='same')
        with self.assertRaises(control.Stopped): control.reset(self.conn,3)
        self.assertTrue(control.state(self.conn)['latched'])

    def test_reset_waits_for_running_work_then_keeps_pause(self):
        job=self.job();control.stop(self.conn)
        with self.assertRaisesRegex(control.Stopped,'still_running'): control.reset(self.conn,1)
        q.finish(self.conn,job['id'],job['lease_token'],{'fixture':True})
        control.reset(self.conn,1)
        self.assertEqual(self.conn.execute('SELECT paused FROM agent_queue_control').fetchone()[0],1)
        self.assertIsNone(q.claim(self.conn,'x',q.KINDS));q.configure(self.conn,paused=False)
        fresh=self.job();self.assertEqual(self.conn.execute('SELECT control_epoch FROM agent_jobs WHERE id=?',(fresh['id'],)).fetchone()[0],2)

    def test_resume_and_raw_pause_change_cannot_bypass_latch(self):
        control.stop(self.conn)
        with self.assertRaises(control.Stopped): q.configure(self.conn,paused=False)
        self.conn.execute('UPDATE agent_queue_control SET paused=0');self.conn.commit()
        ident=q.enqueue(self.conn,'control','test_release',{'target':'saved-during-stop'})
        self.assertIsNone(q.claim(self.conn,'x',q.KINDS))
        self.assertEqual(self.conn.execute('SELECT state FROM agent_jobs WHERE id=?',(ident,)).fetchone()[0],'queued')

    def test_scheduler_does_not_emit_work_even_if_pause_flag_cleared(self):
        control.stop(self.conn);self.conn.execute('UPDATE agent_queue_control SET paused=0');self.conn.commit()
        before=self.conn.execute('SELECT count(*) FROM agent_jobs').fetchone()[0]
        self.assertEqual(scheduler.tick(self.conn),[])
        self.assertEqual(self.conn.execute('SELECT count(*) FROM agent_jobs').fetchone()[0],before)

    def test_old_approved_and_pending_capabilities_stay_invalid(self):
        old=self.approved();pending=approval.request_approval(self.conn,2,'publish','production',{})
        control.stop(self.conn);self.assertFalse(self.authorized(old))
        with self.assertRaises(control.Stopped): approval.request_approval(self.conn,3,'publish','production',{})
        with self.assertRaises(control.Stopped): approval.decide(self.conn,pending,'owner','owner',True)
        control.reset(self.conn,1);self.assertFalse(self.authorized(old))
        with self.assertRaises(control.Stopped): approval.decide(self.conn,pending,'owner','owner',True)
        fresh=self.approved();self.assertTrue(self.authorized(fresh))

    def test_owner_can_reject_stale_request_but_other_actor_cannot(self):
        aid=approval.request_approval(self.conn,1,'publish','production',{});control.stop(self.conn)
        with self.assertRaises(PermissionError): approval.decide(self.conn,aid,'other','owner',False)
        self.assertEqual(approval.decide(self.conn,aid,'owner','owner',False),'rejected')

    def test_control_outbox_survives_inbox_failure_and_retries_once(self):
        with patch.object(inbox,'create',side_effect=sqlite3.OperationalError('fixture inbox unavailable')):
            control.stop(self.conn,source_key='stop')
        self.assertTrue(control.state(self.conn)['latched'])
        self.assertEqual(self.conn.execute('SELECT inbox_id FROM uac_control_outbox').fetchone(),(None,))
        self.assertEqual(control.flush_notifications(self.conn),1);self.assertEqual(control.flush_notifications(self.conn),0)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM owner_notifications WHERE event_key='uac-emergency-stop-1'").fetchone()[0],1)

    def test_second_connection_stop_blocks_new_admission_and_keeps_prior_receipt(self):
        job=self.job();admission=control.admit(self.conn,'github_draft_write','POST /fixture',job_id=job['id'],lease_token=job['lease_token'])
        with sqlite3.connect(self.path) as other: control.stop(other)
        with self.assertRaises(control.Stopped): control.admit(self.conn,'github_draft_write','POST /later',job_id=job['id'],lease_token=job['lease_token'])
        control.acknowledge(self.conn,admission)
        self.assertEqual(self.conn.execute('SELECT state FROM uac_action_admissions').fetchall(),[('acknowledged',)])

    def test_stale_job_epoch_is_rejected_even_without_latch(self):
        job=self.job();self.conn.execute('UPDATE uac_emergency_control SET epoch=2');self.conn.commit()
        with self.assertRaisesRegex(control.Stopped,'job_control_epoch'): control.check_job(self.conn,job['id'],job['lease_token'])

    def test_selftest_stays_off_live_state_and_is_immutable_typed_evidence(self):
        before=control.state(self.conn);q.enqueue(self.conn,'control','test_release',{'target':selftest.PROFILE})
        job=q.claim(self.conn,'fixture',q.KINDS);report=selftest.acceptance();result=selftest.save(self.conn,job,report)
        q.finish(self.conn,job['id'],job['lease_token'],result)
        self.assertEqual(control.state(self.conn),before)
        while memory.sync(self.conn)['scanned']: pass
        row=self.conn.execute("SELECT id FROM project_evidence_memory WHERE event_id IN(SELECT id FROM agent_job_events WHERE job_id=? AND event='succeeded')",(job['id'],)).fetchone()
        self.assertIn('emergency_selftest',memory.detail(self.conn,row[0]))
        self.conn.execute("UPDATE emergency_selftest_runs SET report='{}'");self.conn.commit()
        self.assertIn('повторной проверки',memory.detail(self.conn,row[0]))

    def test_selftest_rejects_forged_counts_and_live_claims(self):
        report=selftest.acceptance();self.assertTrue(selftest.valid(report))
        for field,value in [('live_control_changed',True),('paid_calls',1),('service_signals',1),('network_calls',1),('published',True)]:
            self.assertFalse(selftest.valid(dict(report,**{field:value})))
        bad=dict(report,checks=dict(report['checks'],no_new_claims=False));self.assertFalse(selftest.valid(bad))

    def test_read_only_get_can_finish_during_stop_but_write_cannot(self):
        job=self.job();client=Mock(read_only=False);client.call.return_value={'ok':True}
        guarded=broker.ControlledClient(client,self.conn,job);control.stop(self.conn)
        self.assertEqual(guarded.call('GET','/fixture'),{'ok':True})
        with self.assertRaises(control.Stopped): guarded.call('POST','/fixture',{})
        self.assertEqual(client.call.call_count,1)

    def test_ambiguous_external_write_is_journalled_while_stopped(self):
        job=self.job();client=Mock(read_only=False)
        def send(*args,**kwargs): control.stop(self.conn);raise TimeoutError('fixture')
        client.call.side_effect=send
        with self.assertRaises(TimeoutError): broker.ControlledClient(client,self.conn,job).call('POST','/fixture',{})
        self.assertEqual(self.conn.execute('SELECT state FROM uac_action_admissions').fetchone()[0],'unknown')
        self.assertIn('Допуск #1',control.describe(self.conn))

    def test_worker_interrupted_before_next_action_waits_without_retry_or_duplicate_alert(self):
        ident=q.enqueue(self.conn,'nova','check_site',{'target':'nova'})
        def checker(payload):
            with sqlite3.connect(self.path) as conn: control.stop(conn)
            raise control.Stopped('emergency_latched')
        outcome=queue_worker.run_once(self.path,site_checker=checker)
        self.assertEqual(outcome['state'],'awaiting_owner')
        self.assertEqual(self.conn.execute('SELECT state,attempts FROM agent_jobs WHERE id=?',(ident,)).fetchone(),('awaiting_owner',1))
        self.assertIsNone(queue_worker.run_once(self.path,site_checker=checker))
        self.assertEqual(self.conn.execute("SELECT count(*) FROM owner_notifications WHERE kind='critical'").fetchone()[0],1)

    def test_commands_require_epoch_reset_and_explicit_resume(self):
        import main
        with patch.object(main,'DB',self.path):
            self.assertIn('ВКЛЮЧЕНА',main.command('🚨 Аварийный стоп'))
            self.assertIn('не снимает',main.command('/resume'))
            self.assertIn('сброс не выполнен',main.command('/emergency_reset 3'))
            self.assertIn('отдельно',main.command('/emergency_reset 1'))
            self.assertEqual(self.conn.execute('SELECT paused FROM agent_queue_control').fetchone()[0],1)
            main.command('/resume')
            self.assertFalse(control.state(self.conn)['latched'])
            self.assertEqual(self.conn.execute('SELECT paused FROM agent_queue_control').fetchone()[0],0)

    def test_live_worker_selftest_marks_only_its_completed_work(self):
        import roadmap
        ident=q.enqueue(self.conn,'control','test_release',{'target':selftest.PROFILE})
        self.assertEqual(queue_worker.run_once(self.path)['state'],'succeeded')
        report=roadmap.describe(self.conn)
        self.assertIn('✅ Аварийная блокировка',report)
        self.assertIn('15. Полный автономный цикл',report)
        self.assertFalse(control.state(self.conn)['latched'])


class EmergencyGitHubTests(unittest.TestCase):
    def setUp(self):
        self.fixture=artifact_fixtures.ArtifactPRTests();self.fixture.setUp()
    def tearDown(self): self.fixture.tearDown()

    def test_stop_before_broker_prevents_credential_issue(self):
        f=self.fixture;control.stop(f.conn);issuer=Mock()
        with self.assertRaises(control.Stopped): f.run_broker(issuer=issuer)
        issuer.assert_not_called();self.assertEqual(f.github.calls,[])

    def test_stop_after_first_remote_write_prevents_all_later_writes(self):
        f=self.fixture;original=f.github.call
        def send(method,path,*args,**kwargs):
            result=original(method,path,*args,**kwargs)
            if method!='GET': control.stop(f.conn)
            return result
        f.github.call=send
        with self.assertRaises(control.Stopped): f.run_broker()
        self.assertEqual(sum(m!='GET' for m,_,_ in f.github.calls),1)
        self.assertEqual(f.conn.execute('SELECT state FROM uac_action_admissions').fetchall(),[('acknowledged',)])


class EmergencyProviderTests(unittest.TestCase):
    def setUp(self): self.fixture=provider_fixtures.MeteredProviderTests();self.fixture.setUp()
    def tearDown(self): self.fixture.tearDown()

    def test_stopped_provider_does_not_read_key_reserve_or_send(self):
        import metered_provider as api
        f=self.fixture;control.stop(f.conn);send=Mock()
        with patch.object(api,'private_read',side_effect=AssertionError('key accessed')):
            with self.assertRaises(control.Stopped): f.call(transport=send)
        send.assert_not_called();self.assertEqual(f.conn.execute('SELECT count(*) FROM provider_costs').fetchone()[0],0)

    def test_stop_during_key_read_is_fenced_before_financial_reservation(self):
        import metered_provider as api
        f=self.fixture;read=api.private_read;send=Mock()
        def read_then_stop(path,size):
            value=read(path,size)
            if Path(path)==f.key: control.stop(f.conn)
            return value
        with patch.object(api,'private_read',side_effect=read_then_stop):
            with self.assertRaises(control.Stopped): f.call(transport=send)
        send.assert_not_called();self.assertEqual(f.conn.execute('SELECT count(*) FROM provider_costs').fetchone()[0],0)

    def test_pre_admitted_response_after_stop_keeps_real_fixture_receipt(self):
        f=self.fixture
        def send(*args):
            self.assertFalse(f.conn.in_transaction)
            control.stop(f.conn);return f.body()
        result=f.call(transport=send)
        self.assertEqual(result['cost_microusd'],428)
        self.assertEqual(f.conn.execute('SELECT state,actual_microusd FROM provider_costs').fetchone(),('settled',428))
        self.assertEqual(f.conn.execute('SELECT state FROM uac_action_admissions').fetchone()[0],'acknowledged')
        self.assertTrue(control.state(f.conn)['latched'])

    def test_ambiguous_admitted_send_keeps_hold_and_reset_does_not_allow_blind_retry(self):
        import metered_provider as api
        f=self.fixture;calls=[]
        def send(*args): calls.append(1);control.stop(f.conn);raise TimeoutError('fixture')
        with self.assertRaises(api.ProviderBlocked): f.call(transport=send)
        self.assertEqual(f.conn.execute('SELECT state FROM uac_action_admissions').fetchone()[0],'unknown')
        control.reset(f.conn,1)
        with self.assertRaisesRegex(api.ProviderBlocked,'unresolved'): f.call(key='later',transport=send)
        self.assertEqual(len(calls),1)
        self.assertEqual(f.conn.execute('SELECT state FROM provider_costs').fetchone()[0],'unknown')
