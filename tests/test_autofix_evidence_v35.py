import json
import pathlib
import re
import tempfile
import unittest
import main

class AutofixEvidencePersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.old=main.DB
        main.DB=pathlib.Path(self.tmp.name)/"control.db"
    def tearDown(self):
        main.DB=self.old
        self.tmp.cleanup()
    def test_new_report_approval_and_no_pr(self):
        response=main.command("/autofix35_new newline")
        self.assertIn("Пакет исправления #1",response)
        self.assertIn("не создаёт PR",response)
        approval=re.search(r"/approve ([A-Za-z0-9_-]+)",response).group(1)
        status=main.command("/autofix35_status 1")
        self.assertIn("Состояние: pending",status)
        self.assertIn("Поведенческие проверки: 4/4",status)
        self.assertIn("PR не создаётся",status)
        with main.db() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM github_change_requests").fetchone()[0],0)
        self.assertIn("Recorded: approved",main.command("/approve "+approval))
        self.assertIn("Состояние: approved",main.command("/autofix35_status 1"))
        with main.db() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM github_change_requests").fetchone()[0],0)
    def test_report_tamper_denied(self):
        main.command("/autofix35_new whitespace")
        with main.db() as conn:
            conn.execute("UPDATE autofix_evidence_v35 SET report_json='{}' WHERE id=1")
            conn.commit()
        self.assertIn("не совпадает",main.command("/autofix35_status 1"))
    def test_bad_inputs(self):
        self.assertIn("Использование",main.command("/autofix35_new unrestricted"))
        self.assertIn("Использование",main.command("/autofix35_status abc"))
        self.assertIn("Отчёт не найден",main.command("/autofix35_status 2"))
if __name__=="__main__": unittest.main()
