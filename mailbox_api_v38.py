"""Authenticated mailbox API service layer, no HTTP listener.

Reverse proxy must enforce TLS. Independent per-role bearer secrets are
verified here before calling mailbox storage. No caller-supplied role trusted.
"""
import hashlib
import hmac
from mailbox_core_v37 import publish,claim_next,acknowledge,get_receipt

class MailboxAPI:
    def __init__(self,db,producer_secret,consumer_secret):
        if not isinstance(producer_secret,str) or len(producer_secret)<32:
            raise ValueError("Strong producer secret required")
        if not isinstance(consumer_secret,str) or len(consumer_secret)<32:
            raise ValueError("Strong consumer secret required")
        if hmac.compare_digest(producer_secret,consumer_secret):
            raise ValueError("Credentials must differ")
        self.db=db
        self.tokens={"render-producer":hashlib.sha256(producer_secret.encode()).digest(),
                     "vps-consumer":hashlib.sha256(consumer_secret.encode()).digest()}
    def _auth(self,token,role):
        if not isinstance(token,str) or len(token)<32:
            raise PermissionError("Authentication required")
        digest=hashlib.sha256(token.encode()).digest()
        if not hmac.compare_digest(digest,self.tokens[role]):
            raise PermissionError("Invalid role token")
    def submit(self,token,message_id,envelope):
        self._auth(token,"render-producer")
        return publish(self.db,message_id,envelope,"render-producer")
    def acquire(self,token):
        self._auth(token,"vps-consumer")
        return claim_next(self.db,"vps-consumer")
    def confirm(self,token,message_id,receipt):
        self._auth(token,"vps-consumer")
        return acknowledge(self.db,message_id,receipt,"vps-consumer")
    def receipt(self,token,message_id):
        self._auth(token,"render-producer")
        return get_receipt(self.db,message_id,"render-producer")
