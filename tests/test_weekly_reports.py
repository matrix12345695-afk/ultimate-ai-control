import concurrent.futures
import copy
from datetime import datetime
import json
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import patch
import emergency_control as emergency
import evidence_memory as memory
import main
import owner_notifications as inbox
import queue_worker
import roadmap
import scheduler
import task_queue as q
import weekly_reports as weekly


def at(text):return datetime.fromisoformat(text).replace(tzinfo=weekly.ZONE).timestamp()


class WeeklyReportsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'control.db'
        self.conn=queue_worker.connect(self.path);queue_worker.initialize(self.conn)
    def tearDown(self):self.conn.close();self.temp.cleanup()
    def job(self):
        now=time.time();ident=weekly.enqueue(self.conn,now=now)
        job=q.claim(self.conn,'weekly-fixture',q.KINDS,now=now)
        self.assertEqual(job['id'],ident);return job
    def finish(self):
        job=self.job();snapshot=weekly.observe(self.conn,job)
        result=weekly.complete(self.conn,job,snapshot);return job,snapshot,result

    def test_monday_delivery_and_sunday_month_year_boundaries(self):
        self.assertEqual(weekly.latest_due(at('2026-10-26T08:59:59')),at('2026-10-19T09:00:00'))
        self.assertEqual(weekly.latest_due(at('2026-10-26T09:00:00')),at('2026-10-26T09:00:00'))
        self.assertEqual(weekly.period_end(at('2026-10-27T10:00:00')),at('2026-10-26T00:00:00'))
        self.assertEqual(weekly.period_end(at('2027-01-01T10:00:00')),at('2026-12-28T00:00:00'))
        self.assertEqual(weekly.stamp(at('2026-10-26T00:00:00')),'26.10.2026 00:00')
        for end in (True,float('inf'),at('2026-10-26T01:00:00'),int(at('2026-10-27T00:00:00'))):
            with self.assertRaises(ValueError):weekly.payload(end)

    def test_seed_is_explicit_does_not_change_existing_schedules_or_owner_disable(self):
        self.assertEqual(self.conn.execute('SELECT count(*) FROM agent_schedules').fetchone()[0],0)
        scheduler.seed(self.conn,now=100);before=self.conn.execute('SELECT * FROM agent_schedules ORDER BY name').fetchall()
        weekly.seed(self.conn,now=at('2026-10-27T10:00:00'))
        row=self.conn.execute('SELECT next_due FROM agent_schedules WHERE name=?',(weekly.NAME,)).fetchone()
        self.assertEqual(row[0],at('2026-11-02T09:00:00'))
        self.conn.execute('UPDATE agent_schedules SET enabled=0 WHERE name=?',(weekly.NAME,));self.conn.commit()
        weekly.seed(self.conn,now=at('2026-11-12T10:00:00'))
        self.assertEqual(self.conn.execute('SELECT enabled FROM agent_schedules WHERE name=?',(weekly.NAME,)).fetchone()[0],0)
        self.assertEqual(before,self.conn.execute('SELECT * FROM agent_schedules WHERE name<>? ORDER BY name',(weekly.NAME,)).fetchall())

    def test_tick_is_calendar_aligned_idempotent_and_skips_backlog(self):
        weekly.seed(self.conn,now=at('2026-10-20T12:00:00'))
        now=at('2026-11-17T15:10:00');ids=scheduler.tick(self.conn,now)
        self.assertEqual(len(ids),1);self.assertEqual(scheduler.tick(self.conn,now),[])
        raw,event=self.conn.execute('SELECT payload,event_key FROM agent_jobs').fetchone();end=int(at('2026-11-16T00:00:00'))
        self.assertEqual(json.loads(raw),weekly.payload(end));self.assertEqual(event,weekly.key(end))
        self.assertEqual(self.conn.execute('SELECT next_due FROM agent_schedules').fetchone()[0],at('2026-11-23T09:00:00'))
        self.assertEqual(weekly.enqueue(self.conn,now=now),ids[0])

    def test_pause_and_emergency_leave_due_unchanged(self):
        weekly.seed(self.conn,now=at('2026-10-20T12:00:00'));before=self.conn.execute('SELECT * FROM agent_schedules').fetchall()
        q.configure(self.conn,paused=True);self.assertEqual(scheduler.tick(self.conn,at('2026-11-17T10:00:00')),[])
        self.assertEqual(before,self.conn.execute('SELECT * FROM agent_schedules').fetchall())
        q.configure(self.conn,paused=False);emergency.stop(self.conn)
        self.assertEqual(scheduler.tick(self.conn,at('2026-11-17T10:00:00')),[])
        with self.assertRaises(emergency.Stopped):weekly.enqueue(self.conn)

    def test_schedule_enqueue_and_next_due_rollback_atomically(self):
        weekly.seed(self.conn,now=at('2026-10-20T12:00:00'));before=self.conn.execute('SELECT next_due FROM agent_schedules').fetchone()
        with patch.object(q,'_event',side_effect=sqlite3.OperationalError('fixture fault')):
            with self.assertRaises(sqlite3.OperationalError):weekly.tick(self.conn,at('2026-11-17T10:00:00'))
        self.assertEqual(self.conn.execute('SELECT count(*) FROM agent_jobs').fetchone()[0],0)
        self.assertEqual(before,self.conn.execute('SELECT next_due FROM agent_schedules').fetchone())

    def test_concurrent_ticks_create_one_period_job(self):
        weekly.seed(self.conn,now=at('2026-10-20T12:00:00'))
        def tick(_):
            with queue_worker.connect(self.path) as conn:return weekly.tick(conn,at('2026-10-26T09:00:00'))
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(tick,range(2)))
        self.assertEqual(sum(len(x) for x in results),1)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM agent_jobs').fetchone()[0],1)

    def test_unknown_schedule_is_not_overwritten_and_other_jobs_continue(self):
        weekly.seed(self.conn,now=at('2026-10-20T12:00:00'))
        self.conn.execute('UPDATE agent_schedules SET payload=? WHERE name=?',('{"target":"foreign"}',weekly.NAME));self.conn.commit()
        with self.assertRaises(ValueError):weekly.seed(self.conn)
        scheduler.seed(self.conn,now=100)
        self.assertEqual(len(scheduler.tick(self.conn,at('2026-10-26T09:00:00'))),3)
        scheduler.tick(self.conn,at('2026-10-26T09:00:00'))
        self.assertEqual(self.conn.execute("SELECT count(*) FROM owner_notifications WHERE event_key='weekly-schedule-invalid-v1'").fetchone()[0],1)
        self.assertEqual(self.conn.execute('SELECT payload FROM agent_schedules WHERE name=?',(weekly.NAME,)).fetchone()[0],'{"target":"foreign"}')

    def test_report_boundaries_clip_spans_and_receipts_without_mutating_sources(self):
        end=int(at('2026-10-26T00:00:00'));start=end-weekly.WEEK
        ident=q.enqueue(self.conn,'nova','test_release',{},now=start-100);job=q.claim(self.conn,'fixture',q.KINDS,now=start-20)
        q.add_work_span(self.conn,ident,job['lease_token'],'testing',start-10,start+20,now=start+21)
        q.finish(self.conn,ident,job['lease_token'],{},now=start+22)
        future=q.enqueue(self.conn,'nova','check_site',{},now=end)
        self.conn.execute("INSERT INTO provider_costs VALUES('fixture','2026-10','nova','tester',?,'fixture',10,7,'settled',1,2,?,?)",(ident,start,start+10));self.conn.commit()
        fake={'project':'control','kind':'daily_report','payload':weekly.payload(end)};changes=self.conn.total_changes
        observation=weekly.observe(self.conn,fake,now=end+50)
        self.assertEqual(observation['analytics']['work_seconds'],20)
        self.assertEqual(observation['analytics']['completed'],1)
        self.assertEqual(observation['analytics']['settled_microusd'],7)
        self.assertIsNone(observation['analytics']['idle_seconds']);self.assertEqual(changes,self.conn.total_changes)
        with self.assertRaises(ValueError):weekly.observe(self.conn,fake,now=end-1)

    def test_atomic_completion_report_notice_and_success_event(self):
        job=self.job();snapshot=weekly.observe(self.conn,job)
        with patch.object(q,'_event',side_effect=sqlite3.OperationalError('fixture fault')):
            with self.assertRaises(sqlite3.OperationalError):weekly.complete(self.conn,job,snapshot)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM weekly_analytics_reports').fetchone()[0],0)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM owner_notifications').fetchone()[0],0)
        self.assertEqual(self.conn.execute('SELECT state FROM agent_jobs').fetchone()[0],'running')
        result=weekly.complete(self.conn,job,snapshot)
        self.assertEqual(weekly.record(self.conn,result['weekly_report_id'])[0],snapshot)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM agent_job_events WHERE event='succeeded'").fetchone()[0],1)
        with self.assertRaises(PermissionError):weekly.complete(self.conn,job,snapshot)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM owner_notifications').fetchone()[0],1)

    def test_stale_lease_epoch_wrong_project_and_forged_identity_cannot_complete(self):
        job=self.job();snapshot=weekly.observe(self.conn,job)
        for forged in (dict(job,lease_token='wrong'),dict(job,project='nova'),dict(job,payload=dict(job['payload'],extra=True))):
            with self.assertRaises((ValueError,PermissionError)):weekly.complete(self.conn,forged,snapshot)
        emergency.stop(self.conn)
        with self.assertRaises(emergency.Stopped):weekly.complete(self.conn,job,snapshot)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM weekly_analytics_reports').fetchone()[0],0)

    def test_immutable_snapshot_memory_and_read_only_commands_detect_corrupt_job(self):
        job,snapshot,result=self.finish();end=result['weekly_report_id']
        with self.assertRaises(sqlite3.IntegrityError):self.conn.execute('DELETE FROM weekly_analytics_reports')
        self.conn.rollback()
        while memory.sync(self.conn)['scanned']:pass
        mid=self.conn.execute('SELECT id FROM project_evidence_memory').fetchone()[0]
        self.assertIn('weekly_report',memory.detail(self.conn,mid))
        with patch.object(main,'DB',self.path):
            for command in ('/weekly_report','/weekly_report '+str(end),'/weekly_auto'):
                value=main.command(command);self.assertLessEqual(len(value),3900);self.assertIn('Asia/Tashkent',value)
        before=self.conn.total_changes;weekly.describe(self.conn,end);weekly.status(self.conn)
        self.assertEqual(before,self.conn.total_changes)
        self.conn.execute('UPDATE agent_jobs SET result=? WHERE id=?',('{}',job['id']));self.conn.commit()
        with self.assertRaises(ValueError):weekly.record(self.conn,end)
        self.assertIn('повторной проверки',memory.detail(self.conn,mid))

    def test_plan_keeps_full_stage_active_and_reads_verified_report(self):
        self.finish();roadmap.mark(self.conn,11,'active','full idle accounting pending')
        text=roadmap.describe(self.conn);self.assertIn('Календарный недельный отчёт сохранён',text)
        self.assertIn('11. Рабочее время и аналитика — в работе',text)
        self.assertLessEqual(len(text),3900)

    def test_worker_uses_weekly_branch_and_only_one_period_notification(self):
        ident=weekly.enqueue(self.conn);self.assertEqual(queue_worker.run_once(self.path),{'id':ident,'state':'succeeded'})
        self.assertEqual(weekly.enqueue(self.conn),ident);self.assertIsNone(queue_worker.run_once(self.path))
        result=json.loads(self.conn.execute('SELECT result FROM agent_jobs WHERE id=?',(ident,)).fetchone()[0])
        self.assertIn('weekly_report_id',result)
        self.assertEqual(self.conn.execute('SELECT title FROM owner_notifications').fetchall(),[('Недельный отчёт ULTIMATE',)])
        self.assertEqual(self.conn.execute('SELECT count(*) FROM provider_costs').fetchone()[0],0)
        self.assertIn('Telegram: доставка ещё не подтверждена',weekly.describe(self.conn))

    def test_foreign_notice_event_collision_cannot_bind_another_request(self):
        job=self.job();snapshot=weekly.observe(self.conn,job);end=job['payload']['period_end']
        inbox.create(self.conn,'foreign','decision','fixture unrelated','fixture','fixture',event_key=weekly.key(end))
        with self.assertRaises(ValueError):weekly.complete(self.conn,job,snapshot)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM weekly_analytics_reports').fetchone()[0],0)
        self.assertEqual(self.conn.execute('SELECT state FROM agent_jobs').fetchone()[0],'running')
        self.assertEqual(self.conn.execute('SELECT project,state FROM owner_notifications').fetchall(),[('foreign','pending')])

    def test_reopen_keeps_original_snapshot_and_delivery_is_not_task_or_owner_approval(self):
        job,snapshot,result=self.finish();end=result['weekly_report_id']
        q.enqueue(self.conn,'control','plan_change',{'text':'fixture no private source'})
        self.conn.execute("UPDATE owner_notifications SET delivered_at='fixture-api-receipt',telegram_message_id=42 WHERE id=?",(result['notification_id'],));self.conn.commit()
        with queue_worker.connect(self.path) as reopened:
            self.assertEqual(weekly.record(reopened,end)[0],snapshot)
            self.assertIn('Telegram: доставка записана',weekly.describe(reopened,end))
            self.assertEqual(reopened.execute('SELECT count(*) FROM approvals').fetchone()[0],0)
            self.assertEqual(weekly.enqueue(reopened),job['id'])

    def test_invalid_schedule_status_and_tampered_job_do_not_show_false_completion(self):
        job,snapshot,result=self.finish();weekly.seed(self.conn)
        self.conn.execute("UPDATE agent_schedules SET next_due='fixture-invalid' WHERE name=?",(weekly.NAME,))
        self.conn.execute('UPDATE agent_jobs SET result=? WHERE id=?',('{}',job['id']));self.conn.commit()
        self.assertIn('требует проверки',weekly.status(self.conn))
        self.assertNotIn('Календарный недельный отчёт сохранён',roadmap.describe(self.conn))
        self.assertEqual(weekly.tick(self.conn,time.time()),[])

    def test_invalid_snapshots_and_timestamp_types_fail_closed(self):
        job=self.job();snapshot=weekly.observe(self.conn,job)
        for k,v in (('published',True),('paid_calls',True),('timezone','UTC'),('generated_at',float('nan')),('until',True)):
            modified=copy.deepcopy(snapshot);modified[k]=v;self.assertFalse(weekly.valid(modified,job['payload']['period_end']))
        modified=copy.deepcopy(snapshot);modified['analytics']['work_seconds']+=1;self.assertFalse(weekly.valid(modified,job['payload']['period_end']))

if __name__=='__main__':unittest.main()
