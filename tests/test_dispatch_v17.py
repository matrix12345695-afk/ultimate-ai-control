import sqlite3
import unittest
from approval import init_approvals,decide
from github_requests import initialize as init_requests,create_request
from dispatch_v17 import initialize,reserve_once,record_result

class DispatchTests(unittest.TestCase):
 def setUp(self):
  self.c=sqlite3.connect(":memory:",isolation_level=None)
  init_approvals(self.c)
  init_requests(self.c)
  initialize(self.c)
  self.ident,self.approval,_=create_request(self.c,"control","Docs",{"docs/review.md":"Safe"})
 def tearDown(self):self.c.close()
 def test_requires_approval(self):
  with self.assertRaises(PermissionError):reserve_once(self.c,self.ident,"a"*40)
 def test_one_time_receipt(self):
  decide(self.c,self.approval,"7","7",True)
  p=reserve_once(self.c,self.ident,"a"*40)
  with self.assertRaises(ValueError):reserve_once(self.c,self.ident,"a"*40)
  self.assertEqual(record_result(self.c,self.ident,p["handoff_sha256"],"https://github.com/acme/example/pull/1",True),"completed")
  with self.assertRaises(ValueError):record_result(self.c,self.ident,p["handoff_sha256"],"https://github.com/acme/example/pull/1",True)
 def test_block_untrusted_ref(self):
  decide(self.c,self.approval,"7","7",True)
  p=reserve_once(self.c,self.ident,"a"*40)
  with self.assertRaises(ValueError):record_result(self.c,self.ident,p["handoff_sha256"],"https://evil.invalid/pull/1",True)
