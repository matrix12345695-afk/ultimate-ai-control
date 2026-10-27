"""Read-only analytics from measured intervals, queue events and actual cost receipts.

Task waiting is not worker execution or idle time. Missing observations stay unknown.
Reports make no provider requests and never settle, release or enlarge a reservation.
"""
from collections import defaultdict
from datetime import datetime,timezone,timedelta
import json
import time
import task_queue as queue

ROLES={'review_change':'Разработка','test_release':'Тестирование',
       'inspect_repository':'Мониторинг','check_site':'Мониторинг',
       'daily_report':'Аналитика','plan_change':'Координация'}
STATES={'queued':'queued','claimed':'running','retry_scheduled':'queued',
        'awaiting_owner':'awaiting_owner','succeeded':'succeeded','failed':'failed','cancelled':'cancelled'}


def _waiting(conn,since,until):
    totals={'queued':0.0,'awaiting_owner':0.0}
    rows=conn.execute('''SELECT e.job_id,e.at,e.event,e.detail,j.state,j.updated_at
        FROM agent_job_events e JOIN agent_jobs j ON j.id=e.job_id
        WHERE e.at<? AND j.created_at<?
          AND (j.updated_at>=? OR j.state IN ('queued','running','awaiting_owner'))
        ORDER BY e.job_id,e.at,e.id''',(until,until,since))
    previous=None;state=None;start=None;current=None;updated=None
    unknown_tails=0
    def add(end):
        if state in totals:
            totals[state]+=max(0,min(end,until)-max(start,since))
    for job,at,event,detail,current_state,updated_at in rows:
        next_state=STATES.get(event)
        if event=='lease_expired' and detail in ('queued','failed'): next_state=detail
        if next_state is None: continue
        if job!=previous:
            if previous is not None:
                if updated>=until or current==state: add(until)
                elif state in totals: unknown_tails+=1
            previous=job;state=None;start=at;current=current_state;updated=updated_at
        else: add(at)
        state=next_state;start=at
    if previous is not None:
        if updated>=until or current==state: add(until)
        elif state in totals: unknown_tails+=1
    return dict(totals,unknown_tails=unknown_tails)


def report(conn,since,until):
    since,until=queue._now(since),queue._now(until)
    if not since<until or until-since>31*86400:
        raise ValueError('report window must be positive and at most 31 days')
    # A savepoint gives all queries one snapshot without committing a caller's changes.
    conn.execute('SAVEPOINT uac_analytics_read')
    try:
        categories={name:0.0 for name in ('active','testing','waiting')}
        roles=defaultdict(float);projects=defaultdict(float);workers=defaultdict(float)
        rows=conn.execute('''SELECT s.worker,j.project,j.kind,s.category,
            SUM(MIN(s.ended_at,?)-MAX(s.started_at,?))
            FROM agent_work_spans s JOIN agent_jobs j ON j.id=s.job_id
            WHERE s.started_at<? AND s.ended_at>? GROUP BY s.worker,j.project,j.kind,s.category''',
            (until,since,until,since))
        for worker,project,kind,category,seconds in rows:
            categories[category]+=seconds
            if category in ('active','testing'):
                roles[ROLES.get(kind,'Другие операции')]+=seconds
                projects[project]+=seconds;workers[worker]+=seconds
        events=dict(conn.execute('SELECT event,count(*) FROM agent_job_events WHERE at>=? AND at<? GROUP BY event',(since,until)))
        failures=events.get('failed',0)+conn.execute("SELECT count(*) FROM agent_job_events WHERE event='lease_expired' AND detail='failed' AND at>=? AND at<?",(since,until)).fetchone()[0]
        costs=[{'project':project,'agent':agent,'microusd':cost,'receipts':count,'input_tokens':inputs,'output_tokens':outputs}
               for project,agent,cost,count,inputs,outputs in conn.execute('''SELECT project,agent,SUM(actual_microusd),count(*),SUM(input_tokens),SUM(output_tokens)
                 FROM provider_costs WHERE state='settled' AND actual_microusd IS NOT NULL AND actual_microusd>=0
                 AND settled_at>=? AND settled_at<? GROUP BY project,agent ORDER BY project,agent''',(since,until))]
        incomplete=conn.execute("SELECT count(*) FROM provider_costs WHERE state='settled' AND (actual_microusd IS NULL OR actual_microusd<0 OR settled_at IS NULL)").fetchone()[0]
        holds_count,holds_amount=conn.execute("SELECT count(*),COALESCE(SUM(reserved_microusd),0) FROM provider_costs WHERE state!='settled'").fetchone()
        return {'since':since,'until':until,'measured_seconds':categories,
                'work_seconds':categories['active']+categories['testing'],
                'by_role':dict(roles),'by_project':dict(projects),'by_worker':dict(workers),
                'waiting_task_seconds':_waiting(conn,since,until),
                'completed':events.get('succeeded',0),'failed':failures,
                'retries_scheduled':events.get('retry_scheduled',0),'leases_expired':events.get('lease_expired',0),
                'current_states':dict(conn.execute('SELECT state,count(*) FROM agent_jobs GROUP BY state')),
                'settled_costs':costs,'settled_microusd':sum(row['microusd'] for row in costs),
                'incomplete_receipts':incomplete,
                'unresolved_holds':{'count':holds_count,'microusd':holds_amount},
                'idle_seconds':None,'unmeasured_time':'unknown; never inferred from task age or 24h minus measured work'}
    finally:
        conn.execute('RELEASE SAVEPOINT uac_analytics_read')


def summary(conn,since,until):
    result=report(conn,since,until)
    keys=('since','until','measured_seconds','work_seconds','by_role','by_project',
          'waiting_task_seconds','completed','failed','retries_scheduled','leases_expired',
          'settled_microusd','incomplete_receipts','unresolved_holds','idle_seconds','unmeasured_time')
    return {key:result[key] for key in keys}


def duration(seconds):
    if seconds<60: return f'{seconds:.2f} сек.'
    minutes=int(seconds//60);return f'{minutes//60} ч. {minutes%60} мин.'


def describe(conn,days=1,*,now=None):
    if type(days) is not int or days not in (1,7): raise ValueError('days must be 1 or 7')
    now=queue._now(time.time() if now is None else now)
    result=report(conn,now-days*86400,now)
    stamp=lambda at:datetime.fromtimestamp(at,timezone(timedelta(hours=5),'Asia/Tashkent')).strftime('%d.%m %H:%M')
    lines=[f'📊 Работа за {"24 часа" if days==1 else "7 дней"} · Asia/Tashkent',
           stamp(result['since'])+' — '+stamp(result['until']),
           'Измерено работы: '+duration(result['work_seconds'])+'.',
           'Активное выполнение: '+duration(result['measured_seconds']['active'])+' Тестирование: '+duration(result['measured_seconds']['testing']),
           '\nТипы работ очереди:']
    lines.extend(f'{role}: {duration(seconds)}' for role,seconds in sorted(result['by_role'].items()))
    if not result['by_role']: lines.append('Измеренных интервалов нет.')
    if result['by_worker']:
        lines.append('Исполнители: '+'; '.join(f'{worker[:40]} · {duration(seconds)}' for worker,seconds in sorted(result['by_worker'].items())[:3]))
    lines.append('\nПо проектам:')
    lines.extend(f'{project}: {duration(seconds)}' for project,seconds in sorted(result['by_project'].items()))
    waiting=result['waiting_task_seconds']
    lines.extend([f'\nЗавершено: {result["completed"]}. Ошибок завершения: {result["failed"]}.',
                  f'Повторов назначено: {result["retries_scheduled"]}. Истекших аренд: {result["leases_expired"]}.',
                  f'Сейчас ожидают владельца: {result["current_states"].get("awaiting_owner",0)}. Причины и действия: /owner_later.',
                  'Ожидание в очереди по журналу: '+duration(waiting['queued']),
                  'Ожидание владельца по журналу: '+duration(waiting['awaiting_owner']),
                  'Ожидания суммируются по задачам; это не время работы или простоя агента.',
                  'Квитанции API за период: $'+f'{result["settled_microusd"]/1_000_000:.6f}'+'.'])
    for row in result['settled_costs'][:8]:
        lines.append(f'{row["project"][:40]} / {row["agent"][:40]}: ${row["microusd"]/1_000_000:.6f}')
    if len(result['settled_costs'])>8: lines.append('Показаны первые 8 групп; полные квитанции сохранены в журнале.')
    holds=result['unresolved_holds']
    lines.append(f'Неразрешённые резервы сейчас: {holds["count"]} · ${holds["microusd"]/1_000_000:.6f}. Это не подтверждённый расход.')
    if result['incomplete_receipts']: lines.append('Есть неполные квитанции; показан только известный расход, итог требует сверки.')
    if waiting['unknown_tails']: lines.append('Часть ожидания неизвестна из-за неполного журнала состояний.')
    lines.extend(['Простой и незаписанное время: неизвестны. Измерения не доказывают работу полноценной команды ИИ.',
                  '/analytics4 24h · /analytics4 7d · /cost4 <номер задачи>'])
    return '\n'.join(lines)


def job_cost(conn,ident):
    if type(ident) is not int or not 1<=ident<=9223372036854775807: raise ValueError('invalid job ID')
    job=conn.execute('SELECT project,kind,state FROM agent_jobs WHERE id=?',(ident,)).fetchone()
    if not job: return 'Задача не найдена.'
    rows=conn.execute('''SELECT state,count(*),COALESCE(SUM(CASE WHEN state='settled' THEN CASE WHEN actual_microusd>=0 THEN actual_microusd ELSE 0 END ELSE reserved_microusd END),0),
        SUM(input_tokens),SUM(output_tokens),SUM(state='settled' AND (actual_microusd IS NULL OR actual_microusd<0 OR settled_at IS NULL))
        FROM provider_costs WHERE job_id=? GROUP BY state''',(ident,)).fetchall()
    lines=[f'Задача #{ident} · {job[0]} · {job[1]} · {job[2]}']
    for state,count,amount,inputs,outputs,incomplete in rows:
        label='Подтверждено квитанциями' if state=='settled' else 'Неразрешённый резерв ('+state+')'
        if incomplete: label='Квитанции неполны; известная часть расхода'
        lines.append(f'{label}: ${amount/1_000_000:.6f} · записей {count}.')
        if state=='settled': lines.append(f'Токены по квитанциям: вход {inputs if inputs is not None else "неизвестен"}, выход {outputs if outputs is not None else "неизвестен"}.')
    if not rows: lines.append('API-квитанций и резервов у задачи нет; учтённый расход $0.')
    lines.append('Это локальный реестр, не счёт провайдера. Просмотр не меняет резервы или бюджет $30.')
    return '\n'.join(lines)
