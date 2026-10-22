import sqlite3
import unittest
from approval import init_approvals,decide
from github_requests import initialize as init_requests,create_request
from controller_v20 import initialize as init_controller
from external_runner_v24 import submit_review

class Transport:
 def __init__(self):self.calls=[]
 def get_base_sha(self,r):return "a"*40
 def branch_exists(self,r,b):return False
 def create_branch(self,*x):self.calls.append("branch")
 def create_file(self,*x):self.calls.append("file")
 def get_branch_sha(self,*x):return "b"*40
 def create_draft_pr(self,*x):self.calls.append("draft");return "https://github.com/matrix12345695-afk/ultimate-ai-control/pull/20"
 def fetch_pr(self,repo,url):
  return {"url":url,"draft":True,"merged":False,"head":"ai-review/control-test","head_sha":"b"*40,"base":"main","base_sha":"a"*40,"head_repo_full_name":repo}

class RunnerTests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(":memory:",isolation_level=None)
  init_approvals(self.db);init_requests(self.db);init_controller(self.db)
  self.id,self.approval,_=create_request(self.db,"control","Test",{"docs/test.md":"SAFE"})
  self.t=Transport()
 def tearDown(self):self.db.close()
 def test_requires_enable_and_approval(self):
  with self.assertRaises(PermissionError):submit_review(self.db,self.id,"a"*40,{"docs/test.md":"SAFE"},self.t)
  with self.assertRaises(PermissionError):submit_review(self.db,self.id,"a"*40,{"docs/test.md":"SAFE"},self.t,True)
  self.assertEqual(self.t.calls,[])
 def test_approved_draft_and_replay(self):
  decide(self.db,self.approval,"1","1",True)
  result=submit_review(self.db,self.id,"a"*40,{"docs/test.md":"SAFE"},self.t,True)
  self.assertEqual(result["status"],"draft_review")
  self.assertEqual(self.t.calls,["branch","file","draft"])
  with self.assertRaises(ValueError):submit_review(self.db,self.id,"a"*40,{"docs/test.md":"SAFE"},self.t,True)
 def test_wrong_content(self):
  decide(self.db,self.approval,"1","1",True)
  with self.assertRaises(ValueError):submit_review(self.db,self.id,"a"*40,{"docs/test.md":"EVIL"},self.t,True)
  self.assertEqual(self.t.calls,[])
