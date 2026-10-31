import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch,Mock
import main
import queue_worker
import task_queue as q
import scheduler
import roadmap
import repo_heads
import owner_notifications as inbox
import project_retirement as r
import telegram_menu
import github_watch


class RetirementTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'control.db'
        with patch.object(main,'DB',self.path):main.db().close()
        self.conn=sqlite3.connect(self.path)
        self.nova=q.enqueue(self.conn,'nova','check_site',{'target':'nova'})
        self.kinder=q.enqueue(self.conn,'kinder','inspect_repository',{'target':'kinder'})
        self.control=q.enqueue(self.conn,'control','daily_report',{})
        self.note=inbox.create(self.conn,'Kinder Spa','decision','Setup','Reason','Action',task_id='kinder-setup')
        self.keep=inbox.create(self.conn,'ULTIMATE','decision','Other','Reason','Action')
        scheduler.seed(self.conn,now=1000)
        roadmap.set_setting(self.conn,'active_project','nova')
        roadmap.set_setting(self.conn,'provider_setup_deferred','true')
        q.configure(self.conn,paused=True,reason='owner pause')

    def tearDown(self):self.conn.close();self.temp.cleanup()
    def activate(self):return r.apply(self.conn,now=2000)

    def test_cleanup_is_scoped_and_keeps_control_history_and_owner_pause(self):
        result=self.activate()
        self.assertGreaterEqual(result['cancelled_jobs'],2)
        self.assertEqual(self.conn.execute('SELECT state FROM agent_jobs WHERE id=?',(self.nova,)).fetchone()[0],'cancelled')
        self.assertEqual(self.conn.execute('SELECT state FROM agent_jobs WHERE id=?',(self.control,)).fetchone()[0],'queued')
        self.assertEqual(self.conn.execute('SELECT paused,reason FROM agent_queue_control').fetchone(),(1,'owner pause'))
        self.assertEqual(roadmap.setting(self.conn,'active_project'),'control')
        self.assertEqual(roadmap.setting(self.conn,'provider_setup_deferred'),'true')
        self.assertTrue(self.conn.execute('SELECT 1 FROM agent_job_events WHERE job_id=?',(self.nova,)).fetchone())
        self.assertEqual(self.conn.execute('PRAGMA integrity_check').fetchone()[0],'ok')

    def test_pending_notices_are_resolved_without_fabricating_delivery(self):
        self.activate()
        self.assertEqual(self.conn.execute('SELECT state,delivered_at FROM owner_notifications WHERE id=?',(self.note,)).fetchone(),('resolved',None))
        self.assertEqual(self.conn.execute('SELECT state FROM owner_notifications WHERE id=?',(self.keep,)).fetchone(),('pending',))
        self.assertEqual([x[0] for x in inbox.pending(self.conn)],[self.keep])

    def test_queue_and_sql_writers_cannot_restore_retired_work(self):
        self.activate()
        for project,payload in [('nova',{}),('kinder',{}),('control',{'target':'nova-browser-ci-v1'}),('control',{'project':'kinder'})]:
            with self.subTest(project=project,payload=payload),self.assertRaises(ValueError):q.enqueue(self.conn,project,'plan_change',payload)
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("UPDATE agent_jobs SET state='queued' WHERE id=?",(self.nova,))
        self.conn.rollback()
        q.configure(self.conn,paused=False)
        job=q.claim(self.conn,'retirement-test',q.KINDS)
        self.assertEqual(job['id'],self.control)

    def test_legacy_voice_insert_and_memory_reseed_are_guarded(self):
        self.activate()
        roadmap.initialize(self.conn);scheduler.seed(self.conn,now=3000)
        self.assertFalse(self.conn.execute("SELECT 1 FROM project_memory WHERE project IN ('nova','kinder')").fetchone())
        self.assertFalse(self.conn.execute("SELECT 1 FROM agent_schedules WHERE project IN ('nova','kinder')").fetchone())
        import voice_intake
        with self.assertRaises(sqlite3.IntegrityError):
            voice_intake._enqueue_locked(self.conn,'nova',{'text':'old voice'},'retirement-voice')
        self.conn.rollback()

    def test_menu_commands_help_and_plan_do_not_offer_retired_projects(self):
        self.activate()
        buttons=telegram_menu.keyboard(self.conn)
        self.assertNotIn('NOVA',buttons);self.assertNotIn('Kinder',buttons);self.assertIn('VPS',buttons)
        with patch.object(main,'DB',self.path):
            for command in ('/projects4','/projects','/help','/memory','/roadmap','/voice4','/repo_heads'):
                answer=main.command(command)
                self.assertFalse(__import__('re').search('nova|kinder|нова|киндер',answer,__import__('re').I),(command,answer))
            for command in ('/test_nova','/nova_copy','/project nova','/work kinder task','/repo_check nova','/voice_project 1 kinder','/task nova old task'):
                self.assertEqual(main.command(command),r.MESSAGE)
        self.assertIn('Новый коммерческий AI-продукт',roadmap.describe(self.conn))

    def test_site_and_repository_monitors_do_not_fetch_retired_targets(self):
        self.activate()
        opener=Mock()
        with patch.object(main,'DB',self.path),patch.object(main.urllib.request,'urlopen',opener):
            self.assertIn('No HTTPS',main.check());opener.assert_not_called()
        with patch.object(github_watch,'allowed_repos',return_value={'old':'matrix12345695-afk/nova-web-agency','kinder':'matrix12345695-afk/Kinder-Spa-android'}):
            self.assertEqual(github_watch.scan(opener,excluded=r.PROJECTS),{});opener.assert_not_called()

    def test_repeated_retirement_is_idempotent_and_does_not_change_source_history(self):
        first=self.activate();events=self.conn.execute('SELECT count(*) FROM agent_job_events').fetchone()[0]
        second=self.activate()
        self.assertEqual(second['cancelled_jobs'],0);self.assertEqual(second['resolved_requests'],0)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM agent_job_events').fetchone()[0],events)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM uac_retired_projects').fetchone()[0],2)

    def test_requires_pause_and_refuses_running_project_jobs_atomically(self):
        q.configure(self.conn,paused=False)
        with self.assertRaises(RuntimeError):r.apply(self.conn)
        self.assertFalse(r.enabled(self.conn))
        self.conn.execute("UPDATE agent_jobs SET state='running' WHERE id=?",(self.nova,));self.conn.commit()
        q.configure(self.conn,paused=True)
        with self.assertRaises(RuntimeError):r.apply(self.conn)
        self.assertFalse(r.enabled(self.conn))

    def test_sql_guards_reject_new_notices_and_old_legacy_tasks(self):
        self.activate()
        with self.assertRaises(sqlite3.IntegrityError):inbox.create(self.conn,'NOVA WEB','critical','Old','Reason','Action')
        self.conn.rollback()
        with self.assertRaises(sqlite3.IntegrityError):self.conn.execute("INSERT INTO tasks(project,description,created_at) VALUES('kinder','old','now')")
        self.conn.rollback()
        self.assertEqual(q.enqueue(self.conn,'control','plan_change',{'text':'New product task'}),self.conn.execute('SELECT max(id) FROM agent_jobs').fetchone()[0])

    def test_approval_ids_are_scoped_to_project_not_ambiguous_task_numbers(self):
        import approval
        from github_requests import create_request
        # Approved scopes can share numeric task IDs; only explicit request/project links qualify.
        self.conn.execute("INSERT INTO github_change_requests(project,task,manifest_json,approval_id) VALUES('nova','old','{}','retired-approval')")
        self.conn.execute("INSERT INTO approvals VALUES('retired-approval',1,'github_draft_pr','review_only','digest','approved','2099-01-01','now',NULL,NULL)")
        self.conn.execute("INSERT INTO approvals VALUES('keep-approval',1,'different_action','review_only','digest','approved','2099-01-01','now',NULL,NULL)");self.conn.commit()
        self.activate()
        self.assertEqual(self.conn.execute("SELECT status FROM approvals WHERE id='retired-approval'").fetchone()[0],'rejected')
        self.assertEqual(self.conn.execute("SELECT status FROM approvals WHERE id='keep-approval'").fetchone()[0],'approved')


if __name__=='__main__':unittest.main()
