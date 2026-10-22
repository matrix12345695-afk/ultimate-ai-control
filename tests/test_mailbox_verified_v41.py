import hashlib,hmac,json,os,sqlite3,tempfile,time,unittest
from mailbox_core_v37 import initialize
from mailbox_verified_v41 import VerifiedMailboxAPI
from handoff_envelope_v33 import canonical
from mutual_receipt_v35 import sign_receipt

class PersistentMailboxTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.path=os.path.join(self.tmp.name,"mailbox.sqlite")
  self.db=sqlite3.connect(self.path,isolation_level=None)
  initialize(self.db)
  self.producer="p"*40;self.consumer="c"*40
  self.key=b"h"*32;self.reply=b"r"*32
  self.api=VerifiedMailboxAPI(self.db,self.producer,self.consumer,self.key,self.reply)
  self.pkg={"request_id":71,"mode":"DRAFT_PR_ONLY","merge_allowed":False,"deploy_allowed":False}
  self.pkg["handoff_sha256"]=hashlib.sha256(canonical(self.pkg)).hexdigest()
  ts=int(time.time())
  self.env={"v":1,"issued_at":ts,"expires_at":ts+300,"nonce":"a"*48,"package":self.pkg}
  self.env["signature"]=hmac.new(self.key,canonical(self.env),hashlib.sha256).hexdigest()
 def tearDown(self):
  self.db.close();self.tmp.cleanup()
 def test_restart_and_signed_ack(self):
  self.api.submit(self.producer,"a"*48,self.env)
  self.db.close()
  self.db=sqlite3.connect(self.path,isolation_level=None)
  self.api=VerifiedMailboxAPI(self.db,self.producer,self.consumer,self.key,self.reply)
  self.assertEqual(self.api.acquire(self.consumer)[0],"a"*48)
  with self.assertRaises(PermissionError):
   self.api.confirm(self.consumer,"a"*48,sign_receipt(self.pkg,"accepted",b"x"*32))
  self.api.confirm(self.consumer,"a"*48,sign_receipt(self.pkg,"accepted",self.reply))
  self.db.close()
  self.db=sqlite3.connect(self.path,isolation_level=None)
  self.api=VerifiedMailboxAPI(self.db,self.producer,self.consumer,self.key,self.reply)
  self.assertEqual(self.api.receipt(self.producer,"a"*48)["status"],"accepted")
  self.assertIsNone(self.api.acquire(self.consumer))
 def test_reject_forgery(self):
  changed=dict(self.env,package=dict(self.pkg,request_id=72))
  with self.assertRaises(PermissionError):self.api.submit(self.producer,"a"*48,changed)
  self.assertIsNone(self.api.acquire(self.consumer))
 def test_replay(self):
  self.api.submit(self.producer,"a"*48,self.env)
  with self.assertRaises(PermissionError):self.api.submit(self.producer,"a"*48,self.env)
