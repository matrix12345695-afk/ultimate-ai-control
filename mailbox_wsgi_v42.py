"""Fail-closed WSGI composition: only verified mailbox API is exposed.

No listener, no secret loading, no deployment. An authenticated TLS reverse
proxy remains required for production use.
"""
from mailbox_http_v39 import MailboxHTTP
from mailbox_verified_v41 import VerifiedMailboxAPI

def build_verified_app(db,producer_token,consumer_token,handoff_key,receipt_key):
    api=VerifiedMailboxAPI(db,producer_token,consumer_token,handoff_key,receipt_key)
    return MailboxHTTP(api)
