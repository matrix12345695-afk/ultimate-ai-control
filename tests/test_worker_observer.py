import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import completion_audit
import emergency_control as emergency
import main
import metered_provider
import queue_worker
import roadmap
import task_queue as q
import work_analytics
import worker_observer as observed


class WorkerObserverTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'control.db'
        self.conn=queue_worker.connect(self.path);queue_worker.initialize(self.conn)
        self.observer=observed.Observer.start(self.conn,'operations-1',now=100)
    def tearDown(self):self.conn.close();self.temp.cleanup()
    def interval(self,start=100,end=105,*,reason=None,after=None,mono_end=15,failed=False):
        context=observed.context(self.conn,now=start)
        if reason:context=dict(context,reason=reason)
        return self.observer.record(self.conn,start,end,10,mono_end,context,context if after is None else after,failed=failed)

    def test_completed_wait_is_clipped_and_historical_absence_stays_unknown(self):
        self.assertTrue(self.interval());report=observed.report(self.conn,0,200)
        self.assertEqual(report['observed_wait_seconds'],5);self.assertEqual(report['unobserved_seconds'],195)
        self.assertEqual(report['by_reason'],{'empty_queue':5})
        self.assertEqual(observed.report(self.conn,102,104)['observed_wait_seconds'],2)
        self.assertEqual(observed.report(self.conn,0,99)['observed_wait_seconds'],0)
        self.assertIsNone(work_analytics.report(self.conn,0,200)['idle_seconds'])
        self.assertEqual(work_analytics.summary(self.conn,0,200)['worker_observation'],report)

    def test_clock_jump_long_gap_and_nonfinite_time_do_not_backfill_idle(self):
        for start,end,mono_end in ((100,160,15),(100,105,40),(105,100,15),(100,105,14)):
            self.assertFalse(self.interval(start,end,mono_end=mono_end))
        for value in (True,float('nan'),float('inf')):
            with self.assertRaises(ValueError):self.interval(value,105)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM worker_observer_waits').fetchone()[0],0)
        self.assertEqual(self.conn.execute('SELECT dropped FROM worker_observer_sessions').fetchone()[0],4)

    def test_common_clock_duration_is_conservative(self):
        self.interval(100,105,mono_end=14.9)
        self.assertAlmostEqual(observed.report(self.conn,100,110)['observed_wait_seconds'],4.9)

    def test_restart_has_new_session_fences_old_pulse_and_never_fills_gap(self):
        self.interval();old=self.observer
        self.observer=observed.Observer.start(self.conn,'operations-1',now=300);self.interval(300,305)
        result=observed.report(self.conn,0,400)
        self.assertEqual(result['observed_wait_seconds'],10);self.assertEqual(result['unobserved_seconds'],390)
        self.conn.execute("UPDATE agent_queue_control SET reason='fixture transaction'")
        with self.assertRaises(observed.SessionLost):old.touch(self.conn,now=306)
        self.conn.rollback()
        with self.assertRaises(observed.SessionLost):old.record(self.conn,305,310,15,20,{'reason':'empty_queue'},{'reason':'empty_queue'})
        old.close(self.conn,now=310)
        self.assertEqual(observed.current(self.conn,now=310)['state'],'empty_queue')

    def test_context_records_pause_emergency_ready_retry_and_owner_pending(self):
        self.assertEqual(observed.context(self.conn,now=100)['reason'],'empty_queue')
        ident=q.enqueue(self.conn,'control','plan_change',{},now=100)
        self.assertEqual(observed.context(self.conn,now=101)['reason'],'poll_ready')
        job=q.claim(self.conn,'other',q.KINDS,now=101)
        self.assertEqual(observed.context(self.conn,now=102)['reason'],'capacity')
        q.fail(self.conn,ident,job['lease_token'],'fixture',now=103)
        self.assertEqual(observed.context(self.conn,now=104)['reason'],'retry_delay')
        job=q.claim(self.conn,'other',q.KINDS,now=200);q.finish(self.conn,ident,job['lease_token'],{},awaiting_owner=True,now=201)
        self.assertEqual(observed.context(self.conn,now=202)['reason'],'owner_pending')
        q.configure(self.conn,paused=True)
        self.assertEqual(observed.context(self.conn)['reason'],'paused')
        emergency.stop(self.conn)
        self.assertEqual(observed.context(self.conn)['reason'],'emergency')

    def test_transitions_and_error_backoff_have_explicit_reasons(self):
        before=observed.context(self.conn,now=100);after=dict(before,event=99)
        self.interval(after=after);self.interval(105,110,failed=True)
        result=observed.report(self.conn,0,200)
        self.assertEqual(result['by_reason'],{'changed':5,'tick_error':5})

    def test_busy_work_is_not_double_counted_as_wait(self):
        ident=q.enqueue(self.conn,'control','test_release',{},now=100);job=q.claim(self.conn,'operations-1',q.KINDS,now=100)
        q.add_work_span(self.conn,ident,job['lease_token'],'testing',102,104,now=104)
        self.interval();data=observed.report(self.conn,100,110)
        self.assertEqual(data['work_coverage_seconds'],2);self.assertEqual(data['overlap_seconds'],2)
        self.assertEqual(data['observed_wait_seconds'],3);self.assertEqual(data['unobserved_seconds'],5)

    def test_overlapping_session_times_are_not_trusted_as_complete_coverage(self):
        self.interval();self.observer=observed.Observer.start(self.conn,'operations-1',now=103);self.interval(103,108)
        data=observed.report(self.conn,100,110)
        self.assertEqual(data['observed_wait_seconds'],0);self.assertGreater(data['invalid_rows'],0)
        self.assertEqual(data['unobserved_seconds'],10)

    def test_wait_rows_are_immutable_and_bad_hash_is_excluded(self):
        self.interval()
        with self.assertRaises(sqlite3.IntegrityError):self.conn.execute('DELETE FROM worker_observer_waits')
        self.conn.rollback()
        self.conn.execute('INSERT INTO worker_observer_waits(session,sequence,started_at,ended_at,reason,sha256) VALUES(?,2,105,110,?,?)',(self.observer.session,'empty_queue','a'*64));self.conn.commit()
        data=observed.report(self.conn,100,115);self.assertEqual(data['observed_wait_seconds'],5);self.assertEqual(data['invalid_rows'],1)

    def test_current_signal_distinguishes_busy_stale_closed_and_never_claims_downtime(self):
        self.assertEqual(observed.current(self.conn,now=110)['state'],'empty_queue')
        self.assertEqual(observed.current(self.conn,now=200)['state'],'stale')
        self.assertEqual(observed.current(self.conn,now=99)['state'],'stale')
        ident=q.enqueue(self.conn,'control','plan_change',{},now=100);q.claim(self.conn,'operations-1',q.KINDS,now=105)
        self.assertEqual(observed.current(self.conn,now=110)['state'],'busy')
        self.observer.close(self.conn,now=115)
        self.assertEqual(observed.current(self.conn,now=115)['state'],'closed')
        self.assertIn('не доказывает простой',observed.describe(self.conn,now=200))

    def test_observation_reads_do_not_commit_caller_changes_or_touch_notifications(self):
        self.interval();self.conn.execute("UPDATE agent_queue_control SET reason='uncommitted fixture'")
        before=self.conn.total_changes;observed.report(self.conn,0,200);observed.current(self.conn,now=110);observed.describe(self.conn,now=110)
        self.assertTrue(self.conn.in_transaction);self.assertEqual(before,self.conn.total_changes);self.conn.rollback()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM owner_notifications').fetchone()[0],0)

    def test_polling_wait_records_only_actual_completed_sleeps_and_stopping_is_quiet(self):
        clock=[100.0]
        def sleep(value):clock[0]+=value
        observed.wait_cycle(self.path,self.observer,lambda:False,sleeper=sleep,clock=lambda:clock[0],monotonic=lambda:clock[0])
        self.assertEqual(observed.report(self.conn,100,110)['observed_wait_seconds'],5)
        observed.wait_cycle(self.path,self.observer,lambda:True,sleeper=sleep,clock=lambda:clock[0],monotonic=lambda:clock[0])
        self.assertEqual(self.conn.execute('SELECT count(*) FROM worker_observer_waits').fetchone()[0],1)

    def test_each_poll_observation_closes_its_database_handles(self):
        clock=[100.0];opened=[];original=sqlite3.connect
        def connect(*args,**kwargs):
            conn=original(*args,**kwargs);opened.append(conn);return conn
        def sleep(value):clock[0]+=value
        with patch.object(sqlite3,'connect',side_effect=connect):
            observed.wait_cycle(self.path,self.observer,lambda:False,sleeper=sleep,clock=lambda:clock[0],monotonic=lambda:clock[0])
        self.assertEqual(len(opened),2)
        for conn in opened:
            with self.assertRaises(sqlite3.ProgrammingError):conn.execute('SELECT1')

    def test_worker_pulse_is_fenced_before_claim_and_existing_work_still_completes(self):
        ident=q.enqueue(self.conn,'control','daily_report',{})
        new=observed.Observer.start(self.conn,'operations-1')
        with self.assertRaises(observed.SessionLost):queue_worker.run_once(self.path,observer=self.observer)
        self.assertEqual(self.conn.execute('SELECT state FROM agent_jobs WHERE id=?',(ident,)).fetchone()[0],'queued')
        self.assertEqual(queue_worker.run_once(self.path,observer=new)['state'],'succeeded')
        self.assertNotEqual(observed.current(self.conn)['state'],'stale')

    def test_commands_plan_and_old_weekly_snapshot_compatibility(self):
        now=time.time();self.observer=observed.Observer.start(self.conn,'operations-1',now=now-10)
        self.interval(now-5,now);roadmap.mark(self.conn,11,'active','broader acceptance pending')
        with patch.object(main,'DB',self.path):
            for command in ('/worker4','/worker4 24h','/worker4 7d','/agents','/finish4'):
                value=main.command(command);self.assertLessEqual(len(value),3900)
            self.assertIn('Использование',main.command('/worker4 90d'))
            self.assertIn('Интервалы ожидания исполнителя',main.command('/roadmap'))
        self.assertEqual(self.conn.execute('SELECT state FROM uac_roadmap WHERE id=11').fetchone()[0],'active')
        import weekly_reports
        ident=weekly_reports.enqueue(self.conn);queue_worker.run_once(self.path)
        row=self.conn.execute('SELECT period_end,snapshot,snapshot_sha256 FROM weekly_analytics_reports').fetchone()
        old=json.loads(row[1]);old['analytics'].pop('worker_observation')
        self.assertTrue(weekly_reports.valid(old,row[0]))

    def test_daily_observation_fact_is_bound_to_saved_result_and_rejects_forgery(self):
        import evidence_memory as memory
        self.interval();report=observed.report(self.conn,0,200)
        self.assertTrue(observed.valid_report(report))
        for forged in (dict(report,observed_wait_seconds=999),dict(report,unobserved_seconds=float('nan')),dict(report,invalid_rows=True)):
            self.assertFalse(observed.valid_report(forged))
        ident=q.enqueue(self.conn,'control','daily_report',{});queue_worker.run_once(self.path)
        while memory.sync(self.conn)['scanned']:pass
        mid=self.conn.execute("SELECT id FROM project_evidence_memory WHERE event_id IN(SELECT id FROM agent_job_events WHERE job_id=? AND event='succeeded')",(ident,)).fetchone()[0]
        self.assertIn('worker_observation',memory.detail(self.conn,mid))
        self.conn.execute('UPDATE agent_jobs SET result=? WHERE id=?',('{}',ident));self.conn.commit()
        self.assertIn('повторной проверки',memory.detail(self.conn,mid))

    def test_window_and_row_budget_are_bounded(self):
        self.interval()
        for since,until in ((0,32*86400),(1,1),(True,5),(0,float('inf'))):
            with self.assertRaises(ValueError):observed.report(self.conn,since,until)
        with patch.object(observed,'MAX_ROWS',0):self.assertEqual(observed.report(self.conn,0,200)['observed_wait_seconds'],0)


class CompletionAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'control.db'
        self.conn=queue_worker.connect(self.path);queue_worker.initialize(self.conn)
    def tearDown(self):self.conn.close();self.temp.cleanup()
    def test_deferred_api_is_preserved_without_creating_or_reopening_requests(self):
        roadmap.set_setting(self.conn,'provider_setup_deferred','true');before=self.conn.total_changes
        with patch.object(metered_provider,'private_read',side_effect=AssertionError('no secret/config access')):
            value=completion_audit.describe(self.conn)
        self.assertIn('API отложен вами',value);self.assertIn('Что остаётся разработать',value)
        self.assertFalse(completion_audit.snapshot(self.conn)['full_plan_complete'])
        self.assertEqual(before,self.conn.total_changes);self.assertEqual(self.conn.execute('SELECT count(*) FROM owner_notifications').fetchone()[0],0)
    def test_manual_stage_flags_do_not_prove_a_live_publisher_or_complete_ai_company(self):
        self.conn.execute("UPDATE uac_roadmap SET state='done'");self.conn.commit()
        value=completion_audit.describe(self.conn);self.assertIn('Полный план ещё не завершён',value)
        self.assertFalse(completion_audit.snapshot(self.conn)['live_publisher_implemented'])
        self.assertLessEqual(len(value),3900)
    def test_forged_voice_confirmation_and_mutated_weekly_job_are_not_accepted(self):
        self.conn.execute("INSERT INTO voice_inputs(source_key,fingerprint,owner_id,project,language,duration,received_at,expires_at,state,control_epoch,receipt,receipt_sha256) VALUES('fixture','fixture','101','nova','ru',5,100,1000,'confirmed',0,'{}','fixture')");self.conn.commit()
        self.assertFalse(completion_audit.snapshot(self.conn)['genuine_voice_confirmation_recorded'])
        import weekly_reports
        ident=weekly_reports.enqueue(self.conn);queue_worker.run_once(self.path)
        self.assertTrue(completion_audit.snapshot(self.conn)['weekly_snapshot_verified'])
        self.conn.execute('UPDATE agent_jobs SET result=? WHERE id=?',('{}',ident));self.conn.commit()
        self.assertFalse(completion_audit.snapshot(self.conn)['weekly_snapshot_verified'])
    def test_audit_is_a_snapshot_and_does_not_commit_unrelated_owner_change(self):
        self.conn.execute("UPDATE agent_queue_control SET reason='uncommitted fixture'");before=self.conn.total_changes
        completion_audit.snapshot(self.conn);self.assertEqual(self.conn.total_changes,before);self.assertTrue(self.conn.in_transaction)
        self.conn.rollback()


class RealWorkerObserverTests(unittest.TestCase):
    def test_real_daemon_records_completed_waits_and_closes_cleanly(self):
        with tempfile.TemporaryDirectory(prefix='worker-observer-real-') as name:
            root=Path(name);folder=root/'.ultimate-review-data/live';folder.mkdir(parents=True);path=folder/'control.db'
            with queue_worker.connect(path) as conn:queue_worker.initialize(conn)
            env={'PATH':'/usr/bin:/bin','HOME':str(root),'LANG':'C.UTF-8','DB_PATH':str(path),'PYTHONDONTWRITEBYTECODE':'1'}
            child=subprocess.Popen([sys.executable,str(Path(queue_worker.__file__)),'--loop'],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
            try:
                deadline=time.monotonic()+18;count=0
                while time.monotonic()<deadline and child.poll() is None:
                    with sqlite3.connect(path) as conn:count=conn.execute('SELECT count(*) FROM worker_observer_waits').fetchone()[0]
                    if count>=2:break
                    time.sleep(.1)
                self.assertGreaterEqual(count,2,'real daemon did not record two completed waits')
            finally:
                child.terminate()
                try:stdout,stderr=child.communicate(timeout=4)
                except subprocess.TimeoutExpired:child.kill();stdout,stderr=child.communicate(timeout=2)
            self.assertEqual(child.returncode,0,stderr[-500:])
            with sqlite3.connect(path) as conn:
                self.assertIsNotNone(conn.execute('SELECT closed_at FROM worker_observer_sessions').fetchone()[0])
                self.assertEqual(conn.execute('SELECT count(*) FROM provider_costs').fetchone()[0],0)
                data=observed.report(conn,time.time()-86400,time.time())
                self.assertGreater(data['observed_wait_seconds'],5);self.assertGreater(data['unobserved_seconds'],86000)
                self.assertEqual(conn.execute('SELECT count(*) FROM owner_notifications').fetchone()[0],0)

if __name__=='__main__':unittest.main()
