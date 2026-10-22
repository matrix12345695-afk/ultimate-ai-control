import sqlite3
import unittest
from approval import init_approvals,decide
from github_requests import initialize,create_request
from handoff_v16 import prepare_handoff,verify_material

BASE="a"*40
class HandoffTests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(":memory:")
  init_approvals(self.db)
  initialize(self.db)
  self.idx,self.approval,_=create_request(self.db,"control","Review docs",{"docs/review.md":"SAFE TEXT"})
 def tearDown(self): self.db.close()
 def test_refuse_without_approval(self):
  with self.assertRaises(PermissionError):prepare_handoff(self.db,self.idx,BASE)
 def test_approved_and_exact_content(self):
  decide(self.db,self.approval,"7","7",True)
  package=prepare_handoff(self.db,self.idx,BASE)
  self.assertTrue(verify_material(package,{"docs/review.md":"SAFE TEXT"},BASE))
  self.assertFalse(verify_material(package,{"docs/review.md":"CHANGED"},BASE))
  self.assertFalse(verify_material(package,{"docs/review.md":"SAFE TEXT"},"b"*40))
  self.assertFalse(package["deploy_allowed"])
 def test_invalid_sha(self):
  with self.assertRaises(ValueError):prepare_handoff(self.db,self.idx,"abc")
 def test_rejected(self):
  decide(self.db,self.approval,"7","7",False)
  with self.assertRaises(PermissionError):prepare_handoff(self.db,self.idx,BASE)
