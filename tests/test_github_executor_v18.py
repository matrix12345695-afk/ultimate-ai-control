import unittest
import hashlib
from github_executor_v18 import draft_pr

class Fake:
 def __init__(self): self.calls=[]
 def get_base_sha(self,repo): return 'a'*40
 def branch_exists(self,repo,branch): return False
 def create_branch(self,*args): self.calls.append('branch')
 def create_file(self,*args): self.calls.append('file')
 def get_branch_sha(self,*args): return 'b'*40
 def create_draft_pr(self,*args): self.calls.append('pr'); return 'https://github.com/o/r/pull/1'

class TestExecutor(unittest.TestCase):
 def bundle(self):
  return {'branch':'ai-review/control-test','base_sha':'a'*40,'mode':'DRAFT_PR_ONLY','merge_allowed':False,'deploy_allowed':False,'files':[{'path':'docs/a.md','bytes':5,'sha256':hashlib.sha256(b'hello').hexdigest()}]}
 def test_draft(self):
  f=Fake()
  self.assertEqual(draft_pr(f,'o/r',self.bundle(),{'docs/a.md':'hello'},'a'*40,approved=True)['status'],'draft_review')
  self.assertEqual(f.calls,['branch','file','pr'])
 def test_requires_approval(self):
  f=Fake()
  with self.assertRaises(PermissionError): draft_pr(f,'o/r',self.bundle(),{'docs/a.md':'hello'},'a'*40)
  self.assertEqual(f.calls,[])
 def test_reject_changed_file(self):
  with self.assertRaises(ValueError): draft_pr(Fake(),'o/r',self.bundle(),{'docs/a.md':'wrong'},'a'*40,True)
