import os
import unittest
from unittest.mock import patch
import ai_provider

class AITests(unittest.TestCase):
    def test_disabled_by_default(self):
        with patch.dict(os.environ,{"AI_ENABLED":"false"}):
            self.assertIn("disabled",ai_provider.propose("nova","Improve SEO"))
    def test_no_budget_blocks(self):
        with patch.dict(os.environ,{"AI_ENABLED":"true","AI_MONTHLY_BUDGET_USD":"0"}):
            self.assertIn("no approved budget",ai_provider.propose("nova","Improve SEO"))
    def test_secret_is_rejected(self):
        with self.assertRaises(ValueError):
            ai_provider.build_request("nova","password=hello123")
    def test_untrusted_url_blocks(self):
        with patch.dict(os.environ,{"AI_ENABLED":"true","AI_MONTHLY_BUDGET_USD":"10","AI_PROVIDER":"openai_compatible","AI_MODEL":"example","AI_API_KEY":"dummy","AI_ENDPOINT":"http://example.com/chat","AI_ALLOWED_HOSTS":"example.com"}):
            self.assertIn("endpoint not allowlisted",ai_provider.propose("nova","Inspect site"))
if __name__=="__main__":
    unittest.main()
