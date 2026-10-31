"""Ephemeral GitHub-hosted frontend checks. Never install/run on the VPS."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import time
import urllib.request
import contract

HERE=Path(__file__).resolve().parent


def main():
    if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('RUNNER_ENVIRONMENT')!='github-hosted':
        raise RuntimeError('GitHub-hosted CI only')
    engine=sys.argv[1] if len(sys.argv)==2 else None
    revision=os.environ.get('GITHUB_SHA','')
    if engine not in contract.ENGINES or not re.fullmatch('[0-9a-f]{40}',revision):
        raise ValueError('Fixed engine and harness revision required')
    spec=importlib.util.spec_from_file_location('bounded_ci_utility',HERE.parent/'nova-postgres/run.py')
    utility=importlib.util.module_from_spec(spec);spec.loader.exec_module(utility)
    manifest=(HERE/'source-pins.json').read_bytes();pins=json.loads(manifest)
    if [row[0] for row in pins]!=['index.html','showcase.html']: raise ValueError('HTML-only input required')
    hashes=contract.harness_hashes(HERE.parents[1])
    output=Path.cwd()/('cross-browser-evidence-'+engine)
    output.mkdir()  # Refuse to reuse evidence from a previous run.
    with tempfile.TemporaryDirectory(prefix='nova-cross-browser-') as folder:
        root=Path(folder);source=root/'source';source.mkdir();home=root/'home';home.mkdir()
        deadline=time.monotonic()+45
        for path,size,blob in pins:
            if time.monotonic()>=deadline: raise RuntimeError('Source download deadline')
            url='https://raw.githubusercontent.com/matrix12345695-afk/nova-web-agency/'+contract.REVISION+'/'+path
            with urllib.request.urlopen(url,timeout=15) as response:
                if response.geturl()!=url: raise ValueError('Source redirect refused')
                raw=response.read(size+1)
            if len(raw)!=size or hashlib.sha1(b'blob '+str(size).encode()+b'\0'+raw).hexdigest()!=blob:
                raise ValueError('Source bytes changed')
            (source/path).write_bytes(raw)
        env={'PATH':os.environ['PATH'],'HOME':str(home),'LANG':'C.UTF-8',
             'PLAYWRIGHT_BROWSERS_PATH':os.environ['PLAYWRIGHT_BROWSERS_PATH'],'PYTHONDONTWRITEBYTECODE':'1'}
        print(utility.bounded([sys.executable,str(HERE/'execute.py'),str(source),str(output),engine,revision],source,env,timeout=240),flush=True)
    report=json.loads((output/'report.json').read_text())
    contract.validate(report,engine,hashlib.sha256(manifest).hexdigest(),revision,hashes)
    contract.files(report,output)
    print(json.dumps({'schema':contract.SCHEMA,'engine':engine,'source_revision':contract.REVISION,
                      'harness_revision':revision,'counts':report['counts'],'screenshots':len(report['screenshots']),
                      'report_sha256':hashlib.sha256((output/'report.json').read_bytes()).hexdigest(),
                      'production_access':False,'published':False},sort_keys=True))


if __name__=='__main__': main()
