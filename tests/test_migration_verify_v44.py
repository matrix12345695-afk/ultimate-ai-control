import os,sqlite3,tempfile,unittest
from migration_verify_v44 import inspect_database
class VerifyMigration(unittest.TestCase):
 def test_valid_db(self):
  with tempfile.TemporaryDirectory() as folder:
   path=os.path.join(folder,"source.sqlite")
   db=sqlite3.connect(path)
   for table in ("tasks","approvals","github_change_requests"):
    db.execute("CREATE TABLE "+table+" (id INTEGER)")
   db.execute("INSERT INTO tasks VALUES (1)")
   db.commit();db.close()
   result=inspect_database(path)
   self.assertEqual(result["counts"]["tasks"],1)
   self.assertEqual(len(result["sha256"]),64)
 def test_empty_staging_not_accepted(self):
  with tempfile.TemporaryDirectory() as folder:
   path=os.path.join(folder,"staging.sqlite")
   db=sqlite3.connect(path);db.execute("CREATE TABLE staging_meta (k TEXT)");db.close()
   with self.assertRaises(ValueError):inspect_database(path)
