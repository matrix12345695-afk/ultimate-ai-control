"""Tests for v3.0 review-only model output validation, no model call."""
import json
import unittest
from ai_review_contract_v30 import prepare_task,validate_response,format_plan

GOOD={
 "summary":"Add validation in a review branch",
 "affected_files":["tests/test_review.py"],
 "implementation_steps":["Inspect existing functions","Propose focused change"],
 "tests":["Run unit tests"],
 "risks":["Check regressions"],
}

class ReviewContractTests(unittest.TestCase):
 def test_prepare_task(self):
  item=prepare_task("control","Improve one function")
  self.assertEqual(item["mode"],"REVIEW_ONLY")
  self.assertIn("JSON",item["system"])
 def test_disallowed_project_or_secret(self):
  for project,task in (("other","Do this"),("control",""),("control","x"*1201),
                       ("control","api_key=secretexamplevalue")):
   with self.assertRaises(ValueError):prepare_task(project,task)
 def test_schema_valid_and_format(self):
  result=validate_response(json.dumps(GOOD),{"tests/test_review.py"})
  self.assertIn("только проверка",format_plan(result))
  self.assertIn("Код не изменён",format_plan(result))
 def test_reject_unknown_paths_and_fields(self):
  with self.assertRaises(PermissionError):
   validate_response(json.dumps(GOOD),{"docs/allowed.md"})
  with self.assertRaises(ValueError):
   validate_response(json.dumps(dict(GOOD,execute=True)))
 def test_reject_malformed_output(self):
  for raw in ("hello","[]","{}","x"*10001):
   with self.assertRaises(ValueError):validate_response(raw)
 def test_reject_embedded_secret_or_empty_items(self):
  with self.assertRaises(ValueError):
   validate_response(json.dumps(dict(GOOD,summary="token=privateABC")))
  with self.assertRaises(ValueError):
   validate_response(json.dumps(dict(GOOD,tests=[])))

if __name__=="__main__":unittest.main()
