import io
import json
import sqlite3
import unittest
from mailbox_core_v37 import initialize
from mailbox_api_v38 import MailboxAPI
from mailbox_http_v39 import MailboxHTTP

class HTTPTests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(":memory:",isolation_level=None)
  initialize(self.db)
  self.p="p"*40;self.c="c"*40
  self.app=MailboxHTTP(MailboxAPI(self.db,self.p,self.c))
 def tearDown(self):self.db.close()
 def invoke(self,route,token,body):
  wire=json.dumps(body).encode();status=[]
  env={"REQUEST_METHOD":"POST","PATH_INFO":route,"HTTP_AUTHORIZATION":"Bearer "+token,
       "CONTENT_LENGTH":str(len(wire)),"wsgi.input":io.BytesIO(wire)}
  data=b"".join(self.app(env,lambda code,headers:status.append(code)))
  return status[0],json.loads(data)
 def test_exchange(self):
  msg="a"*48
  self.assertEqual(self.invoke("/v1/submit",self.p,{"message_id":msg,"envelope":{"nonce":msg}})[0],"201 Created")
  self.assertEqual(self.invoke("/v1/acquire",self.c,{})[1]["item"]["message_id"],msg)
  self.assertEqual(self.invoke("/v1/confirm",self.c,{"message_id":msg,"receipt":{"signature":"test"}})[0],"200 OK")
  self.assertEqual(self.invoke("/v1/receipt",self.p,{"message_id":msg})[1]["receipt"]["signature"],"test")
 def test_roles(self):
  status,_=self.invoke("/v1/submit",self.c,{"message_id":"a"*48,"envelope":{"nonce":"a"*48}})
  self.assertEqual(status,"403 Forbidden")
 def test_replay_denied(self):
  body={"message_id":"a"*48,"envelope":{"nonce":"a"*48}}
  self.invoke("/v1/submit",self.p,body)
  self.assertEqual(self.invoke("/v1/submit",self.p,body)[0],"403 Forbidden")
