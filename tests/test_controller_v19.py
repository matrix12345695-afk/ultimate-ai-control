import unittest
import hashlib
from controller_v19 import run_review

class Fake:
 def __init__(self):self.actions=[]
 def get_base_sha(self,repo):return "a"*40
 def branch_exists(self,repo,branch):return False
 def create_branch(self,*args):self.actions.append("branch")
 def create_file(self,*args):self.actions.append("file")
 def get_branch_sha(self,*args):return "b"*40
 def create_draft_pr(self,*args):self.actions.append("pr");return "https://github.com/matrix12345695-afk/ultimate-ai-control/pull/100"

class Tests(unittest.TestCase):
 def manifest(self):
  return {"project":"control","execution_performed":False,
   "branch":"ai-review/control-test","base_sha":"a"*40,
   "mode":"DRAFT_PR_ONLY","merge_allowed":False,"deploy_allowed":False,
   "files":[{"path":"docs/test.md","sha256":hashlib.sha256(b"SAFE").hexdigest(),"bytes":4}]}
 def test_flow(self):
  client=Fake()
  result=run_review(client,self.manifest(),{"docs/test.md":"SAFE"},"a"*40,True)
  self.assertEqual(client.actions,["branch","file","pr"])
  self.assertEqual(result["ci"],"pending_external_check")
  self.assertFalse(result["deployment_performed"])
 def test_reject_unapproved(self):
  client=Fake()
  with self.assertRaises(PermissionError):run_review(client,self.manifest(),{"docs/test.md":"SAFE"},"a"*40)
  self.assertEqual(client.actions,[])
 def test_reject_other_project(self):
  m=self.manifest();m["project"]="nova"
  with self.assertRaises(PermissionError):run_review(Fake(),m,{"docs/test.md":"SAFE"},"a"*40,True)
