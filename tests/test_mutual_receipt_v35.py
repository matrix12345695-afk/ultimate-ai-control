import unittest
from mutual_receipt_v35 import sign_receipt,verify_receipt
class TestMutualReceipts(unittest.TestCase):
 def setUp(self):
  self.package={"handoff_sha256":"a"*64}
  self.receipt=sign_receipt(self.package,"accepted",b"r"*32,now=1000)
 def test_valid(self):
  self.assertEqual(verify_receipt(self.receipt,"a"*64,b"r"*32,now=1000),"accepted")
 def test_other_receiver(self):
  with self.assertRaises(PermissionError):verify_receipt(self.receipt,"a"*64,b"x"*32,now=1000)
 def test_wrong_request(self):
  with self.assertRaises(PermissionError):verify_receipt(self.receipt,"b"*64,b"r"*32,now=1000)
 def test_expiration(self):
  with self.assertRaises(PermissionError):verify_receipt(self.receipt,"a"*64,b"r"*32,now=1201)
 def test_modified_status(self):
  forged=dict(self.receipt,status="rejected")
  with self.assertRaises(PermissionError):verify_receipt(forged,"a"*64,b"r"*32,now=1000)
