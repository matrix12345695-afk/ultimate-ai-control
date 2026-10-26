"""Durable job coordination only. This module never runs code, deploys or calls an API.

Lease ownership and global concurrency are enforced by SQLite transactions. Actual workers
must provide isolation and trustworthy work intervals before enabling execution.
"""
from contextlib import contextmanager
import json
import math
import secrets
import time
import emergency_control as emergency

PROJECTS = {"control", "nova", "kinder", "sap", "qualisift", "iiko-loader", "sap-mb51"}
KINDS = {"inspect_repository", "plan_change", "test_release", "check_site", "review_change", "daily_report"}
CATEGORIES = {"active", "testing", "waiting"}


def initialize(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS agent_queue_control (
        singleton INTEGER PRIMARY KEY CHECK(singleton=1), paused INTEGER NOT NULL DEFAULT 0,
        concurrency INTEGER NOT NULL DEFAULT 1 CHECK(concurrency BETWEEN 1 AND 3), reason TEXT NOT NULL DEFAULT '');
    INSERT OR IGNORE INTO agent_queue_control(singleton) VALUES(1);
    CREATE TABLE IF NOT EXISTS agent_jobs (
        id INTEGER PRIMARY KEY, project TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL,
        event_key TEXT UNIQUE, state TEXT NOT NULL DEFAULT 'queued'
            CHECK(state IN ('queued','running','awaiting_owner','succeeded','failed','cancelled')),
        priority INTEGER NOT NULL, attempts INTEGER NOT NULL DEFAULT 0, max_attempts INTEGER NOT NULL,
        created_at REAL NOT NULL, available_at REAL NOT NULL, updated_at REAL NOT NULL,
        worker TEXT, lease_token TEXT, lease_until REAL, attempt_started REAL,
        result TEXT, last_error TEXT);
    CREATE INDEX IF NOT EXISTS agent_jobs_ready ON agent_jobs(state, available_at, priority);
    CREATE TABLE IF NOT EXISTS agent_job_events (
        id INTEGER PRIMARY KEY, job_id INTEGER, at REAL NOT NULL, event TEXT NOT NULL, detail TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS agent_work_spans (
        id INTEGER PRIMARY KEY, job_id INTEGER NOT NULL, attempt INTEGER NOT NULL,
        worker TEXT NOT NULL, category TEXT NOT NULL CHECK(category IN ('active','testing','waiting')),
        started_at REAL NOT NULL, ended_at REAL NOT NULL CHECK(ended_at>started_at));
    """)
    columns={row[1] for row in conn.execute('PRAGMA table_info(agent_jobs)')}
    if 'control_epoch' not in columns: conn.execute('ALTER TABLE agent_jobs ADD COLUMN control_epoch INTEGER NOT NULL DEFAULT 0')
    conn.commit()
    emergency.initialize(conn)


def _now(value):
    value = time.time() if value is None else value
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError("invalid timestamp")
    return float(value)


def _text(value, limit):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError("invalid text")
    return value


def _json(value):
    raw = json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True)
    if len(raw.encode()) > 16000:
        raise ValueError("job payload too large")
    return raw


@contextmanager
def _write(conn):
    if conn.in_transaction:
        raise RuntimeError("queue needs an independent transaction")
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def _event(conn, job, now, event, detail=""):
    conn.execute("INSERT INTO agent_job_events(job_id,at,event,detail) VALUES(?,?,?,?)",
                 (job, now, event, detail[:1000]))


def enqueue(conn, project, kind, payload, *, priority=50, max_attempts=3, event_key=None, now=None):
    if project not in PROJECTS or kind not in KINDS:
        raise ValueError("project or job kind not enabled; Inventory is protected")
    if type(priority) is not int or not 0 <= priority <= 100:
        raise ValueError("invalid priority")
    if type(max_attempts) is not int or not 1 <= max_attempts <= 5:
        raise ValueError("invalid attempt limit")
    if event_key is not None: _text(event_key, 200)
    now, payload = _now(now), _json(payload)
    with _write(conn):
        if event_key is not None:
            row=conn.execute("SELECT id,project,kind,payload FROM agent_jobs WHERE event_key=?", (event_key,)).fetchone()
            if row:
                if row[1:] != (project,kind,payload):
                    raise ValueError("event key already identifies another job")
                return row[0]
        cur=conn.execute("""INSERT INTO agent_jobs(project,kind,payload,event_key,priority,max_attempts,created_at,available_at,updated_at)
                         VALUES(?,?,?,?,?,?,?,?,?)""", (project,kind,payload,event_key,priority,max_attempts,now,now,now))
        _event(conn,cur.lastrowid,now,"queued")
        return cur.lastrowid


def configure(conn, *, paused=None, concurrency=None, reason="owner control", now=None):
    if paused is not None and type(paused) is not bool: raise ValueError("invalid pause flag")
    if concurrency is not None and (type(concurrency) is not int or not 1 <= concurrency <= 3):
        raise ValueError("invalid concurrency")
    now = _now(now)
    _text(reason,1000)
    with _write(conn):
        if paused is False: emergency.require_open(conn)
        if paused is not None: conn.execute("UPDATE agent_queue_control SET paused=? WHERE singleton=1", (int(paused),))
        if concurrency is not None: conn.execute("UPDATE agent_queue_control SET concurrency=? WHERE singleton=1", (concurrency,))
        conn.execute("UPDATE agent_queue_control SET reason=? WHERE singleton=1", (reason,))
        _event(conn,None,now,"control",reason)


def _recover(conn, now):
    rows=conn.execute("SELECT id,attempts,max_attempts FROM agent_jobs WHERE state='running' AND lease_until<=?", (now,)).fetchall()
    for ident, attempts, maximum in rows:
        state = "failed" if attempts >= maximum else "queued"
        conn.execute("""UPDATE agent_jobs SET state=?,worker=NULL,lease_token=NULL,lease_until=NULL,
                        available_at=?,updated_at=?,last_error='lease_expired' WHERE id=?""", (state,now,now,ident))
        _event(conn,ident,now,"lease_expired",state)


def claim(conn, worker, capabilities, *, lease_seconds=120, now=None):
    _text(worker,100)
    capabilities=set(capabilities)
    if not capabilities or not capabilities <= KINDS:
        raise ValueError("invalid capabilities")
    if type(lease_seconds) is not int or not 5 <= lease_seconds <= 900:
        raise ValueError("invalid lease duration")
    now = _now(now)
    with _write(conn):
        _recover(conn,now)
        paused, maximum=conn.execute("SELECT paused,concurrency FROM agent_queue_control WHERE singleton=1").fetchone()
        current=emergency.state(conn)
        if current['latched'] or paused or conn.execute("SELECT count(*) FROM agent_jobs WHERE state='running'").fetchone()[0] >= maximum:
            return None
        if conn.execute("SELECT 1 FROM agent_jobs WHERE state='running' AND worker=?", (worker,)).fetchone():
            return None
        placeholders=",".join("?" for _ in capabilities)
        row=conn.execute("SELECT id,project,kind,payload,attempts FROM agent_jobs WHERE state='queued' AND available_at<=? AND attempts<max_attempts AND kind IN ("+placeholders+") ORDER BY priority DESC,id LIMIT 1", (now,*sorted(capabilities))).fetchone()
        if row is None: return None
        token=secrets.token_hex(24)
        conn.execute("""UPDATE agent_jobs SET state='running',worker=?,lease_token=?,lease_until=?,attempt_started=?,
                        attempts=attempts+1,updated_at=?,control_epoch=? WHERE id=?""", (worker,token,now+lease_seconds,now,now,current['epoch'],row[0]))
        _event(conn,row[0],now,"claimed",worker)
        return {"id":row[0],"project":row[1],"kind":row[2],"payload":json.loads(row[3]),
                "attempt":row[4]+1,"lease_token":token,"lease_until":now+lease_seconds}


def _owned(conn, ident, token, now):
    row=conn.execute("SELECT worker,attempts,max_attempts,attempt_started FROM agent_jobs WHERE id=? AND state='running' AND lease_token=? AND lease_until>?", (ident,token,now)).fetchone()
    if row is None: raise PermissionError("job lease absent, expired or owned by another worker")
    return row


def heartbeat(conn, ident, token, *, lease_seconds=120, now=None):
    if type(lease_seconds) is not int or not 5 <= lease_seconds <= 900: raise ValueError("invalid lease duration")
    now=_now(now)
    with _write(conn):
        _owned(conn,ident,token,now)
        conn.execute("UPDATE agent_jobs SET lease_until=?,updated_at=? WHERE id=?", (now+lease_seconds,now,ident))
        return {"paused":bool(conn.execute("SELECT paused FROM agent_queue_control WHERE singleton=1").fetchone()[0])}


def finish(conn, ident, token, result, *, awaiting_owner=False, now=None):
    if type(awaiting_owner) is not bool: raise ValueError("invalid awaiting_owner flag")
    now, result = _now(now), _json(result)
    state="awaiting_owner" if awaiting_owner else "succeeded"
    with _write(conn):
        _owned(conn,ident,token,now)
        conn.execute("UPDATE agent_jobs SET state=?,result=?,worker=NULL,lease_token=NULL,lease_until=NULL,updated_at=? WHERE id=?", (state,result,now,ident))
        _event(conn,ident,now,state)


def finish_with_test(conn,ident,token,result,payload,*,event_key,now=None):
    """Commit successful generation and its control-project test job in one transaction."""
    now=_now(now)
    _text(event_key,200)
    if (not isinstance(payload,dict) or set(payload)!={'target','generation_job_id','source_digest'} or
            payload['target']!='developer-bundle' or type(payload['generation_job_id']) is not int or payload['generation_job_id']!=ident or
            not isinstance(payload['source_digest'],str) or len(payload['source_digest'])!=64 or
            any(c not in '0123456789abcdef' for c in payload['source_digest']) or
            not isinstance(result,dict) or result.get('source_digest')!=payload['source_digest']):
        raise ValueError('invalid developer test follow-up')
    raw=_json(payload)
    with _write(conn):
        _owned(conn,ident,token,now)
        parent=conn.execute('SELECT project,kind FROM agent_jobs WHERE id=?',(ident,)).fetchone()
        if parent!=('control','review_change'): raise PermissionError('only ULTIMATE generation may create a test follow-up')
        existing=conn.execute('SELECT id,project,kind,payload FROM agent_jobs WHERE event_key=?',(event_key,)).fetchone()
        if existing:
            if existing[1:]!=('control','test_release',raw): raise ValueError('follow-up event key conflict')
            child=existing[0]
        else:
            child=conn.execute("INSERT INTO agent_jobs(project,kind,payload,event_key,priority,max_attempts,created_at,available_at,updated_at) VALUES('control','test_release',?,?,50,3,?,?,?)",(raw,event_key,now,now,now)).lastrowid
            _event(conn,child,now,'queued')
        saved=_json(dict(result,followup_job_id=child))
        conn.execute("UPDATE agent_jobs SET state='succeeded',result=?,worker=NULL,lease_token=NULL,lease_until=NULL,updated_at=? WHERE id=?",(saved,now,ident))
        _event(conn,ident,now,'succeeded','draft awaits isolated tests')
        return child


def fail(conn, ident, token, error, *, retryable=True, now=None):
    if type(retryable) is not bool: raise ValueError("invalid retry flag")
    now=_now(now)
    _text(error,1000)
    with _write(conn):
        _,attempt,maximum,_=_owned(conn,ident,token,now)
        state="queued" if retryable and attempt < maximum else "failed"
        delay=min(3600,30*2**attempt) if state=="queued" else 0
        conn.execute("""UPDATE agent_jobs SET state=?,last_error=?,available_at=?,updated_at=?,
                        worker=NULL,lease_token=NULL,lease_until=NULL WHERE id=?""", (state,error,now+delay,now,ident))
        _event(conn,ident,now,"retry_scheduled" if state=="queued" else "failed",error)


def cancel(conn, ident, *, now=None):
    now=_now(now)
    with _write(conn):
        changed=conn.execute("UPDATE agent_jobs SET state='cancelled',updated_at=? WHERE id=? AND state IN ('queued','awaiting_owner')", (now,ident)).rowcount
        if changed: _event(conn,ident,now,"cancelled")
        return bool(changed)


def add_work_span(conn, ident, token, category, started_at, ended_at, *, now=None):
    """Trusted workers report measured intervals. Lease occupancy is never work time."""
    if category not in CATEGORIES: raise ValueError("invalid work category")
    now,started_at,ended_at=_now(now),_now(started_at),_now(ended_at)
    if not started_at < ended_at <= now: raise ValueError("invalid work interval")
    with _write(conn):
        worker,attempt,_,start=_owned(conn,ident,token,now)
        if started_at < start: raise ValueError("interval precedes this attempt")
        overlap=conn.execute("SELECT 1 FROM agent_work_spans WHERE worker=? AND started_at<? AND ended_at>? LIMIT 1", (worker,ended_at,started_at)).fetchone()
        if overlap: raise ValueError("work intervals overlap")
        conn.execute("INSERT INTO agent_work_spans(job_id,attempt,worker,category,started_at,ended_at) VALUES(?,?,?,?,?,?)", (ident,attempt,worker,category,started_at,ended_at))


def report(conn, since, until):
    since,until=_now(since),_now(until)
    if since>=until: raise ValueError("invalid reporting window")
    # Clip intervals to the reporting window; include all attempts without hiding failed work.
    spans=conn.execute("""SELECT s.worker,j.project,s.category,SUM(MIN(s.ended_at,?)-MAX(s.started_at,?))
                          FROM agent_work_spans s JOIN agent_jobs j ON j.id=s.job_id
                          WHERE s.started_at<? AND s.ended_at>?
                          GROUP BY s.worker,j.project,s.category""", (until,since,until,since)).fetchall()
    events=dict(conn.execute("SELECT event,count(*) FROM agent_job_events WHERE at>=? AND at<? GROUP BY event", (since,until)).fetchall())
    return {"measured_seconds":[{"worker":w,"project":p,"category":c,"seconds":seconds} for w,p,c,seconds in spans],
            "events":events,"current_states":dict(conn.execute("SELECT state,count(*) FROM agent_jobs GROUP BY state").fetchall()),
            "unmeasured_time":"unknown; never inferred from task age or model output"}
