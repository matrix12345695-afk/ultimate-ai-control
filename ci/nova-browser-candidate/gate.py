"""Pure report/file contract; importing this module never launches a browser."""
import hashlib
import json
from pathlib import Path
import re

REVISION='90f60bdaead95b65857dd0a19a905f43cf8658ef'
VIEWPORTS={'mobile':[360,800],'tablet':[768,1024],'desktop':[1440,900]}
SHOTS=sorted([f'main-{v}-{lang}.png' for v in VIEWPORTS for lang in ('ru','uz')]+[f'{c}-{v}.png' for c in ('beauty','estate','cafe') for v in VIEWPORTS])
ADVISORIES=[]


def validate(report,source_sha):
    if not isinstance(report,dict) or report.get('schema')!='nova-browser-candidate-v1' or report.get('source_revision')!=REVISION or report.get('source_manifest_sha256')!=source_sha: raise ValueError('Browser source evidence changed')
    if report.get('engine')!='chromium' or report.get('browser_version')!='151.0.7922.34' or report.get('playwright_version')!='1.62.0': raise ValueError('Browser version changed')
    expected={'tests':34,'pass':34,'fail':0,'errors':0,'skipped':0}
    if report.get('counts')!=expected or any(type(x) is not int for x in report['counts'].values()): raise ValueError('Browser test gate failed')
    if report.get('viewports')!=VIEWPORTS or report.get('advisories')!=ADVISORIES: raise ValueError('Browser coverage/findings changed')
    if any(report.get(key) is not value for key,value in {'backend_mocked':True,'production_access':False,'page_network_intercepted':True,'physical_device_test':False,'pixel_baseline_test':False,'published':False}.items()): raise ValueError('Browser execution scope changed')
    rows=report.get('screenshots')
    if (not isinstance(rows,list) or [row.get('path') for row in rows]!=SHOTS or
            any(set(row)!={'path','bytes','sha256'} or type(row['bytes']) is not int or not 1000<row['bytes']<=3*1024**2 or
                not isinstance(row['sha256'],str) or not re.fullmatch('[0-9a-f]{64}',row['sha256']) for row in rows) or
            sum(row['bytes'] for row in rows)>20*1024**2): raise ValueError('Screenshot manifest invalid')
    return True


def files(report,folder):
    folder=Path(folder)
    if {p.name for p in folder.iterdir()}!=set(SHOTS)|{'report.json'}: raise ValueError('Screenshot files incomplete')
    for row in report['screenshots']:
        path=folder/row['path'];raw=path.read_bytes()
        if path.is_symlink() or len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256'] or raw[:8]!=b'\x89PNG\r\n\x1a\n': raise ValueError('Screenshot bytes changed')
        width,height=int.from_bytes(raw[16:20],'big'),int.from_bytes(raw[20:24],'big')
        viewport=next(v for v in VIEWPORTS if v in row['path'])
        if width!=VIEWPORTS[viewport][0] or not VIEWPORTS[viewport][1]<=height<=30000: raise ValueError('Screenshot dimensions changed')
