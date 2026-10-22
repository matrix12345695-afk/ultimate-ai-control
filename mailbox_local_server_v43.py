"""Loopback-only mailbox WSGI entrypoint for isolated smoke tests.

This is deliberately not a public HTTPS endpoint. TLS must be supplied by a
separately configured reverse proxy before any network-facing deployment.
"""
import os
import sqlite3
from wsgiref.simple_server import make_server
from mailbox_core_v37 import initialize
from mailbox_wsgi_v42 import build_verified_app

def build_from_environment(env=None):
    env=os.environ if env is None else env
    if env.get("MAILBOX_ENABLED")!="true":
        raise PermissionError("Mailbox listener disabled")
    if env.get("MAILBOX_BIND","127.0.0.1")!="127.0.0.1":
        raise PermissionError("Only loopback binding permitted")
    path=env.get("MAILBOX_DB_PATH")
    if not path or path==":memory:":
        raise ValueError("Durable SQLite path required")
    producer=env.get("MAILBOX_PRODUCER_TOKEN","")
    consumer=env.get("MAILBOX_CONSUMER_TOKEN","")
    signing=env.get("MAILBOX_HANDOFF_KEY_HEX","")
    receiver=env.get("MAILBOX_RECEIPT_KEY_HEX","")
    if len(signing)!=64 or len(receiver)!=64:
        raise ValueError("Strong signature keys required")
    hkey=bytes.fromhex(signing);rkey=bytes.fromhex(receiver)
    db=sqlite3.connect(path,isolation_level=None,check_same_thread=False,timeout=10)
    db.execute("PRAGMA journal_mode=WAL")
    initialize(db)
    return db,build_verified_app(db,producer,consumer,hkey,rkey)

def serve():
    db,app=build_from_environment()
    port=int(os.environ.get("MAILBOX_PORT","8765"))
    if port<1024 or port>65535:raise ValueError("Invalid mailbox port")
    try:
        with make_server("127.0.0.1",port,app) as server:
            server.serve_forever()
    finally:
        db.close()

if __name__=="__main__":
    serve()
