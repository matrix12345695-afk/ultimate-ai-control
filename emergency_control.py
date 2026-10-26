"""Durable UAC-only emergency latch and external-action admission journal.

No processes, signals, service control, credentials or network access. An admitted
request can complete after a stop; stop prevents later admissions, not remote rollback.
"""
from contextlib import contextmanager
import math
import time

class Stopped(PermissionError): pass


def _has(conn,name):
    return bool(conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(name,)).fetchone())


@contextmanager
def atomic(conn):
    if conn.in_transaction: raise RuntimeError('control requires an independent transaction')
    conn.execute('BEGIN IMMEDIATE')
    try:
        yield
        conn.commit()
    except BaseException:
        conn.rollback();raise


def initialize(conn):
    existed=_has(conn,'uac_emergency_control')
    with atomic(conn):
        conn.execute('''CREATE TABLE IF NOT EXISTS uac_emergency_control(
          singleton INTEGER PRIMARY KEY CHECK(singleton=1),epoch INTEGER NOT NULL CHECK(epoch>=0),
          latched INTEGER NOT NULL CHECK(latched IN (0,1)),reason TEXT NOT NULL,changed_at REAL NOT NULL)''')
        if not existed: conn.execute("INSERT INTO uac_emergency_control VALUES(1,0,0,'not activated',?)",(time.time(),))
        conn.execute('''CREATE TABLE IF NOT EXISTS uac_control_events(
          id INTEGER PRIMARY KEY,epoch INTEGER NOT NULL,operation TEXT NOT NULL,at REAL NOT NULL,detail TEXT NOT NULL)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS uac_control_outbox(
          epoch INTEGER PRIMARY KEY,inbox_id INTEGER)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS uac_control_requests(
          source_key TEXT PRIMARY KEY,operation TEXT NOT NULL,argument TEXT NOT NULL,event_epoch INTEGER NOT NULL)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS uac_action_admissions(
          id INTEGER PRIMARY KEY,job_id INTEGER,epoch INTEGER NOT NULL,kind TEXT NOT NULL,
          detail TEXT NOT NULL,state TEXT NOT NULL CHECK(state IN ('admitted','acknowledged','unknown')),
          admitted_at REAL NOT NULL,finished_at REAL)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS approval_control_epochs(
          approval_id TEXT PRIMARY KEY,epoch INTEGER NOT NULL)''')
        state(conn)


def state(conn):
    try: row=conn.execute('SELECT epoch,latched,reason,changed_at FROM uac_emergency_control WHERE singleton=1').fetchone()
    except Exception: raise Stopped('emergency_control_unavailable') from None
    if (not row or type(row[0]) is not int or row[0]<0 or type(row[1]) is not int or row[1] not in (0,1)
        or not isinstance(row[2],str) or len(row[2])>300 or type(row[3]) not in (int,float) or not math.isfinite(row[3])):
        raise Stopped('emergency_control_invalid')
    return dict(epoch=row[0],latched=bool(row[1]),reason=row[2],changed_at=row[3])


def require_open(conn,expected_epoch=None):
    current=state(conn)
    if current['latched']: raise Stopped('emergency_latched')
    if expected_epoch is not None and current['epoch']!=expected_epoch: raise Stopped('emergency_epoch_changed')
    return current['epoch']


def check_job(conn,ident,token):
    import task_queue as q
    q._owned(conn,ident,token,time.time())
    epoch=require_open(conn)
    try: row=conn.execute('SELECT control_epoch FROM agent_jobs WHERE id=?',(ident,)).fetchone()
    except Exception: raise Stopped('job_control_epoch_missing') from None
    if not row or row[0]!=epoch: raise Stopped('job_control_epoch_changed')
    return epoch


def _source(source_key):
    if source_key is not None and (not isinstance(source_key,str) or not 1<=len(source_key)<=200): raise ValueError('invalid control source')


def _prior(conn,key,operation,argument):
    if key is None: return None
    row=conn.execute('SELECT operation,argument,event_epoch FROM uac_control_requests WHERE source_key=?',(key,)).fetchone()
    if row and row[:2]!=(operation,argument): raise ValueError('control_source_conflict')
    return row[2] if row else None


def _remember(conn,key,operation,argument,epoch):
    if key is not None: conn.execute('INSERT INTO uac_control_requests VALUES(?,?,?,?)',(key,operation,argument,epoch))


def _event(conn,epoch,operation,detail):
    at=time.time();conn.execute('INSERT INTO uac_control_events(epoch,operation,at,detail) VALUES(?,?,?,?)',(epoch,operation,at,detail))
    if _has(conn,'agent_job_events'): conn.execute('INSERT INTO agent_job_events(job_id,at,event,detail) VALUES(NULL,?,?,?)',(at,'control','emergency '+operation+' epoch='+str(epoch)))


def flush_notifications(conn):
    # Durable stop is independent of inbox availability; delivery is retried while paused.
    import sqlite3
    from owner_notifications import create
    try:
        with atomic(conn):
            row=conn.execute('SELECT epoch FROM uac_control_outbox WHERE inbox_id IS NULL ORDER BY epoch LIMIT 1').fetchone()
            if not row: return 0
            epoch=row[0]
            ident=create(conn,'ULTIMATE AI CONTROL','critical','Аварийная блокировка зафиксирована',
                         'Зафиксирован аварийный стоп поколения '+str(epoch)+'. Новые допуски и задания блокируются. Ранее допущенный запрос может завершиться; квитанция сохраняется. Это событие журнала; текущее состояние смотри отдельно.',
                         'Открой /emergency. После завершения текущих заданий: /emergency_reset '+str(epoch)+', затем отдельно /resume. Старые согласования не оживают. Inventory и другие службы не останавливались.',event_key='uac-emergency-stop-'+str(epoch),commit=False)
            conn.execute('UPDATE uac_control_outbox SET inbox_id=? WHERE epoch=?',(ident,epoch))
            return 1
    except sqlite3.Error: return 0


def stop(conn,*,source_key=None):
    _source(source_key)
    with atomic(conn):
        prior=_prior(conn,source_key,'stop','');current=state(conn)
        if prior is not None: result=dict(current,event_epoch=prior,replayed=True)
        else:
            if not current['latched']:
                epoch=current['epoch']+1
                conn.execute("UPDATE uac_emergency_control SET epoch=?,latched=1,reason='Telegram owner emergency stop',changed_at=? WHERE singleton=1",(epoch,time.time()))
                if _has(conn,'agent_queue_control'): conn.execute("UPDATE agent_queue_control SET paused=1,reason='emergency stop' WHERE singleton=1")
                _event(conn,epoch,'stop','No new jobs/actions; admitted requests can finish; independent services unchanged')
                conn.execute('INSERT INTO uac_control_outbox(epoch) VALUES(?)',(epoch,))
            else: epoch=current['epoch']
            _remember(conn,source_key,'stop','',epoch)
            result=dict(state(conn),event_epoch=epoch,replayed=False)
    flush_notifications(conn)
    return result


def reset(conn,expected_epoch,*,source_key=None):
    if type(expected_epoch) is not int or not 1<=expected_epoch<=9223372036854775806: raise ValueError('invalid control epoch')
    _source(source_key)
    with atomic(conn):
        prior=_prior(conn,source_key,'reset',str(expected_epoch));current=state(conn)
        if prior is not None: return dict(current,event_epoch=prior,replayed=True)
        if not current['latched'] or current['epoch']!=expected_epoch: raise Stopped('emergency_reset_stale')
        if _has(conn,'agent_jobs') and conn.execute("SELECT count(*) FROM agent_jobs WHERE state='running'").fetchone()[0]: raise Stopped('emergency_jobs_still_running')
        epoch=current['epoch']+1
        conn.execute("UPDATE uac_emergency_control SET epoch=?,latched=0,reason='owner reset; queue stays paused',changed_at=? WHERE singleton=1",(epoch,time.time()))
        if _has(conn,'agent_queue_control'): conn.execute("UPDATE agent_queue_control SET paused=1,reason='emergency reset; explicit resume required' WHERE singleton=1")
        _event(conn,epoch,'reset','Queue remains paused; old job/approval epochs stay invalid')
        _remember(conn,source_key,'reset',str(expected_epoch),epoch)
        return dict(state(conn),event_epoch=epoch,replayed=False)


def admit(conn,kind,detail,*,job_id=None,lease_token=None,expected_epoch=None,commit=True):
    if kind not in ('github_draft_write','provider_dispatch'): raise ValueError('unsupported action admission')
    if not isinstance(detail,str) or not detail or len(detail)>200: raise ValueError('invalid admission detail')
    if type(commit) is not bool or (not commit and not conn.in_transaction): raise ValueError('admission transaction required')
    def locked():
        epoch=require_open(conn,expected_epoch)
        if job_id is not None: check_job(conn,job_id,lease_token)
        return conn.execute("INSERT INTO uac_action_admissions(job_id,epoch,kind,detail,state,admitted_at) VALUES(?,?,?,?,'admitted',?)",(job_id,epoch,kind,detail,time.time())).lastrowid
    if not commit: return locked()
    with atomic(conn): return locked()


def acknowledge(conn,ident,*,unknown=False,commit=True):
    # Bookkeeping is permitted while stopped; it never authorizes another action.
    if type(commit) is not bool or (not commit and not conn.in_transaction): raise ValueError('admission transaction required')
    def locked():
        changed=conn.execute("UPDATE uac_action_admissions SET state=?,finished_at=? WHERE id=? AND state='admitted'",('unknown' if unknown else 'acknowledged',time.time(),ident)).rowcount
        if changed!=1: raise ValueError('admission_already_closed_or_missing')
    if not commit: return locked()
    with atomic(conn): return locked()


def describe(conn):
    current=state(conn);running=conn.execute("SELECT count(*) FROM agent_jobs WHERE state='running'").fetchone()[0] if _has(conn,'agent_jobs') else 0
    unresolved=conn.execute("SELECT count(*) FROM uac_action_admissions WHERE state IN ('admitted','unknown')").fetchone()[0]
    old=conn.execute("SELECT count(*) FROM approvals a LEFT JOIN approval_control_epochs e ON e.approval_id=a.id WHERE a.status IN ('pending','approved') AND (e.epoch IS NULL OR e.epoch<>?)",(current['epoch'],)).fetchone()[0] if _has(conn,'approvals') else 0
    paused=conn.execute('SELECT paused FROM agent_queue_control WHERE singleton=1').fetchone()[0] if _has(conn,'agent_queue_control') else 1
    pending=conn.execute('SELECT count(*) FROM uac_control_outbox WHERE inbox_id IS NULL').fetchone()[0]
    lines=['ULTIMATE · аварийная защита','Блокировка: '+('ВКЛЮЧЕНА' if current['latched'] else 'выключена'),
           'Поколение допуска: '+str(current['epoch']),'Очередь: '+('на паузе' if paused else 'активна'),
           f'Уведомлений, ожидающих очереди доставки: {pending}.',
           f'Текущих заданий: {running}. Допусков без однозначного исхода: {unresolved}. Старых согласований: {old}.',
           'Остановить ULTIMATE: /emergency_stop. Inventory и другие службы эта команда не останавливает.',
           'Новые задачи можно сохранить, но при блокировке они не стартуют. Безопасные ограниченные проверки и уже допущенные запросы могут завершиться; результаты и квитанции сохраняются.',
           'Блокируются новые допуски существующих GitHub Draft/API-посредников и использование согласований. Настоящий исполнитель публикации по-прежнему отключён.',
           'Уже отправленный или ранее допущенный внешний запрос не отменяется; неопределённый исход нужно сверить отдельно. Сброс не разрешает слепой повтор.']
    if current['latched']: lines.append('После завершения текущих заданий: /emergency_reset '+str(current['epoch'])+'. Затем отдельно /resume. Старые согласования остаются недействительными.')
    else: lines.append('Обычная /pause и аварийная блокировка раздельны. /resume снимает только обычную паузу.')
    from datetime import datetime
    from zoneinfo import ZoneInfo
    history=conn.execute('SELECT epoch,operation,at FROM uac_control_events ORDER BY id DESC LIMIT 3').fetchall()
    for epoch,operation,at in history:
        label='стоп' if operation=='stop' else 'сброс'
        stamp=datetime.fromtimestamp(at,ZoneInfo('Asia/Tashkent')).strftime('%d.%m %H:%M')
        lines.append('Журнал: '+label+' · поколение '+str(epoch)+' · '+stamp+' Ташкент')
    for ident,job,kind,status in conn.execute("SELECT id,job_id,kind,state FROM uac_action_admissions WHERE state IN ('admitted','unknown') ORDER BY id DESC LIMIT 4"):
        lines.append('Допуск #'+str(ident)+' · '+kind+' · '+status+(' · /job '+str(job) if job else ''))
    return '\n'.join(lines)
