import sqlite3
import tempfile
import unittest
from pathlib import Path
from backup import backup_database,verify_restore_copy

class BackupTests(unittest.TestCase):
 def test_backup_restore(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   live=root/"live.sqlite3"
   with sqlite3.connect(live) as db:
    db.execute("CREATE TABLE jobs(id INTEGER)")
    db.execute("INSERT INTO jobs VALUES (12)")
   backup=backup_database(live,root/"backups")
   self.assertTrue(verify_restore_copy(backup))
   with sqlite3.connect(backup) as db:
    self.assertEqual(db.execute("SELECT id FROM jobs").fetchone()[0],12)
 def test_missing_database(self):
  with tempfile.TemporaryDirectory() as tmp:
   with self.assertRaises(FileNotFoundError):
    backup_database(Path(tmp)/"none.db",Path(tmp)/"backups")
if __name__=="__main__":unittest.main()
