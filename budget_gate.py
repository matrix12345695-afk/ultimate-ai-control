"""Conservative USD reservations. Hard ceiling $30; ambiguous calls keep their reservation.

Prices and API keys are NOT configured here. No network calls, purchases or automatic raises.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import secrets
import time

HARD_LIMIT_MICROUSD=30_000_000


def initialize(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS provider_costs(id TEXT PRIMARY KEY,month TEXT NOT NULL,
        project TEXT NOT NULL,agent TEXT NOT NULL,job_id INTEGER,model TEXT NOT NULL,
        reserved_microusd INTEGER NOT NULL CHECK(reserved_microusd>0),
        actual_microusd INTEGER,state TEXT NOT NULL CHECK(state IN ('reserved','settled','unknown')),
        input_tokens INTEGER,output_tokens INTEGER,created_at REAL NOT NULL,settled_at REAL)""")
    conn.commit()


def month(): return datetime.now(timezone.utc).strftime('%Y-%m')


def charged(conn,period=None):
    # Unresolved requests retain their hold across UTC month boundaries.
    return conn.execute("SELECT COALESCE(SUM(CASE WHEN state='settled' THEN actual_microusd ELSE reserved_microusd END),0) FROM provider_costs WHERE month=? OR state!='settled'",(period or month(),)).fetchone()[0]


def reserve_locked(conn,project,agent,model,maximum_microusd,*,job_id=None,limit_microusd=HARD_LIMIT_MICROUSD):
    """Caller owns BEGIN IMMEDIATE; atomically combine a hold with its request record."""
    if not conn.in_transaction: raise RuntimeError('budget write transaction required')
    if type(maximum_microusd) is not int or maximum_microusd<=0: raise ValueError('invalid maximum cost')
    if type(limit_microusd) is not int or not 0<limit_microusd<=HARD_LIMIT_MICROUSD: raise ValueError('budget exceeds owner limit')
    for value in (project,agent,model):
        if not isinstance(value,str) or not 1<=len(value)<=100: raise ValueError('invalid cost attribution')
    if charged(conn)+maximum_microusd>limit_microusd: return None
    ident=secrets.token_hex(16)
    conn.execute("INSERT INTO provider_costs VALUES(?,?,?,?,?,?,?,?,'reserved',NULL,NULL,?,NULL)",
                 (ident,month(),project,agent,job_id,model,maximum_microusd,None,time.time()))
    return ident


def reserve(conn,project,agent,model,maximum_microusd,*,job_id=None,limit_microusd=HARD_LIMIT_MICROUSD):
    if type(maximum_microusd) is not int or maximum_microusd<=0: raise ValueError("invalid maximum cost")
    if type(limit_microusd) is not int or not 0<limit_microusd<=HARD_LIMIT_MICROUSD: raise ValueError("budget exceeds owner limit")
    for value in (project,agent,model):
        if not isinstance(value,str) or not 1<=len(value)<=100: raise ValueError("invalid cost attribution")
    if conn.in_transaction: raise RuntimeError("independent budget transaction required")
    conn.execute("BEGIN IMMEDIATE")
    try:
        period=month()
        if charged(conn,period)+maximum_microusd>limit_microusd:
            conn.rollback()
            return None
        ident=secrets.token_hex(16)
        conn.execute("INSERT INTO provider_costs VALUES(?,?,?,?,?,?,?,?,'reserved',NULL,NULL,?,NULL)",
                     (ident,period,project,agent,job_id,model,maximum_microusd,None,time.time()))
        conn.commit()
        return ident
    except Exception:
        conn.rollback()
        raise


def settle(conn,ident,actual_microusd,input_tokens,output_tokens):
    if any(type(value) is not int or value<0 for value in (actual_microusd,input_tokens,output_tokens)):
        raise ValueError("invalid usage receipt")
    row=conn.execute("SELECT reserved_microusd,state FROM provider_costs WHERE id=?",(ident,)).fetchone()
    if not row or row[1]!="reserved": raise ValueError("missing or already settled reservation")
    if actual_microusd>row[0]:
        raise ValueError("usage exceeded reserved maximum: keep reservation and stop provider")
    cur=conn.execute("UPDATE provider_costs SET state='settled',actual_microusd=?,input_tokens=?,output_tokens=?,settled_at=? WHERE id=? AND state='reserved'",(actual_microusd,input_tokens,output_tokens,time.time(),ident))
    conn.commit()
    if cur.rowcount!=1: raise ValueError("reservation already settled")


def summary(conn):
    used=charged(conn)
    return {"month":month(),"limit_usd":30,"accounted_usd":used/1_000_000,
            "remaining_usd":max(0,HARD_LIMIT_MICROUSD-used)/1_000_000,
            "warning":used>=24_000_000,"provider_enabled":False,
            "note":"Local conservative ledger, not provider billing data; priced provider transport is not enabled"}
