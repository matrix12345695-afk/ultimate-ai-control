"""Strict cryptographic boundary for a durable mailbox.

This opt-in adapter validates signed envelopes before storage and signed
receipts before acknowledgement. No network listener or GitHub side effects.
"""
import hashlib
import hmac
import json
import time
from handoff_envelope_v33 import canonical
from mutual_receipt_v35 import verify_receipt
from mailbox_api_v38 import MailboxAPI

class VerifiedMailboxAPI(MailboxAPI):
    def __init__(self,db,producer_secret,consumer_secret,handoff_key,receipt_key):
        super().__init__(db,producer_secret,consumer_secret)
        if not all(isinstance(k,bytes) and len(k)>=32 for k in (handoff_key,receipt_key)):
            raise ValueError("Separate 32-byte signature keys required")
        if hmac.compare_digest(handoff_key,receipt_key):
            raise ValueError("Signature keys must differ")
        self.handoff_key=handoff_key
        self.receipt_key=receipt_key

    def submit(self,token,message_id,envelope):
        self._auth(token,"render-producer")
        if not isinstance(envelope,dict) or set(envelope)!={"v","issued_at","expires_at","nonce","package","signature"}:
            raise ValueError("Invalid envelope")
        sig=envelope["signature"]
        unsigned={k:v for k,v in envelope.items() if k!="signature"}
        if not isinstance(sig,str) or len(sig)!=64:
            raise PermissionError("Missing signature")
        wanted=hmac.new(self.handoff_key,canonical(unsigned),hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig,wanted):
            raise PermissionError("Invalid envelope signature")
        now=int(time.time())
        issued=envelope["issued_at"];expires=envelope["expires_at"]
        if type(issued) is not int or type(expires) is not int or not issued<=now<expires or expires-issued>300:
            raise PermissionError("Expired envelope")
        package=envelope["package"]
        if not isinstance(package,dict) or package.get("mode")!="DRAFT_PR_ONLY" or package.get("merge_allowed") is not False or package.get("deploy_allowed") is not False:
            raise PermissionError("Unsafe package")
        digest=package.get("handoff_sha256")
        if not isinstance(digest,str) or len(digest)!=64:
            raise ValueError("Bad package digest")
        plain=dict(package);plain.pop("handoff_sha256",None)
        if not hmac.compare_digest(hashlib.sha256(canonical(plain)).hexdigest(),digest):
            raise PermissionError("Package digest mismatch")
        return super().submit(token,message_id,envelope)

    def confirm(self,token,message_id,receipt):
        self._auth(token,"vps-consumer")
        row=self.db.execute("SELECT payload FROM review_mailbox WHERE message_id=? AND status='claimed'",(message_id,)).fetchone()
        if row is None: raise ValueError("No claimed message")
        expected=json.loads(row[0])["package"]["handoff_sha256"]
        verify_receipt(receipt,expected,self.receipt_key)
        return super().confirm(token,message_id,receipt)
