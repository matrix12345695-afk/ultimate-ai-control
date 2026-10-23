import os
import tempfile
import unittest
from mailbox_local_server_v43 import build_from_environment

class EntryTests(unittest.TestCase):
 def config(self,path):
  return {"MAILBOX_ENABLED":"true","MAILBOX_BIND":"127.0.0.1",
    "MAILBOX_DB_PATH":path,"MAILBOX_PRODUCER_TOKEN":"p"*40,
    "MAILBOX_CONSUMER_TOKEN":"c"*40,"MAILBOX_HANDOFF_KEY_HEX":"68"*32,
    "MAILBOX_RECEIPT_KEY_HEX":"72"*32}
 def test_disabled_default(self):
  with self.assertRaises(PermissionError):build_from_environment({})
 def test_public_binding_denied(self):
  with tempfile.TemporaryDirectory() as folder:
   env=self.config(os.path.join(folder,"db"))
   env["MAILBOX_BIND"]="0.0.0.0"
   with self.assertRaises(PermissionError):build_from_environment(env)
 def test_durable_db_reopens(self):
  with tempfile.TemporaryDirectory() as folder:
   path=os.path.join(folder,"queue.sqlite")
   env=self.config(path)
   db,app=build_from_environment(env)
   db.close()
   db2,app2=build_from_environment(env)
   rows=db2.execute("SELECT name FROM sqlite_master WHERE name='review_mailbox'").fetchall()
   self.assertEqual(rows,[("review_mailbox",)])
   db2.close()
