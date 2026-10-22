import sqlite3, unittest
from control_v08 import setup,reserve,budget_status,save_proposal,list_proposals,proposal_detail
class ControlTest(unittest.TestCase):
 def setUp(self):
  self.conn=sqlite3.connect(":memory:")
  setup(self.conn)
 def tearDown(self): self.conn.close()
 def test_zero_budget(self):
  self.assertIsNone(reserve(self.conn,0,1))
 def test_budget_cap(self):
  self.assertIsNotNone(reserve(self.conn,15,10))
  self.assertIsNone(reserve(self.conn,15,10))
  self.assertIn("remaining: 5",budget_status(self.conn,15))
 def test_proposal(self):
  key=save_proposal(self.conn,"nova","Improve SEO","Review metadata")
  self.assertIn(key,list_proposals(self.conn))
  self.assertIn("SHA256:",proposal_detail(self.conn,key))
 def test_missing(self):
  self.assertEqual(proposal_detail(self.conn,"bad"),"Proposal not found.")
if __name__=="__main__":unittest.main()
