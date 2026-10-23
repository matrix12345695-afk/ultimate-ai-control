"""Isolated review coordinator. Disabled by default, no embedded credentials.

External trusted transport must provide GitHub operations, CI lookup and sending.
This module never merges, deploys or runs paid AI models.
"""
from controller_v20 import record_ci
from review_outbox_v21 import queue_ci_notification
from telegram_delivery_v22 import deliver_next

def check_and_queue(conn, request_id, pr_url, head_sha, ci_reader, enabled=False):
    if enabled is not True:
        raise PermissionError("Review coordinator disabled")
    if not callable(ci_reader):
        raise ValueError("CI reader required")
    results=ci_reader(head_sha)
    state=record_ci(conn,request_id,head_sha,pr_url,results)
    queue_ci_notification(conn,request_id)
    return state

def notify_admin(conn, sender, admin_chat_id, enabled=False):
    if enabled is not True:
        raise PermissionError("Notifications disabled")
    return deliver_next(conn,sender,admin_chat_id)
