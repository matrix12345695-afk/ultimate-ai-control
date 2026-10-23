"""Tests for disabled GitHub App worker, deterministic content, replay avoidance."""
import base64
import json
import os
import pathlib
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from approval import init_approvals, decide
from github_requests import initialize as init_requests, create_request
from controller_v20 import initialize as init_controller
from review_bot_v45 import _document
from review_executor_v46 import exact_files, find_pending, run_once
from github_app_auth_v46 import make_jwt


class ReviewExecutorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.db = sqlite3.connect(":memory:", isolation_level=None)
        init_approvals(self.db)
        init_requests(self.db)
        init_controller(self.db)
        self.id, self.approval, self.manifest = create_request(
            self.db, "control", "Improve safe documentation",
            {"proposals/review-57f.md": _document("Improve safe documentation")},
        )
        # This manually made proposal intentionally does not match deterministic
        # v45 path and must never be dispatched.
        self.marker = self.root / "review-executor-activation-approved"
        self.env = self.root / "agent.env"
        self.env.write_text("TELEGRAM_BOT_TOKEN=1234:example-very-long-token-1234\nADMIN_TELEGRAM_ID=502438855\n")
        self.env.chmod(0o600)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_unarmed_executor_does_nothing(self):
        with patch("review_executor_v46.dispatch", side_effect=AssertionError("called")):
            self.assertEqual(run_once(self.db, marker=self.marker, env_path=self.env), "DISABLED")

    def test_exact_files_rejects_other_manifest_and_project(self):
        raw = json.dumps(self.manifest)
        with self.assertRaises(PermissionError):
            exact_files("control", "Improve safe documentation", raw)
        with self.assertRaises(PermissionError):
            exact_files("nova", "Improve safe documentation", raw)

    def test_approved_request_appears_but_wrong_manifest_still_denied(self):
        self.assertIsNone(find_pending(self.db))
        decide(self.db, self.approval, "502438855", "502438855", True)
        self.assertEqual(find_pending(self.db), self.id)
        self.marker.touch(mode=0o600)
        with patch("review_executor_v46.dispatch", side_effect=PermissionError("not executable")):
            with self.assertRaises(PermissionError):
                run_once(self.db, marker=self.marker, env_path=self.env,
                         token_issuer=lambda key: "temporary-token")
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM dispatch_receipts").fetchone()[0], 0)

    def test_valid_v45_request_and_receipt_avoid_replay(self):
        import hashlib
        task = "One approved review"
        path = "proposals/review-" + hashlib.sha256(task.encode()).hexdigest()[:16] + ".md"
        ident, aid, manifest = create_request(self.db, "control", task, {path: _document(task)})
        files = exact_files("control", task, json.dumps(manifest))
        self.assertEqual(files, {path: _document(task)})
        decide(self.db, aid, "502438855", "502438855", True)
        self.marker.touch(mode=0o600)
        with patch("review_executor_v46.dispatch", return_value={"draft_pr": "https://github.com/example/pr/2"}):
            reply = run_once(self.db, marker=self.marker, env_path=self.env,
                             token_issuer=lambda key: "temporary-token")
        self.assertIn("DRAFT_PR", reply)
        self.assertIn("DRAFT_PR " + str(ident) + " ", reply)
        # A reserved request is invisible to the automatic next-item selector.
        self.db.execute("""INSERT INTO dispatch_receipts VALUES(
            ?, 'sha-test', ?, 'reserved', ?, NULL)""", (self.id, "a"*40, "2026-10-22"))
        self.assertEqual(find_pending(self.db), ident)


class GitHubAppAuthTests(unittest.TestCase):
    def test_fingerprintless_jwt_shape_without_real_private_key(self):
        with tempfile.TemporaryDirectory() as folder:
            file = pathlib.Path(folder) / "app.pem"
            file.write_text("x" * 400)
            file.chmod(0o600)
            token = make_jwt(file, now=1700000000, signer=lambda path, data: b"fake-rsa-signature")
            parts = token.split(".")
            self.assertEqual(len(parts), 3)
            encoded = parts[1] + "=" * ((-len(parts[1])) % 4)
            payload = json.loads(base64.urlsafe_b64decode(encoded))
            self.assertEqual(payload["iss"], 5424384)
            self.assertEqual(payload["exp"]-payload["iat"], 510)
            file.chmod(0o644)
            with self.assertRaises(PermissionError):
                make_jwt(file, signer=lambda path, data: b"fake")


if __name__ == "__main__":
    unittest.main()
