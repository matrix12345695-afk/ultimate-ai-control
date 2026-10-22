import json
import pathlib
import tempfile
import unittest

import main
from code_recipes_v48 import new_recipe_task,build_files
from execution_gate import stage
from isolated_development_v31 import prepare,format_report

class IsolatedDevelopmentTests(unittest.TestCase):
    def test_python_syntax_and_diff_for_two_recipes(self):
        for recipe in ("safe-paths","sha-check"):
            task=new_recipe_task(recipe)
            bundle=prepare("control",task)
            self.assertEqual(bundle["manifest"],stage("control",task,build_files(task)))
            self.assertEqual(len(bundle["files"]),2)
            self.assertIn("--- /dev/null",bundle["diff"])
            self.assertIn("+++ b/tests/test_",bundle["diff"])
            self.assertTrue(all(i["syntax"]=="passed" for i in bundle["files"]))
            self.assertFalse(bundle["merge"])
            self.assertFalse(bundle["deploy"])
            self.assertIn("изолированный",format_report(bundle))
    def test_denied_untrusted_task(self):
        for project,task in (("nova","CODE_RECIPE:sha-check:12345678"),
                             ("control","rm -rf /"),("control","CODE_RECIPE:any:12345678")):
            with self.assertRaises(PermissionError):
                prepare(project,task)
    def test_read_only_telegram_inspection(self):
        with tempfile.TemporaryDirectory() as directory:
            old=main.DB
            main.DB=pathlib.Path(directory)/"control.db"
            try:
                self.assertIn("Использование",main.command("/dev31 x"))
                self.assertIn("не найдена",main.command("/dev31 999"))
                msg=main.command("/code_new control safe-paths")
                self.assertIn("Кодовая заявка #1",msg)
                status=main.command("/dev31 1")
                self.assertIn("Python",status)
                self.assertIn("Merge/Deploy: запрещены",status)
                with main.db() as conn:
                    self.assertEqual(conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type=? AND name=?",("table","dispatch_receipts")).fetchone()[0],0)
                    conn.execute("UPDATE github_change_requests SET manifest_json='{}' WHERE id=1")
                    conn.commit()
                self.assertIn("SHA-256",main.command("/dev31 1"))
            finally:
                main.DB=old
if __name__=="__main__":unittest.main()
