import sqlite3
import unittest
from approval import init_approvals, decide
from github_requests import initialize as init_requests, create_request
from controller_v20 import initialize as init_controller
from review_outbox_v21 import initialize as init_outbox
from full_review_workflow_v29 import execute_approved_review

class FakeGitHub:
 def __init__(self): self.calls=[]
 def get_base_sha(self,repo):return "a"*40
 def branch_exists(self,repo,branch):return False
 def create_branch(self,*args):self.calls.append("branch")
 def create_file(self,*args):self.calls.append("file")
 def get_branch_sha(self,*args):return "b"*40
 def create_draft_pr(self,*args):
  self.calls.append("draft")
  return "https://github.com/matrix12345695-afk/ultimate-ai-control/pull/50"
 def fetch_pr(self,repo,url):
  return {"url":url,"draft":True,"merged":False,"head":"ai-review/control-test",
    "head_sha":"b"*40,"base":"main","base_sha":"a"*40,
    "head_repo_full_name":repo}

class ReviewWorkflowTests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(":memory:",isolation_level=None)
  init_approvals(self.db);init_requests(self.db);init_controller(self.db);init_outbox(self.db)
  self.ident,self.approval,_=create_request(self.db,"control","Review test",{"docs/test.md":"SAFE"})
  self.github=FakeGitHub()
 def tearDown(self): self.db.close()
 def run_flow(self, enabled=True, ci=None, sender=None):
  return execute_approved_review(self.db,self.ident,"a"*40,{"docs/test.md":"SAFE"},
    self.github,ci or (lambda sha:[{"name":"Safe unit tests","head_sha":sha,"status":"completed","conclusion":"success"}]),
    sender or (lambda chat,text:True),"123",enabled)
 def test_complete_mock_cycle(self):
  decide(self.db,self.approval,"1","1",True)
  sent=[]
  result=self.run_flow(sender=lambda chat,text:sent.append(text) or True)
  self.assertEqual(result["ci"],"success")
  self.assertEqual(result["notification"],"sent")
  self.assertEqual(self.github.calls,["branch","file","draft"])
  self.assertEqual(len(sent),1)
  self.assertFalse(result["deployed"])
 def test_disabled(self):
  with self.assertRaises(PermissionError):self.run_flow(enabled=False)
  self.assertEqual(self.github.calls,[])
 def test_unapproved(self):
  with self.assertRaises(PermissionError):self.run_flow()
  self.assertEqual(self.github.calls,[])
 def test_changed_ci_sha(self):
  decide(self.db,self.approval,"1","1",True)
  result=self.run_flow(ci=lambda sha:[{"name":"Safe unit tests","head_sha":"c"*40,
    "status":"completed","conclusion":"success"}])
  self.assertEqual(result["ci"],"pending")
