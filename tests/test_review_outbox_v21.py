import sqlite3
import unittest
from review_outbox_v21 import initialize,queue_ci_notification,pending_messages,claim
from controller_v20 import initialize as init_controller

class ReviewOutboxTests(unittest.TestCase):
 def setUp(self):
  self.conn=sqlite3.connect(":memory:")
  init_controller(self.conn);initialize(self.conn)
 def tearDown(self):self.conn.close()
 def test_requires_verified_report(self):
  with self.assertRaises(ValueError):queue_ci_notification(self.conn,1)
 def test_once_per_ci_status(self):
  self.conn.execute("INSERT INTO github_ci_reports VALUES(?,?,?,?,?)",(1,"a"*40,"https://github.com/matrix12345695-afk/ultimate-ai-control/pull/18","success","2026-10-22"))
  self.conn.commit()
  body=queue_ci_notification(self.conn,1)
  self.assertIn("CI: success",body)
  queue_ci_notification(self.conn,1)
  self.assertEqual(len(pending_messages(self.conn)),1)
  self.assertTrue(claim(self.conn,1,"a"*40,"success"))
  self.assertFalse(claim(self.conn,1,"a"*40,"success"))
