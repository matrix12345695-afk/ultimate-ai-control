import sqlite3
import unittest
from control_v08 import setup
from approval import init_approvals
from diagnostics import snapshot, format_snapshot
class DiagnosticsTests(unittest.TestCase):
 def test_empty(self):
  with sqlite3.connect(":memory:") as conn:
   conn.execute("CREATE TABLE tasks (status TEXT)")
   setup(conn)
   init_approvals(conn)
   data=snapshot(conn)
   self.assertEqual(data["pending_approvals"],0)
   self.assertIn("Диагностика",format_snapshot(data))
 def test_counts(self):
  with sqlite3.connect(":memory:") as conn:
   conn.execute("CREATE TABLE tasks (status TEXT)")
   conn.execute("INSERT INTO tasks VALUES ('queued')")
   setup(conn)
   init_approvals(conn)
   self.assertEqual(snapshot(conn)["tasks"]["queued"],1)
if __name__=="__main__":unittest.main()
