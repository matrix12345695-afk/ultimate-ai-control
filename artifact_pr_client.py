"""Credential-free bounded pipe to the existing scoped GitHub App broker."""
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time
from artifact_pr_broker import Pending,Blocked


def request(path,job,timeout=25):
    import nova_ci,browser_ci,browser_candidate_ci,nova_release_ci,locked_build_ci,nova_deploy
    script='nova_ci_broker.py' if job.get('kind')=='test_release' and job.get('payload')=={'target':nova_ci.PROFILE} else 'artifact_pr_broker.py'
    if job.get('kind')=='test_release' and job.get('payload')=={'target':browser_ci.PROFILE}: script='browser_ci_broker.py'
    if job.get('kind')=='test_release' and job.get('payload')=={'target':browser_candidate_ci.PROFILE}: script='browser_candidate_broker.py'
    if job.get('kind')=='test_release' and job.get('payload')=={'target':nova_release_ci.PROFILE}: script='nova_release_broker.py'
    if job.get('kind')=='test_release' and job.get('payload')=={'target':locked_build_ci.PROFILE}: script='locked_build_broker.py'
    if job.get('kind')=='test_release' and job.get('payload')=={'target':nova_deploy.PROFILE}: script='nova_deploy_broker.py'
    command=[sys.executable,str(Path(__file__).with_name(script)),'--once',str(Path(path).resolve())]
    env={'HOME':str(Path.home()),'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'}
    proc=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                          env=env,start_new_session=True,close_fds=True)
    raw=b''
    try:
        proc.stdin.write(json.dumps({'job_id':job['id'],'lease_token':job['lease_token']}).encode());proc.stdin.close()
        with selectors.DefaultSelector() as selector:
            selector.register(proc.stdout,selectors.EVENT_READ);deadline=time.monotonic()+timeout
            while selector.get_map():
                if time.monotonic()>=deadline: raise Pending('artifact_pr_pipe_timeout')
                for key,_ in selector.select(.05):
                    chunk=os.read(key.fileobj.fileno(),4096)
                    if not chunk: selector.unregister(key.fileobj);continue
                    raw+=chunk
                    if len(raw)>12000: raise Blocked('artifact_pr_reply_too_large')
        if proc.wait(timeout=1)!=0: raise Pending('artifact_pr_broker_stopped')
        result=json.loads(raw)
        if result.get('ok') is not True:
            code=result.get('code','artifact_pr_failed')
            if not isinstance(code,str) or not code.replace('_','').isalnum() or len(code)>100: code='artifact_pr_failed'
            raise Pending(code) if result.get('pending') is True else Blocked(code)
        return result['result']
    except (OSError,ValueError,KeyError) as exc:
        raise Pending('artifact_pr_protocol_error') from None
    finally:
        if proc.poll() is None: os.killpg(proc.pid,signal.SIGKILL)
        proc.wait(timeout=2)
        if not proc.stdin.closed: proc.stdin.close()
        proc.stdout.close()
