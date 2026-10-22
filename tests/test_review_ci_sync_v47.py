"""Fail-closed CI reconciliation against a real-shaped Draft PR attestation."""
import hashlib
import json
import pathlib
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from approval import init_approvals, decide
from github_requests import initialize as init_requests, create_request
from controller_v20 import initialize as init_controller, record_ci
from review_outbox_v21 import initialize as init_outbox, pending_messages
from dispatch_v17 import reserve_once, record_result
from review_ci_sync_v47 import pending_reviews, refresh_pending, has_work
from review_executor_v46 import run_once
from review_bot_v45 import _document

REPO = "matrix12345695-afk/ultimate-ai-control"
BASE = "a" * 40
HEAD = "b" * 40
URL = "https://github.com/" + REPO + "/pull/21"


class FakeGitHub:
    def __init__(self, branch):
        self.branch = branch
        self.head = HEAD
        self.calls = 0

    def fetch_pr(self, repo, url):
        self.calls += 1
        return {
            "url": url, "draft": True, "merged": False,
            "head": self.branch, "head_sha": self.head,
            "base": "main", "base_sha": BASE,
            "head_repo_full_name": repo
        }


class ReviewCISyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.temp.name)
        self.marker = root / "approval-marker"
        self.marker.touch()
        self.env = root / "agent.env"
        self.env.write_text(
            "TELEGRAM_BOT_TOKEN=1234:fake-test-only-local-token\n"
            "ADMIN_TELEGRAM_ID=502438855\n"
        )
        self.env.chmod(0o600)
        self.conn = sqlite3.connect(":memory:", isolation_level=None)
        init_approvals(self.conn)
        init_requests(self.conn)
        init_controller(self.conn)
        init_outbox(self.conn)
        task = "Review document"
        fn = "proposals/review-" + hashlib.sha256(task.encode()).hexdigest()[:16] + ".md"
        self.ident, approval, manifest = create_request(
            self.conn, "control", task, {fn: _document(task)}
        )
        self.branch = manifest["proposed_branch"]
        decide(self.conn, approval, "502438855", "502438855", True)
        package = reserve_once(self.conn, self.ident, BASE)
        record_result(self.conn, self.ident, package["handoff_sha256"], URL, True)
        record_ci(self.conn, self.ident, HEAD, URL, [])
        self.client = FakeGitHub(self.branch)

    def tearDown(self):
        self.conn.close()
        self.temp.cleanup()

    def test_pending_then_green_updates_db_and_queues_one_notice(self):
        self.assertTrue(has_work(self.conn))
        self.assertEqual(len(pending_reviews(self.conn)), 1)
        result = refresh_pending(self.conn, self.client, lambda sha: [
            {"head_sha": sha, "name": "Safe unit tests",
             "status": "completed", "conclusion": "success"}
        ])
        self.assertEqual(result, [(self.ident, "success")])
        self.assertEqual(self.conn.execute(
            "SELECT ci_state FROM github_ci_reports WHERE request_id=?", (self.ident,)
        ).fetchone()[0], "success")
        self.assertEqual(len(pending_messages(self.conn)), 1)
        self.assertEqual(refresh_pending(self.conn, self.client, lambda sha: []), [])
        self.assertEqual(len(pending_messages(self.conn)), 1)

    def test_pending_ci_does_not_send_false_success(self):
        self.assertEqual(refresh_pending(self.conn, self.client, lambda sha: []),
                         [(self.ident, "pending")])
        self.assertEqual(len(pending_messages(self.conn)), 0)

    def test_wrong_head_or_wrong_base_fails_closed(self):
        self.client.head = "c" * 40
        with self.assertRaises(ValueError):
            refresh_pending(self.conn, self.client, lambda sha: [])
        self.assertEqual(len(pending_reviews(self.conn)), 1)
        self.assertEqual(len(pending_messages(self.conn)), 0)

    def test_not_draft_fails_closed(self):
        class Published(FakeGitHub):
            def fetch_pr(self, repo, url):
                result = super().fetch_pr(repo, url)
                result["draft"] = False
                return result
        with self.assertRaises(ValueError):
            refresh_pending(self.conn, Published(self.branch), lambda sha: [])

    def test_wrong_ci_sha_remains_pending(self):
        result = refresh_pending(self.conn, self.client, lambda sha: [
            {"head_sha": "f" * 40, "name": "Safe unit tests",
             "status": "completed", "conclusion": "success"}
        ])
        self.assertEqual(result, [(self.ident, "pending")])
        self.assertFalse(pending_messages(self.conn))

    def test_automated_recheck_sends_notification(self):
        sent = []
        with patch("review_executor_v46.GithubTransport",
                   side_effect=lambda tok, enabled: self.client), \
             patch("review_executor_v46.GithubCIReader",
                   side_effect=lambda tok, enabled: (
                       lambda sha: [{"head_sha": sha, "name": "Safe unit tests",
                                      "status": "completed", "conclusion": "success"}]
                   )), \
             patch("review_executor_v46.make_sender",
                   side_effect=lambda tok, enabled: (
                       lambda chat, body: sent.append((chat, body)) or True
                   )):
            outcome = run_once(
                self.conn, marker=self.marker, env_path=self.env,
                token_issuer=lambda _: "test-installation-token"
            )
        self.assertIn("CI_SYNC 1 notification=sent", outcome)
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0][0], 502438855)
        self.assertIn("success", sent[0][1])
        self.assertFalse(has_work(self.conn))


if __name__ == "__main__":
    unittest.main()
