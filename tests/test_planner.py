import unittest
from planner import plan,format_plan
class PlannerTests(unittest.TestCase):
 def test_project(self):
  result=plan("nova","Improve website SEO")
  self.assertFalse(result["execution_enabled"])
  self.assertEqual(len(result["steps"]),4)
 def test_sensitive_action(self):
  self.assertEqual(plan("nova","удалить базу")["risk"],"approval_required")
 def test_reject_unknown(self):
  with self.assertRaises(ValueError): plan("unknown","test")
 def test_format(self):
  self.assertIn("preparation only",format_plan(plan("sap","Reconcile exports")))
if __name__=="__main__": unittest.main()
