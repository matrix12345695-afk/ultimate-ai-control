import sqlite3
import unittest
from mailbox_core_v37 import initialize,publish,claim_next,acknowledge,get_receipt

class MailboxTests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(":memory:",isolation_level=None)
  initialize(self.db)
  self.env={"nonce":"a"*48,"sample":"signed envelope"}
 def tearDown(self):self.db.close()
 def test_exchange(self):
  publish(self.db,"a"*48,self.env,"render-producer")
  ident,body=claim_next(self.db,"vps-consumer")
  self.assertEqual(ident,"a"*48)
  self.assertEqual(body,self.env)
  self.assertIsNone(claim_next(self.db,"vps-consumer"))
  acknowledge(self.db,ident,{"signature":"test"},"vps-consumer")
  self.assertEqual(get_receipt(self.db,ident,"render-producer")["signature"],"test")
 def test_denied_and_duplicate(self):
  with self.assertRaises(PermissionError):publish(self.db,"a"*48,self.env,"vps-consumer")
  publish(self.db,"a"*48,self.env,"render-producer")
  with self.assertRaises(PermissionError):publish(self.db,"a"*48,self.env,"render-producer")
  with self.assertRaises(PermissionError):claim_next(self.db,"render-producer")
 def test_ack_requires_claim(self):
  publish(self.db,"a"*48,self.env,"render-producer")
  with self.assertRaises(ValueError):acknowledge(self.db,"a"*48,{"signature":"test"},"vps-consumer")
