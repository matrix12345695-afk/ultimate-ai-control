"""Credential-free bounded pipe client. No key, endpoint or command comes from task text."""
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time
from model_broker import PROTOCOL,MAX_REPLY_BYTES,BrokerDeferred,BrokerFailed,parse_bundle
from isolated_python import manifest
import emergency_control as emergency


def request(path,job,timeout=23):
    envelope={'protocol':PROTOCOL,'job_id':job['id'],'lease_token':job['lease_token']}
    command=[sys.executable,str(Path(__file__).with_name('model_broker.py')),'--once',str(Path(path).resolve())]
    env={'PATH':'/usr/bin:/bin','HOME':str(Path.home()),'LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'}
    proc=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                          env=env,start_new_session=True,close_fds=True)
    raw=b''
    try:
        proc.stdin.write(json.dumps(envelope).encode());proc.stdin.close()
        with selectors.DefaultSelector() as selector:
            selector.register(proc.stdout,selectors.EVENT_READ)
            deadline=time.monotonic()+timeout
            while selector.get_map():
                if time.monotonic()>=deadline: raise BrokerFailed('broker_timeout_no_automatic_paid_retry')
                for key,_ in selector.select(min(.1,max(0,deadline-time.monotonic()))):
                    chunk=os.read(key.fileobj.fileno(),8192)
                    if not chunk: selector.unregister(key.fileobj);continue
                    raw+=chunk
                    if len(raw)>MAX_REPLY_BYTES: raise BrokerFailed('broker_output_limit')
        if proc.wait(timeout=1)!=0: raise BrokerFailed('broker_process_failed')
        reply=json.loads(raw)
        if not isinstance(reply,dict) or type(reply.get('ok')) is not bool: raise BrokerFailed('invalid_broker_reply')
        if not reply['ok']:
            code=reply.get('code')
            if not isinstance(code,str) or not code.replace('_','').isalnum() or len(code)>100: code='broker_rejected'
            if reply.get('stopped') is True: raise emergency.Stopped(code)
            if reply.get('deferred') is True: raise BrokerDeferred(code)
            raise BrokerFailed(code)
        bundle=reply['bundle']
        parsed=parse_bundle(json.dumps({'files':bundle['files'],'summary':bundle['summary']},ensure_ascii=False))
        if bundle['engine'] not in ('offline_broker_demo','openai_broker') or bundle['source_digest']!=manifest(parsed['files'])[1] or bundle['generation_job_id']!=job['id']:
            raise BrokerFailed('broker_reply_digest_or_origin')
        return bundle
    except (ValueError,KeyError,TypeError,OSError,subprocess.SubprocessError):
        raise BrokerFailed('broker_transport_or_protocol_failed') from None
    finally:
        if proc.poll() is None: os.killpg(proc.pid,signal.SIGKILL)
        proc.wait(timeout=2)
        if not proc.stdin.closed: proc.stdin.close()
        proc.stdout.close()
