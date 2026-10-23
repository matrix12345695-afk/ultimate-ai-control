"""Deterministic code drafts plus isolated tests. This is not a generative AI model."""
import hashlib
import json
from pathlib import Path
import os
import tempfile
import time
from code_recipes_v48 import RECIPES,build_files
from isolated_python import run_bundle,manifest,validate_files
import acceptance_checks
import artifact_recovery


def initialize(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS code_artifacts(id INTEGER PRIMARY KEY,job_id INTEGER NOT NULL,
      attempt INTEGER NOT NULL,project TEXT NOT NULL,engine TEXT NOT NULL,source_digest TEXT NOT NULL,
      manifest TEXT NOT NULL,test_status TEXT NOT NULL,test_report TEXT NOT NULL,path TEXT NOT NULL,
      created_at REAL NOT NULL,UNIQUE(job_id,attempt))""")
    conn.commit()


def recipe_files(recipe,job_id):
    if recipe not in RECIPES or type(job_id) is not int or job_id<=0: raise ValueError("recipe is not enabled")
    nonce=hashlib.sha256(('uac4-job-'+str(job_id)).encode()).hexdigest()[:8]
    return build_files('CODE_RECIPE:'+recipe+':'+nonce)


def prepare(conn,job,artifact_root,policy_path,runner=run_bundle):
    if job['project']!='control': raise PermissionError("offline recipes are enabled only for ULTIMATE drafts")
    if type(job.get('attempt')) is not int or not 1<=job['attempt']<=5: raise ValueError("invalid job attempt")
    files=recipe_files(job['payload'].get('recipe'),job['id'])
    return prepare_files(conn,job,artifact_root,policy_path,files,engine='deterministic_recipe',runner=runner)


def prepare_files(conn,job,artifact_root,policy_path,files,*,engine,provenance=None,runner=run_bundle,acceptance_profile=None):
    if job['project']!='control' or engine not in ('deterministic_recipe','offline_broker_demo','openai_broker'):
        raise PermissionError('draft source is not enabled')
    if type(job.get('attempt')) is not int or not 1<=job['attempt']<=5: raise ValueError('invalid job attempt')
    if type(job.get('id')) is not int or job['id']<=0: raise ValueError('invalid job identity')
    if acceptance_profile is not None and (engine!='offline_broker_demo' or acceptance_profile!=acceptance_checks.PROFILE):
        raise ValueError('acceptance profile is enabled only for the reviewed offline demo')
    entries,digest=manifest(files)
    root=Path(artifact_root).absolute()
    if 'inventory-bot' in root.resolve().parts: raise PermissionError('invalid artifact root')
    root.mkdir(parents=True,exist_ok=True,mode=0o700)
    artifact_recovery.private_directory(root)
    existing=artifact_recovery.restore(conn,job,root,files,engine,acceptance_profile,provenance)
    if existing: return existing
    if len(list(root.iterdir()))>=100: raise ValueError('artifact retention cap reached; reviewed cleanup required')
    # The reviewed demo gets two eight-second runs in separate namespaces, within the
    # worker's existing 30-second tick deadline. General bundles keep their existing limit.
    report=runner(files,policy_path,timeout=8) if acceptance_profile else runner(files,policy_path)
    if report.get('source_digest')!=digest: raise ValueError("test report source digest mismatch")
    own_status=report['status']
    checks={'status':'not_configured','profile':None}
    if acceptance_profile:
        checks=(acceptance_checks.check(files,policy_path,acceptance_profile,runner=runner) if own_status=='passed'
                else {'status':'not_run','profile':acceptance_profile,'harness_sha256':acceptance_checks.HARNESS_SHA256,
                      'candidate_source_digest':digest,'reason':'candidate_tests_failed'})
    report=dict(report,candidate_test_status=own_status,independent_acceptance=checks)
    if acceptance_profile and checks['status']!='passed': report['status']='failed'
    report['elapsed_seconds']+=checks.get('elapsed_seconds',0)
    if provenance is not None: report=dict(report,provenance=provenance)
    target=root/('job-'+str(job['id'])+'-attempt-'+str(job['attempt']))
    if target.exists() or target.is_symlink(): raise artifact_recovery.ArtifactRecoveryBlocked('artifact directory appeared during execution')
    created=time.time()
    report=dict(report,artifact_identity=dict(format='uac-artifact-v1',job_id=job['id'],attempt=job['attempt'],project='control',engine=engine,source_digest=digest),artifact_created_at=created)
    with tempfile.TemporaryDirectory(prefix='.artifact-',dir=root) as folder:
        stage=Path(folder)/'bundle'
        stage.mkdir(mode=0o700)
        for name,body in files.items():
            p=stage/name
            p.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
            artifact_recovery.write_private(p,body.encode())
        for name,data in (('manifest.json',entries),('test-report.json',report)):
            p=stage/name
            artifact_recovery.write_private(p,(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
        for directory in sorted((p for p in stage.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):
            artifact_recovery.sync_directory(directory)
        artifact_recovery.sync_directory(stage)
        stage.rename(target)
        artifact_recovery.sync_directory(root)
    cur=conn.execute("INSERT INTO code_artifacts(job_id,attempt,project,engine,source_digest,manifest,test_status,test_report,path,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                     (job['id'],job['attempt'],'control',engine,digest,json.dumps(entries),report['status'],json.dumps(report,ensure_ascii=False),str(target),created))
    conn.commit()
    return artifact_recovery.outcome(cur.lastrowid,engine,digest,entries,report)


def describe(conn,ident):
    row=conn.execute('SELECT project,engine,source_digest,manifest,test_status,test_report FROM code_artifacts WHERE id=?',(ident,)).fetchone()
    if row is None: return 'Артефакт не найден.'
    report=json.loads(row[5])
    label='OpenAI: результат требует проверки' if row[1]=='openai_broker' else 'без LLM'
    return (f'Кодовый черновик #{ident} · {row[0]}\nДвижок: {row[1]} ({label})\n'
            f'SHA-256: {row[2]}\nТесты: {row[4]} · {report.get("elapsed_seconds",0):.3f} сек.\n'
            f'Независимая приёмка: {report.get("independent_acceptance",{}).get("status","not_configured")}\n'
            f'Изоляция: {report.get("backend")} · сеть отключена\n'
            +'\n'.join(item['path'] for item in json.loads(row[3]))
            +'\nПубликация не выполнялась. Полный отчёт и исходники сохранены отдельно.')[:3900]


def source_preview(conn,ident,index=1):
    row=conn.execute('SELECT path,manifest FROM code_artifacts WHERE id=?',(ident,)).fetchone()
    if row is None: return 'Артефакт не найден.'
    entries=json.loads(row[1])
    if type(index) is not int or not 1<=index<=len(entries): raise ValueError('invalid source file index')
    root=Path(row[0])
    if root.is_symlink(): raise ValueError('artifact symlink refused')
    root=root.resolve()
    p=root/entries[index-1]['path']
    if p.is_symlink() or root not in p.resolve().parents: raise ValueError('source path refused')
    raw=p.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=entries[index-1]['sha256']: raise ValueError('artifact source changed')
    return (f"Артефакт #{ident} · файл {index}/{len(entries)}\n"+entries[index-1]['path']+'\n\n'+raw.decode()[:3300])
