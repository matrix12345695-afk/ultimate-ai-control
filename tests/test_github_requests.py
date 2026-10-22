import sqlite3
import unittest
from approval import init_approvals,decide
from github_requests import initialize,create_request,describe
class TestGithubRequests(unittest.TestCase):
 def setUp(self):
  self.c=sqlite3.connect(":memory:")
  init_approvals(self.c)
  initialize(self.c)
 def tearDown(self): self.c.close()
 def test_proposal_and_approval(self):
  ident,approval,manifest=create_request(self.c,"control","Review docs",{"docs/review.md":"Approved text"})
  self.assertIn("Готово к передаче на ручную проверку: нет",describe(self.c,ident))
  decide(self.c,approval,"123","123",True)
  self.assertIn("Готово к передаче на ручную проверку: да",describe(self.c,ident))
 def test_multiple_requests(self):
  a=create_request(self.c,"control","First",{"docs/first.md":"First"})
  b=create_request(self.c,"control","Second",{"docs/second.md":"Second"})
  self.assertNotEqual(a[0],b[0])
  self.assertNotEqual(a[1],b[1])
 def test_missing(self):
  self.assertIn("не найдена",describe(self.c,500))
