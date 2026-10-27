"""Real isolated public-audio test plus explicitly synthetic inbox/confirmation cases."""
import base64
from contextlib import contextmanager
import copy
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import tempfile
import time
import emergency_control as control
import local_voice
import owner_notifications as inbox
import roadmap
import task_queue as q
import voice_intake as intake
import voice_native as native

PROFILE='voice-intake-v1'
CHECKS={'capture_authenticated_deduplicated','preview_before_confirm','confirmation_once_exact_project',
        'project_change_invalidates_code','expired_and_rejected_blocked','emergency_invalidates_confirm',
        'raw_audio_removed','slash_text_never_dispatches'}

def initialize(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS voice_flow_runs(
      id INTEGER PRIMARY KEY,job_id INTEGER NOT NULL UNIQUE,report TEXT NOT NULL,report_sha256 TEXT NOT NULL,created_at REAL NOT NULL)''');conn.commit()

def implementation_digest():
    root=Path(__file__).parent
    return local_voice.util.digest({n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in
        ('voice_native.py','voice_intake.py','telegram_voice_file.py','voice_flow_test.py','main.py','queue_worker.py','runtime_commands.py',
         'local_voice.py','voice_assets.py','isolated_python.py','isolated_node.py')})

def observe(root):
    root=Path(root);audio=base64.b64decode((Path(__file__).parent/'fixtures/voice-jfk8.ogg.b64').read_bytes().strip(),validate=True)
    outcome=native.transcribe(audio,'en',root/native.POLICY)
    if not all(w in outcome['text'].lower() for w in ('fellow','americans','country')):raise ValueError('voice_native_fixture_words')
    checks={}
    def check(name,condition):
        if not condition:raise AssertionError('voice_flow_'+name)
        checks[name]=True
    meta={'update_id':1,'message':{'from':{'id':101},'chat':{'id':101,'type':'private'},'voice':{
        'file_id':'fixture-only','file_unique_id':'fixture-unique','duration':8,'file_size':len(audio),'mime_type':'audio/ogg'}}}
    @contextmanager
    def fixture():
        with tempfile.TemporaryDirectory(prefix='voice-flow-fixture-') as name:
            folder=Path(name);p=folder/native.POLICY;p.write_bytes((root/native.POLICY).read_bytes());p.chmod(0o600)
            conn=sqlite3.connect(':memory:')
            try:
                q.initialize(conn);roadmap.initialize(conn);inbox.initialize(conn);intake.initialize(conn)
                roadmap.set_setting(conn,'active_project','nova');roadmap.set_setting(conn,'voice_intake_gate','enabled');yield conn,folder
            finally:conn.close()
    def ready(conn,folder,text='Проверь сайт NOVA.'):
        ident=intake.capture(conn,folder,meta,'101',lambda _:audio);job=q.claim(conn,'fixture-only',q.KINDS)
        def fake_transcriber(*args):
            receipt=copy.deepcopy(outcome['receipt']);receipt.update(language='ru',transcript_sha256=local_voice.assets.digest(text.encode()))
            return {'text':text,'receipt':receipt}
        result=intake.process(conn,folder,job,transcriber=fake_transcriber);q.finish(conn,job['id'],job['lease_token'],result)
        if intake.get(conn,ident)['state']!='ready':raise AssertionError('fixture_state_setup')
        return ident
    with fixture() as (conn,folder):
        calls=[]
        ident=intake.capture(conn,folder,meta,'101',lambda _:(calls.append(1) or audio))
        again=intake.capture(conn,folder,meta,'101',lambda _:(_ for _ in ()).throw(AssertionError('duplicate fetch')))
        try:intake.capture(conn,folder,meta,'999',lambda _:audio)
        except PermissionError:denied=True
        else:denied=False
        check('capture_authenticated_deduplicated',ident==again and len(calls)==1 and denied and conn.execute('SELECT count(*) FROM agent_jobs').fetchone()[0]==1)
    with fixture() as (conn,folder):
        ident=ready(conn,folder);code=intake.get(conn,ident)['preview_code']
        try:intake.confirm(conn,ident,'nova',code,'101')
        except native.VoiceError:denied=True
        else:denied=False
        check('preview_before_confirm',denied)
        intake.preview(conn,folder,ident,'101');task=intake.confirm(conn,ident,'nova',code,'101')
        check('confirmation_once_exact_project',intake.confirm(conn,ident,'nova',code,'101')==task
              and conn.execute("SELECT count(*) FROM agent_jobs WHERE event_key=?",('voice-confirmed-'+str(ident),)).fetchone()[0]==1
              and conn.execute('SELECT project FROM agent_jobs WHERE id=?',(task,)).fetchone()[0]=='nova')
        check('raw_audio_removed',not list((folder/'voice-audio').glob('*.ogg')))
    with fixture() as (conn,folder):
        ident=ready(conn,folder);intake.preview(conn,folder,ident,'101');old=intake.get(conn,ident)['preview_code']
        intake.change_project(conn,folder,ident,'kinder','101')
        try:intake.confirm(conn,ident,'nova',old,'101')
        except native.VoiceError:denied=True
        else:denied=False
        check('project_change_invalidates_code',denied and intake.get(conn,ident)['preview_code']!=old)
    with fixture() as (conn,folder):
        ident=ready(conn,folder);intake.preview(conn,folder,ident,'101');code=intake.get(conn,ident)['preview_code']
        conn.execute('UPDATE voice_inputs SET expires_at=? WHERE id=?',(time.time()-1,ident));conn.commit()
        try:intake.confirm(conn,ident,'nova',code,'101')
        except native.VoiceError:denied=True
        else:denied=False
        intake.reject(conn,folder,ident,'101')
        check('expired_and_rejected_blocked',denied and intake.get(conn,ident)['task_id'] is None)
    with fixture() as (conn,folder):
        ident=ready(conn,folder);intake.preview(conn,folder,ident,'101');code=intake.get(conn,ident)['preview_code']
        control.stop(conn);control.reset(conn,1)
        try:intake.confirm(conn,ident,'nova',code,'101')
        except control.Stopped:denied=True
        else:denied=False
        check('emergency_invalidates_confirm',denied and intake.get(conn,ident)['task_id'] is None)
    with fixture() as (conn,folder):
        ident=ready(conn,folder,text='/emergency_stop');intake.preview(conn,folder,ident,'101')
        task=intake.confirm(conn,ident,'nova',intake.get(conn,ident)['preview_code'],'101')
        payload=json.loads(conn.execute('SELECT payload FROM agent_jobs WHERE id=?',(task,)).fetchone()[0])
        check('slash_text_never_dispatches',payload['text']=='/emergency_stop' and not control.state(conn)['latched'])
    return {'schema':PROFILE,'checks':checks,'counts':{'tests':9,'pass':9,'fail':0},'native_receipt':outcome['receipt'],
            'real_native_case_count':1,'synthetic_state_case_count':8,'implementation_sha256':implementation_digest(),
            'telegram_roundtrip_verified':False,'owner_confirmation_real':False,'live_inbox_changed':False,
            'paid_calls':0,'published':False,'checked_at':time.time()}

def valid(report):
    try:
        return (set(report)=={'schema','checks','counts','native_receipt','real_native_case_count','synthetic_state_case_count','implementation_sha256','telegram_roundtrip_verified','owner_confirmation_real','live_inbox_changed','paid_calls','published','checked_at'}
            and report['schema']==PROFILE and set(report['checks'])==CHECKS and all(v is True for v in report['checks'].values())
            and report['counts']=={'tests':9,'pass':9,'fail':0} and all(type(v) is int for v in report['counts'].values())
            and native.valid_receipt(report['native_receipt']) and report['native_receipt']['language']=='en'
            and report['native_receipt']['audio_sha256']==local_voice.assets.contract()['fixture_sha256']
            and type(report['real_native_case_count']) is int and report['real_native_case_count']==1
            and type(report['synthetic_state_case_count']) is int and report['synthetic_state_case_count']==8
            and isinstance(report['implementation_sha256'],str) and re.fullmatch('[0-9a-f]{64}',report['implementation_sha256']) is not None
            and all(report[k] is False for k in ('telegram_roundtrip_verified','owner_confirmation_real','live_inbox_changed','published'))
            and type(report['paid_calls']) is int and report['paid_calls']==0 and type(report['checked_at']) in (int,float) and 0<report['checked_at']<float('inf'))
    except (KeyError,TypeError,ValueError):return False

def save(conn,job,report):
    if job.get('project')!='control' or job.get('kind')!='test_release' or job.get('payload')!={'target':PROFILE}:raise PermissionError('voice_flow_scope')
    if not valid(report):raise ValueError('voice_flow_evidence')
    with q._write(conn):
        now=time.time();owned=q._owned(conn,job['id'],job['lease_token'],now)
        row=conn.execute('SELECT project,kind,payload FROM agent_jobs WHERE id=?',(job['id'],)).fetchone()
        if row[:2]!=('control','test_release') or json.loads(row[2])!={'target':PROFILE} or not owned[3]<=report['checked_at']<=now:raise PermissionError('voice_flow_job_changed')
        old=conn.execute('SELECT id,report,report_sha256 FROM voice_flow_runs WHERE job_id=?',(job['id'],)).fetchone()
        if old:
            report=json.loads(old[1])
            if not valid(report) or local_voice.util.digest(report)!=old[2]:raise ValueError('voice_flow_saved_evidence_changed')
            ident=old[0]
        else:ident=conn.execute('INSERT INTO voice_flow_runs(job_id,report,report_sha256,created_at) VALUES(?,?,?,?)',(job['id'],local_voice.util.canonical(report),local_voice.util.digest(report),now)).lastrowid
    return {'voice_flow_id':ident,'report_sha256':local_voice.util.digest(report),'test_status':'passed','test_counts':report['counts'],'telegram_roundtrip_verified':False,'published':False}
