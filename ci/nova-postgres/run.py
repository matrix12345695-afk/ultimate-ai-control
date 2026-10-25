"""Run only on an ephemeral GitHub-hosted runner with its disposable PG16 service."""
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import signal
import subprocess
import tempfile
import time
import urllib.request

REVISION='1a23239a0a9c7d79905c91505a8741d8350d7e75'
EXPECTED=34
HERE=Path(__file__).resolve().parent
URL='postgresql://postgres:postgres@127.0.0.1:15432/novaweb_test'


def bounded(command,cwd,env,timeout=120):
    proc=subprocess.Popen(command,cwd=cwd,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
    output=b'';deadline=time.monotonic()+timeout
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(proc.stdout,selectors.EVENT_READ)
            while selector.get_map():
                if time.monotonic()>=deadline: raise RuntimeError('CI command timed out')
                for key,_ in selector.select(.1):
                    chunk=os.read(key.fileobj.fileno(),8192)
                    if not chunk: selector.unregister(key.fileobj);continue
                    output+=chunk
                    if len(output)>512000: raise RuntimeError('CI output limit')
        if proc.wait(timeout=2)!=0: raise RuntimeError('CI command failed: '+output[-12000:].decode(errors='replace'))
        return output.decode()
    finally:
        if proc.poll() is None: os.killpg(proc.pid,signal.SIGKILL)
        proc.wait(timeout=3);proc.stdout.close()


def parse(output):
    actual={}
    for field in ('tests','pass','fail','cancelled','skipped','todo'):
        rows=re.findall(r'^# '+field+r' (\d+)$',output,re.M)
        if len(rows)!=1: raise ValueError('Incomplete test summary')
        actual[field]=int(rows[0])
    if actual!={'tests':EXPECTED,'pass':EXPECTED,'fail':0,'cancelled':0,'skipped':0,'todo':0}: raise ValueError('NOVA test gate failed: '+str(actual))
    for name in ('PostgreSQL CRM survives module reload and records status history','Real PostgreSQL backup is restored into an isolated empty destination'):
        if not re.search(r'^ok \d+ - '+re.escape(name)+r'$',output,re.M): raise ValueError('Database test not completed: '+name)
    return actual


def main():
    # No user/prod URL, .env, npm hook or GitHub credential enters the test child.
    if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('RUNNER_ENVIRONMENT')!='github-hosted': raise RuntimeError('Hosted CI only; never use this harness on the VPS')
    import shutil
    node=shutil.which('node');npm=shutil.which('npm');assert node and npm
    pins=json.loads((HERE/'source-pins.json').read_text());lock=(HERE/'package-lock.json').read_bytes()
    metadata=json.loads(lock)
    assert len(metadata['packages'])==15
    for name,item in metadata['packages'].items():
        if not name: continue
        assert item['license'] in ('MIT','ISC') and item['resolved'].startswith('https://registry.npmjs.org/')
        assert item['integrity'].startswith('sha512-') and not item.get('hasInstallScript')
    with tempfile.TemporaryDirectory(prefix='nova-pg-ci-') as folder:
        root=Path(folder);source=root/'source';source.mkdir();home=root/'home';home.mkdir()
        deadline=time.monotonic()+90
        for path,size,blob in pins:
            assert time.monotonic()<deadline
            url='https://raw.githubusercontent.com/matrix12345695-afk/nova-web-agency/'+REVISION+'/'+path
            with urllib.request.urlopen(url,timeout=10) as response:
                assert response.geturl()==url
                raw=response.read(size+1)
            assert len(raw)==size and hashlib.sha1(b'blob '+str(size).encode()+b'\0'+raw).hexdigest()==blob
            target=source/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        (source/'package-lock.json').write_bytes(lock)
        env={'PATH':os.environ['PATH'],'HOME':str(home),'LANG':'C.UTF-8','CI':'true','TEST_POSTGRES_URL':URL}
        assert bounded([node,'--version'],source,env).strip()=='v24.21.0'
        bounded([npm,'ci','--ignore-scripts','--no-audit','--no-fund'],source,env,timeout=90)
        tests=sorted(path for path,_,_ in pins if path.startswith('tests/'))
        assert len(tests)==14
        output=bounded([node,'--test','--test-concurrency=1','--test-timeout=15000','--test-force-exit','--test-reporter=tap',*tests],source,env,timeout=120)
        print(output,flush=True);counts=parse(output)
        database=json.loads(bounded([node,str(HERE/'assert-database.cjs')],source,env,timeout=15))
        assert database=={'postgres_major':16,'persisted_status_history':True,'restored_fields':True}
        print(json.dumps({'profile':'nova-postgres-ci-v1','revision':REVISION,'counts':counts,'database':database,'source_manifest_sha256':hashlib.sha256((HERE/'source-pins.json').read_bytes()).hexdigest(),'dependency_lock_sha256':hashlib.sha256(lock).hexdigest(),'production_access':False,'published':False},sort_keys=True))


if __name__=='__main__': main()
