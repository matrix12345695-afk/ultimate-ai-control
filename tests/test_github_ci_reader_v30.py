import io
import json
import unittest
from github_ci_reader_v30 import GithubCIReader

class Response(io.BytesIO):
 def __enter__(self):return self
 def __exit__(self,*args):self.close()

class CIReaderTests(unittest.TestCase):
 def test_disabled(self):
  with self.assertRaises(PermissionError):GithubCIReader("x"*30)
 def test_filters_other_sha_and_event(self):
  good={"head_sha":"a"*40,"name":"Safe unit tests","event":"pull_request","status":"completed","conclusion":"success"}
  bad=dict(good,head_sha="b"*40)
  bad_event=dict(good,event="push")
  def opener(req,timeout):
   return Response(json.dumps({"workflow_runs":[bad,bad_event,good]}).encode())
  reader=GithubCIReader("x"*30,True,opener)
  self.assertEqual(reader("a"*40),[{"head_sha":"a"*40,"name":"Safe unit tests","status":"completed","conclusion":"success"}])
 def test_invalid_response(self):
  reader=GithubCIReader("x"*30,True,lambda req,timeout:Response(b'{"workflow_runs":{}}'))
  with self.assertRaises(ValueError):reader("a"*40)
 def test_reject_invalid_sha(self):
  reader=GithubCIReader("x"*30,True,lambda *a:None)
  with self.assertRaises(ValueError):reader("main")
