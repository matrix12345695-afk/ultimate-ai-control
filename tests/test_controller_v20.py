import sqlite3
import unittest
from approval import init_approvals,decide
from github_requests import initialize as init_req, create_request
from dispatch_v17 import reserve_once,record_result
from controller_v20 import initialize,verify_request,record_ci,telegram_report

class ControllerV20Tests(unittest.TestCase):
 def setUp(self):
  self.c=sqlite3.connect(":memory:",isolation_level=None)
  init_approvals(self.c);init_req(self.c);initialize(self.c)
  self.req,self.approval,_=create_request(self.c,"control","Review docs",{"docs/a.md":"Hello"})
  self.sha="a"*40
  self.head="b"*40
  self.url="https://github.com/matrix12345695-afk/ultimate-ai-control/pull/123"
 def tearDown(self):self.c.close()
 def test_reject_unapproved(self):
  with self.assertRaises(PermissionError):verify_request(self.c,self.req,self.sha)
 def test_ci_receipt_and_report(self):
  decide(self.c,self.approval,"123","123",True)
  package=verify_request(self.c,self.req,self.sha)
  self.assertEqual(package["base_sha"],self.sha)
  with self.assertRaises(PermissionError):record_ci(self.c,self.req,self.head,self.url,[])
  reserved=reserve_once(self.c,self.req,self.sha)
  record_result(self.c,self.req,reserved["handoff_sha256"],self.url,True)
  state=record_ci(self.c,self.req,self.head,self.url,[{"head_sha":self.head,"name":"Safe unit tests","status":"completed","conclusion":"success"}])
  self.assertEqual(state,"success")
  self.assertIn("owner approval",telegram_report(self.req,self.url,self.head,state))
 def test_ci_wrong_commit(self):
  decide(self.c,self.approval,"123","123",True)
  reserved=reserve_once(self.c,self.req,self.sha)
  record_result(self.c,self.req,reserved["handoff_sha256"],self.url,True)
  self.assertEqual(record_ci(self.c,self.req,self.head,self.url,[{"head_sha":"c"*40,"name":"Safe unit tests","status":"completed","conclusion":"success"}]),"pending")
