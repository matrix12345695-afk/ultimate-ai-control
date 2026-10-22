"""Authenticated single-use handoff envelope for Render -> isolated VPS.

Only the trusted Render producer may sign a DB-approved handoff. The consumer
must verify the signature and reserve the nonce in its own persistent SQLite DB
before any GitHub side effect. This is a library, not a network endpoint.
"""
import hashlib
import hmac
import json
import secrets
import sqlite3
import time

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")

def seal(conn,request_id,base_sha,shared_key,now=None):
    from controller_v20 import verify_request
    if not isinstance(shared_key,bytes) or len(shared_key)<32:
        raise ValueError("Shared key must be at least 32 bytes")
    package=verify_request(conn,request_id,base_sha)
    ts=int(time.time() if now is None else now)
    envelope={"v":1,"issued_at":ts,"expires_at":ts+300,
              "nonce":secrets.token_hex(24),"package":package}
    envelope["signature"]=hmac.new(shared_key,canonical(envelope),hashlib.sha256).hexdigest()
    return envelope

def verify_and_reserve(conn,envelope,shared_key,now=None):
    if not isinstance(shared_key,bytes) or len(shared_key)<32:
        raise ValueError("Invalid shared key")
    if not isinstance(envelope,dict) or set(envelope)!={"v","issued_at","expires_at","nonce","package","signature"}:
        raise ValueError("Malformed envelope")
    supplied=envelope["signature"]
    if not isinstance(supplied,str) or len(supplied)!=64:
        raise PermissionError("Invalid signature")
    payload={key:value for key,value in envelope.items() if key!="signature"}
    expected=hmac.new(shared_key,canonical(payload),hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected,supplied):
        raise PermissionError("Signature mismatch")
    ts=int(time.time() if now is None else now)
    if envelope["v"]!=1 or not isinstance(envelope["issued_at"],int) or not isinstance(envelope["expires_at"],int):
        raise ValueError("Invalid time fields")
    if not envelope["issued_at"]<=ts<envelope["expires_at"] or envelope["expires_at"]-envelope["issued_at"]>300:
        raise PermissionError("Expired handoff")
    nonce=envelope["nonce"]
    package=envelope["package"]
    if not isinstance(nonce,str) or len(nonce)!=48 or not all(x in "0123456789abcdef" for x in nonce):
        raise ValueError("Invalid nonce")
    if not isinstance(package,dict) or package.get("mode")!="DRAFT_PR_ONLY" or package.get("merge_allowed") is not False or package.get("deploy_allowed") is not False:
        raise PermissionError("Unsafe requested action")
    conn.execute("CREATE TABLE IF NOT EXISTS received_handoffs (nonce TEXT PRIMARY KEY, request_id INTEGER NOT NULL, received_at INTEGER NOT NULL)")
    try:
        conn.execute("INSERT INTO received_handoffs VALUES (?,?,?)",(nonce,package["request_id"],ts))
        conn.commit()
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        raise PermissionError("Replay denied") from exc
    return package
