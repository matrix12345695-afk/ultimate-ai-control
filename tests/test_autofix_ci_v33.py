import unittest
from autofix_ci_v33 import validate_fixture

class AutofixCITests(unittest.TestCase):
    def test_compile_after_real_patch(self):
        result=validate_fixture("proposals/review_example.py","answer = 42","missing-final-newline")
        self.assertEqual(result["status"],"passed")
        self.assertTrue(result["tests_passed"])
        self.assertIn("+++ b/",result["diff"])
        self.assertFalse(result["git_write"])
        self.assertFalse(result["merge"])
    def test_noop_fails_closed(self):
        result=validate_fixture("tests/test_review_example.py","answer = 42\n","missing-final-newline")
        self.assertEqual(result["status"],"unchanged")
        self.assertFalse(result["tests_passed"])
    def test_bad_path_rejected(self):
        with self.assertRaises(PermissionError):
            validate_fixture("main.py","x=1","missing-final-newline")
    def test_invalid_source_rejected(self):
        with self.assertRaises(SyntaxError):
            validate_fixture("proposals/review_example.py","def f(:","missing-final-newline")
if __name__=="__main__":unittest.main()
