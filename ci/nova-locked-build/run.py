"""Hosted-only reproducible production build, original tests, restart and browser gate."""
import hashlib,importlib.util,json,os,shutil,tempfile,urllib.request
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE='1a23239a0a9c7d79905c91505a8741d8350d7e75'
CANDIDATE='a3c3e77e0e74d33241935d25dd3bdfdd306ccd90'
CHANGED=['.github/workflows/checks.yml','.node-version','.npmrc','index.html','package-lock.json','package.json','render.yaml']
REPO='matrix12345695-afk/nova-web-agency'


def read(url,limit):
    with urllib.request.urlopen(url,timeout=15) as response:
        assert response.geturl()==url
        raw=response.read(limit+1);assert len(raw)<=limit;return raw


def main():
    if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('RUNNER_ENVIRONMENT')!='github-hosted': raise RuntimeError('Hosted locked build only; no production or VPS execution')
    spec=importlib.util.spec_from_file_location('pg_utility',HERE.parent/'nova-postgres/run.py');u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)
    manifest=(HERE/'source-pins.json').read_bytes();pins=json.loads(manifest)
    diff=json.loads(read('https://api.github.com/repos/'+REPO+'/compare/'+BASE+'...'+CANDIDATE,220000))
    assert diff['base_commit']['sha']==BASE and diff['merge_base_commit']['sha']==BASE and diff['commits'][-1]['sha']==CANDIDATE
    assert sorted(row['filename'] for row in diff['files'])==CHANGED
    evidence=Path.cwd()/'locked-build-evidence';assert not evidence.exists();evidence.mkdir()
    with tempfile.TemporaryDirectory(prefix='nova-locked-ci-') as folder:
        root=Path(folder);home=root/'home';home.mkdir();baseline=root/'baseline';candidate=root/'candidate'
        for key,revision,target in [('baseline',BASE,baseline),('candidate',CANDIDATE,candidate)]:
            target.mkdir()
            for path,size,blob in pins[key]:
                raw=read('https://raw.githubusercontent.com/'+REPO+'/'+revision+'/'+path,size)
                assert len(raw)==size and hashlib.sha1(b'blob '+str(size).encode()+b'\0'+raw).hexdigest()==blob
                out=target/path;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw)
        lock=(candidate/'package-lock.json').read_bytes();metadata=json.loads(lock);reviewed=json.loads((HERE.parent/'nova-postgres/package-lock.json').read_text())
        assert {k:v for k,v in metadata['packages'].items() if k}=={k:v for k,v in reviewed['packages'].items() if k}
        package=json.loads((candidate/'package.json').read_text())
        assert package['dependencies']=={'pg':'8.23.1'} and package['engines']=={'node':'24.21.0'}
        assert metadata['packages']['']['dependencies']==package['dependencies'] and metadata['packages']['']['engines']==package['engines']
        assert (candidate/'.node-version').read_text()=='24.21.0\n' and (candidate/'.npmrc').read_text()=='engine-strict=true\n'
        yaml=(candidate/'render.yaml').read_text();assert 'buildCommand: npm ci --omit=dev --ignore-scripts --no-audit --no-fund' in yaml and 'healthCheckPath: /health' in yaml and 'autoDeployTrigger: "off"' in yaml
        (baseline/'package-lock.json').write_bytes((HERE.parent/'nova-postgres/package-lock.json').read_bytes())
        env={'PATH':os.environ['PATH'],'HOME':str(home),'LANG':'C.UTF-8','CI':'true','TEST_POSTGRES_URL':u.URL,'PYTHONDONTWRITEBYTECODE':'1','PLAYWRIGHT_BROWSERS_PATH':os.environ['PLAYWRIGHT_BROWSERS_PATH']}
        node=shutil.which('node');npm=shutil.which('npm');assert u.bounded([node,'--version'],candidate,env).strip()=='v24.21.0'
        npm_version=u.bounded([npm,'--version'],candidate,env).strip()
        u.bounded([npm,'ci','--ignore-scripts','--no-audit','--no-fund'],baseline,env,timeout=90)
        u.bounded([npm,'ci','--omit=dev','--ignore-scripts','--no-audit','--no-fund'],candidate,env,timeout=90)
        installed=json.loads((candidate/'node_modules/.package-lock.json').read_text())['packages']
        assert set(installed)=={k for k in metadata['packages'] if k}
        for name,row in installed.items(): assert row['version']==metadata['packages'][name]['version'] and row['integrity']==metadata['packages'][name]['integrity']
        audit=json.loads(u.bounded([npm,'audit','--omit=dev','--json'],candidate,env,timeout=30))
        assert all(value==0 for value in audit['metadata']['vulnerabilities'].values())
        for mode,expected in [('lock','EUSAGE'),('runtime','EBADENGINE')]:
            negative=root/mode;negative.mkdir();bad=json.loads((candidate/'package.json').read_text())
            if mode=='lock': bad['dependencies']['pg']='8.13.3'
            else: bad['engines']['node']='0.0.0'
            (negative/'package.json').write_text(json.dumps(bad));(negative/'package-lock.json').write_bytes(lock);(negative/'.npmrc').write_text('engine-strict=true\n')
            try: u.bounded([npm,'ci','--ignore-scripts','--no-audit','--no-fund'],negative,env,timeout=30)
            except RuntimeError as exc: assert 'code '+expected in str(exc)
            else: raise AssertionError('Invalid build accepted')
        tests=sorted(path for path,_,_ in pins['candidate'] if path.startswith('tests/'));assert len(tests)==14
        output=u.bounded([node,'--test','--test-concurrency=1','--test-timeout=15000','--test-force-exit','--test-reporter=tap',*tests],candidate,env,timeout=120);print(output,flush=True);counts=u.parse(output)
        env['DATABASE_URL']=u.URL
        output=u.bounded([shutil.which('python3'),str(HERE/'rehearsal.py'),str(baseline),str(candidate),str(evidence/'rehearsal.json'),node],candidate,env,timeout=90);print(output,flush=True)
        browser_env={k:v for k,v in env.items() if k not in ('DATABASE_URL','TEST_POSTGRES_URL')}
        output=u.bounded([shutil.which('python3'),str(HERE/'browser.py'),str(candidate),str(evidence/'browser')],candidate,browser_env,timeout=180);print(output,flush=True)
    rehearsal=json.loads((evidence/'rehearsal.json').read_text());browser=json.loads((evidence/'browser/report.json').read_text())
    assert rehearsal['counts']=={'tests':15,'pass':15,'fail':0,'errors':0,'skipped':0}
    for key in ('source_diff_only_approved_build_config','failed_candidate_not_promoted','upgrade_preserved_all_tables','rollback_html_restored','rollback_preserved_all_tables'): assert rehearsal['proof'][key] is True
    assert browser['counts']=={'tests':34,'pass':34,'fail':0,'errors':0,'skipped':0} and browser['advisories']==[]
    assert browser['source_revision']==CANDIDATE and browser['browser_version']=='151.0.7922.34' and browser['playwright_version']=='1.62.0'
    spec=importlib.util.spec_from_file_location('image_gate',HERE.parent/'nova-browser/gate.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g);g.files(browser,evidence/'browser')
    report={'schema':'nova-locked-build-v1','base_revision':BASE,'candidate_revision':CANDIDATE,'source_manifest_sha256':hashlib.sha256(manifest).hexdigest(),
            'production_lock_sha256':hashlib.sha256(lock).hexdigest(),'node_version':'24.21.0','npm_version':npm_version,'pg_version':'8.23.1','dependency_count':14,
            'nova_test_counts':counts,'rehearsal_counts':rehearsal['counts'],'browser_counts':browser['counts'],'screenshots':len(browser['screenshots']),
            'approved_diff':CHANGED,'lock_mismatch_rejected':True,'runtime_mismatch_rejected':True,'reviewed_dependency_tree_unchanged':True,'npm_known_advisories':0,
            'http_and_data_preservation':True,'blueprint_proposed_only':True,'Render_settings_applied':False,'Render_rollback_executed':False,'production_access':False,'published':False}
    (evidence/'report.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps(report,sort_keys=True),flush=True);print('locked_report_sha256='+hashlib.sha256((evidence/'report.json').read_bytes()).hexdigest())


if __name__=='__main__': main()
