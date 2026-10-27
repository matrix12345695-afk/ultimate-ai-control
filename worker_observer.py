"""Completed polling waits and current worker signals; never infer downtime from silence."""
from bisect import bisect_right
from contextlib import closing
import hashlib
import json
import math
import os
import secrets
import time
import emergency_control as emergency
import task_queue as q

MAX_WAIT=8.0
FRESH=45.0
MAX_ROWS=600000
REASONS={'empty_queue':'нет заданий','owner_pending':'нет доступных заданий; есть ожидающие решения',
    'retry_delay':'задания ждут срока повтора','capacity':'лимит параллельности занят',
    'poll_ready':'интервал опроса; есть доступное задание','paused':'пауза владельца',
    'emergency':'аварийная блокировка','changed':'состояние изменилось во время ожидания','tick_error':'пауза после ошибки цикла'}

class SessionLost(RuntimeError):pass


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def initialize(conn):
    conn.executescript('''CREATE TABLE IF NOT EXISTS worker_observer_sessions(
      id TEXT PRIMARY KEY,worker TEXT NOT NULL,pid INTEGER NOT NULL,started_at REAL NOT NULL,
      last_seen REAL NOT NULL,closed_at REAL,sequence INTEGER NOT NULL DEFAULT 0,dropped INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS worker_observer_current(worker TEXT PRIMARY KEY,session TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS worker_observer_waits(
      id INTEGER PRIMARY KEY,session TEXT NOT NULL,sequence INTEGER NOT NULL,started_at REAL NOT NULL,
      ended_at REAL NOT NULL,reason TEXT NOT NULL,sha256 TEXT NOT NULL,UNIQUE(session,sequence));
    CREATE INDEX IF NOT EXISTS worker_wait_window ON worker_observer_waits(started_at,ended_at);
    CREATE TRIGGER IF NOT EXISTS worker_wait_no_update BEFORE UPDATE ON worker_observer_waits
      BEGIN SELECT RAISE(ABORT,'worker waits are immutable'); END;
    CREATE TRIGGER IF NOT EXISTS worker_wait_no_delete BEFORE DELETE ON worker_observer_waits
      BEGIN SELECT RAISE(ABORT,'worker waits are immutable'); END;''');conn.commit()


def context(conn,*,now=None):
    now=q._now(time.time() if now is None else now)
    conn.execute('SAVEPOINT observer_context')
    try:
        control=emergency.state(conn);paused,maximum=conn.execute('SELECT paused,concurrency FROM agent_queue_control').fetchone()
        counts=dict(conn.execute('SELECT state,count(*) FROM agent_jobs GROUP BY state'))
        ready=conn.execute("SELECT count(*) FROM agent_jobs WHERE state='queued' AND available_at<=? AND attempts<max_attempts",(now,)).fetchone()[0]
        event=conn.execute('SELECT COALESCE(MAX(id),0) FROM agent_job_events').fetchone()[0]
        if control['latched']:reason='emergency'
        elif paused:reason='paused'
        elif counts.get('running',0)>=maximum:reason='capacity'
        elif ready:reason='poll_ready'
        elif counts.get('queued',0):reason='retry_delay'
        elif counts.get('awaiting_owner',0):reason='owner_pending'
        else:reason='empty_queue'
        return {'reason':reason,'epoch':control['epoch'],'paused':paused,'event':event,'counts':counts,'ready':ready}
    finally:conn.execute('RELEASE SAVEPOINT observer_context')


class Observer:
    def __init__(self,worker,session):self.worker=worker;self.session=session;self.pid=os.getpid()
    @classmethod
    def start(cls,conn,worker,*,now=None):
        q._text(worker,80);now=q._now(time.time() if now is None else now);session=secrets.token_hex(16)
        with q._write(conn):
            conn.execute('INSERT INTO worker_observer_sessions(id,worker,pid,started_at,last_seen) VALUES(?,?,?,?,?)',(session,worker,os.getpid(),now,now))
            conn.execute('INSERT INTO worker_observer_current VALUES(?,?) ON CONFLICT(worker) DO UPDATE SET session=excluded.session',(worker,session))
        return cls(worker,session)
    def owned(self,conn):
        row=conn.execute('SELECT s.sequence,s.started_at FROM worker_observer_sessions s JOIN worker_observer_current c ON c.session=s.id AND c.worker=s.worker WHERE s.id=? AND s.worker=? AND s.pid=? AND s.closed_at IS NULL',(self.session,self.worker,self.pid)).fetchone()
        if not row:raise SessionLost('worker observation session superseded or closed')
        return row
    def touch(self,conn,*,now=None):
        if not conn.in_transaction:raise ValueError('observer pulse requires existing transaction')
        self.owned(conn);conn.execute('UPDATE worker_observer_sessions SET last_seen=? WHERE id=?',(q._now(time.time() if now is None else now),self.session))
    def record(self,conn,start,end,mono_start,mono_end,before,after,*,failed=False):
        values=[q._now(x) for x in (start,end,mono_start,mono_end)];start,end,mono_start,mono_end=values
        elapsed=mono_end-mono_start;wall=end-start
        reason=before['reason'] if before==after else 'changed'
        if failed and reason not in ('emergency','paused','changed'):reason='tick_error'
        if reason not in REASONS:raise ValueError('unknown wait reason')
        with q._write(conn):
            sequence,created=self.owned(conn)
            prior=conn.execute('SELECT MAX(ended_at) FROM worker_observer_waits WHERE session=?',(self.session,)).fetchone()[0]
            valid=(0<elapsed<=MAX_WAIT and 0<wall<=MAX_WAIT and abs(elapsed-wall)<=.25 and start>=created and (prior is None or start>=prior))
            if not valid:
                conn.execute('UPDATE worker_observer_sessions SET dropped=dropped+1,last_seen=? WHERE id=?',(end,self.session));return False
            # Credit only the common monotonic/wall duration; any remainder is unknown.
            finish=start+min(elapsed,wall);sequence+=1;raw=[self.session,sequence,start,finish,reason]
            conn.execute('INSERT INTO worker_observer_waits(session,sequence,started_at,ended_at,reason,sha256) VALUES(?,?,?,?,?,?)',(*raw,digest(raw)))
            conn.execute('UPDATE worker_observer_sessions SET sequence=?,last_seen=? WHERE id=?',(sequence,end,self.session))
        return True
    def close(self,conn,*,now=None):
        with q._write(conn):conn.execute('UPDATE worker_observer_sessions SET closed_at=?,last_seen=? WHERE id=? AND pid=? AND closed_at IS NULL',(q._now(time.time() if now is None else now),q._now(time.time() if now is None else now),self.session,self.pid))


def wait_cycle(path,observer,stopping,*,failed=False,sleeper=time.sleep,clock=time.time,monotonic=time.monotonic):
    import sqlite3
    with closing(sqlite3.connect(path,timeout=15)) as conn:before=context(conn)
    start=clock();mono_start=monotonic()
    slept=0
    for _ in range(5):
        if stopping():break
        sleeper(1);slept+=1
    mono_end=monotonic();end=clock()
    if not slept or mono_end<=mono_start:return
    with closing(sqlite3.connect(path,timeout=15)) as conn:
        after=context(conn);observer.record(conn,start,end,mono_start,mono_end,before,after,failed=failed)


def _merge(rows,since,until):
    merged=[]
    for start,end in rows:
        start=max(start,since);end=min(end,until)
        if start>=end:continue
        if merged and start<=merged[-1][1]:merged[-1]=(merged[-1][0],max(end,merged[-1][1]))
        else:merged.append((start,end))
    return merged


def report(conn,since,until,worker='operations-1'):
    since,until=q._now(since),q._now(until);q._text(worker,80)
    if not since<until or until-since>31*86400:raise ValueError('bounded observation period required')
    result={'worker':worker,'since':since,'until':until,'observed_wait_seconds':0.0,'by_reason':{},
            'work_coverage_seconds':0.0,'unobserved_seconds':until-since,'invalid_rows':0,'overlap_seconds':0.0}
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='worker_observer_waits'").fetchone():return result
    conn.execute('SAVEPOINT observer_report')
    try:
        work=_merge(conn.execute('SELECT started_at,ended_at FROM agent_work_spans WHERE worker=? AND started_at<? AND ended_at>? ORDER BY started_at,ended_at',(worker,until,since)),since,until)
        result['work_coverage_seconds']=sum(b-a for a,b in work);ends=[b for a,b in work]
        cursor=since;count=0;overlapping=False
        rows=conn.execute('''SELECT w.session,w.sequence,w.started_at,w.ended_at,w.reason,w.sha256,s.started_at
          FROM worker_observer_waits w JOIN worker_observer_sessions s ON s.id=w.session
          WHERE s.worker=? AND w.started_at<? AND w.ended_at>? ORDER BY w.started_at,w.id LIMIT ?''',(worker,until,since,MAX_ROWS+1))
        for session,seq,start,end,reason,sha,created in rows:
            count+=1
            if count>MAX_ROWS:result['invalid_rows']+=1;overlapping=True;break
            raw=[session,seq,start,end,reason]
            if (type(seq) is not int or seq<1 or reason not in REASONS or type(start) not in (int,float) or type(end) not in (int,float)
                or not math.isfinite(start) or not math.isfinite(end) or type(created) not in (int,float) or not math.isfinite(created) or not 0<end-start<=MAX_WAIT or start<created or digest(raw)!=sha):
                result['invalid_rows']+=1;continue
            start=max(start,since);end=min(end,until)
            if start<cursor:overlapping=True;result['invalid_rows']+=1;continue
            cursor=end;credit=end-start
            i=bisect_right(ends,start)
            while i<len(work) and work[i][0]<end:
                overlap=max(0,min(end,work[i][1])-max(start,work[i][0]));credit-=overlap;result['overlap_seconds']+=overlap;i+=1
            result['by_reason'][reason]=result['by_reason'].get(reason,0)+max(0,credit)
        if overlapping:result['by_reason']={}
        result['observed_wait_seconds']=sum(result['by_reason'].values())
        result['unobserved_seconds']=max(0,until-since-result['work_coverage_seconds']-result['observed_wait_seconds'])
        return result
    finally:conn.execute('RELEASE SAVEPOINT observer_report')


def valid_report(data):
    try:
        keys={'worker','since','until','observed_wait_seconds','by_reason','work_coverage_seconds','unobserved_seconds','invalid_rows','overlap_seconds'}
        if not isinstance(data,dict) or set(data)!=keys or not isinstance(data['worker'],str) or not 1<=len(data['worker'])<=80:return False
        q._now(data['since']);q._now(data['until']);window=data['until']-data['since']
        if not 0<window<=31*86400 or not isinstance(data['by_reason'],dict) or set(data['by_reason'])-set(REASONS):return False
        values=[data[k] for k in ('observed_wait_seconds','work_coverage_seconds','unobserved_seconds','overlap_seconds')]+list(data['by_reason'].values())
        if any(type(x) not in (int,float) or not math.isfinite(x) or x<0 for x in values):return False
        return (type(data['invalid_rows']) is int and data['invalid_rows']>=0
            and abs(sum(data['by_reason'].values())-data['observed_wait_seconds'])<.000001
            and abs(data['observed_wait_seconds']+data['work_coverage_seconds']+data['unobserved_seconds']-window)<.000001)
    except (ValueError,TypeError,KeyError):return False


def current(conn,*,now=None,worker='operations-1'):
    now=q._now(time.time() if now is None else now)
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='worker_observer_current'").fetchone():return {'state':'unobserved'}
    row=conn.execute('SELECT s.last_seen,s.closed_at,s.dropped FROM worker_observer_sessions s JOIN worker_observer_current c ON c.session=s.id WHERE c.worker=?',(worker,)).fetchone()
    if not row:return {'state':'unobserved'}
    age=now-row[0]
    if row[1] is not None:return {'state':'closed','age_seconds':age}
    if not 0<=age<=FRESH:return {'state':'stale','age_seconds':age}
    state=context(conn,now=now)['reason']
    if conn.execute("SELECT 1 FROM agent_jobs WHERE worker=? AND state='running' AND lease_until>?",(worker,now)).fetchone():state='busy'
    return {'state':state,'age_seconds':age,'dropped_intervals':row[2]}


def describe(conn,days=1,*,now=None):
    if type(days) is not int or days not in (1,7):raise ValueError('days must be1 or7')
    now=q._now(time.time() if now is None else now);data=report(conn,now-days*86400,now);signal=current(conn,now=now)
    names=dict(REASONS,busy='выполняет задание',unobserved='наблюдение ещё не запускалось',stale='нет свежего сигнала; состояние неизвестно',closed='наблюдатель завершён')
    from work_analytics import duration
    first=conn.execute('SELECT MIN(started_at) FROM worker_observer_sessions WHERE worker=?',('operations-1',)).fetchone()[0]
    lines=['🤖 Исполнитель · operations-1','Сейчас: '+names[signal['state']],
           'Наблюдавшееся ожидание: '+duration(data['observed_wait_seconds'])+' за '+str(days)+' дн.']
    if first is not None:
        from datetime import datetime,timedelta,timezone
        lines.append('Наблюдение начато: '+datetime.fromtimestamp(first,timezone(timedelta(hours=5))).strftime('%d.%m.%Y %H:%M')+' Ташкент')
    lines.extend(REASONS[k]+': '+duration(v) for k,v in sorted(data['by_reason'].items()))
    lines.extend(['Покрыто измеренной работой: '+duration(data['work_coverage_seconds']),
                  'Время без наблюдений: '+duration(data['unobserved_seconds']),
                  'Ожидание записывается только после завершённого интервала опроса. Состояние между снимками может измениться.',
                  'Пропавший сигнал не доказывает простой или отключение VPS. Старые дни не восстанавливаются по возрасту задач.'])
    if data['invalid_rows']:lines.append('Есть непроверенные/перекрывающиеся интервалы; неподтверждённая часть не учтена.')
    lines.append('/worker4 24h · /worker4 7d · /finish4')
    return '\n'.join(lines)
