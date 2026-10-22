"""Fail-closed Telegram delivery of verified review outbox messages.

Sender is injected. This code never reads tokens or calls Telegram itself.
"""
from review_outbox_v21 import pending_messages, claim

def deliver_next(conn, send, admin_chat_id):
    if not str(admin_chat_id).isdigit() or int(admin_chat_id)<=0:
        raise ValueError("Explicit administrator chat required")
    items=pending_messages(conn)
    if not items: return "empty"
    request_id,sha,state,body=items[0]
    if not claim(conn,request_id,sha,state): return "already_claimed"
    try:
        confirmed=send(int(admin_chat_id),body)
        if confirmed is not True:
            raise RuntimeError("No delivery acknowledgement")
    except Exception:
        conn.execute("UPDATE review_outbox SET status='pending' WHERE request_id=? AND head_sha=? AND ci_state=? AND status='claimed'",(request_id,sha,state))
        conn.commit()
        raise
    updated=conn.execute("UPDATE review_outbox SET status='sent' WHERE request_id=? AND head_sha=? AND ci_state=? AND status='claimed'",(request_id,sha,state)).rowcount
    conn.commit()
    if updated!=1: raise RuntimeError("Receipt transition failed")
    return "sent"
