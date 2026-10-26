"""Hosted acceptance for exact NOVA private-copy tools; never reads live credentials/data."""
import hashlib,importlib.util,json,os,re,shutil,subprocess,tempfile,urllib.request
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE='a3c3e77e0e74d33241935d25dd3bdfdd306ccd90'
CANDIDATE='9df2a1c9fcc35e83f1a2fe35bee2480afac3254f'
REPO='matrix12345695-afk/nova-web-agency'
IMAGE='postgres@sha256:9770878138a2e83abcb10856d30cc3f24dae0d317bb956db6ab9159de6c3c80d'
CHANGED=['PRIVATE_COPY.md','scripts/export-private-copy.js','scripts/private-copy.js','scripts/restore-private-copy.js','tests/private-copy.test.js']
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*a,**k): raise RuntimeError('source_redirect_denied')

def diagnostic_tests(command,cwd,env):
    import selectors,signal,time
    proc=subprocess.Popen(command,cwd=cwd,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
    output=b'';deadline=time.monotonic()+180
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(proc.stdout,selectors.EVENT_READ)
            while selector.get_map():
                if time.monotonic()>=deadline: raise RuntimeError('private_copy_test_timeout')
                for key,_ in selector.select(.1):
                    chunk=os.read(key.fileobj.fileno(),8192)
                    if not chunk: selector.unregister(key.fileobj);continue
                    output+=chunk
                    if len(output)>512000: raise RuntimeError('private_copy_output_limit')
        text=output.decode();print(text,flush=True)
        assert proc.wait(timeout=3)==0,'private_copy_tests_failed'
        return text
    finally:
        if proc.poll() is None: os.killpg(proc.pid,signal.SIGKILL)
        proc.wait(timeout=3);proc.stdout.close()

def main():
    if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('RUNNER_ENVIRONMENT')!='github-hosted': raise RuntimeError('hosted_disposable_only')
    container=os.environ.get('PG_FIXTURE_CONTAINER','');assert re.fullmatch('[0-9a-f]{64}',container)
    compare='https://api.github.com/repos/'+REPO+'/compare/'+BASE+'...'+CANDIDATE
    def read(url,limit):
        request=urllib.request.Request(url)
        if url==compare: request.add_header('Authorization','Bearer '+os.environ['GH_READ_TOKEN'])
        with urllib.request.build_opener(NoRedirect()).open(request,timeout=15) as response:
            assert response.geturl()==url
            raw=response.read(limit+1);assert len(raw)<=limit;return raw
    diff=json.loads(read(compare,100000));assert diff['base_commit']['sha']==BASE and diff['merge_base_commit']['sha']==BASE and diff['commits'][-1]['sha']==CANDIDATE
    assert sorted(row['filename'] for row in diff['files'])==CHANGED
    os.environ.pop('GH_READ_TOKEN',None)
    clean={'PATH':os.environ['PATH'],'LANG':'C.UTF-8'}
    def docker(*args): return subprocess.run(['docker','exec',container,*args],check=True,capture_output=True,env=clean,timeout=30).stdout
    assert subprocess.run(['docker','inspect','--format','{{.Config.Image}}',container],check=True,capture_output=True,env=clean,timeout=15).stdout.decode().strip()==IMAGE
    for database in ('nova_private_source','nova_private_restore'): docker('createdb','-U','postgres',database)
    evidence=Path.cwd()/'private-copy-evidence';assert not evidence.exists();evidence.mkdir()
    spec=importlib.util.spec_from_file_location('bounded_pg',HERE.parent/'nova-postgres/run.py');utility=importlib.util.module_from_spec(spec);spec.loader.exec_module(utility)
    manifest=(HERE/'source-pins.json').read_bytes();pins=json.loads(manifest)
    with tempfile.TemporaryDirectory(prefix='nova-private-copy-ci-') as name:
        root=Path(name);source=root/'source';source.mkdir();home=root/'home';home.mkdir()
        for path,size,blob in pins:
            raw=read('https://raw.githubusercontent.com/'+REPO+'/'+CANDIDATE+'/'+path,size)
            assert len(raw)==size and hashlib.sha1(b'blob '+str(size).encode()+b'\0'+raw).hexdigest()==blob
            dest=source/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
        env={**clean,'HOME':str(home),'CI':'true','DATABASE_URL':'postgresql://postgres:postgres@127.0.0.1:15432/nova_private_source'}
        node=shutil.which('node');npm=shutil.which('npm');assert utility.bounded([node,'--version'],source,env).strip()=='v24.21.0'
        openssl=utility.bounded(['openssl','version'],source,env).strip();assert openssl.startswith('OpenSSL 3.')
        utility.bounded([npm,'ci','--omit=dev','--ignore-scripts','--no-audit','--no-fund'],source,env,90)
        output=diagnostic_tests([node,'--test','--test-reporter=tap','--test-concurrency=1','--test-timeout=60000','--test-force-exit','tests/private-copy.test.js',str(HERE/'fixture.test.cjs')],source,env)
        print(output,flush=True);counts={}
        for field in ('tests','pass','fail','cancelled','skipped','todo'):
            rows=re.findall(r'^# '+field+r' (\d+)$',output,re.M);assert len(rows)==1;counts[field]=int(rows[0])
        assert counts=={'tests':30,'pass':30,'fail':0,'cancelled':0,'skipped':0,'todo':0}
        for title in ('correct recovery restores all four full tables and verifies row text before commit','large bigint IDs, raw JSON numeric precision, microseconds and Unicode survive','encrypted cursor export captures one5003-row snapshot while another fixture writer proceeds','real SQL failure aborts export and releases its source transaction'):
            assert re.search(r'^ok \d+ - '+re.escape(title)+'$',output,re.M)
        version=docker('psql','-U','postgres','-d','postgres','-Atqc',"SELECT current_setting('server_version')").decode().strip();assert version.startswith('18.')
        report={'schema':'nova-private-copy-acceptance-v1','source_revision':CANDIDATE,'base_revision':BASE,'source_manifest_sha256':hashlib.sha256(manifest).hexdigest(),'dependency_lock_sha256':hashlib.sha256((source/'package-lock.json').read_bytes()).hexdigest(),'counts':counts,'unit_tests':18,'postgres_integration_tests':12,'fixture_leads':5003,'tables':4,'cipher':'AES-256-GCM','key_wrap':'RSA-OAEP-SHA256','container':'OpenSSL CMS DER','openssl_version':openssl,'postgres_version':version,'postgres_image':IMAGE,'node_version':'24.21.0','exact_data_readback_before_commit':True,'bigint_json_precision_preserved':True,'sequence_constraints_dedup_preserved':True,'private_ciphertext_only':True,'unchanged_server_routes':True,'production_access':False,'production_backup_verified':False,'production_key_generated':False,'durable_retention_verified':False,'Render_execution_path_available':False,'published':False}
    (evidence/'report.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');(evidence/'source-pins.json').write_bytes(manifest)
    assert sorted(p.name for p in evidence.iterdir())==['report.json','source-pins.json']
    print(json.dumps(report,sort_keys=True),flush=True)
if __name__=='__main__': main()
