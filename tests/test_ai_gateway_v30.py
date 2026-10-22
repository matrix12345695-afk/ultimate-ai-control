import json
import unittest
from ai_gateway_v30 import (DEFAULT_POLICY,offline_review,validate_policy,
                            validate_endpoint,validate_model_response,validate_task)
from ai_commands_v30 import handle
import main

class Stage30Tests(unittest.TestCase):
    def test_free_offline_plan(self):
        x=offline_review("control","Add tests")
        self.assertEqual(x["provider"],"none")
        self.assertFalse(x["code_changed"])
        self.assertFalse(x["pr_created"])
        self.assertFalse(x["deployed"])
        self.assertIn("Add tests",handle("/ai30_plan control Add tests"))
        self.assertIn("AI Gateway",main.command("/ai30"))
        self.assertIn("AI-модель пока не подключена",main.command("/ai30_plan nova Fix landing page"))

    def test_no_secrets_or_unapproved_projects(self):
        for project,task in (("unknown","test"),("control","token=example_secret"),
                             ("control","sk-"+"1"*20),("control","a"*1501)):
            with self.assertRaises(ValueError):
                validate_task(project,task)
        self.assertIn("отклонено",handle("/ai30_plan control token=example_secret"))

    def test_disabled_provider_and_no_writes(self):
        with self.assertRaises(PermissionError):
            validate_policy(DEFAULT_POLICY)
        policy=dict(DEFAULT_POLICY,enabled=True,network_enabled=True,
                    max_monthly_spend_usd=0,max_calls_per_task=1)
        with self.assertRaises(PermissionError):
            validate_policy(policy)
        policy["max_monthly_spend_usd"]=1
        self.assertTrue(validate_policy(policy))
        policy["allow_deploy"]=True
        with self.assertRaises(PermissionError):
            validate_policy(policy)

    def test_endpoint_allowlist(self):
        self.assertEqual(validate_endpoint("https://api.openai.com/v1/chat/completions"),
                         "https://api.openai.com/v1/chat/completions")
        for url in ("http://api.openai.com/v1/chat/completions",
                    "https://api.openai.com.evil.test/v1/chat/completions",
                    "https://api.openai.com@evil.test/v1/chat/completions",
                    "https://api.openai.com/v1/chat/completions?x=y"):
            with self.assertRaises(PermissionError):
                validate_endpoint(url)

    def test_model_answer_schema(self):
        raw=json.dumps({"summary":"Plan","steps":["Read"],"tests":["Unit"],"risks":["Review"]})
        result=validate_model_response(raw)
        self.assertFalse(result["deployed"])
        for value in ('{"summary":"hello"}',raw.replace("Plan","token=hidden-value")):
            with self.assertRaises(ValueError):
                validate_model_response(value)

if __name__=="__main__":
    unittest.main()
