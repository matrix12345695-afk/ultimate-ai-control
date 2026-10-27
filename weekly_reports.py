"""Calendar-week reports from recorded work; one durable snapshot/notice per period.

No model, billing API, publication or coding automation. Times use Asia/Tashkent.
"""
from datetime import datetime,timedelta,timezone
import json
import math
import time
import worker_observer
import emergency_control as emergency
import owner_notifications as inbox
import task_queue as q
import work_analytics as analytics
import evidence_memory as memory

PROFILE='weekly-calendar-v1'
NAME='weekly-analytics-v1'
ZONE=timezone(timedelta(hours=5),'Asia/Tashkent')
WEEK=7*86400
CONFIG=json.dumps({'target':PROFILE},sort_keys=True)


def initialize(conn):
    conn.executescript('''CREATE TABLE IF NOT EXISTS weekly_analytics_reports(
        period_end INTEGER PRIMARY KEY,job_id INTEGER NOT NULL UNIQUE,snapshot TEXT NOT NULL,
        snapshot_sha256 TEXT NOT NULL,notification_id INTEGER NOT NULL,created_at REAL NOT NULL);
      CREATE TRIGGER IF NOT EXISTS weekly_analytics_no_update BEFORE UPDATE ON weekly_analytics_reports
        BEGIN SELECT RAISE(ABORT,'weekly reports are immutable'); END;
      CREATE TRIGGER IF NOT EXISTS weekly_analytics_no_delete BEFORE DELETE ON weekly_analytics_reports
        BEGIN SELECT RAISE(ABORT,'weekly reports are immutable'); END;''');conn.commit()


def stamp(at):return datetime.fromtimestamp(at,ZONE).strftime('%d.%m.%Y %H:%M')


def latest_due(now):
    local=datetime.fromtimestamp(q._now(now),ZONE)
    monday=(local-timedelta(days=local.weekday())).replace(hour=9,minute=0,second=0,microsecond=0)
    if monday>local:monday-=timedelta(days=7)
    return int(monday.timestamp())


def period_end(now):return latest_due(now)-9*3600


def valid_end(end):
    if type(end) is not int or not 1577836800<=end<=4102444800:return False
    dt=datetime.fromtimestamp(end,ZONE)
    return dt.weekday()==0 and (dt.hour,dt.minute,dt.second,dt.microsecond)==(0,0,0,0)


def payload(end):
    if not valid_end(end):raise ValueError('invalid weekly calendar boundary')
    return {'target':PROFILE,'period_end':end}


def key(end):return 'weekly-report:'+str(end)


def _enqueue(conn,end,now):
    raw=q._json(payload(end));old=conn.execute('SELECT id,project,kind,payload FROM agent_jobs WHERE event_key=?',(key(end),)).fetchone()
    if old:
        if old[1:]!=('control','daily_report',raw):raise ValueError('weekly period event conflict')
        return old[0]
    ident=conn.execute("INSERT INTO agent_jobs(project,kind,payload,event_key,priority,max_attempts,created_at,available_at,updated_at) VALUES('control','daily_report',?,?,55,3,?,?,?)",(raw,key(end),now,now,now)).lastrowid
    q._event(conn,ident,now,'queued');return ident


def enqueue(conn,*,now=None):
    now=q._now(time.time() if now is None else now)
    with q._write(conn):
        emergency.require_open(conn)
        return _enqueue(conn,period_end(now),now)


def seed(conn,*,now=None):
    now=q._now(time.time() if now is None else now)
    with q._write(conn):
        conn.execute('INSERT OR IGNORE INTO agent_schedules VALUES(?,?,?,?,?,?,1)',(NAME,'control','daily_report',CONFIG,WEEK,latest_due(now)+WEEK))
        row=conn.execute('SELECT project,kind,payload,interval_seconds FROM agent_schedules WHERE name=?',(NAME,)).fetchone()
        if row!=('control','daily_report',CONFIG,WEEK):raise ValueError('unknown weekly schedule; no override')


def valid_schedule(row):
    if not row or len(row)!=6:return False
    due=row[4]
    return (row[:4]==('control','daily_report',CONFIG,WEEK) and row[5] in (0,1) and
        type(due) in (int,float) and math.isfinite(due) and valid_end(int(due)-9*3600) and due==int(due))


def tick(conn,now):
    now=q._now(now)
    with q._write(conn):
        if emergency.state(conn)['latched'] or conn.execute('SELECT paused FROM agent_queue_control').fetchone()[0]:return []
        row=conn.execute('SELECT project,kind,payload,interval_seconds,next_due,enabled FROM agent_schedules WHERE name=?',(NAME,)).fetchone()
        if not row or row[5]==0:return []
        due=row[4]
        valid=valid_schedule(row)
        if not valid:
            inbox.create(conn,'ULTIMATE AI CONTROL','critical','Недельное расписание требует проверки','Определение расписания не совпало с разрешённым профилем. Оно не изменено; остальные задания продолжаются.','Проверь /weekly_auto. Расписание отчётов не разрешает разработку, публикации или оплату.',event_key='weekly-schedule-invalid-v1',commit=False)
            return []
        if due>now:return []
        current=latest_due(now)
        ident=_enqueue(conn,current-9*3600,now)
        conn.execute('UPDATE agent_schedules SET next_due=? WHERE name=?',(current+WEEK,NAME))
        return [ident]


def scope(job):
    data=job.get('payload')
    if (job.get('project')!='control' or job.get('kind')!='daily_report' or not isinstance(data,dict)
        or set(data)!={'target','period_end'} or data.get('target')!=PROFILE or not valid_end(data.get('period_end'))):
        raise ValueError('weekly report scope denied')
    return data['period_end']


def observe(conn,job,*,now=None):
    end=scope(job);now=q._now(time.time() if now is None else now)
    if now<end:raise ValueError('weekly report period is not closed')
    return {'schema':PROFILE,'since':end-WEEK,'until':end,'timezone':'Asia/Tashkent','generated_at':now,
            'analytics':analytics.summary(conn,end-WEEK,end),'published':False,'paid_calls':0}


def valid(snapshot,end):
    try:
        a=snapshot['analytics']
        return (set(snapshot)=={'schema','since','until','timezone','generated_at','analytics','published','paid_calls'}
            and snapshot['schema']==PROFILE and valid_end(end) and type(snapshot['until']) is int and snapshot['until']==end
            and snapshot['since']==end-WEEK and snapshot['timezone']=='Asia/Tashkent'
            and q._now(snapshot['generated_at'])>=end and snapshot['published'] is False and type(snapshot['paid_calls']) is int and snapshot['paid_calls']==0
            and a['since']==end-WEEK and a['until']==end and a['idle_seconds'] is None
            and a['work_seconds']==a['measured_seconds']['active']+a['measured_seconds']['testing']
            and ('worker_observation' not in a or worker_observer.valid_report(a['worker_observation']))
            and len(memory.canonical(snapshot).encode())<=16000)
    except (KeyError,TypeError,ValueError,OverflowError):return False


def result(end,sha,notice):return {'weekly_report_id':end,'report_sha256':sha,'notification_id':notice,'published':False}


def complete(conn,job,snapshot,*,now=None):
    end=scope(job);now=q._now(time.time() if now is None else now)
    if not valid(snapshot,end):raise ValueError('invalid weekly observation')
    with q._write(conn):
        q._owned(conn,job['id'],job['lease_token'],now);emergency.check_job(conn,job['id'],job['lease_token'])
        actual=conn.execute('SELECT project,kind,payload,event_key FROM agent_jobs WHERE id=?',(job['id'],)).fetchone()
        if actual!=('control','daily_report',q._json(payload(end)),key(end)):raise ValueError('weekly job identity changed')
        old=conn.execute('SELECT job_id,snapshot_sha256,notification_id FROM weekly_analytics_reports WHERE period_end=?',(end,)).fetchone()
        if old:raise ValueError('weekly period already committed')
        a=snapshot['analytics'];sha=memory.digest(snapshot)
        reason=(stamp(end-WEEK)+' — '+stamp(end)+' · Asia/Tashkent. '+
            'Измерено: '+analytics.duration(a['work_seconds'])+f" Завершено: {a['completed']}. Ошибок: {a['failed']}. "+
            f"Известно по квитанциям API: ${a['settled_microusd']/1000000:.6f}. Неполных: {a['incomplete_receipts']}. "+'Простой без наблюдений неизвестен.')
        notice=inbox.create(conn,'ULTIMATE AI CONTROL','info','Недельный отчёт ULTIMATE',reason[:500],
            f'/weekly_report {end} — роли, проекты, ожидания и резервы. Период фиксирован; резервы показаны на момент подготовки. Это не подтверждение работы полноценной команды ИИ.',task_id=str(job['id']),event_key=key(end),commit=False)
        binding=conn.execute('SELECT project,task_id,kind,title FROM owner_notifications WHERE id=?',(notice,)).fetchone()
        if binding!=('ULTIMATE AI CONTROL',str(job['id']),'info','Недельный отчёт ULTIMATE'):raise ValueError('weekly notification binding conflict')
        conn.execute('INSERT INTO weekly_analytics_reports VALUES(?,?,?,?,?,?)',(end,job['id'],memory.canonical(snapshot),sha,notice,now))
        saved=result(end,sha,notice)
        conn.execute("UPDATE agent_jobs SET state='succeeded',result=?,worker=NULL,lease_token=NULL,lease_until=NULL,updated_at=? WHERE id=?",(q._json(saved),now,job['id']))
        q._event(conn,job['id'],now,'succeeded')
        return saved


def record(conn,end):
    row=conn.execute('SELECT job_id,snapshot,snapshot_sha256,notification_id FROM weekly_analytics_reports WHERE period_end=?',(end,)).fetchone()
    if not row:raise ValueError('weekly report absent')
    snapshot=json.loads(row[1])
    if not valid(snapshot,end) or memory.digest(snapshot)!=row[2]:raise ValueError('weekly report needs evidence review')
    job=conn.execute('SELECT state,result,payload,event_key,project,kind FROM agent_jobs WHERE id=?',(row[0],)).fetchone()
    if (not job or job[0]!='succeeded' or json.loads(job[1])!=result(end,row[2],row[3]) or json.loads(job[2])!=payload(end)
        or job[3:]!=(key(end),'control','daily_report')):raise ValueError('weekly report job changed')
    return snapshot,row[2],row[3]


def describe(conn,end=None):
    if end is None:
        row=conn.execute('SELECT period_end FROM weekly_analytics_reports ORDER BY period_end DESC LIMIT 1').fetchone()
        if not row:return 'Сохранённых недельных отчётов пока нет. /weekly_auto'
        end=row[0]
    if not valid_end(end):raise ValueError('invalid weekly report ID')
    snapshot,sha,notice=record(conn,end);a=snapshot['analytics']
    lines=['📊 Недельный отчёт · Asia/Tashkent',stamp(end-WEEK)+' — '+stamp(end)+' (конец не включён)',
           'Измерено работы: '+analytics.duration(a['work_seconds']),
           f"Завершено: {a['completed']}. Ошибок: {a['failed']}. Повторов: {a['retries_scheduled']}.", 'По типам работ:']
    lines.extend(k+': '+analytics.duration(v) for k,v in sorted(a['by_role'].items()))
    lines.append('По проектам:');lines.extend(k+': '+analytics.duration(v) for k,v in sorted(a['by_project'].items()))
    w=a['waiting_task_seconds'];lines.extend(['Ожидание очереди: '+analytics.duration(w['queued']),
       'Ожидание владельца: '+analytics.duration(w['awaiting_owner']),
       'Ожидания суммируются по задачам; это не простой исполнителя.',
       f"API по квитанциям периода: ${a['settled_microusd']/1000000:.6f}. Неполных квитанций: {a['incomplete_receipts']}.",
       f"Неразрешённые резервы на момент подготовки: {a['unresolved_holds']['count']} · ${a['unresolved_holds']['microusd']/1000000:.6f}.",
       'Простой и незаписанное время: неизвестны. Полноценная команда ИИ этими данными не подтверждается.',
       'Подготовлен: '+stamp(snapshot['generated_at']), 'SHA-256: '+sha])
    if w['unknown_tails']:lines.append('Есть ожидания с неполной историей; показана только известная часть.')
    observed=a.get('worker_observation')
    if observed:
        lines.extend(['Наблюдавшееся ожидание operations-1: '+analytics.duration(observed['observed_wait_seconds']),
                      'Время без наблюдений operations-1: '+analytics.duration(observed['unobserved_seconds'])+'. /worker4'])
    else:lines.append('Этот исторический снимок не содержит новых наблюдений исполнителя; он не пересчитывается.')
    delivery=conn.execute('SELECT delivered_at,telegram_message_id FROM owner_notifications WHERE id=?',(notice,)).fetchone()
    lines.append('Telegram: '+('доставка записана' if delivery and all(delivery) else 'доставка ещё не подтверждена')+'.')
    return '\n'.join(lines)[:3900]


def status(conn):
    row=conn.execute('SELECT project,kind,payload,interval_seconds,next_due,enabled FROM agent_schedules WHERE name=?',(NAME,)).fetchone()
    if row and not valid_schedule(row):return '📆 Недельные отчёты · Asia/Tashkent\nОпределение расписания требует проверки. Оно не перезаписано; остальные задания продолжаются.'
    row=(row[4],row[5]) if row else None
    return ('📆 Недельные отчёты · Asia/Tashkent\n'+('Расписание отсутствует.' if not row else
        ('Включено. Следующий запуск: ' if row[1] else 'Выключено. Сохранённая дата: ')+stamp(row[0]))+
        '\nПонедельник 09:00, за предыдущую календарную неделю. Пропущенные недели не создают очередь старых отчётов.\n/weekly_report — последний сохранённый отчёт. /weekly — текущие скользящие 7 дней.')
