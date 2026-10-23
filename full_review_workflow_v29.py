"""Isolated, opt-in review workflow. Never invoked by the Render Telegram bot.

Credentials and transport interfaces are supplied by an external trusted runner.
No merge, production deployment or paid AI call exists in this workflow.
"""
from external_runner_v24 import submit_review
from coordinator_v23 import check_and_queue, notify_admin

def execute_approved_review(conn, request_id, base_sha, files, github_transport,
                            ci_reader, telegram_sender, admin_chat_id, enabled=False):
    if enabled is not True:
        raise PermissionError("Workflow is disabled")
    if not callable(ci_reader) or not callable(telegram_sender):
        raise ValueError("Explicit transport interfaces required")
    if not str(admin_chat_id).isdigit() or int(admin_chat_id)<=0:
        raise ValueError("Administrator chat required")
    result=submit_review(conn,request_id,base_sha,files,github_transport,enabled=True)
    ci_status=check_and_queue(conn,request_id,result["url"],result["head_sha"],ci_reader,enabled=True)
    delivery=notify_admin(conn,telegram_sender,admin_chat_id,enabled=True)
    return {"draft_pr":result["url"],"head_sha":result["head_sha"],
            "ci":ci_status,"notification":delivery,
            "merged":False,"deployed":False}
