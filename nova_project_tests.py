"""Exact pinned NOVA read-only test subset. No npm, server start, database or deployment."""
import hashlib
import json
from pathlib import Path
import re
import time
import artifact_recovery
import isolated_node
import project_registry

PROFILE='nova-readonly-node-v1'
REVISION='1a23239a0a9c7d79905c91505a8741d8350d7e75'
PINS=json.loads(Path(__file__).with_name('nova_test_pins.json').read_text())
TEST_FILES=sorted(path for path,_,_ in PINS if path.startswith('tests/'))
DRIVER='\n'.join('require('+json.dumps('/workspace/'+path)+');' for path in TEST_FILES)+'\n'
DRIVER_SHA256=hashlib.sha256(DRIVER.encode()).hexdigest()
EXPECTED_TESTS=24


def initialize(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS project_test_runs(
        id INTEGER PRIMARY KEY,job_id INTEGER NOT NULL UNIQUE,attempt INTEGER NOT NULL,
        project TEXT NOT NULL,profile TEXT NOT NULL,revision TEXT NOT NULL,source_digest TEXT NOT NULL,
        report TEXT NOT NULL,report_sha256 TEXT NOT NULL,created_at REAL NOT NULL)''')
    conn.commit()


def check_scope(job):
    if (job.get('project')!='nova' or job.get('kind')!='test_release' or
            job.get('payload')!={'target':PROFILE} or type(job.get('id')) is not int or job['id']<=0 or
            type(job.get('attempt')) is not int or not 1<=job['attempt']<=5):
        raise PermissionError('NOVA test scope not enabled; Inventory is protected')


def check_sources(files):
    if set(files)!={p for p,_,_ in PINS}: raise ValueError('NOVA source scope changed')
    for path,size,blob in PINS:
        raw=files[path].encode()
        if len(raw)!=size or project_registry.blob_id(raw)!=blob:
            raise ValueError('NOVA pinned source hash mismatch')
    return isolated_node.source_manifest(files)


def cache_path(data):
    return Path(data)/'project-sources'/'nova'/REVISION


def load_sources(data):
    root=cache_path(data)
    artifact_recovery.private_directory(root)
    files={}
    for path,size,_ in PINS:
        p=root/path
        for folder in p.parents:
            if folder==root: break
            artifact_recovery.private_directory(folder)
        files[path]=artifact_recovery.private_read(p,size).decode('utf8')
    check_sources(files)
    return files


def counts(output):
    fields={}
    for key in ('tests','pass','fail','cancelled','skipped','todo'):
        found=re.findall(r'^# '+key+r' ([0-9]{1,5})$',output,re.M)
        if len(found)!=1: return None
        fields[key]=int(found[0])
    return fields


def verdict(report):
    test_counts=counts(report.get('output',''))
    passed={'tests':EXPECTED_TESTS,'pass':EXPECTED_TESTS,'fail':0,'cancelled':0,'skipped':0,'todo':0}
    if report.get('status')=='passed' and (test_counts!=passed or report.get('exit_code')!=0):
        report=dict(report,status='failed')
    return dict(report,test_counts=test_counts,profile=PROFILE,revision=REVISION,
                tests_files=len(TEST_FILES),database_integration=False,browser_test=False,published=False)


def valid_report(report,source_digest):
    return (isinstance(report,dict) and report.get('profile')==PROFILE and report.get('revision')==REVISION
            and report.get('source_digest')==source_digest and report.get('backend')==isolated_node.BACKEND
            and report.get('driver_sha256')==DRIVER_SHA256
            and report.get('status') in ('passed','failed','timeout','output_limit')
            and report.get('database_integration') is False and report.get('browser_test') is False
            and report.get('published') is False and report.get('network') is False
            and report.get('process_forks') is False and report.get('new_threads_after_guard') is False
            and report.get('writable_filesystem') is False and verdict(report)==report)


def serialized(report):
    return json.dumps(report,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False)


def outcome(ident,report,reused):
    return {'project_test_id':ident,'test_status':report['status'],'source_digest':report['source_digest'],
            'profile':PROFILE,'revision':REVISION,'test_counts':report['test_counts'],
            'tests_reused':reused,'published':False,'database_integration':False,'browser_test':False}


def execute(conn,job,data,runner=isolated_node.run):
    check_scope(job)
    files=load_sources(data);_,source_digest=check_sources(files)
    row=conn.execute('SELECT id,attempt,project,profile,revision,source_digest,report,report_sha256 FROM project_test_runs WHERE job_id=?',
                     (job['id'],)).fetchone()
    if row:
        report=json.loads(row[6])
        if (not 1<=row[1]<=job['attempt'] or row[2:6]!=('nova',PROFILE,REVISION,source_digest)
                or hashlib.sha256(row[6].encode()).hexdigest()!=row[7] or not valid_report(report,source_digest)):
            raise artifact_recovery.ArtifactRecoveryBlocked('NOVA saved test evidence changed')
        return outcome(row[0],report,True)
    report=verdict(runner(files,Path(data)/'node-policy.json',DRIVER))
    if not valid_report(report,source_digest): raise ValueError('NOVA test evidence does not match the pinned source')
    raw=serialized(report)
    ident=conn.execute('''INSERT INTO project_test_runs(job_id,attempt,project,profile,revision,source_digest,
        report,report_sha256,created_at) VALUES(?,?,'nova',?,?,?,?,?,?)''',
        (job['id'],job['attempt'],PROFILE,REVISION,source_digest,raw,hashlib.sha256(raw.encode()).hexdigest(),time.time())).lastrowid
    conn.commit()
    return outcome(ident,report,False)


def describe(conn):
    row=conn.execute('SELECT id,job_id,source_digest,report,report_sha256 FROM project_test_runs ORDER BY id DESC LIMIT 1').fetchone()
    lines=['🧪 NOVA WEB · закреплённый набор тестов','Версия: '+REVISION]
    if row:
        try: report=json.loads(row[3])
        except ValueError: report=None
        if hashlib.sha256(row[3].encode()).hexdigest()!=row[4] or not valid_report(report,row[2]):
            lines.append('Основание изменено или неполно: нужна повторная проверка.')
        else:
            lines.extend([f'Отчёт #{row[0]} · /job {row[1]} · {report["status"]}',
                          'Результаты: '+json.dumps(report['test_counts'],ensure_ascii=False),
                          'SHA-256 исходников: '+row[2],f'Файлов тестов: {len(TEST_FILES)}; изоляция: '+report['backend']])
    else: lines.append('Запуск на VPS пока не подтверждён.')
    lines.extend(['Запустить: /test_nova',
                  'Выполняется только выбранный набор. PostgreSQL, полный npm test, рабочий сервер и браузер не проверяются.',
                  'Файлы доступны только для чтения; сеть, новые процессы и потоки после старта Node запрещены. Публикации нет.'])
    return '\n'.join(lines)
