import hashlib,hmac,io,json,sqlite3,time,unittest
from mailbox_core_v37 import initialize
from mailbox_wsgi_v42 import build_verified_app
from handoff_envelope_v33 import canonical
from mutual_receipt_v35 import sign_receipt

class WSGITests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(":memory:",isolation_level=None);initialize(self.db)
  self.p="p"*40;self.c="c"*40;self.h=b"h"*32;self.r=b"r"*32
  self.app=build_verified_app(self.db,self.p,self.c,self.h,self.r)
  self.pkg={"request_id":31,"mode":"DRAFT_PR_ONLY","merge_allowed":False,"deploy_allowed":False}
  self.pkg["handoff_sha256"]=hashlib.sha256(canonical(self.pkg)).hexdigest()
  now=int(time.time())
  self.env={"v":1,"nonce":"a"*48,"issued_at":now,"expires_at":now+300,"package":self.pkg}
  self.env["signature"]=hmac.new(self.h,canonical(self.env),hashlib.sha256).hexdigest()
 def tearDown(self):self.db.close()
 def call(self,path,token,payload):
  raw=json.dumps(payload).encode();status=[]
  environ={"REQUEST_METHOD":"POST","PATH_INFO":path,"HTTP_AUTHORIZATION":"Bearer "+token,
    "CONTENT_LENGTH":str(len(raw)),"wsgi.input":io.BytesIO(raw)}
  obj=json.loads(b"".join(self.app(environ,lambda s,h:status.append(s))))
  return status[0],obj
 def test_verified_flow(self):
  body={"message_id":"a"*48,"envelope":self.env}
  self.assertEqual(self.call("/v1/submit",self.p,body)[0],"201 Created")
  self.assertEqual(self.call("/v1/acquire",self.c,{})[0],"200 OK")
  self.assertEqual(self.call("/v1/confirm",self.c,{"message_id":"a"*48,
    "receipt":sign_receipt(self.pkg,"accepted",self.r)})[0],"200 OK")
  self.assertEqual(self.call("/v1/receipt",self.p,{"message_id":"a"*48})[1]["receipt"]["status"],"accepted")
  self.assertIsNone(self.call("/v1/acquire",self.c,{})[1]["item"])
 def test_forged_envelope(self):
  tampered=dict(self.env,package=dict(self.pkg,request_id=999))
  self.assertEqual(self.call("/v1/submit",self.p,{"message_id":"a"*48,"envelope":tampered})[0],"403 Forbidden")
 def test_wrong_receipt(self):
  self.call("/v1/submit",self.p,{"message_id":"a"*48,"envelope":self.env})
  self.call("/v1/acquire",self.c,{})
  self.assertEqual(self.call("/v1/confirm",self.c,{"message_id":"a"*48,
    "receipt":sign_receipt(self.pkg,"accepted",b"x"*32)})[0],"403 Forbidden")
