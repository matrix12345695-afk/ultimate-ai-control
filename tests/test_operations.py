import sqlite3,tempfile,unittest
from pathlib import Path
from operations import snapshot_once,backup_status,AlertLimiter
class OperationalTests(unittest.TestCase):
 def test_daily_snapshot(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d); live=root/"db.sqlite"
   with sqlite3.connect(live) as c: c.execute("CREATE TABLE x(id INTEGER)")
   self.assertIsNotNone(snapshot_once(live,root/"backups",now=100000))
   self.assertIsNone(snapshot_once(live,root/"backups",now=100001))
   self.assertIn("1",backup_status(root/"backups"))
 def test_alert_cooldown(self):
  alert=AlertLimiter(60)
  self.assertTrue(alert.should_send("error",now=100))
  self.assertFalse(alert.should_send("error",now=110))
  self.assertTrue(alert.should_send("error",now=161))
if __name__=="__main__":unittest.main()
