import sqlite3
import unittest
from review_outbox_v21 import initialize as init_outbox
from telegram_delivery_v22 import deliver_next
from github_client_v22 import RestrictedGithub

class TestV22(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(":memory:")
  init_outbox(self.db)
  self.db.execute("INSERT INTO review_outbox VALUES (?,?,?,?,?,?)",(1,"a"*40,"success","Approved CI","pending","2026-10-22"))
  self.db.commit()
 def tearDown(self):self.db.close()
 def test_deliver_once(self):
  sent=[]
  self.assertEqual(deliver_next(self.db,lambda chat,text:sent.append((chat,text)) or True,"123"),"sent")
  self.assertEqual(deliver_next(self.db,lambda *args: True,"123"),"empty")
  self.assertEqual(len(sent),1)
 def test_send_failure_requeues(self):
  with self.assertRaises(RuntimeError):deliver_next(self.db,lambda *args:False,"123")
  self.assertEqual(self.db.execute("SELECT status FROM review_outbox").fetchone()[0],"pending")
 def test_no_admin_blocks(self):
  with self.assertRaises(ValueError):deliver_next(self.db,lambda *args:True,"invalid")
 def test_repo_gate(self):
  g=RestrictedGithub(object())
  with self.assertRaises(PermissionError):g.create_branch("other/repo","ai-review/safe","a"*40)
  with self.assertRaises(PermissionError):g.create_branch("matrix12345695-afk/ultimate-ai-control","main","a"*40)
