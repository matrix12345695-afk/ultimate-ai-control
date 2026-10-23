import sqlite3
import unittest
from pr_attestation_v25 import verify_draft_pr,reconciliation_required

class Tests(unittest.TestCase):
 def setUp(self):
  self.repo="matrix12345695-afk/ultimate-ai-control"
  self.pr={"url":"https://github.com/matrix12345695-afk/ultimate-ai-control/pull/21",
    "draft":True,"merged":False,"head":"ai-review/control-abc",
    "head_sha":"b"*40,"base":"main","base_sha":"a"*40,
    "head_repo_full_name":self.repo}
 def test_valid(self):
  self.assertTrue(verify_draft_pr(self.pr,self.repo,"ai-review/control-abc","a"*40,"b"*40)["verified"])
 def test_not_draft(self):
  p=dict(self.pr,draft=False)
  with self.assertRaises(ValueError):verify_draft_pr(p,self.repo,"ai-review/control-abc","a"*40,"b"*40)
 def test_wrong_repo_and_sha(self):
  with self.assertRaises(PermissionError):verify_draft_pr(self.pr,"other/repo","ai-review/control-abc","a"*40,"b"*40)
  with self.assertRaises(ValueError):verify_draft_pr(self.pr,self.repo,"ai-review/control-abc","a"*40,"c"*40)
 def test_receipt(self):
  c=sqlite3.connect(":memory:")
  c.execute("CREATE TABLE dispatch_receipts(request_id INTEGER PRIMARY KEY,state TEXT,result_ref TEXT)")
  c.execute("INSERT INTO dispatch_receipts VALUES(1,'reserved',NULL)")
  self.assertTrue(reconciliation_required(c,1))
  self.assertFalse(reconciliation_required(c,2))
  c.close()
