import io
import json
import unittest
from telegram_http_sender_v27 import make_sender

class FakeResponse(io.BytesIO):
 def __enter__(self):return self
 def __exit__(self,*args):self.close()

class TestSender(unittest.TestCase):
 def test_default_disabled(self):
  with self.assertRaises(PermissionError):make_sender("1"*30)
 def test_success(self):
  calls=[]
  def opener(request,timeout):
   calls.append((request.full_url,request.data))
   return FakeResponse(json.dumps({"ok":True,"result":{"message_id":12}}).encode())
  send=make_sender("1"*30,True,opener)
  self.assertTrue(send(123,"CI passed"))
  self.assertEqual(json.loads(calls[0][1])["chat_id"],123)
 def test_bad_acknowledgement(self):
  send=make_sender("1"*30,True,lambda r,timeout:FakeResponse(b'{"ok":false}'))
  self.assertFalse(send(123,"CI failed"))
 def test_invalid_chat(self):
  send=make_sender("1"*30,True,lambda *args:None)
  with self.assertRaises(ValueError):send(0,"No")
