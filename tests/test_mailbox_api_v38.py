import sqlite3
import unittest
from mailbox_core_v37 import initialize
from mailbox_api_v38 import MailboxAPI

class APITests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(":memory:",isolation_level=None)
  initialize(self.db)
  self.producer="p"*40;self.consumer="c"*40
  self.api=MailboxAPI(self.db,self.producer,self.consumer)
  self.msg={"nonce":"a"*48}
 def tearDown(self):self.db.close()
 def test_roles(self):
  with self.assertRaises(PermissionError):self.api.submit(self.consumer,"a"*48,self.msg)
  with self.assertRaises(PermissionError):self.api.acquire(self.producer)
  self.api.submit(self.producer,"a"*48,self.msg)
  self.assertEqual(self.api.acquire(self.consumer)[0],"a"*48)
  self.api.confirm(self.consumer,"a"*48,{"signature":"mock"})
  self.assertEqual(self.api.receipt(self.producer,"a"*48)["signature"],"mock")
 def test_separate_secrets(self):
  with self.assertRaises(ValueError):MailboxAPI(self.db,"a"*40,"a"*40)
 def test_bad_token(self):
  with self.assertRaises(PermissionError):self.api.acquire("")
