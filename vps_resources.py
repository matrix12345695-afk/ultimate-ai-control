"""Bounded read-only host observations and atomic, scoped resource incidents."""
from datetime import datetime,timezone
import hashlib
import json
import math
import os
from pathlib import Path
import time
import task_queue as q
from owner_notifications import create

TARGET='vps-resources-v1'
SCHEDULE='vps-resources-v1'
METRICS=('cpu','memory','disk','inodes','telemetry')
LABELS={'cpu':'Нагрузка CPU','memory':'Доступная память','disk':'Свободное место','inodes':'Свободные inode','telemetry':'Сбор показателей'}
MIN_GAP=60
MAX_GAP=900


def initialize(conn):
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS vps_resource_samples(
      id INTEGER PRIMARY KEY,job_id INTEGER NOT NULL UNIQUE,observed_at REAL NOT NULL,
      sample TEXT NOT NULL,report TEXT NOT NULL,report_sha256 TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS vps_resource_streaks(
      metric TEXT PRIMARY KEY,bad INTEGER NOT NULL,good INTEGER NOT NULL,last_at REAL NOT NULL,boot INTEGER);
    CREATE TABLE IF NOT EXISTS vps_resource_incidents(
      id INTEGER PRIMARY KEY,metric TEXT NOT NULL,opened_job_id INTEGER NOT NULL,
      notification_id INTEGER NOT NULL UNIQUE,state TEXT NOT NULL CHECK(state IN ('open','recovered')),
      recovered_job_id INTEGER,recovery_notification_id INTEGER);
    CREATE UNIQUE INDEX IF NOT EXISTS vps_resource_one_open ON vps_resource_incidents(metric) WHERE state='open';
    ''')
    conn.commit()


def read(path,limit):
    with Path(path).open('rb') as stream: raw=stream.read(limit+1)
    if len(raw)>limit: raise ValueError('proc_read_limit')
    return raw.decode('ascii')


def collect(data,*,proc=Path('/proc'),statvfs=os.statvfs,clock=time.time):
    sample={'schema':TARGET,'cpu':None,'boot':None,'cores':None,'memory':None,'disk':None,'inodes':None,'load':None,'errors':[]}
    try:
        rows=read(proc/'stat',65536).splitlines();parts=rows[0].split()
        if parts[0]!='cpu' or len(parts)<9: raise ValueError('cpu_shape')
        counters=[int(x) for x in parts[1:9]] # guest values already included in user/nice
        boot=int(next(row.split()[1] for row in rows if row.startswith('btime ')))
        cores=sum(row.startswith('cpu') and len(row.split()[0])>3 and row.split()[0][3:].isdigit() for row in rows)
        if min(counters)<0 or boot<=0 or cores<=0: raise ValueError('cpu_values')
        sample.update(cpu=counters,boot=boot,cores=cores)
    except (OSError,ValueError,IndexError,StopIteration,UnicodeError): sample['errors'].append('cpu')
    try:
        info={row.split(':')[0]:row.split(':',1)[1].split() for row in read(proc/'meminfo',65536).splitlines() if ':' in row}
        if any(len(info[k])!=2 or info[k][1]!='kB' for k in ('MemTotal','MemAvailable')): raise ValueError('memory_units')
        total,available=[int(info[k][0])*1024 for k in ('MemTotal','MemAvailable')]
        if not 0<=available<=total or total<=0: raise ValueError('memory_values')
        sample['memory']=[total,available]
    except (OSError,ValueError,KeyError,IndexError,UnicodeError): sample['errors'].append('memory')
    try:
        fs=statvfs(data);total,available=fs.f_blocks*fs.f_frsize,fs.f_bavail*fs.f_frsize
        if not 0<=available<=total or total<=0: raise ValueError('disk_values')
        sample['disk']=[total,available]
        if fs.f_files>0 and 0<=fs.f_favail<=fs.f_files: sample['inodes']=[fs.f_files,fs.f_favail]
        else: sample['errors'].append('inodes')
    except (OSError,ValueError): sample['errors'].append('disk')
    try:
        load=[float(x) for x in read(proc/'loadavg',256).split()[:3]]
        if len(load)!=3 or any(not math.isfinite(x) or x<0 for x in load): raise ValueError('load_values')
        sample['load']=load
    except (OSError,ValueError,UnicodeError): sample['errors'].append('load')
    sample['observed_at']=clock()
    validate(sample)
    return sample


def validate(sample):
    keys={'schema','cpu','boot','cores','memory','disk','inodes','load','errors','observed_at'}
    if not isinstance(sample,dict) or set(sample)!=keys or sample['schema']!=TARGET: raise ValueError('resource_sample_scope')
    at=sample['observed_at']
    if type(at) not in (int,float) or not math.isfinite(at) or at<=0: raise ValueError('resource_sample_time')
    errors=sample['errors']
    if not isinstance(errors,list) or len(errors)!=len(set(errors)) or set(errors)-{'cpu','memory','disk','inodes','load'}: raise ValueError('resource_sample_errors')
    for name in ('memory','disk','inodes'):
        value=sample[name]
        if value is not None and (not isinstance(value,list) or len(value)!=2 or any(type(x) is not int for x in value) or not 0<=value[1]<=value[0] or value[0]<=0): raise ValueError('resource_sample_values')
        if value is None and name not in errors and not (name=='inodes' and 'disk' in errors): raise ValueError('resource_missing_evidence')
        if value is not None and name in errors: raise ValueError('resource_conflicting_evidence')
    if sample['cpu'] is None:
        if sample['boot'] is not None or sample['cores'] is not None or 'cpu' not in errors: raise ValueError('cpu_missing_evidence')
    elif ('cpu' in errors or not isinstance(sample['cpu'],list) or len(sample['cpu'])!=8 or any(type(x) is not int or x<0 for x in sample['cpu']) or type(sample['boot']) is not int or sample['boot']<=0 or type(sample['cores']) is not int or sample['cores']<=0): raise ValueError('cpu_evidence_values')
    load=sample['load']
    if load is None:
        if 'load' not in errors: raise ValueError('load_missing_evidence')
    elif 'load' in errors or not isinstance(load,list) or len(load)!=3 or any(type(x) not in (int,float) or not math.isfinite(x) or x<0 for x in load): raise ValueError('load_values')


def assess(sample,previous):
    values={'cpu':None,'memory':sample['memory'],'disk':sample['disk'],'inodes':sample['inodes'],'telemetry':sample['errors']}
    interval=None
    if (previous and sample['cpu'] is not None and previous.get('cpu') is not None and
            sample['boot']==previous['boot'] and sample['cores']==previous['cores']):
        elapsed=sample['observed_at']-previous['observed_at']
        delta=[new-old for new,old in zip(sample['cpu'],previous['cpu'])]
        if MIN_GAP<=elapsed<=MAX_GAP and min(delta)>=0 and sum(delta)>0:
            values['cpu']=round(100*(sum(delta)-delta[3]-delta[4])/sum(delta),2);interval=elapsed
    grades={}
    for metric,value in values.items():
        if value is None: grades[metric]='unknown';continue
        if metric=='cpu': bad=value>=90;good=value<75
        elif metric=='telemetry': bad=bool(value);good=not value
        else:
            total,available=value;fraction=available/total
            bad=fraction<=({'inodes':.05}.get(metric,.10))
            good=fraction>({'inodes':.08}.get(metric,.15))
            floor={'memory':512*1024**2,'disk':2*1024**3}.get(metric,0)
            recover={'memory':768*1024**2,'disk':3*1024**3}.get(metric,0)
            bad=bad or available<=floor;good=good and available>recover
        grades[metric]='bad' if bad else ('good' if good else 'band')
    return values,grades,interval


def canonical(value): return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(value): return hashlib.sha256(canonical(value).encode()).hexdigest()


def scope(job):
    if job.get('project')!='control' or job.get('kind')!='inspect_repository' or job.get('payload')!={'target':TARGET}: raise PermissionError('resource_job_scope')


def complete(conn,job,sample,*,now=None):
    scope(job);validate(sample);now=q._now(now);observed=sample['observed_at']
    with q._write(conn):
        owned=q._owned(conn,job['id'],job['lease_token'],now)
        stored=conn.execute('SELECT project,kind,payload FROM agent_jobs WHERE id=?',(job['id'],)).fetchone()
        if stored[:2]!=('control','inspect_repository') or json.loads(stored[2])!={'target':TARGET} or not owned[3]<=observed<=now: raise PermissionError('resource_job_observation_changed')
        last=conn.execute('SELECT observed_at,sample FROM vps_resource_samples ORDER BY observed_at DESC,id DESC LIMIT 1').fetchone()
        previous=json.loads(last[1]) if last else None
        values,grades,interval=assess(sample,previous)
        report={'schema':TARGET,'observed_at':observed,'values':values,'grades':grades,'cpu_interval_seconds':interval,
                'cores':sample['cores'],'load':sample['load'],'superseded':bool(last and observed<=last[0]),'opened':[],'recovered':[]}
        if not report['superseded']:
            for metric,grade in grades.items():
                old=conn.execute('SELECT bad,good,last_at,boot FROM vps_resource_streaks WHERE metric=?',(metric,)).fetchone()
                if old and observed-old[2]<MIN_GAP: continue # manual bursts cannot advance alarm or recovery
                adjacent=old and observed-old[2]<=MAX_GAP and old[3]==sample['boot']
                bad=(old[0] if adjacent else 0)+1 if grade=='bad' else 0
                good=(old[1] if adjacent else 0)+1 if grade=='good' else 0
                conn.execute('INSERT INTO vps_resource_streaks VALUES(?,?,?,?,?) ON CONFLICT(metric) DO UPDATE SET bad=excluded.bad,good=excluded.good,last_at=excluded.last_at,boot=excluded.boot',
                             (metric,min(bad,2),min(good,2),observed,sample['boot']))
                incident=conn.execute("SELECT id,notification_id FROM vps_resource_incidents WHERE metric=? AND state='open'",(metric,)).fetchone()
                if bad>=2 and not incident:
                    note=create(conn,'ULTIMATE AI CONTROL','critical','Ресурсы VPS: '+LABELS[metric],
                                'Два измерения подтвердили проблему. Метрика: '+metric+'. Проверка #'+str(job['id'])+'.',
                                'Открой /vps4. Автоматическая очистка, остановка и перезапуск сервисов не выполняются.',
                                task_id=str(job['id']),event_key='vps-resource-open-'+metric+'-'+str(job['id']),commit=False)
                    ident=conn.execute("INSERT INTO vps_resource_incidents(metric,opened_job_id,notification_id,state) VALUES(?,?,?,'open')",(metric,job['id'],note)).lastrowid
                    report['opened'].append(ident)
                elif good>=2 and incident:
                    note=create(conn,'ULTIMATE AI CONTROL','info','Ресурсы VPS восстановлены: '+LABELS[metric],
                                'Два измерения подтвердили восстановление. Проверка #'+str(job['id'])+'.',
                                'История сохранена. /vps4. Сервисы и файлы не изменялись.',task_id=str(job['id']),
                                event_key='vps-resource-recovery-'+str(incident[0]),commit=False)
                    stamp=datetime.fromtimestamp(now,timezone.utc).isoformat()
                    # Only the exact notification linked to this typed incident can resolve.
                    conn.execute("UPDATE owner_notifications SET state='resolved',resolved_at=? WHERE id=? AND kind='critical' AND state='pending' AND project='ULTIMATE AI CONTROL' AND event_key LIKE ?",(stamp,incident[1],'vps-resource-open-'+metric+'-%'))
                    conn.execute("UPDATE vps_resource_incidents SET state='recovered',recovered_job_id=?,recovery_notification_id=? WHERE id=?",(job['id'],note,incident[0]))
                    report['recovered'].append(incident[0])
        sha=digest(report)
        ident=conn.execute('INSERT INTO vps_resource_samples(job_id,observed_at,sample,report,report_sha256) VALUES(?,?,?,?,?)',
                           (job['id'],observed,canonical(sample),canonical(report),sha)).lastrowid
        result={'resource_sample_id':ident,'report_sha256':sha,'observed_at':observed,'grades':grades,'opened':report['opened'],'recovered':report['recovered'],'read_only':True,'published':False}
        conn.execute("UPDATE agent_jobs SET state='succeeded',result=?,worker=NULL,lease_token=NULL,lease_until=NULL,updated_at=? WHERE id=?",(q._json(result),now,job['id']))
        q._event(conn,job['id'],now,'succeeded','read-only VPS sample and resource incidents committed together')
        return result


def seed(conn,now=None):
    now=time.time() if now is None else now
    conn.execute('INSERT OR IGNORE INTO agent_schedules(name,project,kind,payload,interval_seconds,next_due) VALUES(?,?,?,?,?,?)',
                 (SCHEDULE,'control','inspect_repository',canonical({'target':TARGET}),300,now+300));conn.commit()


def describe(conn,*,now=None):
    now=time.time() if now is None else now
    row=conn.execute('SELECT job_id,report,report_sha256 FROM vps_resource_samples ORDER BY observed_at DESC,id DESC LIMIT 1').fetchone()
    lines=['Ресурсы VPS · чтение без изменения сервисов']
    if not row: return '\n'.join(lines+['Замеров пока нет. /vps_check'])
    report=json.loads(row[1])
    if digest(report)!=row[2]: return '\n'.join(lines+['Отчёт изменён; нужна повторная проверка. /vps_check'])
    stamp=datetime.fromtimestamp(report['observed_at'],timezone.utc).strftime('%d.%m %H:%M:%S UTC')
    lines.append('Замер: '+stamp+' · /job '+str(row[0]))
    if now-report['observed_at']>MAX_GAP: lines.append('Данные устарели; текущее состояние не подтверждено.')
    values=report['values']
    if values['cpu'] is None: lines.append('CPU: недостаточно двух сопоставимых замеров.')
    else: lines.append(f"CPU: {values['cpu']:.2f}% за {report['cpu_interval_seconds']:.0f} сек., суммарно по {report['cores']} ядрам.")
    for metric in ('memory','disk','inodes'):
        pair=values[metric]
        if pair is None: lines.append(LABELS[metric]+': нет данных.');continue
        total,available=pair
        unit=f'{available/1024**3:.2f} / {total/1024**3:.2f} ГиБ' if metric!='inodes' else f'{available} / {total}'
        lines.append(LABELS[metric]+': '+unit+f' · свободно {100*available/total:.1f}%')
    if report['load'] is not None: lines.append('Load 1/5/15 мин: '+' / '.join(str(x) for x in report['load'])+' (это не процент CPU).')
    if values['telemetry']: lines.append('Недоступные показатели: '+', '.join(values['telemetry']))
    count=conn.execute("SELECT count(*) FROM vps_resource_incidents WHERE state='open'").fetchone()[0]
    lines.append(f'Открытых ресурсных тревог: {count}. Два подтверждения с интервалом ≥60 сек.; разрыв >15 мин сбрасывает серию.')
    lines.append('Новый замер: /vps_check. Раздел данных ULTIMATE; память/CPU всего VPS. Остановка, очистка и перезапуск не выполняются.')
    return '\n'.join(lines)
