"""Durable mailbox core for authenticated handoff exchange.

Storage only: no server, endpoint, listening socket, or credentials.
Caller MUST authenticate producer/consumer before invoking these functions.
"""
import json
import sqlite3
from datetime import datetime,timezone
from handoff_envelope_v33 import canonical

def initialize(db):
    db.execute("""CREATE TABLE IF NOT EXISTS review_mailbox (
        message_id TEXT PRIMARY KEY,
        payload TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('pending','claimed','acknowledged')),
        claim_owner TEXT,
        receipt TEXT,
        created_at TEXT NOT NULL)""")
    db.commit()

def publish(db,message_id,envelope,identity):
    if identity!="render-producer":raise PermissionError("Producer only")
    if not isinstance(message_id,str) or len(message_id)!=48 or any(c not in "0123456789abcdef" for c in message_id):
        raise ValueError("Invalid message ID")
    if not isinstance(envelope,dict) or envelope.get("nonce")!=message_id:
        raise ValueError("Envelope mismatch")
    data=canonical(envelope).decode()
    if len(data)>65536:raise ValueError("Too large")
    try:
        db.execute("INSERT INTO review_mailbox VALUES(?,?,'pending',NULL,NULL,?)",
                   (message_id,data,datetime.now(timezone.utc).isoformat()))
        db.commit()
    except sqlite3.IntegrityError as exc:
        db.rollback()
        raise PermissionError("Duplicate message") from exc

def claim_next(db,identity):
    if identity!="vps-consumer":raise PermissionError("Consumer only")
    db.execute("BEGIN IMMEDIATE")
    try:
        row=db.execute("SELECT message_id,payload FROM review_mailbox WHERE status='pending' ORDER BY created_at,message_id LIMIT 1").fetchone()
        if row:
            db.execute("UPDATE review_mailbox SET status='claimed',claim_owner=? WHERE message_id=? AND status='pending'",(identity,row[0]))
        db.commit()
    except Exception:
        db.rollback()
        raise
    return (row[0],json.loads(row[1])) if row else None

def acknowledge(db,message_id,receipt,identity):
    if identity!="vps-consumer":raise PermissionError("Consumer only")
    if not isinstance(receipt,dict) or not receipt.get("signature"):
        raise ValueError("Signed receipt required")
    updated=db.execute("""UPDATE review_mailbox SET status='acknowledged',receipt=?
                          WHERE message_id=? AND status='claimed' AND claim_owner=?""",
                       (canonical(receipt).decode(),message_id,identity)).rowcount
    db.commit()
    if updated!=1:raise ValueError("Not claimed or already acknowledged")

def get_receipt(db,message_id,identity):
    if identity!="render-producer":raise PermissionError("Producer only")
    row=db.execute("SELECT receipt FROM review_mailbox WHERE message_id=? AND status='acknowledged'",(message_id,)).fetchone()
    return json.loads(row[0]) if row and row[0] else None
