import sqlite3
import unittest
from unittest.mock import patch
from handoff_envelope_v33 import seal,verify_and_reserve

class EnvelopeTests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(":memory:")
  self.key=b"x"*32
  self.packet={"v":1,"issued_at":100,"expires_at":400,"nonce":"f"*48,
     "package":{"request_id":7,"mode":"DRAFT_PR_ONLY","merge_allowed":False,"deploy_allowed":False}}
  import hashlib,hmac
  from handoff_envelope_v33 import canonical
  self.packet["signature"]=hmac.new(self.key,canonical(self.packet),hashlib.sha256).hexdigest()
 def tearDown(self):self.db.close()
 def test_one_time(self):
  p=verify_and_reserve(self.db,self.packet,self.key,now=101)
  self.assertEqual(p["request_id"],7)
  with self.assertRaises(PermissionError):verify_and_reserve(self.db,self.packet,self.key,now=102)
 def test_tamper(self):
  x=dict(self.packet,package=dict(self.packet["package"],request_id=8))
  with self.assertRaises(PermissionError):verify_and_reserve(self.db,x,self.key,now=101)
 def test_expired(self):
  with self.assertRaises(PermissionError):verify_and_reserve(self.db,self.packet,self.key,now=401)
 def test_wrong_key(self):
  with self.assertRaises(PermissionError):verify_and_reserve(self.db,self.packet,b"z"*32,now=101)
