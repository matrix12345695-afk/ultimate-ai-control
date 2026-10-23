"""Short-lived typed credential broker. It never executes generated Python or shell."""
import ast
import ctypes
import hashlib
import json
import os
from pathlib import Path
import resource
import sqlite3
import sys
import time
import metered_provider as api
from isolated_python import manifest,validate_files

PROTOCOL='uac-model-broker-v1'
DEFAULT_POLICY={'enabled':False,'allow_paid':False,'allow_demo':True}
KEY_PATH=Path.home()/'.config/ultimate-review/openai-api.key'
DEMO_TASK='Проверить демонстрационный путь: компонент процента выполнения и его unit-тесты.'
DEMO_FILES={
    'draft_component.py':'''def bounded_percent(done, total):
    if type(done) is not int or type(total) is not int or done < 0 or total <= 0:
        raise ValueError("nonnegative progress and positive total required")
    return min(100, (done * 100) // total)
''',
    'tests/test_component.py':'''import unittest
from draft_component import bounded_percent
class ProgressTests(unittest.TestCase):
    def test_partial(self): self.assertEqual(bounded_percent(1, 4), 25)
    def test_zero(self): self.assertEqual(bounded_percent(0, 4), 0)
    def test_cap(self): self.assertEqual(bounded_percent(8, 4), 100)
    def test_invalid(self):
        for done,total in ((-1,4),(1,0),(True,4),(1,False)):
            with self.assertRaises(ValueError): bounded_percent(done,total)
'''
}
MAX_REPLY_BYTES=64000


class BrokerDeferred(RuntimeError): pass
class BrokerFailed(RuntimeError): pass


def initialize(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS developer_bundles(job_id INTEGER PRIMARY KEY,
      task_digest TEXT NOT NULL,engine TEXT NOT NULL,bundle TEXT NOT NULL,source_digest TEXT NOT NULL,
      provider_request_key TEXT,model TEXT,created_at REAL NOT NULL,elapsed_seconds REAL NOT NULL)""")
    conn.commit()


def policy(path):
    cfg=json.loads(api.private_read(path,4096))
    if not isinstance(cfg,dict) or set(cfg)!=set(DEFAULT_POLICY) or any(type(x) is not bool for x in cfg.values()):
        raise BrokerFailed('invalid_broker_policy')
    return cfg


def no_duplicates(pairs):
    result={}
    for key,value in pairs:
        if key in result: raise BrokerFailed('duplicate_json_key')
        result[key]=value
    return result


def parse_bundle(text):
    if not isinstance(text,str) or len(text.encode())>16000 or api.SECRET.search(text): raise BrokerFailed('invalid_bundle')
    value=json.loads(text,object_pairs_hook=no_duplicates)
    if not isinstance(value,dict) or set(value)!= {'summary','files'}: raise BrokerFailed('bundle_schema')
    if not isinstance(value['summary'],str) or not 1<=len(value['summary'])<=300: raise BrokerFailed('bundle_summary')
    files=validate_files(value['files'])
    if len(files)>8 or sum(len(x.encode()) for x in files.values())>12000: raise BrokerFailed('bundle_size')
    tests=0
    for name,body in files.items():
        tree=ast.parse(body,filename=name)
        if name.startswith('tests/test_'):
            tests+=sum(isinstance(node,ast.FunctionDef) and node.name.startswith('test_') for node in ast.walk(tree))
    if tests==0: raise BrokerFailed('bundle_has_no_test_methods')
    return value


def authorize(conn,request,*,min_lease=30):
    if not isinstance(request,dict) or set(request)!={'protocol','job_id','lease_token'} or request['protocol']!=PROTOCOL:
        raise BrokerFailed('broker_protocol')
    if type(request['job_id']) is not int or request['job_id']<=0 or not isinstance(request['lease_token'],str):
        raise BrokerFailed('broker_identity')
    row=conn.execute("SELECT project,kind,payload,state,worker,lease_token,lease_until FROM agent_jobs WHERE id=?",(request['job_id'],)).fetchone()
    if not row or row[0:2]!=('control','review_change') or row[3]!='running' or row[4]!='operations-1' or row[5]!=request['lease_token'] or row[6]<time.time()+min_lease:
        raise BrokerFailed('unauthorized_or_expired_job')
    if conn.execute('SELECT paused FROM agent_queue_control WHERE singleton=1').fetchone()[0]: raise BrokerDeferred('queue_paused')
    payload=json.loads(row[2])
    if not isinstance(payload,dict) or not set(payload)<= {'ai_task','broker_demo','source'}: raise BrokerFailed('developer_payload')
    task=payload.get('ai_task')
    if not isinstance(task,str) or not 1<=len(task)<=2500 or api.SECRET.search(task): raise BrokerFailed('developer_task')
    demo=payload.get('broker_demo',False)
    if type(demo) is not bool or (demo and task!=DEMO_TASK): raise BrokerFailed('unsupported_demo_task')
    digest=hashlib.sha256(json.dumps([task,demo],ensure_ascii=False).encode()).hexdigest()
    return task,demo,digest


def load_bundle(conn,job_id,digest=None):
    row=conn.execute('SELECT task_digest,engine,bundle,source_digest,provider_request_key,model,elapsed_seconds FROM developer_bundles WHERE job_id=?',(job_id,)).fetchone()
    if not row: raise BrokerFailed('broker_bundle_missing')
    bundle=parse_bundle(row[2])
    if row[1] not in ('offline_broker_demo','openai_broker') or manifest(bundle['files'])[1]!=row[3] or (digest and digest!=row[3]):
        raise BrokerFailed('broker_bundle_digest_mismatch')
    return {'files':bundle['files'],'summary':bundle['summary'],'engine':row[1],'source_digest':row[3],
            'generation_job_id':job_id,'provider_request_key':row[4],'model':row[5],'generation_elapsed_seconds':row[6]}


def process(conn,folder,request,*,transport=None):
    task,demo,task_digest=authorize(conn,request)
    cfg=policy(Path(folder)/'broker-policy.json')
    if demo:
        if not cfg['allow_demo']: raise BrokerDeferred('demo_disabled')
    elif not (cfg['enabled'] and cfg['allow_paid']): raise BrokerDeferred('broker_disabled')
    initialize(conn)
    existing=conn.execute('SELECT task_digest FROM developer_bundles WHERE job_id=?',(request['job_id'],)).fetchone()
    if existing:
        if existing[0]!=task_digest: raise BrokerFailed('broker_task_changed')
        return load_bundle(conn,request['job_id'])
    if conn.execute('SELECT count(*) FROM developer_bundles').fetchone()[0]>=100: raise BrokerFailed('broker_retention_limit')
    started=time.monotonic()
    request_key=None;model=None
    if demo:
        bundle=parse_bundle(json.dumps({'summary':'Демонстрационный фиксированный черновик; LLM не вызывалась.','files':DEMO_FILES},ensure_ascii=False))
        engine='offline_broker_demo'
    else:
        request_key='developer-bundle:'+str(request['job_id'])
        try:
            response=api.generate(conn,Path(folder)/'provider-policy.json',KEY_PATH,request_key,task,
                                  project='control',agent='developer',job_id=request['job_id'],
                                  purpose='python_bundle',transport=transport)
        except FileNotFoundError: raise BrokerDeferred('private_provider_configuration_missing') from None
        except api.ProviderBlocked as exc:
            if str(exc) in ('provider_disabled','pricing_review_expired','monthly_budget_exhausted'):
                raise BrokerDeferred(str(exc)) from None
            reason=str(exc)
            safe=reason if len(reason)<=60 and reason.replace('_','').isalpha() else 'blocked'
            raise BrokerFailed('provider_'+safe) from None
        if not response['usable']: raise BrokerFailed('model_output_unusable')
        bundle=parse_bundle(response['text'])
        engine='openai_broker';model=response['model']
    digest=manifest(bundle['files'])[1]
    # Completed response survives a worker crash; paid request identity ignores retry attempt.
    conn.execute('INSERT INTO developer_bundles VALUES(?,?,?,?,?,?,?,?,?)',
                 (request['job_id'],task_digest,engine,json.dumps(bundle,ensure_ascii=False),digest,request_key,model,time.time(),time.monotonic()-started))
    conn.commit()
    authorize(conn,request,min_lease=1)
    return load_bundle(conn,request['job_id'])


def harden():
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,256*1024*1024))
    resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
    resource.setrlimit(resource.RLIMIT_CPU,(12,12))
    libc=ctypes.CDLL(None,use_errno=True)
    if libc.prctl(4,0,0,0,0)!=0: raise BrokerFailed('broker_dump_protection_failed')
    parent=os.getppid()
    if libc.prctl(1,9,0,0,0)!=0 or os.getppid()!=parent: raise BrokerFailed('broker_parent_protection_failed')


def status(conn,folder):
    initialize(conn)
    try: cfg=policy(Path(folder)/'broker-policy.json')
    except (OSError,ValueError,BrokerFailed): cfg={'enabled':False,'allow_paid':False,'allow_demo':False}
    return dict(cfg,bundles=dict(conn.execute('SELECT engine,count(*) FROM developer_bundles GROUP BY engine').fetchall()),
                key_access_checked=False,execution_model='short_lived_subprocess',projects=['control'])


def main():
    os.umask(0o077)
    try:
        if len(sys.argv)!=3 or sys.argv[1]!='--once': raise BrokerFailed('broker_cli')
        harden()
        path=Path(sys.argv[2]).absolute()
        info=path.stat()
        if path.resolve()!=path or 'inventory-bot' in path.parts or info.st_uid!=os.getuid() or info.st_mode & 0o777!=0o600:
            raise BrokerFailed('broker_database_boundary')
        raw=sys.stdin.buffer.read(4097)
        if len(raw)>4096: raise BrokerFailed('broker_request_size')
        request=json.loads(raw,object_pairs_hook=no_duplicates)
        with sqlite3.connect(path,timeout=5) as conn:
            reply={'ok':True,'bundle':process(conn,path.parent,request)}
    except BrokerDeferred as exc:
        reply={'ok':False,'deferred':True,'code':str(exc)}
    except BaseException as exc:
        reply={'ok':False,'deferred':False,'code':str(exc) if isinstance(exc,BrokerFailed) else type(exc).__name__}
    sys.stdout.write(json.dumps(reply,ensure_ascii=False,separators=(',',':'))+'\n')


if __name__=='__main__': main()
