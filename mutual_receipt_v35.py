"""Mutually authenticated response receipts for a pull-based handoff channel.

The request is authenticated with handoff_envelope_v33. The receiver signs
a response with a DIFFERENT key. This module opens no network ports.
"""
import hashlib
import hmac
import time
from handoff_envelope_v33 import canonical

def sign_receipt(package, status, receiver_key, now=None):
    if not isinstance(receiver_key,bytes) or len(receiver_key)<32:
        raise ValueError("Receiver key must have 32 bytes")
    if status not in ("accepted","rejected"):
        raise ValueError("Invalid status")
    digest=package.get("handoff_sha256") if isinstance(package,dict) else None
    if not isinstance(digest,str) or len(digest)!=64:
        raise ValueError("Invalid handoff reference")
    msg={"v":1,"handoff_sha256":digest,"status":status,
         "time":int(time.time() if now is None else now)}
    msg["signature"]=hmac.new(receiver_key,canonical(msg),hashlib.sha256).hexdigest()
    return msg

def verify_receipt(receipt,expected_digest,receiver_key,now=None):
    if not isinstance(receiver_key,bytes) or len(receiver_key)<32:
        raise ValueError("Invalid receiver key")
    if not isinstance(receipt,dict) or set(receipt)!={"v","handoff_sha256","status","time","signature"}:
        raise ValueError("Invalid receipt")
    payload={k:v for k,v in receipt.items() if k!="signature"}
    signature=receipt["signature"]
    if not isinstance(signature,str):
        raise PermissionError("Invalid signature")
    wanted=hmac.new(receiver_key,canonical(payload),hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature,wanted):
        raise PermissionError("Receiver authentication failed")
    timestamp=receipt["time"]
    current=int(time.time() if now is None else now)
    if type(timestamp) is not int or abs(current-timestamp)>120:
        raise PermissionError("Stale receipt")
    if receipt["v"]!=1 or receipt["handoff_sha256"]!=expected_digest or receipt["status"] not in ("accepted","rejected"):
        raise PermissionError("Wrong handoff or status")
    return receipt["status"]
