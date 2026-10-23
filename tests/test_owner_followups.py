from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import main
import owner_followups as followups
import owner_notifications as notes
import queue_worker
import roadmap
import telegram_menu


class OwnerFollowupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)/'control.db'
        self.conn = queue_worker.connect(self.path)
        queue_worker.initialize(self.conn)

    def tearDown(self):
        self.conn.close()
        self.temp.cleanup()

    def note(self,kind='decision',label='review',**kwargs):
        return notes.create(self.conn,'control',kind,label,'Reason for '+label,'Action for '+label,**kwargs)

    def test_reading_preserves_inbox_and_does_not_create_notifications_or_enable_setup(self):
        roadmap.set_setting(self.conn,'provider_setup_deferred','true')
        key = self.note(label='API',event_key='developer-private-key-setup-v1')
        notes.resolve(self.conn,key)
        critical = self.note('critical','Sandbox failed')
        decision = self.note(label='Version review')
        notes.mark_delivered(self.conn,decision,message_id=913)
        before = self.conn.total_changes
        result = followups.describe(self.conn)
        self.assertIn('Отложено тобой: подключение API',result)
        self.assertIn('Нерешённых критических запросов: 1',result)
        self.assertLess(result.index(f'#{critical}'),result.index(f'#{decision}'))
        self.assertNotIn('API\nПричина',result)
        self.assertIn('отложено владельцем; подключение API не выполнено',followups.detail(self.conn,key))
        self.assertIn('сообщение 913',followups.detail(self.conn,decision))
        self.assertEqual(self.conn.total_changes,before)
        self.assertEqual(self.conn.execute('SELECT id,state FROM owner_notifications ORDER BY id').fetchall(),[(key,'resolved'),(critical,'pending'),(decision,'pending')])

    def test_plan_shows_verified_followup_component_without_completing_memory_stage(self):
        roadmap.mark(self.conn,12,'active','Evidence-linked memory remains in progress')
        roadmap.set_setting(self.conn,'owner_followups_verified_release','a'*40)
        result = roadmap.describe(self.conn)
        self.assertIn('12. Память проектов — в работе',result)
        self.assertIn('Список отложенных действий владельца проверен',result)

    def test_pagination_reaches_all_decisions_and_prioritizes_critical(self):
        decisions = [self.note(label=f'Decision{i}') for i in range(9)]
        critical = self.note('critical','Critical')
        info = self.note('info','Informational')
        resolved = self.note(label='Already closed')
        notes.resolve(self.conn,resolved)
        pages = [followups.describe(self.conn,i) for i in range(1,4)]
        self.assertIn(f'Критическое #{critical}',pages[0])
        for ident in decisions+[critical]:
            self.assertEqual(sum(f'/owner_item {ident}.' in text for text in pages),1)
        self.assertTrue(all(f'/owner_item {info}.' not in text and f'/owner_item {resolved}.' not in text for text in pages))
        self.assertIn('/owner_later 2',pages[0])
        self.assertIn('Такой страницы нет',followups.describe(self.conn,4))

    def test_compact_pages_are_bounded_and_detail_preserves_complete_action(self):
        action = 'Действие '*55
        ids = [notes.create(self.conn,'П'*500,'decision','Т'*500,'П'*500,action) for _ in range(4)]
        self.assertLessEqual(len(followups.describe(self.conn)),3900)
        self.assertIn(action.strip(),followups.detail(self.conn,ids[-1]))
        self.assertLessEqual(len(followups.detail(self.conn,ids[-1])),3900)

    def test_optional_chat_followup_tracks_persisted_binding_and_setup_not_invented(self):
        self.assertIn('Позже, по желанию',followups.describe(self.conn))
        self.assertNotIn('Отложено тобой',followups.describe(self.conn))
        roadmap.set_setting(self.conn,'current_chat_url','https://chatgpt.com/c/example')
        self.assertNotIn('/chat_bind',followups.describe(self.conn))
        self.assertIn('Запрос не найден',followups.detail(self.conn,99))

    def test_commands_reject_invalid_unbounded_numbers_and_route_button(self):
        with patch.object(main,'DB',self.path):
            for value in ('0','-1','+1','01','١','９','1'*200,'9223372036854775808'):
                self.assertIn('Отклонено',main.command('/owner_item '+value))
                self.assertIn('Отклонено',main.command('/owner_later '+value))
            self.assertIn('Использование',main.command('/owner_item'))
            self.assertIn('Использование',main.command('/owner_later 1 extra'))
            self.assertIn('сохранено в журнале',main.command('/owner_later'))
        self.assertEqual(telegram_menu.route('📌 Для владельца'),'/owner_later')
        for value in (True,None,0,-1,1.0):
            with self.assertRaises(ValueError): followups.detail(self.conn,value)
            with self.assertRaises(ValueError): followups.describe(self.conn,value)

    def test_later_status_survives_reopening_database(self):
        roadmap.set_setting(self.conn,'provider_setup_deferred','true')
        ident = self.note(label='Retained request')
        notes.mark_delivered(self.conn,ident,message_id=914)
        with queue_worker.connect(self.path) as reopened:
            self.assertIn('Отложено тобой',followups.describe(reopened))
            self.assertIn('сообщение 914',followups.detail(reopened,ident))
