"""Deterministic code drafts plus isolated tests. This is not a generative AI model."""
import hashlib
import json
from pathlib import Path
import os
import tempfile
import time
from code_recipes_v48 import RECIPES,build_files
from isolated_python import run_bundle,manifest,validate_files


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
    existing=conn.execute('SELECT id,source_digest,test_status FROM code_artifacts WHERE job_id=? AND attempt=?',(job['id'],job['attempt'])).fetchone()
    if existing:
        return {'artifact_id':existing[0],'source_digest':existing[1],'test_status':existing[2],'engine':'deterministic_recipe','code_draft_created':True,'published':False}
    files=recipe_files(job['payload'].get('recipe'),job['id'])
    entries,digest=manifest(files)
    report=runner(files,policy_path)
    if report.get('source_digest')!=digest: raise ValueError("test report source digest mismatch")
    root=Path(artifact_root)
    root.mkdir(parents=True,exist_ok=True,mode=0o700)
    if root.is_symlink() or 'inventory-bot' in root.resolve().parts: raise PermissionError("invalid artifact root")
    if len(list(root.iterdir()))>=100: raise ValueError("artifact retention cap reached; reviewed cleanup required")
    target=root/('job-'+str(job['id'])+'-attempt-'+str(job['attempt']))
    if target.exists(): raise ValueError("artifact directory already exists; manual recovery required")
    with tempfile.TemporaryDirectory(prefix='.artifact-',dir=root) as folder:
        stage=Path(folder)/'bundle'
        stage.mkdir(mode=0o700)
        for name,body in files.items():
            p=stage/name
            p.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
            p.write_text(body)
            p.chmod(0o600)
        for name,data in (('manifest.json',entries),('test-report.json',report)):
            p=stage/name
            p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
            p.chmod(0o600)
        stage.rename(target)
    cur=conn.execute("INSERT INTO code_artifacts(job_id,attempt,project,engine,source_digest,manifest,test_status,test_report,path,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                     (job['id'],job['attempt'],'control','deterministic_recipe',digest,json.dumps(entries),report['status'],json.dumps(report,ensure_ascii=False),str(target),time.time()))
    conn.commit()
    return {'artifact_id':cur.lastrowid,'source_digest':digest,'test_status':report['status'],
            'engine':'deterministic_recipe','code_draft_created':True,'published':False,
            'test_elapsed_seconds':report['elapsed_seconds'],'backend':report['backend'],
            'writable_tmp':report['writable_tmp'],'files':entries}


def describe(conn,ident):
    row=conn.execute('SELECT project,engine,source_digest,manifest,test_status,test_report FROM code_artifacts WHERE id=?',(ident,)).fetchone()
    if row is None: return 'Артефакт не найден.'
    report=json.loads(row[5])
    return (f'Кодовый черновик #{ident} · {row[0]}\nДвижок: {row[1]} (без LLM)\n'
            f'SHA-256: {row[2]}\nТесты: {row[4]} · {report.get("elapsed_seconds",0):.3f} сек.\n'
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
