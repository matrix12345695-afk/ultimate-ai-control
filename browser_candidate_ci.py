"""Hosted Chromium frontend evidence with expiring screenshot archive metadata."""
from datetime import datetime
import json
import math
from pathlib import Path
import re
import time
import artifact_prs as util
import artifact_pr_broker as broker
import hosted_ci
import task_queue as q

PROFILE='nova-browser-candidate-v1'
CONTRACT=json.loads(Path(__file__).with_name('browser_candidate_contract.json').read_text())
REPO='matrix12345695-afk/ultimate-ai-control'


import browser_ci as baseline


def observe(client): return baseline.observe(client,CONTRACT)


def valid(report): return baseline.valid(report,CONTRACT)


def initialize(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS browser_candidate_runs(
      id INTEGER PRIMARY KEY,job_id INTEGER NOT NULL UNIQUE,report TEXT NOT NULL,
      report_sha256 TEXT NOT NULL,created_at REAL NOT NULL)''');conn.commit()


def scope(job):
    if job.get('project')!='nova' or job.get('kind')!='test_release' or job.get('payload')!={'target':PROFILE}: raise broker.Blocked('browser_ci_scope_denied')


def save(conn,job,report):
    scope(job)
    if not valid(report): raise broker.Blocked('browser_ci_report_contract_changed')
    with q._write(conn):
        now=time.time();owned=q._owned(conn,job['id'],job['lease_token'],now)
        row=conn.execute('SELECT project,kind,payload FROM agent_jobs WHERE id=?',(job['id'],)).fetchone()
        if row[:2]!=('nova','test_release') or json.loads(row[2])!={'target':PROFILE} or not owned[3]<=report['checked_at']<=now: raise broker.Blocked('browser_ci_observation_changed')
        row=conn.execute('SELECT id,report,report_sha256 FROM browser_candidate_runs WHERE job_id=?',(job['id'],)).fetchone()
        if row:
            old=json.loads(row[1])
            if not valid(old) or util.digest(old)!=row[2] or {k:v for k,v in old.items() if k!='checked_at'}!={k:v for k,v in report.items() if k!='checked_at'}: raise broker.Blocked('browser_ci_saved_evidence_changed')
            report=old;ident=row[0]
        else:
            ident=conn.execute('INSERT INTO browser_candidate_runs(job_id,report,report_sha256,created_at) VALUES(?,?,?,?)',
                               (job['id'],util.canonical(report),util.digest(report),now)).lastrowid
    return {'browser_candidate_id':ident,'report_sha256':util.digest(report),'test_status':report['status'],'test_counts':report['counts'],
            'revision':report['source_revision'],'harness_commit':report['harness_commit'],'ci_url':report['ci_url'],
            'ci_run_id':report['ci_run_id'],'ci_attempt':report['ci_attempt'],'artifact_url':report['artifact']['url'] if report['artifact'] else None,
            'screenshots':report['screenshots'],'advisories':report['advisories'],'backend_mocked':True,'vps_local_execution':False,'published':False}


def describe(conn):
    lines=['NOVA WEB · проверенный черновик интерфейса',
           'Версия NOVA: '+CONTRACT['source_revision'],
           'Draft PR: https://github.com/matrix12345695-afk/nova-web-agency/pull/15']
    row=conn.execute('SELECT id,job_id,report,report_sha256 FROM browser_candidate_runs ORDER BY id DESC LIMIT 1').fetchone()
    if row:
        report=json.loads(row[2])
        if not valid(report) or util.digest(report)!=row[3]: lines.append('Основание изменено; нужна новая сверка.')
        else:
            lines.extend([f'Отчёт #{row[0]} · /job {row[1]} · {report["status"]}',report['ci_url'],
                          'Сверка UTC: '+time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(report['checked_at']))])
            if report['status']=='passed':
                lines.append('✅ Выполнено в черновике: перевод двух подсказок RU/UZ, кнопки языка44×44px, положение на мобильном экране и клавиатурный фокус. Chromium:34 проверки,3 размера экрана,15 снимков.')
                lines.extend([report['artifact']['url'],'Архив до '+report['artifact']['expires_at']])
                if baseline.expires(report['artifact']['expires_at'])<=time.time(): lines.append('Срок хранения архива истёк; это исторический результат.')
            else: lines.append('Проверки черновика не прошли; исправления не подтверждены.')
    else: lines.append('Сверка черновика на VPS ещё не завершена.')
    lines.extend(['Сайт не опубликован. Требуются решение владельца и проверенный способ публикации/отката.',
                  'API подставной; реальных заявок нет. Это не полный аудит перевода, доступности или реальных телефонов.',
                  'Обновить сверку: /test_nova_candidate. Исходная версия и её замечания: /nova_browser.'])
    return '\n'.join(lines)
