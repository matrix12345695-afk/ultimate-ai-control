import io
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
import main
from owner_delivery import deliver_one
from owner_notifications import initialize, initialize_delivery, create, claim_delivery, release_delivery


class OwnerDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/"control.db"
        self.db_patch=patch.object(main,"DB",self.path)
        self.db_patch.start()
        self.connect=main.db
        with self.connect() as conn:
            self.ident=create(conn,"control","decision","Проверка","Нужно решение","Открой чат проекта",event_key="one")

    def tearDown(self):
        self.db_patch.stop()
        self.temp.cleanup()

    def test_receipt_and_inbox_does_not_approve(self):
        calls=[]
        def send(admin,text):
            calls.append(text)
            return {"message_id":123}
        self.assertTrue(deliver_one(self.connect,send,"12345"))
        self.assertFalse(deliver_one(self.connect,send,"12345"))
        self.assertEqual(len(calls),1)
        self.assertIn("Нужно решение",main.command("/owner_inbox"))
        with self.connect() as conn:
            self.assertEqual(conn.execute("SELECT telegram_message_id,state FROM owner_notifications").fetchone(),(123,"pending"))

    def test_backoff_and_retry_after(self):
        def limited(*args):
            raise HTTPError("redacted",429,"limited",{},io.BytesIO(json.dumps({"parameters":{"retry_after":3600}}).encode()))
        self.assertFalse(deliver_one(self.connect,limited,"12345"))
        with self.connect() as conn:
            self.assertIsNone(claim_delivery(conn))
            retry=conn.execute("SELECT next_attempt_at FROM owner_notifications").fetchone()[0]
            self.assertGreater(datetime.fromisoformat(retry),datetime.now(timezone.utc)+timedelta(seconds=3500))

    def test_permanent_failure_does_not_block_other_messages(self):
        def blocked(*args):
            raise HTTPError("redacted",403,"blocked",{},io.BytesIO(b"{}"))
        self.assertFalse(deliver_one(self.connect,blocked,"12345"))
        with self.connect() as conn:
            other=create(conn,"nova","info","Другая задача","Готова","Проверь")
            self.assertEqual(claim_delivery(conn)[0],other)
            self.assertEqual(conn.execute("SELECT delivery_error FROM owner_notifications WHERE id=?",(self.ident,)).fetchone()[0],"HTTP_403")

    def test_event_key_is_idempotent(self):
        with self.connect() as conn:
            again=create(conn,"control","decision","Проверка","Нужно решение","Открой чат проекта",event_key="one")
            self.assertEqual(again,self.ident)
            self.assertEqual(conn.execute("SELECT count(*) FROM owner_notifications").fetchone()[0],1)

    def test_legacy_migration_and_crash_recovery(self):
        conn=sqlite3.connect(":memory:")
        initialize(conn)
        initialize_delivery(conn)
        create(conn,"control","info","Title","Reason","Action")
        then=datetime.now(timezone.utc)-timedelta(minutes=6)
        self.assertIsNotNone(claim_delivery(conn,now=then))
        self.assertIsNotNone(claim_delivery(conn))
        conn.close()

    def test_failed_receipt_is_not_delivery_and_attempts_are_bounded(self):
        self.assertFalse(deliver_one(self.connect,lambda *a: {},"12345"))
        with self.connect() as conn:
            conn.execute("UPDATE owner_notifications SET delivery_attempts=8")
            conn.commit()
            release_delivery(conn,self.ident)
            self.assertIsNone(claim_delivery(conn,now=datetime.now(timezone.utc)+timedelta(days=3)))
            self.assertIsNotNone(conn.execute("SELECT delivery_failed_at FROM owner_notifications").fetchone()[0])

    def test_real_monitor_event_is_deduplicated(self):
        for _ in range(2): main.owner_event("nova","critical","Сайт недоступен","HTTP 500","Проверь /check")
        with self.connect() as conn:
            self.assertEqual(conn.execute("SELECT count(*) FROM owner_notifications WHERE project='nova'").fetchone()[0],1)


if __name__=="__main__": unittest.main()
