import sqlite3
import unittest
from approval import init_approvals, decide
from github_requests import initialize, create_request
from github_handoff import claim
FILES={"docs/review.md":"review only"}
BASE="a"*40
class HandoffTests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(":memory:")
  init_approvals(self.db)
  initialize(self.db)
  self.ident,self.approval,_=create_request(self.db,"control","Review docs",FILES)
 def tearDown(self):self.db.close()
 def test_cannot_claim_before_approval(self):
  with self.assertRaises(PermissionError):claim(self.db,self.ident,FILES,BASE)
 def test_exact_content_and_single_use(self):
  decide(self.db,self.approval,"42","42",True)
  with self.assertRaises(ValueError):claim(self.db,self.ident,{"docs/review.md":"tampered"},BASE)
  payload=claim(self.db,self.ident,FILES,BASE)
  self.assertEqual(payload["base_commit_sha"],BASE)
  self.assertFalse(payload["github_writes"])
  with self.assertRaises(ValueError):claim(self.db,self.ident,FILES,BASE)
 def test_reject_unpinned_branch(self):
  decide(self.db,self.approval,"42","42",True)
  with self.assertRaises(ValueError):claim(self.db,self.ident,FILES,"main")
