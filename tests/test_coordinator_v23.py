import sqlite3
import unittest
from coordinator_v23 import check_and_queue,notify_admin
from controller_v20 import initialize as init_controller
from review_outbox_v21 import initialize as init_outbox
from dispatch_v17 import initialize as init_dispatch

class CoordinatorTests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(":memory:")
  init_controller(self.db);init_outbox(self.db)
 def tearDown(self):self.db.close()
 def test_disabled(self):
  with self.assertRaises(PermissionError):check_and_queue(self.db,1,"https://github.com/matrix12345695-afk/ultimate-ai-control/pull/1","a"*40,lambda sha:[])
  with self.assertRaises(PermissionError):notify_admin(self.db,lambda *args:True,123)
 def test_no_receipt(self):
  with self.assertRaises(PermissionError):check_and_queue(self.db,1,"https://github.com/matrix12345695-afk/ultimate-ai-control/pull/1","a"*40,lambda sha:[],True)
 def test_missing_admin(self):
  with self.assertRaises(ValueError):notify_admin(self.db,lambda *args:True,"invalid",True)
