import sqlite3
import unittest
from recovery_v26 import inspect_reserved
class RecoveryTests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(":memory:")
  self.db.execute("CREATE TABLE dispatch_receipts(request_id INTEGER PRIMARY KEY,state TEXT,base_sha TEXT,result_ref TEXT)")
  self.db.execute("CREATE TABLE github_change_requests(id INTEGER PRIMARY KEY,manifest_json TEXT)")
  self.db.execute("INSERT INTO dispatch_receipts VALUES(1,'reserved',?,NULL)",("a"*40,))
  self.db.execute('INSERT INTO github_change_requests VALUES(1,?)',('{"proposed_branch":"ai-review/control-test"}',))
 def tearDown(self):self.db.close()
 def test_no_retry_missing_branch(self):
  self.assertEqual(inspect_reserved(self.db,1,lambda *a:None,lambda *a:None)["status"],"manual_review")
 def test_existing_branch_no_pr(self):
  result=inspect_reserved(self.db,1,lambda *a:{"sha":"b"*40},lambda *a:None)
  self.assertEqual(result["status"],"manual_review")
 def test_valid_pr_operator_required(self):
  def pr(*args):
   return {"url":"https://github.com/matrix12345695-afk/ultimate-ai-control/pull/22","draft":True,"merged":False,"head":"ai-review/control-test","head_sha":"b"*40,"base":"main","base_sha":"a"*40,"head_repo_full_name":"matrix12345695-afk/ultimate-ai-control"}
  result=inspect_reserved(self.db,1,lambda *a:{"sha":"b"*40},pr)
  self.assertEqual(result["status"],"verified_needs_operator")
  self.assertEqual(self.db.execute("SELECT state FROM dispatch_receipts").fetchone()[0],"reserved")
