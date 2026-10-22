"""Recheck pending GitHub CI for immutable, verified Draft PRs.

This worker is isolated from the polling bot. It has no merge or deploy method.
CI is accepted only for the same approved request, PR, head commit and branch.
"""
import json

from controller_v20 import record_ci
from github_client_v22 import ALLOWED as REPO
from pr_attestation_v25 import verify_draft_pr
from review_outbox_v21 import queue_ci_notification, pending_messages


def pending_reviews(conn, limit=5):
    if not isinstance(limit, int) or not 1 <= limit <= 20:
        raise ValueError("Invalid batch size")
    return conn.execute(
        """SELECT r.request_id,r.head_sha,r.pr_url,d.base_sha,g.manifest_json
           FROM github_ci_reports AS r
           JOIN dispatch_receipts AS d ON d.request_id=r.request_id
           JOIN github_change_requests AS g ON g.id=r.request_id
           WHERE r.ci_state='pending' AND d.state='completed'
             AND d.result_ref=r.pr_url AND g.project='control'
           ORDER BY r.request_id LIMIT ?""",
        (limit,),
    ).fetchall()


def has_work(conn):
    return bool(pending_reviews(conn, 1) or pending_messages(conn))


def refresh_pending(conn, github, ci_reader, limit=5):
    if not callable(ci_reader) or not callable(getattr(github, "fetch_pr", None)):
        raise ValueError("Trusted read-only transports required")
    outcomes = []
    for request_id, head_sha, pr_url, base_sha, encoded_manifest in pending_reviews(conn, limit):
        manifest = json.loads(encoded_manifest)
        branch = manifest["proposed_branch"]
        # Read remote PR again before trusting any CI data.
        pr = github.fetch_pr(REPO, pr_url)
        if pr.get("url") != pr_url:
            raise PermissionError("GitHub returned a different PR")
        verify_draft_pr(pr, REPO, branch, base_sha, head_sha)
        runs = ci_reader(head_sha)
        state = record_ci(conn, request_id, head_sha, pr_url, runs)
        if state in ("success", "failure"):
            queue_ci_notification(conn, request_id)
        outcomes.append((request_id, state))
    return outcomes
