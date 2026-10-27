"""Owner voice inbox: private audio, immutable recognition receipt, explicit task confirmation."""
from datetime import datetime,timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import stat
import time
from zoneinfo import ZoneInfo
import emergency_control as control
import local_voice
import owner_notifications as inbox
import roadmap
import task_queue as q
import voice_native as native

TTL=900
ACTIVE=('receiving','queued','ready')
PROJECTS={'control':'ULTIMATE','nova':'NOVA WEB','kinder':'Kinder Spa','sap':'SAP/iiko','qualisift':'QualiSift','iiko-loader':'iiko Loader','sap-mb51':'SAP MB51'}

def initialize(conn):
    conn.executescript('''CREATE TABLE IF NOT EXISTS voice_inputs(
      id INTEGER PRIMARY KEY,source_key TEXT UNIQUE NOT NULL,fingerprint TEXT NOT NULL,
      owner_id TEXT NOT NULL,project TEXT NOT NULL,language TEXT NOT NULL,duration INTEGER NOT NULL,
      received_at REAL NOT NULL,expires_at REAL NOT NULL,state TEXT NOT NULL,
      audio_sha256 TEXT,audio_bytes INTEGER,job_id INTEGER UNIQUE,control_epoch INTEGER NOT NULL,
      transcript TEXT,transcript_sha256 TEXT,preview_code TEXT,previewed_at REAL,task_id INTEGER,
      notice_id INTEGER,error_code TEXT,receipt TEXT,receipt_sha256 TEXT);
      CREATE INDEX IF NOT EXISTS voice_inputs_active ON voice_inputs(state,expires_at);''');conn.commit()

def _ident(value):
    if type(value) is not int or not 1<=value<=9223372036854775807: raise native.VoiceError('voice_id')
    return value

def get(conn,ident):
    cur=conn.execute('SELECT * FROM voice_inputs WHERE id=?',(_ident(ident),));row=cur.fetchone()
    return dict(zip([x[0] for x in cur.description],row)) if row else None

def _owner(row,actor):
    if not row or not isinstance(actor,str) or not actor.isdecimal() or actor!=row['owner_id']: raise PermissionError('voice_owner_required')

def require_enabled(conn):
    if roadmap.setting(conn,'voice_intake_gate','disabled')!='enabled':raise native.VoiceError('voice_intake_disabled')

def _spool(root,*,create=False):
    root=Path(root)
    if not root.is_absolute() or root.resolve()!=root: raise native.VoiceError('voice_storage_path')
    folder=root/'voice-audio'
    if create: folder.mkdir(mode=0o700,exist_ok=True)
    if not folder.exists() and not folder.is_symlink(): return None
    st=folder.lstat()
    if folder.resolve()!=folder or not stat.S_ISDIR(st.st_mode) or st.st_uid!=os.getuid() or stat.S_IMODE(st.st_mode)!=0o700:
        raise native.VoiceError('voice_storage_permissions')
    return folder

def _remove(root,ident):
    try:
        folder=_spool(root)
        if folder is None:return True
        path=folder/(str(_ident(ident))+'.ogg')
        try:st=path.lstat()
        except FileNotFoundError:return True
        if not stat.S_ISREG(st.st_mode) or st.st_uid!=os.getuid() or stat.S_IMODE(st.st_mode)!=0o600:return False
        path.unlink();return True
    except (OSError,native.VoiceError):return False

def _resolve_notice(conn,row):
    if row['notice_id']:
        conn.execute("UPDATE owner_notifications SET state='resolved',resolved_at=? WHERE id=? AND state='pending'",(datetime.now(timezone.utc).isoformat(),row['notice_id']))

def _cancel_processing(conn,row,reason):
    job=conn.execute('SELECT state,payload FROM agent_jobs WHERE id=?',(row['job_id'],)).fetchone()
    if job and job[0]=='queued' and json.loads(job[1])=={'voice_input':row['id']}:
        conn.execute("UPDATE agent_jobs SET state='cancelled',updated_at=? WHERE id=?",(time.time(),row['job_id']));q._event(conn,row['job_id'],time.time(),'cancelled',reason)

def cleanup(conn,root):
    now=time.time();remove=[];expired=0
    with q._write(conn):
        epoch=control.state(conn)['epoch']
        for ident, in conn.execute("SELECT id FROM voice_inputs WHERE state IN ('receiving','queued','ready')").fetchall():
            row=get(conn,ident)
            stale=(row['expires_at']<=now or row['control_epoch']!=epoch)
            interrupted=row['state']=='receiving' and now-row['received_at']>30
            job=conn.execute('SELECT state FROM agent_jobs WHERE id=?',(row['job_id'],)).fetchone() if row['job_id'] else None
            failed=row['state']=='queued' and job and job[0] in ('failed','cancelled','awaiting_owner')
            if stale or interrupted or failed:
                target='expired' if stale else 'failed';code='voice_expired_or_stale' if stale else 'voice_capture_interrupted' if interrupted else 'voice_worker_stopped'
                conn.execute('UPDATE voice_inputs SET state=?,error_code=?,transcript=NULL,preview_code=NULL WHERE id=?',(target,code,ident))
                _resolve_notice(conn,row);_cancel_processing(conn,row,code);expired+=1
        remove=[x[0] for x in conn.execute("SELECT id FROM voice_inputs WHERE state NOT IN ('receiving','queued')")]
    pending=sum(not _remove(root,i) for i in remove)
    return {'expired':expired,'cleanup_pending':pending}

def _enqueue_locked(conn,project,payload,key,*,priority=50):
    # Atomic job + voice-row linking, using the existing unchanged queue schema/contract.
    if project not in q.PROJECTS or project not in PROJECTS:raise native.VoiceError('voice_project')
    now=time.time();raw=q._json(payload)
    ident=conn.execute('''INSERT INTO agent_jobs(project,kind,payload,event_key,priority,max_attempts,created_at,available_at,updated_at)
                         VALUES(?,'plan_change',?,?,?,1,?,?,?)''',(project,raw,key,priority,now,now,now)).lastrowid
    q._event(conn,ident,now,'queued','owner voice pipeline');return ident

def capture(conn,root,update,owner_id,fetch):
    if not isinstance(owner_id,str) or not owner_id.isdecimal():raise PermissionError('voice_owner_required')
    message=update.get('message',{});sender=message.get('from',{});chat=message.get('chat',{})
    if str(sender.get('id'))!=owner_id or str(chat.get('id'))!=owner_id or chat.get('type')!='private':raise PermissionError('voice_owner_required')
    uid=update.get('update_id');meta=message.get('voice')
    if type(uid) is not int or not 0<=uid<2**63 or not isinstance(meta,dict):raise native.VoiceError('voice_metadata')
    ident=meta.get('file_id');unique=meta.get('file_unique_id');duration=meta.get('duration');size=meta.get('file_size')
    if (not isinstance(ident,str) or not re.fullmatch('[A-Za-z0-9_-]{1,200}',ident) or not isinstance(unique,str)
        or not re.fullmatch('[A-Za-z0-9_-]{1,200}',unique) or type(duration) is not int or not 1<=duration<=native.MAX_SECONDS
        or (size is not None and (type(size) is not int or not 1<=size<=native.MAX_BYTES))
        or meta.get('mime_type') not in (None,'audio/ogg','audio/opus')):raise native.VoiceError('voice_max10s_mono_ogg_256k')
    native.policy(Path(root)/native.POLICY,check_assets=False);require_enabled(conn);cleanup(conn,root)
    key='telegram:'+str(uid);fingerprint=local_voice.util.digest([ident,unique,duration,size,meta.get('mime_type')])
    with q._write(conn):
        old=conn.execute('SELECT id,fingerprint,owner_id FROM voice_inputs WHERE source_key=?',(key,)).fetchone()
        if old:
            if old[1:]!=(fingerprint,owner_id):raise native.VoiceError('voice_update_conflict')
            return old[0]
        epoch=control.require_open(conn);require_enabled(conn)
        if conn.execute("SELECT count(*) FROM voice_inputs WHERE state IN ('receiving','queued','ready')").fetchone()[0]>=5:raise native.VoiceError('voice_five_pending_limit')
        if conn.execute('SELECT count(*) FROM voice_inputs WHERE received_at>=?',(time.time()-86400,)).fetchone()[0]>=30:raise native.VoiceError('voice_daily_limit')
        project=roadmap.setting(conn,'active_project','control');language=roadmap.setting(conn,'voice_language','ru')
        if project not in PROJECTS or language not in native.LANGUAGES:raise native.VoiceError('voice_project_or_language')
        now=time.time()
        voice_id=conn.execute('''INSERT INTO voice_inputs(source_key,fingerprint,owner_id,project,language,duration,received_at,expires_at,state,control_epoch)
          VALUES(?,?,?,?,?,?,?,?,'receiving',?)''',(key,fingerprint,owner_id,project,language,duration,now,now+TTL,epoch)).lastrowid
    try:
        data=fetch(ident);native.validate_audio(data)
        if size is not None and len(data)!=size:raise native.VoiceError('voice_download_truncated')
        folder=_spool(root,create=True);path=folder/(str(voice_id)+'.ogg')
        fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
        with q._write(conn):
            current=get(conn,voice_id);control.require_open(conn,epoch);require_enabled(conn)
            if current['state']!='receiving' or current['expires_at']<=time.time():raise native.VoiceError('voice_capture_expired')
            job=_enqueue_locked(conn,'control',{'voice_input':voice_id},'voice-process-'+str(voice_id))
            conn.execute("UPDATE voice_inputs SET state='queued',audio_sha256=?,audio_bytes=?,job_id=? WHERE id=?",(local_voice.assets.digest(data),len(data),job,voice_id))
    except Exception as exc:
        with q._write(conn):
            conn.execute("UPDATE voice_inputs SET state='failed',error_code=? WHERE id=? AND state='receiving'",('voice_capture_stopped' if isinstance(exc,control.Stopped) else 'voice_capture_failed',voice_id))
        _remove(root,voice_id)
    return voice_id

def capture_response(conn,ident,actor):
    row=get(conn,ident);_owner(row,actor)
    if row['state']=='queued':return f'Голосовое #{ident} сохранено для локального распознавания. Язык: {row["language"]}, проект: {PROJECTS[row["project"]]}. До 15 минут на обработку и подтверждение; результат придёт уведомлением. /voice {ident}'
    if row['state']=='receiving':return f'Голосовое #{ident} уже принимается. /voice {ident}'
    return f'Голосовое #{ident}: {row["state"]}. /voice {ident}. При ошибке отправь короткую запись заново или задачу текстом.'

def _read_audio(root,row):
    folder=_spool(root)
    if folder is None:raise native.VoiceError('voice_audio_missing')
    fd=os.open(folder/(str(row['id'])+'.ogg'),os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        st=os.fstat(stream.fileno())
        if not stat.S_ISREG(st.st_mode) or st.st_uid!=os.getuid() or stat.S_IMODE(st.st_mode)!=0o600 or st.st_size>native.MAX_BYTES:raise native.VoiceError('voice_audio_permissions')
        data=stream.read(native.MAX_BYTES+1)
    if len(data)!=row['audio_bytes'] or local_voice.assets.digest(data)!=row['audio_sha256']:raise native.VoiceError('voice_audio_changed')
    return data

def _code(row):
    return local_voice.util.digest({k:row[k] for k in ('id','owner_id','project','language','audio_sha256','transcript_sha256','expires_at','control_epoch')})[:12]

def process(conn,root,job,*,transcriber=None):
    payload=job.get('payload');ident=payload.get('voice_input') if isinstance(payload,dict) else None
    if job.get('project')!='control' or job.get('kind')!='plan_change' or payload!={'voice_input':ident}:raise PermissionError('voice_job_scope')
    _ident(ident);control.check_job(conn,job['id'],job['lease_token']);require_enabled(conn);row=get(conn,ident)
    if not row or row['job_id']!=job['id']:raise PermissionError('voice_job_scope')
    if row['state']!='queued' or row['expires_at']<=time.time() or row['control_epoch']!=control.state(conn)['epoch']:
        cleanup(conn,root);return {'voice_input_id':ident,'voice_recognition':'skipped','published':False}
    try:
        data=_read_audio(root,row)
        outcome=(transcriber or native.transcribe)(data,row['language'],Path(root)/native.POLICY)
        text=native.clean_text(outcome['text']);receipt=outcome['receipt']
        if (not native.valid_receipt(receipt) or receipt['audio_sha256']!=row['audio_sha256'] or receipt['audio_bytes']!=row['audio_bytes']
            or receipt['language']!=row['language'] or abs(receipt['decoded_seconds']-row['duration'])>1.1
            or receipt['transcript_sha256']!=local_voice.assets.digest(text.encode())):
            raise native.VoiceError('voice_receipt_mismatch')
        with q._write(conn):
            q._owned(conn,job['id'],job['lease_token'],time.time());current=get(conn,ident)
            fresh=(current['state']=='queued' and current['expires_at']>time.time() and current['control_epoch']==control.state(conn)['epoch']
                   and roadmap.setting(conn,'voice_intake_gate','disabled')=='enabled')
            conn.execute('UPDATE voice_inputs SET receipt=?,receipt_sha256=? WHERE id=?',(local_voice.util.canonical(receipt),local_voice.util.digest(receipt),ident))
            if fresh:
                conn.execute("UPDATE voice_inputs SET state='ready',transcript=?,transcript_sha256=?,previewed_at=NULL WHERE id=?",(text,receipt['transcript_sha256'],ident))
                code=_code(get(conn,ident));conn.execute('UPDATE voice_inputs SET preview_code=? WHERE id=?',(code,ident))
                note=inbox.create(conn,'ULTIMATE AI CONTROL','decision',f'Расшифровка голосового #{ident} готова',
                    'Текст получен локально. Задача ещё не создана; сначала проверь расшифровку и проект.',f'Открой /voice {ident}. Там появятся текст и команда подтверждения. Можно сменить проект или отклонить запись.',
                    event_key='voice-input-ready-'+str(ident),commit=False)
                conn.execute('UPDATE voice_inputs SET notice_id=? WHERE id=?',(note,ident))
            elif current['state']=='queued':conn.execute("UPDATE voice_inputs SET state='expired',error_code='voice_expired_or_stale' WHERE id=?",(ident,))
        return {'voice_input_id':ident,'voice_recognition':'transcribed','receipt_sha256':local_voice.util.digest(receipt),'published':False}
    except control.Stopped:raise
    except Exception:
        with q._write(conn):
            q._owned(conn,job['id'],job['lease_token'],time.time())
            current=get(conn,ident)
            if current['state']=='queued':
                note=inbox.create(conn,'ULTIMATE AI CONTROL','info',f'Голосовое #{ident} не распознано',
                    'Текст не сохранён и задача не создана. Сработала проверка данных, лимит обработки или недоступен локальный движок.',
                    'Отправь более короткую запись без паролей либо создай задачу текстом. /voice '+str(ident),event_key='voice-input-failed-'+str(ident),commit=False)
                conn.execute("UPDATE voice_inputs SET state='failed',error_code='voice_recognition_failed',transcript=NULL,notice_id=? WHERE id=?",(note,ident))
        return {'voice_input_id':ident,'voice_recognition':'failed','published':False}
    finally:_remove(root,ident)

def _ready(conn,row,actor):
    _owner(row,actor);require_enabled(conn)
    control.require_open(conn,row['control_epoch'])
    if row['state']!='ready' or row['expires_at']<=time.time():raise native.VoiceError('voice_not_ready_or_expired')
    if (not row['transcript'] or row['transcript_sha256']!=local_voice.assets.digest(row['transcript'].encode())
        or row['preview_code']!=_code(row)):raise native.VoiceError('voice_preview_changed')
    try:
        receipt=json.loads(row['receipt'])
        if (not native.valid_receipt(receipt) or local_voice.util.digest(receipt)!=row['receipt_sha256']
            or receipt['transcript_sha256']!=row['transcript_sha256'] or receipt['audio_sha256']!=row['audio_sha256']):
            raise ValueError('changed')
    except (ValueError,TypeError):raise native.VoiceError('voice_preview_changed') from None

def preview(conn,root,ident,actor):
    cleanup(conn,root)
    with q._write(conn):
        row=get(conn,ident);_owner(row,actor)
        if row['state']!='ready':
            return f'Голосовое #{ident}: {row["state"]}. '+(f'Подтверждённая задача: /job {row["task_id"]}.' if row['task_id'] else 'Задача ещё не создана. При ошибке/истечении срока отправь запись заново или задачу текстом.')
        _ready(conn,row,actor);conn.execute('UPDATE voice_inputs SET previewed_at=? WHERE id=?',(time.time(),ident))
        deadline=datetime.fromtimestamp(row['expires_at'],ZoneInfo('Asia/Tashkent')).strftime('%H:%M')
        return (f'Голосовое #{ident} · проект: {PROJECTS[row["project"]]} · язык: {row["language"]}\n\n'+row['transcript']
                +f'\n\nПроверь текст. Задача ещё не создана. Подтвердить до {deadline} Ташкент:\n/voice_confirm {ident} {row["project"]} {row["preview_code"]}'
                +f'\nСменить проект: /voice_project {ident} nova\nОтклонить: /voice_reject {ident}\nЭто текстовая задача; публикации и расходы так не согласуются.')

def change_project(conn,root,ident,project,actor):
    if project not in PROJECTS:raise native.VoiceError('voice_project')
    with q._write(conn):
        row=get(conn,ident);_ready(conn,row,actor)
        conn.execute('UPDATE voice_inputs SET project=?,previewed_at=NULL WHERE id=?',(project,ident))
        conn.execute('UPDATE voice_inputs SET preview_code=? WHERE id=?',(_code(get(conn,ident)),ident))
    return preview(conn,root,ident,actor)

def confirm(conn,ident,project,code,actor):
    if project not in PROJECTS or not isinstance(code,str) or not re.fullmatch('[0-9a-f]{12}',code):raise native.VoiceError('voice_confirmation_format')
    with q._write(conn):
        row=get(conn,ident);_owner(row,actor)
        if row['state']=='confirmed':
            if row['project']!=project or not hmac.compare_digest(row['preview_code'] or '',code):raise native.VoiceError('voice_confirmation_conflict')
            return row['task_id']
        _ready(conn,row,actor)
        if not row['previewed_at'] or row['project']!=project or not hmac.compare_digest(row['preview_code'],code):raise native.VoiceError('voice_preview_or_project_required')
        text=native.clean_text(row['transcript'])
        task=_enqueue_locked(conn,project,{'text':text,'source':'voice_confirmed','voice_input_id':ident},'voice-confirmed-'+str(ident))
        conn.execute("UPDATE voice_inputs SET state='confirmed',task_id=?,transcript=NULL WHERE id=?",(task,ident));_resolve_notice(conn,row)
        q._event(conn,task,time.time(),'voice_confirmed','explicit owner transcript/project confirmation')
        return task

def reject(conn,root,ident,actor):
    with q._write(conn):
        row=get(conn,ident);_owner(row,actor)
        if row['state']=='confirmed':raise native.VoiceError('voice_already_confirmed_use_job_cancel')
        if row['state']!='rejected':
            conn.execute("UPDATE voice_inputs SET state='rejected',transcript=NULL,preview_code=NULL WHERE id=?",(ident,))
            _resolve_notice(conn,row);_cancel_processing(conn,row,'owner rejected voice')
    _remove(root,ident);return 'Голосовое отклонено. Текстовая задача не создана.'

def expire_pending_for_rollback(conn,root):
    # Operator-only rollback primitive; not exposed as a Telegram command.
    if roadmap.setting(conn,'voice_intake_gate','disabled')!='disabled':raise PermissionError('disable_voice_before_cleanup')
    with q._write(conn):
        rows=[get(conn,x[0]) for x in conn.execute("SELECT id FROM voice_inputs WHERE state IN ('receiving','queued','ready')").fetchall()]
        for row in rows:
            conn.execute("UPDATE voice_inputs SET state='expired',error_code='voice_rollback',transcript=NULL,preview_code=NULL WHERE id=?",(row['id'],))
            _resolve_notice(conn,row);_cancel_processing(conn,row,'voice feature rollback')
        q._event(conn,None,time.time(),'control','voice intake disabled; unconfirmed voice inputs expired')
    return {'expired':len(rows),'cleanup_pending':sum(not _remove(root,row['id']) for row in rows)}

def describe(conn,root):
    try:native.policy(Path(root)/native.POLICY,check_assets=False);require_enabled(conn);enabled=True
    except (OSError,ValueError,PermissionError):enabled=False
    lines=['ULTIMATE · голосовые сообщения',
        'Экспериментальный приём: включён.' if enabled else 'Голосовые задачи владельца ещё не принимаются. Приём выключен.',
        'Только владелец в личном чате. До10 секунд/256 КиБ, моно OGG/Opus; до5 ожидающих и30 записей за24 часа.',
        'Язык новых записей: '+roadmap.setting(conn,'voice_language','ru')+'. /voice_lang ru или /voice_lang uz. Русский/узбекский ещё требуют проверки на вашей речи.',
        'Сначала /project nova (или control, kinder, sap, qualisift, iiko-loader, sap-mb51), затем короткая голосовая без паролей.',
        'После распознавания придёт уведомление. /voice_inbox и /voice НОМЕР показывают текст и подтверждение. До него задачи нет; публикации/расходы отдельно.',
        'Срок подтверждения15 минут, включая паузу. Аудио удаляется после обработки или при уборке просроченных записей. /voice_reject НОМЕР — отклонить. Подтверждённые задачи сохраняются в журнале.',
        'Аварийный стоп: '+('включён' if control.state(conn)['latched'] else 'выключен')+'. /emergency',
        'Повторить проверку движка: /test_voice4. Проверить цепочку: /test_voice_flow.']
    pilot=local_voice.describe(conn).splitlines()[-1]
    lines.append('Исторический пилот: '+pilot)
    return '\n'.join(lines)

def list_pending(conn,root,actor):
    if not isinstance(actor,str) or not actor.isdecimal():raise PermissionError('voice_owner_required')
    cleanup(conn,root)
    rows=conn.execute('SELECT id,state,project,language,task_id FROM voice_inputs WHERE owner_id=? ORDER BY id DESC LIMIT 10',(actor,)).fetchall()
    return '\n'.join(f'#{i} · {state} · {PROJECTS.get(project,project)} · {lang}'+(f' · /job {task}' if task else f' · /voice {i}') for i,state,project,lang,task in rows) or 'Голосовых записей пока нет.'

def error_message(exc):
    code=str(exc)
    return {
        'voice_owner_required':'Доступно только владельцу в личном чате.',
        'voice_intake_disabled':'Приём голосовых временно выключен. Можно отправить задачу текстом. /voice4',
        'voice_max10s_mono_ogg_256k':'Нужна голосовая до10 секунд и256 КиБ, моно OGG/Opus. Можно отправить задачу текстом.',
        'voice_five_pending_limit':'Уже ожидают5 записей. Проверь /voice_inbox и подтверди или отклони их.',
        'voice_daily_limit':'Достигнут предел30 записей за24 часа. Отправь задачу текстом.',
        'voice_not_ready_or_expired':'Расшифровка ещё не готова либо срок истёк. Проверь /voice_inbox; при необходимости отправь запись заново.',
        'voice_preview_or_project_required':'Сначала открой /voice НОМЕР, проверь текст и используй указанную там команду с проектом и кодом.',
        'voice_confirmation_conflict':'Эта запись уже подтверждена с другими параметрами. Проверь /voice НОМЕР.',
        'voice_already_confirmed_use_job_cancel':'Задача уже создана. Для её отмены используй /job_cancel НОМЕР_ЗАДАЧИ.',
        'voice_project':'Проект не включён. Inventory защищён. Допустимы: '+', '.join(PROJECTS),
        'emergency_latched':'Включён аварийный стоп. Новые голосовые и подтверждения остановлены. /emergency',
        'emergency_epoch_changed':'После аварийного стопа эта расшифровка устарела. Отправь запись заново после возобновления.',
    }.get(code,'Голосовая операция отклонена. Проверь /voice4 и /voice_inbox; при ошибке распознавания отправь задачу текстом.')
