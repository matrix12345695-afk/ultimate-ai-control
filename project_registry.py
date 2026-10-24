"""Reviewed public source reads. No checkout, package install, source execution or writes.

Repository identity, revision, paths, byte lengths and Git object IDs are pinned here.
Incoming tasks cannot supply a URL, repository, revision or path. Raw source stays in
memory and is never copied into notifications or the task journal.
"""
from datetime import datetime, timezone
import hashlib
import json
import re
import time
import urllib.error
import urllib.request

OWNER = 'matrix12345695-afk'
OWNER_ID = 250530390
METHOD = 'pinned_public_read_only_v1'
PROTECTED = {'inventory', 'inventory-mini-app'}
REPOSITORIES = {
    'nova': {'name':'NOVA WEB', 'repository':'nova-web-agency', 'repository_id':1426666605,
        'revision':'1a23239a0a9c7d79905c91505a8741d8350d7e75',
        'files':(
            ('package.json',250,'a0c57553743dfc67afb661ff9c420af4da8571b5'),
            ('server.js',15598,'f68fd3adceb46850a7b9a110d6341251272950b6'),
            ('tests/health.test.js',1355,'5780384b1fe50d6083ea1a0d81ec416059a22754'),
            ('tests/domain-boundaries.test.js',1265,'1207206fbf904e53497eb1312ab1c32e725b6c92'))},
    'kinder': {'name':'Kinder Spa Android', 'repository':'Kinder-Spa-android', 'repository_id':1427568609,
        'revision':'0ef936334629accfd59ae33987462c3c693d33f9',
        'files':(
            ('README.md',1720,'12ed2cb7d85278e50fa7002be13d9342adea5a5f'),
            ('SECURITY.md',615,'13f4c75af894acf55d0b88f14d10c19d4d08b6b2'))}
}


class RepositoryScopeError(PermissionError):
    pass


class RepositoryReadUnavailable(RuntimeError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RepositoryScopeError('repository_redirect_denied')


def check_scope(project, payload):
    if project in PROTECTED:
        raise RepositoryScopeError('Inventory is protected')
    if (project not in REPOSITORIES or not isinstance(payload,dict) or
            payload != {'target':project, 'source':METHOD}):
        raise RepositoryScopeError('repository_read_scope_not_enabled')
    return REPOSITORIES[project]


def blob_id(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


def _read(url, limit, deadline, opener):
    remaining = deadline-time.monotonic()
    if remaining <= 0:
        raise RepositoryReadUnavailable('repository_read_deadline')
    request = urllib.request.Request(url,method='GET',headers={
        'User-Agent':'ULTIMATE-Pinned-Source-Read/4.0',
        'Accept':'application/vnd.github+json' if url.startswith('https://api.github.com/') else 'text/plain',
        'Accept-Encoding':'identity'})
    try:
        with opener(request,timeout=min(5,remaining)) as response:
            if response.geturl() != url or response.status != 200:
                raise RepositoryScopeError('repository_response_destination_or_status')
            if response.headers.get('Content-Encoding','identity').lower() != 'identity':
                raise RepositoryScopeError('repository_encoded_response_denied')
            raw = response.read(limit+1)
    except urllib.error.HTTPError as exc:
        raise RepositoryReadUnavailable('github_http_'+str(exc.code)) from None
    except RepositoryScopeError:
        raise
    except (OSError,ValueError) as exc:
        raise RepositoryReadUnavailable('github_read_'+type(exc).__name__) from None
    if len(raw)>limit:
        raise RepositoryScopeError('repository_response_too_large')
    if time.monotonic()>deadline:
        raise RepositoryReadUnavailable('repository_read_deadline')
    return raw


def _digest(files):
    return hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def inspect_remote(project, payload, *, opener=None):
    scope = check_scope(project,payload)
    opener = opener or urllib.request.build_opener(NoRedirect()).open
    deadline = time.monotonic()+18
    full_name = OWNER+'/'+scope['repository']
    try:
        metadata = json.loads(_read('https://api.github.com/repos/'+full_name,65536,deadline,opener))
    except (ValueError,UnicodeError):
        raise RepositoryScopeError('repository_metadata_invalid') from None
    if (not isinstance(metadata,dict) or type(metadata.get('id')) is not int or
            metadata['id'] != scope['repository_id'] or metadata.get('full_name') != full_name or
            metadata.get('private') is not False or metadata.get('fork') is not False or
            not isinstance(metadata.get('owner'),dict) or metadata['owner'].get('login') != OWNER or
            type(metadata['owner'].get('id')) is not int or metadata['owner']['id'] != OWNER_ID):
        raise RepositoryScopeError('repository_identity_or_visibility_changed')
    fingerprints = []
    facts = {}
    for path, size, expected in scope['files']:
        raw = _read('https://raw.githubusercontent.com/'+full_name+'/'+scope['revision']+'/'+path,size,deadline,opener)
        if len(raw) != size or blob_id(raw) != expected:
            raise RepositoryScopeError('repository_pinned_file_changed')
        fingerprints.append({'path':path,'bytes':len(raw),'git_blob':expected,'sha256':hashlib.sha256(raw).hexdigest()})
        if path == 'package.json':
            try: manifest = json.loads(raw)
            except (ValueError,UnicodeError): raise RepositoryScopeError('package_manifest_invalid') from None
            if not isinstance(manifest,dict) or manifest.get('name') != scope['repository']:
                raise RepositoryScopeError('package_manifest_identity_changed')
            dependencies = manifest.get('dependencies',{})
            scripts = manifest.get('scripts',{})
            if not isinstance(dependencies,dict) or not isinstance(scripts,dict):
                raise RepositoryScopeError('package_manifest_shape_invalid')
            facts = {'stack':'Node.js','test_script_present':isinstance(scripts.get('test'),str),
                     'dependency_names':[name for name in sorted(dependencies) if re.fullmatch(r'[@A-Za-z0-9_./-]{1,80}',name)][:30]}
    if project == 'kinder':
        facts = {'stack':'documentation_scaffold','android_build_verified':False,'backend_verified':False}
    return {'method':METHOD,'project':project,'repository':full_name,'repository_id':scope['repository_id'],
            'revision':scope['revision'],'files':fingerprints,'source_digest':_digest(fingerprints),
            'facts':facts,'code_executed':False,'tests_executed':False,'published':False,
            'complete_project_audit':False}


def valid_result(project, result):
    scope = REPOSITORIES.get(project)
    if (not scope or not isinstance(result,dict) or result.get('method') != METHOD or
            result.get('project') != project or result.get('repository') != OWNER+'/'+scope['repository'] or
            type(result.get('repository_id')) is not int or result['repository_id'] != scope['repository_id'] or
            result.get('revision') != scope['revision'] or
            any(result.get(key) is not False for key in ('code_executed','tests_executed','published','complete_project_audit'))):
        return False
    files = result.get('files')
    if not isinstance(files,list) or len(files) != len(scope['files']): return False
    for file, expected in zip(files,scope['files']):
        if (not isinstance(file,dict) or set(file) != {'path','bytes','git_blob','sha256'} or
                (file.get('path'),file.get('bytes'),file.get('git_blob')) != expected or
                type(file.get('bytes')) is not int or not isinstance(file.get('sha256'),str) or
                not re.fullmatch(r'[0-9a-f]{64}',file['sha256'])):
            return False
    return result.get('source_digest') == _digest(files)


def verified(conn):
    found = {}
    rows = conn.execute("""SELECT id,project,payload,result,updated_at FROM agent_jobs
        WHERE kind='inspect_repository' AND state='succeeded' AND project IN ('nova','kinder')
        ORDER BY updated_at DESC,id DESC LIMIT 200""").fetchall()
    for ident,project,raw_payload,raw_result,at in rows:
        if project in found: continue
        try: payload,result = json.loads(raw_payload),json.loads(raw_result)
        except (TypeError,ValueError): continue
        if payload == {'target':project,'source':METHOD} and valid_result(project,result):
            found[project] = {'job_id':ident,'checked_at':at,'result':result}
    return found


def describe(conn):
    found = verified(conn)
    lines = ['📁 Проекты · доступ ULTIMATE',
             'control: собственный исходный код; отдельные черновики и тесты.',
             'inventory и inventory-mini-app: защищены, доступ исполнителю запрещён.']
    for project,scope in REPOSITORIES.items():
        lines.append('\n'+scope['name']+' · '+OWNER+'/'+scope['repository'])
        lines.append('Разрешено только чтение закреплённых файлов. Версия: '+scope['revision'])
        proof = found.get(project)
        if proof:
            stamp = datetime.fromtimestamp(proof['checked_at'],timezone.utc).strftime('%d.%m %H:%M UTC')
            lines.append(f'✅ Файлы и хеши проверены: {len(proof["result"]["files"])} · #{proof["job_id"]} · {stamp}.')
        else: lines.append('Проверка на VPS ещё не подтверждена.')
        lines.append('/repo_check '+project)
    lines.extend(['\nSAP/iiko, iiko Loader, SAP MB51 и QualiSift: требования сохранены; репозитории и доступ ещё не подтверждены.',
                  'Kinder: закреплённый репозиторий содержит документацию каркаса. Готовый Android-клиент не подтверждён.',
                  'Чтение файлов не означает запуск тестов, изменение сайта, разрешение публикации или соответствие рабочей версии.'])
    return '\n'.join(lines)
