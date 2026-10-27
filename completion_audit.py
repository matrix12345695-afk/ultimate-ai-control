"""Read-only handover status from recorded facts; no invented completion or new requests."""
import json
from pathlib import Path
import roadmap
import worker_observer

# The installed application still has no live publisher; simulation is not a deploy adapter.
LIVE_PUBLISHER_IMPLEMENTED=False
ENGINEERING_REMAINS=('Исполнитель публикаций и проверенный рабочий откат ещё не подключены.',
    'Общий цикл разработки с моделью и охват остальных проектов ещё не проверены.')


def voice_confirmed(conn):
    import voice_native
    import voice_flow_test as flow
    rows=conn.execute("SELECT id,task_id,receipt,receipt_sha256 FROM voice_inputs WHERE state='confirmed' ORDER BY id DESC LIMIT 50")
    for ident,job,raw,sha in rows:
        try:
            receipt=json.loads(raw);task=conn.execute('SELECT kind,payload FROM agent_jobs WHERE id=?',(job,)).fetchone()
            event=conn.execute("SELECT 1 FROM agent_job_events WHERE job_id=? AND event='voice_confirmed'",(job,)).fetchone()
            payload=json.loads(task[1]) if task else {}
            if (voice_native.valid_receipt(receipt) and flow.local_voice.util.digest(receipt)==sha and task and task[0]=='plan_change' and event
                and isinstance(payload,dict) and isinstance(payload.get('text'),str) and payload.get('source')=='voice_confirmed' and payload.get('voice_input_id')==ident
                and flow.local_voice.assets.digest(payload.get('text','').encode())==receipt['transcript_sha256']):return True
        except (ValueError,TypeError,KeyError):continue
    return False


def snapshot(conn,*,now=None):
    conn.execute('SAVEPOINT completion_audit')
    try:
        stages=[{'id':ident,'title':title,'state':state} for ident,title,state in conn.execute('SELECT id,title,state FROM uac_roadmap ORDER BY id')]
        paid_receipts=conn.execute("SELECT count(*) FROM provider_costs WHERE state='settled' AND actual_microusd>=0 AND settled_at IS NOT NULL").fetchone()[0]
        model_bundles=conn.execute("SELECT count(*) FROM developer_bundles WHERE engine='openai_broker'").fetchone()[0]
        pending=dict(conn.execute("SELECT kind,count(*) FROM owner_notifications WHERE state='pending' AND kind IN ('critical','decision') GROUP BY kind"))
        weekly=False
        row=conn.execute('SELECT period_end FROM weekly_analytics_reports ORDER BY period_end DESC LIMIT 1').fetchone()
        if row:
            import weekly_reports
            try:weekly_reports.record(conn,row[0]);weekly=True
            except (ValueError,TypeError):pass
        return {'full_plan_complete':False,'stages':stages,'provider_setup_deferred':roadmap.setting(conn,'provider_setup_deferred')=='true',
                'recorded_paid_receipts':paid_receipts,'recorded_model_bundles':model_bundles,'live_publisher_implemented':LIVE_PUBLISHER_IMPLEMENTED,
                'genuine_voice_confirmation_recorded':voice_confirmed(conn),'weekly_snapshot_verified':weekly,
                'pending_owner':pending,'worker_signal':worker_observer.current(conn,now=now),
                'engineering_remaining':list(ENGINEERING_REMAINS)}
    finally:conn.execute('RELEASE SAVEPOINT completion_audit')


def describe(conn,*,now=None):
    data=snapshot(conn,now=now);labels={'done':'✅ выполнено','active':'в работе','blocked':'есть препятствие','planned':'запланировано'}
    lines=['ULTIMATE 4.0 · готовность','Полный план ещё не завершён. Проверенные части сохраняются отдельно.', '\nЭтапы:']
    lines.extend(str(row['id'])+'. '+row['title']+' — '+labels.get(row['state'],'требует проверки') for row in data['stages'])
    lines.append('\nЧто требует участия владельца:')
    if data['provider_setup_deferred']:lines.append('API отложен вами. Повторного запроса на ключ нет; пока продолжаются независимые работы.')
    elif not (data['recorded_paid_receipts'] and data['recorded_model_bundles']):lines.append('Реальная задача с моделью и финансовой квитанцией ещё не подтверждена. /provider4')
    if not data['genuine_voice_confirmation_recorded']:lines.append('Первая настоящая голосовая и проверка её текста ещё ожидаются; исходный запрос уже сохранён. /voice4')
    else:lines.append('Есть подтверждённая голосовая задача; это не полная проверка RU/UZ качества.')
    lines.append('Нерешённые запросы: критических '+str(data['pending_owner'].get('critical',0))+', решений '+str(data['pending_owner'].get('decision',0))+'. /owner_later')
    lines.append('\nЧто остаётся разработать:');lines.extend(data['engineering_remaining'])
    lines.extend(['Мониторинг, очередь, отчёты и ограниченные тесты работают отдельно от общего AI-разработчика.',
                  'Публикации требуют точного согласования. Inventory защищён. /worker4 — состояние исполнителя; /roadmap — выполненные части.'])
    return '\n'.join(lines)[:3900]
