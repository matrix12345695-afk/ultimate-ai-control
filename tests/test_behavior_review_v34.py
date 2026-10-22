import unittest
from behavior_review_v34 import evidence,review_message

class BehavioralEvidenceTests(unittest.TestCase):
    def test_both_rules_preserve_literal_behavior(self):
        for path in ("proposals/review_example.py","tests/test_review_example.py"):
            for source,rule in (("answer = 42","missing-final-newline"),
                                ("answer = 42   \n","trim-trailing-whitespace")):
                with self.subTest(path=path,rule=rule):
                    report=evidence(path,source,rule)
                    self.assertTrue(report["passed"])
                    self.assertEqual(len(report["tests"]),4)
                    self.assertTrue(all(report["tests"].values()))
                    self.assertEqual(len(report["evidence_sha256"]),64)
                    self.assertIn("согласование",review_message(report))
    def test_wrong_semantics_are_rejected(self):
        with self.assertRaises(ValueError):
            evidence("proposals/review_example.py","answer = 41","missing-final-newline")
    def test_noop_is_rejected(self):
        with self.assertRaises(ValueError):
            evidence("proposals/review_example.py","answer = 42\n","missing-final-newline")
    def test_arbitrary_python_never_executes(self):
        source="__import__('os').system('echo unsafe')"
        with self.assertRaises(PermissionError):
            evidence("proposals/review_example.py",source,"missing-final-newline")
    def test_paths_restricted(self):
        with self.assertRaises(PermissionError):
            evidence("main.py","answer=42","missing-final-newline")
if __name__=="__main__":unittest.main()
