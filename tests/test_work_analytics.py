import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import main
import queue_worker
import roadmap
import task_queue as queue
import telegram_menu
import work_analytics as analytics


class WorkAnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'control.db'
        self.conn=queue_worker.connect(self.path);queue_worker.initialize(self.conn)
    def tearDown(self): self.conn.close();self.temp.cleanup()
    def job(self,project='control',kind='test_release',at=0):
        return queue.enqueue(self.conn,project,kind,{},now=at)
    def cost(self,ident,*,state='settled',actual=1000000,created=0,settled=12,project='control',agent='tester',job=None):
        self.conn.execute('INSERT INTO provider_costs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (ident,'2026-09',project,agent,job,'test-model',2000000,actual if state=='settled' else None,state,10 if state=='settled' else None,3 if state=='settled' else None,created,settled if state=='settled' else None))
        self.conn.commit()

    def test_measured_work_clips_window_and_groups_actual_worker_project_and_role(self):
        ident=self.job('nova',at=0)
        lease=queue.claim(self.conn,'actual-worker',queue.KINDS,now=1)
        queue.add_work_span(self.conn,ident,lease['lease_token'],'active',2,6,now=6)
        queue.add_work_span(self.conn,ident,lease['lease_token'],'testing',8,14,now=14)
        queue.add_work_span(self.conn,ident,lease['lease_token'],'waiting',15,16,now=16)
        queue.finish(self.conn,ident,lease['lease_token'],{},now=18)
        report=analytics.report(self.conn,5,12)
        self.assertEqual(report['measured_seconds'],{'active':1,'testing':4,'waiting':0})
        self.assertEqual(report['work_seconds'],5)
        self.assertEqual(report['by_worker'],{'actual-worker':5})
        self.assertEqual(report['by_project'],{'nova':5})
        self.assertEqual(report['by_role'],{'Тестирование':5})
        self.assertIsNone(report['idle_seconds'])
        self.assertEqual(analytics.report(self.conn,5,20)['measured_seconds']['waiting'],1)

    def test_queue_retry_and_owner_wait_use_only_state_events_and_are_not_work(self):
        ident=self.job(at=0)
        lease=queue.claim(self.conn,'worker',queue.KINDS,now=2)
        queue.fail(self.conn,ident,lease['lease_token'],'temporary',now=4)
        lease=queue.claim(self.conn,'worker',queue.KINDS,now=65)
        queue.finish(self.conn,ident,lease['lease_token'],{'artifact_id':1},awaiting_owner=True,now=67)
        report=analytics.report(self.conn,1,70)
        self.assertEqual(report['waiting_task_seconds'],{'queued':62,'awaiting_owner':3,'unknown_tails':0})
        self.assertEqual(report['work_seconds'],0)
        self.assertEqual(report['retries_scheduled'],1)
        queue.cancel(self.conn,ident,now=75)
        self.assertEqual(analytics.report(self.conn,68,80)['waiting_task_seconds']['awaiting_owner'],7)
        self.assertEqual(analytics.report(self.conn,68,72)['waiting_task_seconds']['awaiting_owner'],4)

    def test_overlapping_owner_waits_sum_by_task_not_worker_idle_or_elapsed_day(self):
        for at in (0,3):
            ident=self.job(at=at)
            lease=queue.claim(self.conn,'worker',queue.KINDS,now=at+1)
            queue.finish(self.conn,ident,lease['lease_token'],{},awaiting_owner=True,now=at+2)
        report=analytics.report(self.conn,6,10)
        self.assertEqual(report['waiting_task_seconds']['awaiting_owner'],8)
        self.assertEqual(report['work_seconds'],0)
        self.assertIsNone(report['idle_seconds'])

    def test_missing_history_and_inconsistent_tail_are_unknown_not_inferred_from_age(self):
        ident=self.job(at=0)
        self.conn.execute('DELETE FROM agent_job_events WHERE job_id=?',(ident,));self.conn.commit()
        self.assertEqual(analytics.report(self.conn,2,10)['waiting_task_seconds']['queued'],0)
        self.conn.execute("INSERT INTO agent_job_events(job_id,at,event,detail) VALUES(?,1,'awaiting_owner','')",(ident,))
        self.conn.commit()
        result=analytics.report(self.conn,2,10)
        self.assertEqual(result['waiting_task_seconds']['awaiting_owner'],0)
        self.assertEqual(result['waiting_task_seconds']['unknown_tails'],1)

    def test_expired_final_lease_and_failed_finish_count_once_each(self):
        self.job(at=0)
        queue.claim(self.conn,'worker',queue.KINDS,lease_seconds=5,now=1)
        # Force exhaustion at first attempt without inventing a failed work span.
        self.conn.execute('UPDATE agent_jobs SET max_attempts=1');self.conn.commit()
        queue.claim(self.conn,'worker',queue.KINDS,now=7)
        ident=self.job(at=8);lease=queue.claim(self.conn,'worker',queue.KINDS,now=9)
        queue.fail(self.conn,ident,lease['lease_token'],'failure',retryable=False,now=10)
        report=analytics.report(self.conn,0,20)
        self.assertEqual(report['failed'],2)
        self.assertEqual(report['leases_expired'],1)
        self.assertEqual(report['work_seconds'],0)

    def test_costs_use_receipt_time_and_keep_cross_month_unknown_holds_separate(self):
        job=self.job()
        self.cost('in',created=-100,settled=12,job=job)
        self.cost('out',actual=500000,created=12,settled=25,job=job)
        self.cost('at-end',actual=500000,settled=20,job=job)
        self.cost('unknown',state='unknown',created=-100,job=job)
        result=analytics.report(self.conn,10,20)
        self.assertEqual(result['settled_microusd'],1000000)
        self.assertEqual(result['settled_costs'][0]['receipts'],1)
        self.assertEqual(result['unresolved_holds'],{'count':1,'microusd':2000000})
        self.assertIn('Неразрешённый резерв (unknown)',analytics.job_cost(self.conn,job))
        self.assertIn('Токены по квитанциям: вход 30, выход 9',analytics.job_cost(self.conn,job))

    def test_missing_receipt_is_not_presented_as_verified_zero_cost(self):
        job=self.job();self.cost('broken',actual=None,job=job)
        result=analytics.report(self.conn,0,20)
        self.assertEqual(result['incomplete_receipts'],1)
        self.assertIn('неполные квитанции',analytics.describe(self.conn,now=20))
        self.assertIn('Квитанции неполны',analytics.job_cost(self.conn,job))

    def test_reads_do_not_mutate_or_commit_callers_changes_and_preserve_reopening(self):
        self.job(at=0)
        self.conn.execute("UPDATE agent_queue_control SET reason='uncommitted owner change'")
        before=self.conn.total_changes
        analytics.report(self.conn,0,10)
        self.assertTrue(self.conn.in_transaction)
        self.assertEqual(self.conn.total_changes,before)
        self.conn.rollback()
        with queue_worker.connect(self.path) as reopened:
            self.assertEqual(analytics.report(reopened,0,10)['waiting_task_seconds']['queued'],10)
            self.assertNotEqual(reopened.execute('SELECT reason FROM agent_queue_control').fetchone()[0],'uncommitted owner change')

    def test_commands_and_plan_keep_partial_stage_and_reject_unbounded_inputs(self):
        with patch.object(main,'DB',self.path):
            for text in ('/analytics4','/analytics4 24h','/analytics4 7d','/weekly','/daily'):
                result=main.command(text);self.assertIn('Измерено работы',result);self.assertLessEqual(len(result),3900)
            self.assertIn('Использование',main.command('/analytics4 90d'))
            self.assertIn('Отклонено',main.command('/cost4 '+'1'*100))
        roadmap.mark(self.conn,11,'active','broader analytics remain pending')
        roadmap.set_setting(self.conn,'work_analytics_verified_release','a'*40)
        self.assertIn('11. Рабочее время и аналитика — в работе',roadmap.describe(self.conn))
        self.assertIn('Отчёты за сутки/неделю',roadmap.describe(self.conn))
        self.assertEqual(telegram_menu.route('📆 Работа за неделю'),'/weekly')
        for since,until in ((1,1),(5,1),(0,32*86400),(True,20),(0,float('inf'))):
            with self.assertRaises(ValueError): analytics.report(self.conn,since,until)

    def test_daily_job_persists_bounded_measured_summary_without_creating_api_records(self):
        ident=queue.enqueue(self.conn,'control','daily_report',{})
        self.assertEqual(queue_worker.run_once(self.path)['state'],'succeeded')
        result=json.loads(self.conn.execute('SELECT result FROM agent_jobs WHERE id=?',(ident,)).fetchone()[0])
        self.assertIn('analytics',result)
        self.assertEqual(result['analytics']['settled_microusd'],0)
        self.assertIsNone(result['analytics']['idle_seconds'])
        self.assertEqual(self.conn.execute('SELECT count(*) FROM provider_costs').fetchone()[0],0)
        self.assertLess(len(json.dumps(result).encode()),16000)


if __name__=='__main__': unittest.main()
