"""Generated offline recipe smoke tests; review before adoption."""
import unittest
from proposals.review_safe_paths_4fa33d175f438c20 import safe_review_path

class ReviewPathTests(unittest.TestCase):
    def test_allowed(self):
        self.assertTrue(safe_review_path("tests/review_case.py"))
        self.assertTrue(safe_review_path("proposals/new_feature.py"))
    def test_reject_parent_and_hidden(self):
        for path in ("../readme.md", "docs/../a.md", "docs//a.md",
                     "tests/.env", "docs/private-secret.txt",
                     "docs\\file.py", "/etc/passwd", "src/app.py"):
            self.assertFalse(safe_review_path(path), path)
    def test_reject_wrong_types(self):
        self.assertFalse(safe_review_path(None))
        self.assertFalse(safe_review_path(13))

if __name__ == "__main__":
    unittest.main()
