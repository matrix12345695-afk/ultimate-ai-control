import io
import json
import os
import unittest
from unittest.mock import patch
from github_readonly import allowed_repos, repository_summary, command

class FakeResponse(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self,*args): self.close()

class GithubReadonlyTests(unittest.TestCase):
    def test_default_allowlist(self):
        with patch.dict(os.environ, {"GITHUB_READONLY_REPOS": ""}):
            self.assertIn("control", allowed_repos())
    def test_no_arbitrary_repo(self):
        with patch.dict(os.environ, {"GITHUB_READONLY_REPOS": "control=matrix12345695-afk/ultimate-ai-control"}):
            self.assertIn("Unknown repository", repository_summary("other"))
    def test_reject_malformed_allowlist(self):
        with patch.dict(os.environ, {"GITHUB_READONLY_REPOS": "bad=../../private,okay=acme/example"}):
            self.assertEqual(allowed_repos(), {"okay": "acme/example"})
    def test_http_read_only(self):
        seen=[]
        def fake_open(req, timeout):
            seen.append(req)
            return FakeResponse(json.dumps({"full_name":"acme/example","private":True,"default_branch":"main","open_issues_count":2,"pushed_at":"2026-01-01","html_url":"https://github.com/acme/example"}).encode())
        with patch.dict(os.environ, {"GITHUB_READONLY_REPOS":"example=acme/example","GITHUB_READ_TOKEN":""}):
            result=repository_summary("example",opener=fake_open)
        self.assertIn("Visibility: private",result)
        self.assertEqual(seen[0].get_method(),"GET")
    def test_commands(self):
        self.assertIn("control",command("/repos"))
        self.assertIsNone(command("/help"))
if __name__=="__main__":
    unittest.main()
