"""Offline speech acceptance only. Owner voice ingestion is deliberately not enabled."""
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import re
import resource
import selectors
import signal
import stat
import subprocess
import tempfile
import time
import wave
from functools import partial
import artifact_prs as util
import isolated_python as isolation
import isolated_node
import task_queue as q
import voice_assets as assets

PROFILE='voice-local-v1'
ROOT=Path(__file__).resolve().parent
MAX_PCM=15*16000*2

def initialize(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS voice_local_runs(
      id INTEGER PRIMARY KEY,job_id INTEGER NOT NULL UNIQUE,report TEXT NOT NULL,report_sha256 TEXT NOT NULL,created_at REAL NOT NULL)''');conn.commit()

def policy(path):
    path=assets.regular(Path(path),True);cfg=json.loads(path.read_text())
    if set(cfg)!={'enabled','mode','runtime','contract_sha256'} or cfg['enabled'] is not True or cfg['mode']!='acceptance_only' or cfg['contract_sha256']!=assets.contract_sha():
        raise isolation.SandboxUnavailable('voice_candidate_policy')
    cfg['manifest']=assets.verify(Path(cfg['runtime']))
    cfg['bwrap']=isolation.load_policy(path.with_name('sandbox-policy.json'))['binary']
    return cfg

def limits(bind_data=False):
    resource.setrlimit(resource.RLIMIT_AS,(768*1024*1024,768*1024*1024))
    resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    size=512*1024 if bind_data else 0
    resource.setrlimit(resource.RLIMIT_FSIZE,(size,size))
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})

def _arguments(cfg,root,source,input_fd=None):
    args=[cfg['bwrap'],'--unshare-all','--die-with-parent','--new-session','--cap-drop','ALL','--clearenv',
          '--dir','/runtime','--dir','/runtime/lib']
    # Bind inherited data before replacing /proc (the setup helper uses host fd paths).
    args+=['--ro-bind',str(source),'/input'] if input_fd is None else ['--ro-bind-data',str(input_fd),'/input','--ro-bind','/usr/bin/prlimit','/runtime/prlimit']
    args+=['--proc','/proc','--dev','/dev','--remount-ro','/dev','--dir','/etc','--dir','/home',
          '--tmpfs','/tmp','--remount-ro','/tmp','--chdir','/tmp',
          '--setenv','HOME','/tmp','--setenv','LANG','C.UTF-8','--setenv','MALLOC_ARENA_MAX','1','--setenv','LD_LIBRARY_PATH','/runtime/lib']
    for name in assets.FILES: args+=['--ro-bind',str(Path(cfg['runtime'])/name),'/runtime/'+name]
    for path in ('/lib/x86_64-linux-gnu','/usr/lib/x86_64-linux-gnu','/lib64'):
        if Path(path).exists(): args+=['--ro-bind',path,path]
    return args+['--remount-ro','/']

def _execute(cfg,source,argv,*,limit,seconds,input_fd=None):
    # Exact pthread clone flags only; process forks/network/mounts denied by seccomp.
    # Trusted native model code may create threads; no untrusted project code is loaded.
    started=time.monotonic();stdout=bytearray();stderr=bytearray();status=None;proc=None
    if input_fd is not None:
        st=Path('/usr/bin/prlimit').lstat()
        if not stat.S_ISREG(st.st_mode) or st.st_uid!=0 or st.st_mode&0o7022:raise isolation.SandboxUnavailable('voice_limit_wrapper_unavailable')
        # Only trusted bwrap setup may populate its private input tmpfs. Restore the
        # zero hard file-size cap before decoding/inference, with all mounts read-only.
        argv=['/runtime/prlimit','--fsize=0:0','--',*argv]
    with tempfile.TemporaryFile() as filt:
        filt.write(isolated_node.seccomp_filter());filt.flush();filt.seek(0)
        args=_arguments(cfg,None,source,input_fd=input_fd)+['--seccomp',str(filt.fileno()),'--',*argv]
        try:
            inherited=(filt.fileno(),) if input_fd is None else (filt.fileno(),input_fd)
            proc=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                  env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8'},pass_fds=inherited,
                                  preexec_fn=partial(limits,input_fd is not None),start_new_session=True)
            with selectors.DefaultSelector() as selector:
                selector.register(proc.stdout,selectors.EVENT_READ,stdout);selector.register(proc.stderr,selectors.EVENT_READ,stderr)
                while selector.get_map() and not status:
                    if time.monotonic()-started>=seconds: status='timeout';break
                    for key,_ in selector.select(.02):
                        chunk=os.read(key.fileobj.fileno(),8192)
                        if not chunk: selector.unregister(key.fileobj);continue
                        key.data.extend(chunk)
                        if len(stdout)>limit or len(stderr)>16000: status='output_limit';break
            if status and proc.poll() is None: os.killpg(proc.pid,signal.SIGKILL)
            code=proc.wait(timeout=2)
            if status or code!=0:
                raise isolation.SandboxUnavailable('voice_'+(status or 'native_failed'))
            return bytes(stdout),round(time.monotonic()-started,4)
        finally:
            if proc is not None:
                if proc.poll() is None: os.killpg(proc.pid,signal.SIGKILL)
                proc.wait(timeout=2);proc.stdout.close();proc.stderr.close()

def observe(path):
    cfg=policy(path);fixture=base64.b64decode((ROOT/'fixtures/voice-jfk8.ogg.b64').read_bytes().strip(),validate=True)
    if len(fixture)>64000 or assets.digest(fixture)!=assets.contract()['fixture_sha256'] or not fixture.startswith(b'OggS'):
        raise ValueError('voice_fixture_pin')
    with tempfile.TemporaryDirectory(prefix='uac-voice-') as name:
        root=Path(name);source=root/'fixture.ogg';source.write_bytes(fixture);source.chmod(0o400)
        pcm,decode_seconds=_execute(cfg,source,['/runtime/opusdec','--quiet','--rate','16000','--no-dither','/input','-'],limit=MAX_PCM,seconds=4)
        if len(pcm)%2 or not 7*16000*2<=len(pcm)<=9*16000*2: raise ValueError('voice_fixture_duration')
        wav=root/'fixture.wav'
        with wave.open(str(wav),'wb') as writer:
            writer.setnchannels(1);writer.setsampwidth(2);writer.setframerate(16000);writer.writeframes(pcm)
        wav.chmod(0o400)
        raw,recognize_seconds=_execute(cfg,wav,['/runtime/whisper-cli','-m','/runtime/model.bin','-f','/input','-t','1','-p','1','-bo','1','-bs','1','-ng','-np','-nt','-nf','-l','en'],limit=16000,seconds=18)
        text=raw.decode('utf-8').strip();normalized=re.sub('[^a-z ]','',text.lower())
        if not all(word in normalized.split() for word in ('fellow','americans','country')): raise ValueError('voice_fixture_transcription_mismatch')
    return {'schema':PROFILE,'status':'passed','checks':{'asset_pins_verified':True,'opus_decode_verified':True,'english_fixture_transcribed':True},
            'counts':{'tests':3,'pass':3,'fail':0},'fixture_sha256':assets.contract()['fixture_sha256'],
            'contract_sha256':assets.contract_sha(),'manifest_sha256':util.digest(cfg['manifest']),
            'model_sha256':cfg['manifest']['files']['model.bin']['sha256'],'source_commit':assets.contract()['whisper_commit'],
            'fixture_language':'en','fixture_seconds':len(pcm)/32000,'decode_seconds':decode_seconds,'recognize_seconds':recognize_seconds,
            'transcript_sha256':assets.digest(text.encode()),'checked_at':time.time(),'network':False,'paid_calls':0,
            'owner_voice_enabled':False,'acceptance_only':True,'published':False,'address_space_mib':768,'cpu_count':1}

def valid(report):
    try:
        return (set(report)=={'schema','status','checks','counts','fixture_sha256','contract_sha256','manifest_sha256','model_sha256','source_commit','fixture_language','fixture_seconds','decode_seconds','recognize_seconds','transcript_sha256','checked_at','network','paid_calls','owner_voice_enabled','acceptance_only','published','address_space_mib','cpu_count'}
                and report['schema']==PROFILE and report['status']=='passed'
                and report['checks']=={'asset_pins_verified':True,'opus_decode_verified':True,'english_fixture_transcribed':True} and all(x is True for x in report['checks'].values())
                and report['counts']=={'tests':3,'pass':3,'fail':0} and all(type(x) is int for x in report['counts'].values())
                and report['fixture_sha256']==assets.contract()['fixture_sha256'] and report['contract_sha256']==assets.contract_sha()
                and report['source_commit']==assets.contract()['whisper_commit'] and report['model_sha256']==assets.contract()['downloads'][2]['sha256']
                and all(isinstance(report[k],str) and re.fullmatch('[0-9a-f]{64}',report[k]) for k in ('manifest_sha256','transcript_sha256'))
                and report['fixture_language']=='en' and 7<=report['fixture_seconds']<=9
                and all(type(report[k]) in (int,float) and 0<report[k]<limit for k,limit in [('decode_seconds',4),('recognize_seconds',18),('checked_at',float('inf'))])
                and all(report[k] is False for k in ('network','owner_voice_enabled','published')) and report['acceptance_only'] is True
                and type(report['paid_calls']) is int and report['paid_calls']==0 and type(report['address_space_mib']) is int and report['address_space_mib']==768 and type(report['cpu_count']) is int and report['cpu_count']==1)
    except (KeyError,TypeError,ValueError): return False

def save(conn,job,report):
    if job.get('project')!='control' or job.get('kind')!='test_release' or job.get('payload')!={'target':PROFILE}: raise PermissionError('voice_acceptance_scope')
    if not valid(report): raise ValueError('voice_acceptance_evidence')
    with q._write(conn):
        now=time.time();owned=q._owned(conn,job['id'],job['lease_token'],now)
        row=conn.execute('SELECT project,kind,payload FROM agent_jobs WHERE id=?',(job['id'],)).fetchone()
        if row[:2]!=('control','test_release') or json.loads(row[2])!={'target':PROFILE} or not owned[3]<=report['checked_at']<=now: raise PermissionError('voice_acceptance_job_changed')
        old=conn.execute('SELECT id,report,report_sha256 FROM voice_local_runs WHERE job_id=?',(job['id'],)).fetchone()
        if old:
            report=json.loads(old[1])
            if not valid(report) or util.digest(report)!=old[2]: raise ValueError('voice_saved_evidence_changed')
            ident=old[0]
        else: ident=conn.execute('INSERT INTO voice_local_runs(job_id,report,report_sha256,created_at) VALUES(?,?,?,?)',(job['id'],util.canonical(report),util.digest(report),now)).lastrowid
    return {'voice_local_id':ident,'report_sha256':util.digest(report),'test_status':'passed','test_counts':report['counts'],'owner_voice_enabled':False,'published':False}

def describe(conn):
    lines=['ULTIMATE · голосовое управление','Локальный движок: пилот без платного API. /test_voice4 — повторить проверку.',
           'Голосовые задачи владельца ещё не принимаются. Следующий шаг — закрытый приём аудио, показ расшифровки и отдельное подтверждение задачи. Команды из распознанного текста не исполняются.',
           'Пилот проверяет только закреплённую публичную английскую запись OGG/Opus. Качество русской/узбекской речи, шум и реальная Telegram-доставка аудио ещё не проверены.']
    row=conn.execute('SELECT id,job_id,report,report_sha256 FROM voice_local_runs ORDER BY id DESC LIMIT 1').fetchone()
    if row:
        try: report=json.loads(row[2]);passed=valid(report) and util.digest(report)==row[3]
        except (ValueError,TypeError): passed=False
        if passed: lines.append(f"✅ Серверный пилот #{row[0]} · /job {row[1]}:3 проверки; запись{report['fixture_seconds']:.1f}с, распознавание{report['recognize_seconds']:.2f}с. Сеть отключена, лимит768 МиБ/1 CPU.")
        else: lines.append('Сохранённый отчёт изменился; нужна повторная сверка.')
    else: lines.append('Серверная проверка ещё не подтверждена.')
    return '\n'.join(lines)
