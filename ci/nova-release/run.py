"""Hosted-only exact-source restart rehearsal; no Render or production credential."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import urllib.request

HERE=Path(__file__).resolve().parent
BASE='1a23239a0a9c7d79905c91505a8741d8350d7e75'
CANDIDATE='495a7f1a1a3a25c45fd98101fffa9c02e58f3970'
REPO='matrix12345695-afk/nova-web-agency'


def read(url,limit):
    with urllib.request.urlopen(url,timeout=15) as response:
        assert response.geturl()==url
        raw=response.read(limit+1);assert len(raw)<=limit;return raw


def main():
    if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('RUNNER_ENVIRONMENT')!='github-hosted': raise RuntimeError('Hosted-only rehearsal; never run on production or VPS')
    spec=importlib.util.spec_from_file_location('pg_ci_utility',HERE.parent/'nova-postgres/run.py')
    utility=importlib.util.module_from_spec(spec);spec.loader.exec_module(utility)
    manifest=(HERE/'source-pins.json').read_bytes();pins=json.loads(manifest)
    diff=json.loads(read('https://api.github.com/repos/'+REPO+'/compare/'+BASE+'...'+CANDIDATE,200000))
    assert diff['base_commit']['sha']==BASE and diff['merge_base_commit']['sha']==BASE
    assert diff['commits'][-1]['sha']==CANDIDATE and len(diff['files'])==1
    assert diff['files'][0]['filename']=='index.html' and diff['files'][0]['status']=='modified'
    assert diff['files'][0]['sha']==next(row[2] for row in pins['candidate'] if row[0]=='index.html')
    lock=(HERE.parent/'nova-postgres/package-lock.json').read_bytes();metadata=json.loads(lock)
    assert len(metadata['packages'])==15
    for name,item in metadata['packages'].items():
        if name: assert item['license'] in ('MIT','ISC') and item['resolved'].startswith('https://registry.npmjs.org/') and item['integrity'].startswith('sha512-') and not item.get('hasInstallScript')
    evidence=Path.cwd()/'release-evidence';assert not evidence.exists();evidence.mkdir()
    with tempfile.TemporaryDirectory(prefix='nova-release-ci-') as folder:
        root=Path(folder);home=root/'home';home.mkdir();baseline=root/'baseline';candidate=root/'candidate'
        for key,revision,target in [('baseline',BASE,baseline),('candidate',CANDIDATE,candidate)]:
            target.mkdir()
            for path,size,blob in pins[key]:
                raw=read('https://raw.githubusercontent.com/'+REPO+'/'+revision+'/'+path,size)
                assert len(raw)==size and hashlib.sha1(b'blob '+str(size).encode()+b'\0'+raw).hexdigest()==blob
                out=target/path;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw)
            (target/'package-lock.json').write_bytes(lock)
        env={'PATH':os.environ['PATH'],'HOME':str(home),'LANG':'C.UTF-8','CI':'true','TEST_POSTGRES_URL':utility.URL,'PYTHONDONTWRITEBYTECODE':'1'}
        node=shutil.which('node');npm=shutil.which('npm');assert node and npm
        assert utility.bounded([node,'--version'],baseline,env).strip()=='v24.21.0'
        utility.bounded([npm,'ci','--ignore-scripts','--no-audit','--no-fund'],baseline,env,timeout=90)
        shutil.copytree(baseline/'node_modules',candidate/'node_modules')
        tests=sorted(path for path,_,_ in pins['candidate'] if path.startswith('tests/'));assert len(tests)==14
        output=utility.bounded([node,'--test','--test-concurrency=1','--test-timeout=15000','--test-force-exit','--test-reporter=tap',*tests],candidate,env,timeout=120)
        print(output,flush=True);counts=utility.parse(output)
        env['DATABASE_URL']=utility.URL
        guard_check="const a=require('node:assert/strict'),n=require('node:net');a.throws(()=>n.connect(443,'example.com'),/denied/);a.throws(()=>n.createServer().listen(19999,'0.0.0.0'),/denied/);console.log('external_network_and_unexpected_listener_denied=PASS')"
        print(utility.bounded([node,'--require',str(HERE/'loopback-guard.cjs'),'-e',guard_check],baseline,env,timeout=5),flush=True)
        output=utility.bounded([shutil.which('python3'),str(HERE/'execute.py'),str(baseline),str(candidate),str(evidence/'report.json'),node],baseline,env,timeout=90)
        print(output,flush=True)
    report=json.loads((evidence/'report.json').read_text())
    assert report['counts']=={'tests':15,'pass':15,'fail':0,'errors':0,'skipped':0}
    assert report['schema']=='nova-release-rehearsal-v1' and report['base_revision']==BASE and report['candidate_revision']==CANDIDATE
    for key in ('source_diff_only_index','failed_candidate_not_promoted','upgrade_preserved_all_tables','rollback_html_restored','rollback_preserved_all_tables'): assert report['proof'][key] is True
    for key in ('render_api_rollback_executed','production_access','published','database_restored'): assert report[key] is False
    assert report['real_http'] is True and report['fixture_data_only'] is True and report['loopback_only'] is True
    report.update(nova_test_counts=counts,source_manifest_sha256=hashlib.sha256(manifest).hexdigest(),dependency_lock_sha256=hashlib.sha256(lock).hexdigest(),node_version='24.21.0',execution_location='github_hosted_disposable_runner',render_artifact_availability_verified=False)
    (evidence/'report.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'profile':report['schema'],'candidate_revision':CANDIDATE,'counts':report['counts'],'nova_test_counts':counts,'proof':report['proof'],'report_sha256':hashlib.sha256((evidence/'report.json').read_bytes()).hexdigest(),'render_rollback_executed':False,'production_access':False,'published':False},sort_keys=True))


if __name__=='__main__': main()
