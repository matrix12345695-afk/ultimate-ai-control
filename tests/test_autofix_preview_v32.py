import hashlib
import unittest
from autofix_preview_v32 import preview

class AutofixPreviewTests(unittest.TestCase):
    def test_missing_newline_creates_exact_diff(self):
        old="value = 3"
        result=preview("proposals/review_example.py",old,hashlib.sha256(old.encode()).hexdigest(),"missing-final-newline")
        self.assertTrue(result["changed"])
        self.assertEqual(result["proposed_content"],"value = 3\n")
        self.assertIn("+++ b/proposals/review_example.py",result["diff"])
        self.assertFalse(result["git_write"])
        self.assertFalse(result["merge"])
        self.assertFalse(result["deploy"])
    def test_wrong_source_hash_fails(self):
        with self.assertRaises(PermissionError):
            preview("proposals/review_example.py","x=1","a"*64,"missing-final-newline")
    def test_restricted_paths_and_rules(self):
        source="x = 1\n"
        sha=hashlib.sha256(source.encode()).hexdigest()
        for path in ("main.py",".env","../tests/test_review_example.py","tests/test_other.py"):
            with self.assertRaises(PermissionError):
                preview(path,source,sha,"trim-trailing-whitespace")
        with self.assertRaises(PermissionError):
            preview("proposals/review_example.py",source,sha,"eval")
    def test_syntax_errors_are_not_repaired_or_executed(self):
        source="def broken(:\n"
        with self.assertRaises(SyntaxError):
            preview("proposals/review_example.py",source,hashlib.sha256(source.encode()).hexdigest(),"missing-final-newline")
    def test_idempotence(self):
        source="x = 1\n"
        r=preview("tests/test_review_example.py",source,hashlib.sha256(source.encode()).hexdigest(),"missing-final-newline")
        self.assertFalse(r["changed"])
        self.assertEqual(r["diff"],"")
if __name__=="__main__": unittest.main()
