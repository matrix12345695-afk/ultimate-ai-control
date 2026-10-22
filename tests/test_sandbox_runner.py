import tempfile
import unittest
from pathlib import Path
from sandbox_runner import run_tests

class RunnerTests(unittest.TestCase):
    def test_requires_tests_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                run_tests(directory)
    def test_rejects_oversized_timeout(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory)/"tests").mkdir()
            with self.assertRaises(ValueError):
                run_tests(directory,999)
    def test_runs_clean_suite(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/"tests").mkdir()
            (root/"tests"/"test_ok.py").write_text(
                "import unittest\nclass TestOK(unittest.TestCase):\n def test_ok(self): self.assertEqual(2,2)\n")
            response=run_tests(root,10)
            self.assertEqual(response["status"],"passed")
if __name__=="__main__":
    unittest.main()
