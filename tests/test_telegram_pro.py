import tempfile
import unittest
from pathlib import Path
import main

class TelegramProTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        main.DB=Path(self.tmp.name)/"control.db"
        main.ADMIN="12345"
        main.db().close()
    def tearDown(self):
        self.tmp.cleanup()
    def test_create_status_cancel(self):
        self.assertIn("queued",main.command("/task nova Check website"))
        self.assertIn("[queued]",main.command("/taskstatus 1"))
        self.assertIn("cancelled",main.command("/cancel 1"))
        self.assertIn("[cancelled]",main.command("/tasks"))
    def test_approval_without_request(self):
        self.assertIn("Refused",main.command("/approve invalid"))
    def test_audit(self):
        main.command("/task sap Reconcile sales")
        self.assertIn("task_created",main.command("/audit"))
if __name__=="__main__":
    unittest.main()
