"""Hosted browser CI only; no browser or writable runtime is installed on the VPS."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import urllib.request
import gate
import importlib.util

HERE=Path(__file__).resolve().parent


def main():
    if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('RUNNER_ENVIRONMENT')!='github-hosted': raise RuntimeError('Hosted CI only')
    # Reuse only the bounded child-process utility; no PG service or main() is run.
    spec=importlib.util.spec_from_file_location('pg_ci_utility',HERE.parent/'nova-postgres/run.py')
    utility=importlib.util.module_from_spec(spec);spec.loader.exec_module(utility)
    pins=(HERE/'source-pins.json').read_bytes();source_sha=hashlib.sha256(pins).hexdigest()
    evidence=Path.cwd()/'browser-candidate-evidence'
    if evidence.exists(): raise RuntimeError('Evidence output must start empty')
    evidence.mkdir()
    with tempfile.TemporaryDirectory(prefix='nova-browser-ci-') as folder:
        root=Path(folder);source=root/'source';source.mkdir();home=root/'home';home.mkdir()
        for path,size,blob in json.loads(pins):
            url='https://raw.githubusercontent.com/matrix12345695-afk/nova-web-agency/'+gate.REVISION+'/'+path
            with urllib.request.urlopen(url,timeout=15) as response:
                assert response.geturl()==url
                raw=response.read(size+1)
            assert len(raw)==size and hashlib.sha1(b'blob '+str(size).encode()+b'\0'+raw).hexdigest()==blob
            (source/path).write_bytes(raw)
        env={'PATH':os.environ['PATH'],'HOME':str(home),'LANG':'C.UTF-8','PLAYWRIGHT_BROWSERS_PATH':os.environ['PLAYWRIGHT_BROWSERS_PATH'],'PYTHONDONTWRITEBYTECODE':'1'}
        output=utility.bounded([shutil.which('python'),str(HERE/'execute.py'),str(source),str(evidence)],source,env,timeout=180)
        print(output,flush=True)
    report=json.loads((evidence/'report.json').read_text());gate.validate(report,source_sha);gate.files(report,evidence)
    print(json.dumps({'profile':'nova-browser-candidate-v1','source_revision':gate.REVISION,'counts':report['counts'],'browser_version':report['browser_version'],'screenshots':len(report['screenshots']),'advisories':report['advisories'],'report_sha256':hashlib.sha256((evidence/'report.json').read_bytes()).hexdigest(),'production_access':False,'backend_mocked':True},sort_keys=True))


if __name__=='__main__': main()
