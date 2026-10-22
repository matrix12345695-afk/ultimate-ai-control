"""Isolated opt-in GitHub review worker for already approved Telegram requests.

Only the pre-approved, deterministic proposals/review-*.md content is allowed.
Never merges, deploys or sends paid AI requests. Keep this out of main.py.
"""
import hashlib
import json
import os
import pathlib
import sqlite3
import stat
import sys
from datetime import datetime, timezone

from controller_v20 import initialize as init_controller
from github_ci_reader_v30 import GithubCIReader
from github_rest_transport_v28 import GithubTransport
from github_app_auth_v46 import installation_token
from review_bot_v45 import _document
from review_outbox_v21 import initialize as init_outbox
from full_review_workflow_v29 import execute_approved_review
from telegram_http_sender_v27 import make_sender
from telegram_delivery_v22 import deliver_next
from review_ci_sync_v47 import has_work as has_ci_work, refresh_pending
from review_outbox_v21 import pending_messages

BASE = pathlib.Path.home()
DATA = BASE / ".ultimate-review-data" / "live"
CREDENTIALS = BASE / ".config" / "ultimate-review"
REVIEW_KEY = CREDENTIALS / "github-app.pem"
ACTIVATION = DATA / "review-executor-activation-approved"


def local_env(path):
    p = pathlib.Path(path)
    info = p.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
        raise PermissionError("Local configuration is not owned by the runner")
    if stat.S_IMODE(info.st_mode) != 0o600:
        raise PermissionError("Local configuration permissions must be 600")
    data = dict(line.split("=", 1) for line in p.read_text().splitlines() if "=" in line)
    if data.get("ADMIN_TELEGRAM_ID") != "502438855":
        raise PermissionError("Administrator mismatch")
    return data


def exact_files(project, task, raw_manifest):
    if project != "control" or not isinstance(task, str) or not 1 <= len(task) <= 300:
        raise PermissionError("Only verified control review requests can execute")
    manifest = json.loads(raw_manifest)
    digest = hashlib.sha256(task.encode("utf-8")).hexdigest()[:16]
    path = "proposals/review-" + digest + ".md"
    content = _document(task)
    expected = [{"path": path, "sha256": hashlib.sha256(content.encode()).hexdigest(), "bytes": len(content.encode())}]
    if manifest.get("project") != "control" or manifest.get("files") != expected:
        raise PermissionError("Requested file no longer matches the approved content")
    return {path: content}


def find_pending(conn):
    row = conn.execute("""SELECT g.id FROM github_change_requests AS g
      JOIN approvals AS a ON a.id=g.approval_id
      LEFT JOIN dispatch_receipts AS d ON d.request_id=g.id
      WHERE g.project='control' AND g.status='awaiting_review'
        AND a.status='approved' AND a.expires_at>?
        AND d.request_id IS NULL
      ORDER BY g.id LIMIT 1""", (datetime.now(timezone.utc).isoformat(),)).fetchone()
    return int(row[0]) if row else None


def dispatch(conn, request_id, token, telegram_token, admin_id,
             github_factory=GithubTransport, ci_factory=GithubCIReader, send_factory=make_sender):
    row = conn.execute(
        "SELECT project,task,manifest_json FROM github_change_requests WHERE id=?",
        (request_id,),
    ).fetchone()
    if not row:
        raise ValueError("Unknown request")
    files = exact_files(*row)
    github = github_factory(token, enabled=True)
    base_sha = github.get_base_sha("matrix12345695-afk/ultimate-ai-control")
    ci_reader = ci_factory(token, enabled=True)
    sender = send_factory(telegram_token, enabled=True)
    return execute_approved_review(
        conn, request_id, base_sha, files, github,
        ci_reader, sender, admin_id, enabled=True,
    )


def run_once(connection, marker=ACTIVATION, key_path=REVIEW_KEY,
             env_path=CREDENTIALS / "agent.env", token_issuer=installation_token):
    if not pathlib.Path(marker).is_file():
        return "DISABLED"
    cfg = local_env(env_path)
    init_controller(connection)
    init_outbox(connection)
    ident = find_pending(connection)
    if ident is not None:
        token = token_issuer(key_path)
        result = dispatch(connection, ident, token, cfg["TELEGRAM_BOT_TOKEN"], cfg["ADMIN_TELEGRAM_ID"])
        return "DRAFT_PR " + str(ident) + " " + result["draft_pr"]
    if not has_ci_work(connection):
        return "EMPTY"
    token = token_issuer(key_path)
    github = GithubTransport(token, enabled=True)
    ci_reader = GithubCIReader(token, enabled=True)
    reports = refresh_pending(connection, github, ci_reader)
    delivery = "none"
    if pending_messages(connection):
        sender = make_sender(cfg["TELEGRAM_BOT_TOKEN"], enabled=True)
        delivery = deliver_next(connection, sender, cfg["ADMIN_TELEGRAM_ID"])
    return "CI_SYNC " + str(len(reports)) + " notification=" + delivery


def main():
    db_path = DATA / "control.db"
    if len(sys.argv) != 2 or sys.argv[1] != "--once":
        raise SystemExit("Usage: review_executor_v46.py --once")
    if not db_path.is_file():
        raise SystemExit("Review DB absent")
    conn = sqlite3.connect(db_path, isolation_level=None, timeout=15)
    try:
        result = run_once(conn)
        print(result)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
