import unittest
from execution_gate import stage,release_ready

class GateTests(unittest.TestCase):
 def test_manifest(self):
  item=stage("control","Document approval workflow",{"docs/approval.md":"Review steps"})
  self.assertEqual(item["status"],"AWAITING_REVIEW")
  self.assertFalse(item["github_write_performed"])
  self.assertEqual(len(item["files"][0]["sha256"]),64)
 def test_reject_traversal(self):
  with self.assertRaises(ValueError):
   stage("control","bad",{"docs/../.env":"secret"})
 def test_reject_unauthorized_path(self):
  with self.assertRaises(ValueError):
   stage("control","bad",{"main.py":"print('hi')"})
 def test_approval_gate(self):
  item=stage("control","Doc",{"docs/one.md":"Content"})
  self.assertFalse(release_ready(item,False,"success"))
  self.assertFalse(release_ready(item,True,"failure"))
  self.assertTrue(release_ready(item,True,"success"))
