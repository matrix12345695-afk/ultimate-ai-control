import concurrent.futures
import json
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import patch
import main
import budget_gate
import chat_binding
import queue_worker
import roadmap
import runtime_commands
import scheduler
import task_queue as queue


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/'control.db'
        self.root=Path(self.temp.name)/'source'
        self.root.mkdir()
        (self.root/'hello.py').write_text('answer=42\n')
        with queue_worker.connect(self.path) as conn: queue_worker.initialize(conn)
        self.db_patch=patch.object(main,'DB',self.path)
        self.db_patch.start()

    def tearDown(self):
        self.db_patch.stop()
        self.temp.cleanup()

    def test_imported_memory_and_roadmap_persist(self):
        with queue_worker.connect(self.path) as conn:
            self.assertEqual(conn.execute('SELECT count(*) FROM uac_roadmap').fetchone()[0],16)
            kinder=json.loads(conn.execute("SELECT content FROM project_memory WHERE project='kinder'").fetchone()[0])
            self.assertIn('19:00',kinder['cancellation'])
            self.assertIn('planned',conn.execute('SELECT state FROM uac_roadmap WHERE id=16').fetchone()[0])
            self.assertRaises(ValueError,roadmap.mark,conn,2,'done','')

    def test_chat_binding_accepts_owner_private_link_but_not_foreign_urls(self):
        with queue_worker.connect(self.path) as conn:
            for url in ('http://chatgpt.com/c/123','https://evil.test/c/123','https://chatgpt.com@evil.test/c/123','https://chatgpt.com/share/123','https://chatgpt.com/c/123?token=secret'):
                with self.assertRaises(ValueError): chat_binding.bind(conn,url)
            url='https://chatgpt.com/c/01234567-1234-1234-1234-0123456789ab'
            chat_binding.bind(conn,url)
            self.assertEqual(chat_binding.current(conn)['url'],url)
            self.assertFalse(chat_binding.current(conn)['automatic_chat_ingestion'])
        self.assertIn(url,main.command('/chat_link'))

    def test_schedules_are_persistent_idempotent_and_skip_catchup_flood(self):
        with queue_worker.connect(self.path) as conn:
            scheduler.seed(conn,now=100)
            self.assertEqual(len(scheduler.tick(conn,now=101)),2)
            self.assertEqual(scheduler.tick(conn,now=101),[])
            scheduler.seed(conn,now=102)
            scheduler.tick(conn,now=10*86400)
            self.assertLessEqual(conn.execute('SELECT count(*) FROM agent_jobs').fetchone()[0],5)

    def test_pause_prevents_schedule_creation(self):
        with queue_worker.connect(self.path) as conn:
            scheduler.seed(conn,now=100)
            queue.configure(conn,paused=True)
            self.assertEqual(scheduler.tick(conn,now=200),[])

    def test_worker_inspects_source_and_records_real_time(self):
        with queue_worker.connect(self.path) as conn:
            ident=queue.enqueue(conn,'control','inspect_repository',{'target':'control'})
        result=queue_worker.run_once(self.path,self.root)
        self.assertEqual(result,{'id':ident,'state':'succeeded'})
        with queue_worker.connect(self.path) as conn:
            actual=json.loads(conn.execute('SELECT result FROM agent_jobs WHERE id=?',(ident,)).fetchone()[0])
            self.assertEqual(actual['inspected_files'],1)
            self.assertEqual(conn.execute('SELECT count(*) FROM agent_work_spans').fetchone()[0],1)

    def test_text_job_blocks_and_independent_monitoring_continues(self):
        with queue_worker.connect(self.path) as conn:
            one=runtime_commands.submit_text(conn,'Улучши мобильную версию',project='nova',event_key='chat:test')
            two=queue.enqueue(conn,'nova','check_site',{'target':'nova'})
        result=queue_worker.run_once(self.path,self.root)
        self.assertEqual(result['state'],'awaiting_owner')
        result=queue_worker.run_once(self.path,self.root,site_checker=lambda _: {'target':'nova','url':'https://novaweb.uz/','healthy':False,'detail':'HTTP 500'})
        self.assertEqual(result['id'],two)
        with queue_worker.connect(self.path) as conn:
            notes=conn.execute('SELECT kind,title,next_action FROM owner_notifications ORDER BY id').fetchall()
            self.assertEqual([n[0] for n in notes],['decision','critical'])
            self.assertIn('текущий чат',notes[0][2])
            self.assertEqual(conn.execute('SELECT state FROM agent_jobs WHERE id=?',(one,)).fetchone()[0],'awaiting_owner')

    def test_blockers_and_unchanged_health_do_not_spam(self):
        for _ in range(2):
            with queue_worker.connect(self.path) as conn:
                runtime_commands.submit_text(conn,'Добавь функцию',project='nova')
                queue.enqueue(conn,'nova','check_site',{'target':'nova'})
            queue_worker.run_once(self.path,self.root)
            queue_worker.run_once(self.path,self.root,site_checker=lambda _: {'target':'nova','url':'https://novaweb.uz/','healthy':False,'detail':'HTTP 500'})
        with queue_worker.connect(self.path) as conn:
            self.assertEqual(conn.execute('SELECT count(*) FROM owner_notifications').fetchone()[0],2)

    def test_no_arbitrary_url_repository_or_source_execution(self):
        self.assertRaises(ValueError,queue_worker.check_site,{'target':'http://127.0.0.1/'})
        self.assertFalse(queue_worker.allowed_url('https://127.0.0.1/'))
        self.assertFalse(queue_worker.allowed_url('https://novaweb.uz@evil.test/'))
        self.assertRaises(ValueError,queue_worker.inspect_source,{'target':'inventory'},self.root)
        (self.root/'bad.py').write_text('if :\n')
        result=queue_worker.inspect_source({'target':'control'},self.root)
        self.assertEqual(result['syntax_errors'],['bad.py'])

    def test_monitor_checks_get_page_instead_of_unsupported_head(self):
        requests=[]
        class Response:
            status=200
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def read(self,size):
                self_size=size
                if self_size!=1024: raise AssertionError('unbounded monitor read')
                return b'page'
        def opener(request,timeout):
            requests.append(request)
            self.assertEqual(request.get_method(),'GET')
            self.assertEqual(timeout,12)
            return Response()
        result=queue_worker.check_site({'target':'nova'},opener=opener)
        self.assertTrue(result['healthy'])
        self.assertEqual(result['detail'],'HTTP 200')
        self.assertEqual(len(requests),1)

    def test_commands_and_secret_rejection(self):
        self.assertIn('16.',main.command('/roadmap'))
        self.assertIn('сохранена',main.command('/work nova Проверить сайт'))
        self.assertIn('queued',main.command('/queue'))
        self.assertIn('приостановлены',main.command('/pause'))
        self.assertIn('возобновлена',main.command('/resume'))
        self.assertIn('$30',main.command('/budget4'))
        self.assertIn('19:00',main.command('/memory kinder'))
        self.assertIn('Отклонено',main.command('/work nova password=mysecret'))
        self.assertIn('Отклонено',main.command('/work inventory Измени код'))

    def test_telegram_event_id_deduplicates_text(self):
        text='/work nova Проверить сайт'
        main.command(text,source_key='telegram:123')
        main.command(text,source_key='telegram:123')
        with queue_worker.connect(self.path) as conn:
            self.assertEqual(conn.execute('SELECT count(*) FROM agent_jobs').fetchone()[0],1)

    def test_budget_atomic_hard_limit_and_usage_settlement(self):
        with queue_worker.connect(self.path) as conn:
            ident=budget_gate.reserve(conn,'nova','developer','not-configured',20_000_000)
            self.assertIsNotNone(ident)
            self.assertIsNone(budget_gate.reserve(conn,'nova','developer','not-configured',11_000_000))
            budget_gate.settle(conn,ident,1_000_000,100,20)
            self.assertEqual(budget_gate.charged(conn),1_000_000)
            with self.assertRaises(ValueError): budget_gate.reserve(conn,'nova','agent','model',1,limit_microusd=31_000_000)
            with self.assertRaises(ValueError): budget_gate.settle(conn,ident,1_000_000,100,20)

    def test_concurrent_budget_reservations_never_exceed_thirty(self):
        def attempt(_):
            with queue_worker.connect(self.path) as conn:
                return budget_gate.reserve(conn,'nova','developer','model',10_000_000)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            results=list(pool.map(attempt,range(5)))
        self.assertEqual(sum(x is not None for x in results),3)
        with queue_worker.connect(self.path) as conn:
            self.assertEqual(budget_gate.charged(conn),30_000_000)

    def test_daily_report_uses_measured_intervals_and_no_model_calls(self):
        with queue_worker.connect(self.path) as conn:
            queue.enqueue(conn,'control','daily_report',{})
        self.assertEqual(queue_worker.run_once(self.path,self.root)['state'],'succeeded')
        with queue_worker.connect(self.path) as conn:
            self.assertIn('Измеренная работа',conn.execute('SELECT reason FROM owner_notifications').fetchone()[0])


if __name__=='__main__': unittest.main()
