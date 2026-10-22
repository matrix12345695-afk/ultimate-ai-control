"""Identify abandoned mailbox claims without repeating remote side effects.

Claimed requests require manual reconciliation, including after restart.
This module does not alter mailbox rows or execute actions.
"""
from datetime import datetime,timezone

def inspect_claims(db,older_than_seconds=300,now=None):
    if not isinstance(older_than_seconds,int) or older_than_seconds<60:
        raise ValueError("Invalid threshold")
    current=now or datetime.now(timezone.utc)
    rows=db.execute("SELECT message_id,created_at FROM review_mailbox WHERE status='claimed'").fetchall()
    flagged=[]
    for message_id,created_at in rows:
        created=datetime.fromisoformat(created_at)
        age=(current-created).total_seconds()
        if age>=older_than_seconds:
            flagged.append({"message_id":message_id,"state":"manual_reconciliation","age_seconds":int(age)})
    return flagged
