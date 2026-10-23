import unittest
from executor_preflight_v31 import preflight

def config():
 return {"REVIEW_EXECUTOR_ENABLED":"true","REVIEW_REPO":"matrix12345695-afk/ultimate-ai-control",
 "GITHUB_APP_ID":"123","GITHUB_INSTALLATION_ID":"321",
 "GITHUB_APP_PRIVATE_KEY":"-----BEGIN PRIVATE KEY-----\\nEXAMPLE",
 "REVIEW_ADMIN_CHAT_ID":"123456","REVIEW_TELEGRAM_BOT_TOKEN":"123456:TEST_ONLY_NOT_A_REAL_SECRET"}

class PreflightTests(unittest.TestCase):
 def test_disabled(self):
  d=config();d["REVIEW_EXECUTOR_ENABLED"]="false"
  with self.assertRaises(PermissionError):preflight(d)
 def test_missing_key(self):
  d=config();d["GITHUB_APP_PRIVATE_KEY"]=""
  with self.assertRaises(ValueError):preflight(d)
 def test_block_merge(self):
  d=config();d["REVIEW_ALLOW_MERGE"]="true"
  with self.assertRaises(PermissionError):preflight(d)
 def test_safe_config(self):
  self.assertEqual(preflight(config())["mode"],"draft_only")
