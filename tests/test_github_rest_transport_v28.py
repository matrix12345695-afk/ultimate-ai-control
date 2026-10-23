import io
import json
import unittest
from github_rest_transport_v28 import GithubTransport

class Response(io.BytesIO):
 def __enter__(self):return self
 def __exit__(self,*args):self.close()

class TransportTests(unittest.TestCase):
 def test_disabled_by_default(self):
  with self.assertRaises(PermissionError):GithubTransport("x"*30)
 def test_base_and_draft(self):
  calls=[]
  def opener(req,timeout):
   calls.append((req.get_method(),req.full_url,req.data))
   if req.full_url.endswith("/git/ref/heads/main"):
    return Response(json.dumps({"object":{"sha":"a"*40}}).encode())
   return Response(json.dumps({"html_url":"https://github.com/matrix12345695-afk/ultimate-ai-control/pull/21"}).encode())
  client=GithubTransport("x"*30,True,opener)
  self.assertEqual(client.get_base_sha("matrix12345695-afk/ultimate-ai-control"),"a"*40)
  self.assertEqual(client.create_draft_pr("matrix12345695-afk/ultimate-ai-control","ai-review/test","a"*40,"b"*40,"Review","Docs"),
      "https://github.com/matrix12345695-afk/ultimate-ai-control/pull/21")
  self.assertTrue(json.loads(calls[1][2])["draft"])
 def test_reject_other_repo(self):
  transport=GithubTransport("x"*30,True,lambda *args:None)
  with self.assertRaises(PermissionError):transport.get_base_sha("other/repo")
  with self.assertRaises(PermissionError):transport.create_branch("matrix12345695-afk/ultimate-ai-control","main","a"*40)
 def test_reject_path_traversal(self):
  transport=GithubTransport("x"*30,True,lambda *args:None)
  with self.assertRaises(ValueError):transport.create_file("matrix12345695-afk/ultimate-ai-control","ai-review/test","docs/../secret","text")
