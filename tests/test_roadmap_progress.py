import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import main
import queue_worker
import roadmap
import task_queue as queue


class RoadmapProgressTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/'control.db'
        with queue_worker.connect(self.path) as conn: queue_worker.initialize(conn)

    def tearDown(self): self.temp.cleanup()

    def test_done_label_and_missing_runtime_tables(self):
        with sqlite3.connect(':memory:') as conn:
            roadmap.initialize(conn)
            roadmap.mark(conn,1,'done','verified receipt')
            text=roadmap.describe(conn)
            self.assertIn('1. Уведомления владельцу — ✅ выполнено',text)
            self.assertIn('16.',text)

    def test_committed_worker_outcome_is_visible_without_separate_status_write(self):
        with queue_worker.connect(self.path) as conn:
            ident=queue.enqueue(conn,'nova','check_site',{'target':'nova'})
            roadmap.mark(conn,6,'active','one target only')
        checker=lambda _:dict(target='nova',url='https://novaweb.uz/',healthy=True,detail='HTTP 200')
        queue_worker.run_once(self.path,site_checker=checker)
        with patch.object(main,'DB',self.path): text=main.command('/roadmap')
        self.assertIn('Выполнено проверок доступности: 1',text)
        self.assertIn(f'Последняя работа #{ident}: выполнено',text)
        self.assertIn('6. Мониторинг сайтов и приложений — в работе',text)
        self.assertLess(len(text),3900)

    def test_blocked_or_failed_task_is_never_counted_as_complete(self):
        with queue_worker.connect(self.path) as conn:
            ident=queue.enqueue(conn,'control','plan_change',{'text':'Prepare a feature'})
        queue_worker.run_once(self.path)
        with queue_worker.connect(self.path) as conn:
            text=roadmap.describe(conn)
            self.assertIn('Выполнено заданий: 0. Ожидают решения: 1',text)
            self.assertEqual(conn.execute('SELECT state FROM agent_jobs WHERE id=?',(ident,)).fetchone()[0],'awaiting_owner')
            conn.execute("UPDATE agent_jobs SET kind='review_change',state='failed',result=NULL WHERE id=?",(ident,));conn.commit()
            text=roadmap.describe(conn)
            self.assertIn(f'Последняя работа #{ident}: ошибка',text)
            self.assertIn('Выполнено заданий: 0',text)

    def test_passed_draft_waits_for_owner_and_does_not_complete_developer_stage(self):
        with queue_worker.connect(self.path) as conn:
            ident=queue.enqueue(conn,'control','test_release',{'target':'developer-bundle'})
            conn.execute("UPDATE agent_jobs SET state='awaiting_owner',result=? WHERE id=?",(json.dumps(dict(artifact_id=3,test_status='passed')),ident));conn.commit()
            roadmap.mark(conn,4,'active','live model pending')
            roadmap.mark(conn,5,'active','other stacks pending')
            before=conn.execute('SELECT id,state FROM uac_roadmap').fetchall()
            text=roadmap.describe(conn)
            self.assertIn('тесты выполнены; ожидает согласования',text)
            self.assertIn('4. Агент-разработчик — в работе',text)
            self.assertEqual(before,conn.execute('SELECT id,state FROM uac_roadmap').fetchall())

