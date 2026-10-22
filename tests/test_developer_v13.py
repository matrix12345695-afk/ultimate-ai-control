import unittest
from developer_v13 import prepare,render
class DeveloperTests(unittest.TestCase):
 def test_branch_deterministic(self):
  p=prepare("nova","Improve mobile navigation")
  self.assertEqual(p["proposed_branch"],prepare("nova","Improve mobile navigation")["proposed_branch"])
  self.assertTrue(p["proposed_branch"].startswith("ai-review/nova-"))
  self.assertEqual(p["execution_status"],"NOT_EXECUTED")
 def test_reject_unknown(self):
  with self.assertRaises(ValueError):prepare("other","Task")
 def test_reject_empty(self):
  with self.assertRaises(ValueError):prepare("nova","")
 def test_render(self):
  self.assertIn("без исполнения",render(prepare("control","Improve tests")))
