"""Acceptance tests for Telegram-facing review-only v2.0 adapter."""
import pathlib
import re
import sqlite3
import tempfile
import unittest

import main
from review_bot_v45 import help_text


class TelegramReviewPilotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.saved_db, self.saved_admin = main.DB, main.ADMIN
        main.DB = pathlib.Path(self.temp.name) / "control.db"
        main.ADMIN = "502438855"

    def tearDown(self):
        main.DB, main.ADMIN = self.saved_db, self.saved_admin
        self.temp.cleanup()

    def make_review(self, task="Review release notes"):
        message = main.command("/review_new control " + task)
        self.assertIn("Заявка #1", message)
        match = re.search(r"Одобрение: ([A-Za-z0-9_-]+)", message)
        self.assertIsNotNone(match)
        return match.group(1)

    def test_help_has_explicit_no_write_limit(self):
        reply = main.command("/review")
        self.assertEqual(reply, help_text())
        self.assertIn("НЕ выполняются", reply)

    def test_new_request_pending_status_and_denied_handoff(self):
        approval = self.make_review()
        status = main.command("/review_status 1")
        self.assertIn("Заявка #1", status)
        self.assertIn("Готово к передаче на ручную проверку: нет", status)
        self.assertIn("Отклонено:", main.command("/review_prepare 1 " + "a" * 40))
        with main.db() as conn:
            rows = conn.execute(
                "SELECT COUNT(*) FROM github_change_requests"
            ).fetchone()[0]
            self.assertEqual(rows, 1)
            self.assertEqual(
                conn.execute("SELECT status FROM approvals WHERE id=?", (approval,)).fetchone()[0],
                "pending",
            )

    def test_approved_handoff_must_match_hash_and_never_executes(self):
        approval = self.make_review("Review test docs")
        self.assertIn("Recorded: approved", main.command("/approve " + approval))
        response = main.command("/review_prepare 1 " + "b" * 40)
        self.assertIn("Проверенный пакет", response)
        self.assertIn("GitHub ещё не изменён", response)
        self.assertIn("Готово к передаче на ручную проверку: да",
                      main.command("/review_status 1"))
        self.assertIn("CI ещё не подтверждён", main.command("/review_ci 1"))
        with main.db() as conn:
            self.assertEqual(
                conn.execute("SELECT COUNT(*) FROM dispatch_receipts").fetchone()[0],
                0,
            )
            self.assertEqual(
                conn.execute("SELECT COUNT(*) FROM github_ci_reports").fetchone()[0],
                0,
            )

    def test_rejection_or_bad_inputs_fail_closed(self):
        self.assertIn("Использование", main.command("/review_new nova Not allowlisted"))
        self.assertIn("Недопустимое описание", main.command("/review_new control " + "z" * 301))
        self.assertIn("Использование", main.command("/review_status xyz"))
        approval = self.make_review("Reject this")
        self.assertIn("Recorded: rejected", main.command("/reject " + approval))
        self.assertIn("Отклонено:", main.command("/review_prepare 1 " + "c" * 40))

    def test_genuine_approval_bound_to_exact_file_digest(self):
        approval = self.make_review("Propose safe docs")
        with main.db() as conn:
            row = conn.execute(
                "SELECT manifest_json FROM github_change_requests WHERE id=1"
            ).fetchone()
            self.assertIsNotNone(row)
            conn.execute(
                "UPDATE github_change_requests SET manifest_json=? WHERE id=1",
                ('{"different":"payload"}',),
            )
            conn.commit()
        self.assertIn("Recorded: approved", main.command("/approve " + approval))
        self.assertIn("Отклонено:", main.command("/review_prepare 1 " + "d" * 40))


if __name__ == "__main__":
    unittest.main()
