import pathlib
import sqlite3
import tempfile
import unittest
import main

class AutofixTelegramTests(unittest.TestCase):
    def test_readonly_two_behavior_reports(self):
        for cmd in ("/autofix34 newline","/autofix34 whitespace"):
            report=main.command(cmd)
            self.assertIn("Поведенческие проверки: 4/4",report)
            self.assertIn("SHA-256 отчёта",report)
            self.assertIn("Merge и Deploy запрещены",report)
    def test_validation_does_not_initialize_database(self):
        with tempfile.TemporaryDirectory() as root:
            old=main.DB
            main.DB=pathlib.Path(root)/"never_created.sqlite"
            try:
                main.command("/autofix34 newline")
                self.assertFalse(main.DB.exists())
                self.assertIn("Использование",main.command("/autofix34 unknown"))
            finally:
                main.DB=old
if __name__=="__main__": unittest.main()
