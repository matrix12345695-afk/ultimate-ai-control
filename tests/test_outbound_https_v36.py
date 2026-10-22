import io
import unittest
from outbound_https_v36 import OutboundChannel,validate_endpoint

class Response(io.BytesIO):
 status=200
 def __enter__(self):return self
 def __exit__(self,*args):self.close()

class Tests(unittest.TestCase):
 def test_disabled(self):
  with self.assertRaises(PermissionError):OutboundChannel("https://example.com/box")
 def test_https_only(self):
  for url in ("http://example.com","https://user:secret@example.com","https://example.com:8080"):
   with self.assertRaises(ValueError):validate_endpoint(url)
 def test_exchange(self):
  calls=[]
  def transport(req,timeout):
   calls.append(req)
   return Response(b'{"receipt":"test"}')
  c=OutboundChannel("https://example.com/box",transport,True)
  self.assertEqual(c.exchange({"nonce":"abc"})["receipt"],"test")
  self.assertEqual(calls[0].get_method(),"POST")
 def test_bad_response(self):
  c=OutboundChannel("https://example.com/box",lambda r,timeout:Response(b"[]"),True)
  with self.assertRaises(ValueError):c.exchange({})
