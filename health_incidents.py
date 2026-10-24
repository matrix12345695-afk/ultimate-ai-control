"""Atomic availability results, scoped incident recovery and transactional notifications."""
from datetime import datetime,timezone,timedelta
import hashlib
import json
import math
import re
import time
import task_queue as queue
from owner_notifications import create
import readiness_monitor

TARGETS={'nova':'https://novaweb.uz/',readiness_monitor.TARGET:readiness_monitor.URL}
TARGET_PROJECTS={target:'nova' for target in TARGETS}
TITLES={'nova':'Состояние NOVA WEB изменилось',readiness_monitor.TARGET:'Готовность API NOVA WEB изменилась'}
RECOVERIES={'nova':'Доступность NOVA WEB восстановлена',readiness_monitor.TARGET:'Готовность API NOVA WEB восстановлена'}
PROJECT='ULTIMATE AI CONTROL'


def initialize(conn):
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS agent_health_incidents(
      id INTEGER PRIMARY KEY,target TEXT NOT NULL,notification_id INTEGER NOT NULL UNIQUE,
      opened_job_id INTEGER,source TEXT NOT NULL,opened_at REAL NOT NULL,
      state TEXT NOT NULL CHECK(state IN ('open','recovered')),
      recovery_job_id INTEGER,recovery_notification_id INTEGER,recovered_at REAL);
    CREATE INDEX IF NOT EXISTS health_incident_target_state ON agent_health_incidents(target,state);
    CREATE TABLE IF NOT EXISTS agent_health_incident_events(
      id INTEGER PRIMARY KEY,incident_id INTEGER NOT NULL,job_id INTEGER,event TEXT NOT NULL,
      at REAL NOT NULL,UNIQUE(incident_id,job_id,event));
    ''')
    conn.commit()


def parsed(raw):
    try: value=json.loads(raw)
    except (TypeError,ValueError): return {}
    return value if isinstance(value,dict) else {}


def origin(conn,note,target,observed):
    ident,project,kind,title,reason,task,key,created=note
    if kind!='critical': return None
    try:
        stamp=datetime.fromisoformat(created)
        if stamp.tzinfo is None or stamp.timestamp()>observed: return None
    except (TypeError,ValueError,OverflowError): return None
    if (project==PROJECT and title==TITLES[target] and isinstance(task,str) and
        re.fullmatch(r'[1-9][0-9]{0,18}',task) and int(task)<=9223372036854775807 and key=='health-job-'+task):
        job=conn.execute('SELECT project,kind,state,payload,result,updated_at FROM agent_jobs WHERE id=?',(int(task),)).fetchone()
        if job and job[:3]==(TARGET_PROJECTS[target],'check_site','succeeded') and job[5]<=observed:
            payload=parsed(job[3]);result=parsed(job[4])
            if payload.get('target')==target and result.get('target')==target and result.get('url')==TARGETS[target] and result.get('healthy') is False:
                if target==readiness_monitor.TARGET and not readiness_monitor.valid_result(result,stored=True): return None
                return int(task),'queue',job[5]
    # The older hourly poller has no queue job. Recognize only its fixed first-party
    # format, canonical URL, title, project and reproducible hourly event fingerprint.
    if target=='nova' and project=='monitoring' and title=='Изменилось состояние сайта' and task is None:
        pattern=r'^(WARNING|DOWN) '+re.escape(TARGETS[target])+r': unavailable \([A-Za-z][A-Za-z0-9_]{0,60}\)$'
        if isinstance(reason,str) and re.fullmatch(pattern,reason):
            hours=[stamp.astimezone(timezone.utc)]
            if stamp.minute==0 and stamp.second<2: hours.append(hours[0]-timedelta(hours=1))
            if any(key==hashlib.sha256((project+kind+title+reason+hour.strftime('%Y%m%d%H')).encode()).hexdigest() for hour in hours):
                return None,'legacy-poller',stamp.timestamp()
    return None


def import_legacy(conn,target,observed):
    rows=conn.execute('''SELECT n.id,n.project,n.kind,n.title,n.reason,n.task_id,n.event_key,n.created_at
      FROM owner_notifications n WHERE n.kind='critical' AND n.state='pending'
      AND ((n.project='ULTIMATE AI CONTROL' AND n.title=? AND n.event_key LIKE 'health-job-%')
        OR (?='nova' AND n.project='monitoring' AND n.title='Изменилось состояние сайта'))
      AND NOT EXISTS(SELECT 1 FROM agent_health_incidents i WHERE i.notification_id=n.id)
      ORDER BY n.id LIMIT 100''',(TITLES[target],target)).fetchall()
    for row in rows:
        proof=origin(conn,row,target,observed)
        if proof:
            job,source,opened=proof
            ident=conn.execute("INSERT INTO agent_health_incidents(target,notification_id,opened_job_id,source,opened_at,state) VALUES(?,?,?,?,?,'open')",(target,row[0],job,source,opened)).lastrowid
            conn.execute('INSERT INTO agent_health_incident_events(incident_id,job_id,event,at) VALUES(?,?,?,?)',(ident,job,'imported',time.time()))


def complete(conn,job,result,*,observed_at=None,now=None):
    now=queue._now(now)
    observed=now if observed_at is None else observed_at
    if type(observed) not in (int,float) or not math.isfinite(observed) or observed>now: raise ValueError('invalid health observation time')
    target=job['payload'].get('target')
    if (target not in TARGETS or job['project']!=TARGET_PROJECTS[target] or job['kind']!='check_site' or set(job['payload'])!={'target'} or
        not isinstance(result,dict) or result.get('target')!=target or result.get('url')!=TARGETS[target] or type(result.get('healthy')) is not bool or
        not isinstance(result.get('detail'),str) or not 1<=len(result['detail'])<=100):
        raise ValueError('health result is outside configured scope')
    if target==readiness_monitor.TARGET:
        if not readiness_monitor.valid_result(result): raise ValueError('readiness contract evidence invalid')
    else:
        if result['healthy'] and not re.fullmatch(r'HTTP [23][0-9]{2}',result['detail']): raise ValueError('healthy result needs HTTP evidence')
        if not result['healthy'] and re.fullmatch(r'HTTP [23][0-9]{2}',result['detail']): raise ValueError('health verdict contradicts HTTP evidence')
    with queue._write(conn):
        owned=queue._owned(conn,job['id'],job['lease_token'],now)
        stored=conn.execute('SELECT project,kind,payload FROM agent_jobs WHERE id=?',(job['id'],)).fetchone()
        if stored[:2]!=(TARGET_PROJECTS[target],'check_site') or parsed(stored[2])!=job['payload'] or observed<owned[3]:
            raise PermissionError('health job identity or observation changed')
        old=conn.execute('SELECT healthy,checked_at FROM agent_health WHERE target=?',(target,)).fetchone()
        final=dict(result,observed_at=observed,resolved_incidents=0)
        if old and old[1]>observed:
            final['superseded']=True
        else:
            import_legacy(conn,target,observed)
            if result['healthy']:
                eligible=[]
                for row in conn.execute('''SELECT n.id,n.project,n.kind,n.title,n.reason,n.task_id,n.event_key,n.created_at,i.id
                  FROM agent_health_incidents i JOIN owner_notifications n ON n.id=i.notification_id
                  WHERE i.target=? AND i.state='open' ''',(target,)).fetchall():
                    if origin(conn,row[:8],target,observed): eligible.append((row[0],row[8]))
                if (old and not old[0]) or eligible:
                    note=create(conn,PROJECT,'info',RECOVERIES[target],
                        TARGETS[target]+': '+result['detail']+f'. Проверка #{job["id"]}; закрыто прежних тревог: {len(eligible)}.',
                        'Доступность подтверждена новой проверкой. История тревог сохранена; остальные запросы владельцу продолжают действовать.',
                        task_id=str(job['id']),event_key='health-recovery-job-'+str(job['id']),commit=False)
                    stamp=datetime.fromtimestamp(now,timezone.utc).isoformat()
                    for notification,incident in eligible:
                        conn.execute("UPDATE owner_notifications SET state='resolved',resolved_at=? WHERE id=? AND kind='critical' AND state='pending'",(stamp,notification))
                        conn.execute("UPDATE agent_health_incidents SET state='recovered',recovery_job_id=?,recovery_notification_id=?,recovered_at=? WHERE id=?",(job['id'],note,now,incident))
                        conn.execute('INSERT INTO agent_health_incident_events(incident_id,job_id,event,at) VALUES(?,?,?,?)',(incident,job['id'],'recovered',now))
                    final['resolved_incidents']=len(eligible)
            else:
                open_one=conn.execute("SELECT id FROM agent_health_incidents WHERE target=? AND state='open' LIMIT 1",(target,)).fetchone()
                if old is None or bool(old[0]) or not open_one:
                    note=create(conn,PROJECT,'critical',TITLES[target],TARGETS[target]+': '+result['detail'],
                        'Проверь /monitor4. Доступность нарушена; независимые задания продолжаются.',
                        task_id=str(job['id']),event_key='health-job-'+str(job['id']),commit=False)
                    cur=conn.execute("INSERT OR IGNORE INTO agent_health_incidents(target,notification_id,opened_job_id,source,opened_at,state) VALUES(?,?,?,'queue',?,'open')",(target,note,job['id'],now))
                    if cur.rowcount: conn.execute('INSERT INTO agent_health_incident_events(incident_id,job_id,event,at) VALUES(?,?,?,?)',(cur.lastrowid,job['id'],'opened',now))
            conn.execute('INSERT INTO agent_health VALUES(?,?,?,?) ON CONFLICT(target) DO UPDATE SET healthy=excluded.healthy,detail=excluded.detail,checked_at=excluded.checked_at',(target,int(result['healthy']),result['detail'],observed))
        conn.execute("UPDATE agent_jobs SET state='succeeded',result=?,worker=NULL,lease_token=NULL,lease_until=NULL,updated_at=? WHERE id=?",(queue._json(final),now,job['id']))
        queue._event(conn,job['id'],now,'succeeded','availability and incident state committed together')
        return final


def describe(conn):
    lines=['Мониторинг ULTIMATE']
    for target,healthy,detail,checked in conn.execute('SELECT target,healthy,detail,checked_at FROM agent_health ORDER BY target'):
        state=('готов' if healthy else 'не готов') if target==readiness_monitor.TARGET else ('доступен' if healthy else 'проблема доступности')
        stamp=datetime.fromtimestamp(checked,timezone.utc).strftime('%d.%m %H:%M UTC')
        lines.append(f'{target}: {state} · {detail} · {stamp}')
        if target==readiness_monitor.TARGET:
            lines.append('API и PostgreSQL: результат публичного /health; это не проверка всех бизнес-функций.')
            rows=conn.execute("SELECT result FROM agent_jobs WHERE project='nova' AND kind='check_site' AND state='succeeded' ORDER BY updated_at DESC,id DESC LIMIT 30").fetchall()
            for raw, in rows:
                result=parsed(raw)
                if readiness_monitor.valid_result(result,stored=True) and result.get('observed_at')==checked:
                    labels=('HTTP','JSON','Приложение','PostgreSQL','Версия')
                    lines.append(' · '.join(label+(' ✅' if result['checks'][key] else ' ❌') for label,key in zip(labels,readiness_monitor.CHECKS)))
                    break
    counts=dict(conn.execute('SELECT state,count(*) FROM agent_health_incidents GROUP BY state'))
    lines.append(f'Открытых тревог: {counts.get("open",0)}. Подтверждённых восстановлений: {counts.get("recovered",0)}.')
    lines.append('Старые тревоги закрываются только по более свежей успешной проверке того же сайта. История и Telegram-квитанции сохраняются.')
    return '\n'.join(lines)
