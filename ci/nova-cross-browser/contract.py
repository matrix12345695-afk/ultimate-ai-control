"""Exact offline frontend evidence contract; no browser or network at import."""
import hashlib
import json
from pathlib import Path
import re

REVISION='9df2a1c9fcc35e83f1a2fe35bee2480afac3254f'
SCHEMA='nova-cross-browser-v1'
ENGINES={'chromium':'151.0.7922.34','firefox':'153.0','webkit':'26.5'}
VIEWPORTS={'mobile':[360,800],'tablet':[768,1024],'desktop':[1440,900]}
SHOTS=sorted([f'main-{v}-{lang}.png' for v in VIEWPORTS for lang in ('ru','uz')]+[f'{c}-{v}.png' for c in ('beauty','estate','cafe') for v in VIEWPORTS])
HARNESS_FILES=('ci/nova-cross-browser/contract.py','ci/nova-cross-browser/execute.py',
               'ci/nova-cross-browser/run.py','ci/nova-cross-browser/source-pins.json',
               'ci/nova-browser/browser_suite.py','ci/nova-browser/requirements.txt',
               'ci/nova-browser-candidate/browser_candidate.py','ci/nova-postgres/run.py',
               '.github/workflows/nova-cross-browser.yml')


def harness_hashes(root):
    return {p:hashlib.sha256((Path(root)/p).read_bytes()).hexdigest() for p in HARNESS_FILES}


def validate(report,engine,source_sha,harness_revision,hashes):
    if engine not in ENGINES: raise ValueError('Unknown engine')
    if (not isinstance(report,dict) or report.get('schema')!=SCHEMA or
            report.get('source_revision')!=REVISION or report.get('source_manifest_sha256')!=source_sha or
            not isinstance(harness_revision,str) or not re.fullmatch('[0-9a-f]{40}',harness_revision) or
            report.get('harness_revision')!=harness_revision or report.get('harness_sha256')!=hashes):
        raise ValueError('Source or harness evidence changed')
    if (report.get('engine')!=engine or report.get('browser_version')!=ENGINES[engine] or
            report.get('playwright_version')!='1.62.0'): raise ValueError('Engine version changed')
    counts={'tests':34,'pass':34,'fail':0,'errors':0,'skipped':0}
    if report.get('counts')!=counts or any(type(x) is not int for x in report['counts'].values()):
        raise ValueError('Browser test gate failed')
    if report.get('viewports')!=VIEWPORTS or report.get('advisories')!=[]:
        raise ValueError('Coverage or known findings changed')
    flags={'backend_mocked':True,'production_access':False,'page_network_intercepted':True,
           'physical_device_test':False,'pixel_baseline_test':False,'published':False,
           'mobile_emulation':engine!='firefox'}
    if any(report.get(k) is not v for k,v in flags.items()): raise ValueError('Execution scope changed')
    rows=report.get('screenshots')
    if (not isinstance(rows,list) or len(rows)!=len(SHOTS) or
            any(not isinstance(row,dict) or set(row)!={'path','bytes','sha256'} or
                type(row.get('bytes')) is not int or not 1000<row['bytes']<=3*1024**2 or
                not isinstance(row.get('sha256'),str) or not re.fullmatch('[0-9a-f]{64}',row['sha256']) for row in rows) or
            [row['path'] for row in rows]!=SHOTS or sum(row['bytes'] for row in rows)>20*1024**2):
        raise ValueError('Screenshot manifest invalid')
    return True


def files(report,folder):
    folder=Path(folder)
    if {p.name for p in folder.iterdir()}!=set(SHOTS)|{'report.json'}:
        raise ValueError('Unexpected or missing evidence files')
    for row in report['screenshots']:
        path=folder/row['path']
        if path.is_symlink() or not path.is_file() or path.stat().st_size>3*1024**2:
            raise ValueError('Invalid screenshot file')
        raw=path.read_bytes()
        if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256'] or raw[:8]!=b'\x89PNG\r\n\x1a\n':
            raise ValueError('Screenshot bytes changed')
        width,height=int.from_bytes(raw[16:20],'big'),int.from_bytes(raw[20:24],'big')
        viewport=next(v for v in VIEWPORTS if v in row['path'])
        if width!=VIEWPORTS[viewport][0] or not VIEWPORTS[viewport][1]<=height<=30000:
            raise ValueError('Screenshot dimensions changed')
