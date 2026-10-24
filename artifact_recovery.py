"""Recover only complete, private artifacts for the same job and exact test contract."""
import json
import math
import os
from pathlib import Path
import re
import stat
import acceptance_checks
from isolated_python import manifest


class ArtifactRecoveryBlocked(ValueError): pass


def require(value,message):
    if not value: raise ArtifactRecoveryBlocked(message)


def private_directory(path):
    require(path.absolute()==path.resolve(),'artifact directory symlink refused')
    info=path.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid==os.getuid() and stat.S_IMODE(info.st_mode)==0o700,'artifact directory permissions changed')


def private_read(path,maximum):
    require(path.absolute()==path.resolve(),'artifact file symlink refused')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        info=os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_uid==os.getuid() and stat.S_IMODE(info.st_mode)==0o600,'artifact file permissions changed')
        with os.fdopen(fd,'rb',closefd=False) as stream: raw=stream.read(maximum+1)
        require(len(raw)<=maximum,'artifact file exceeds expected size')
        return raw
    finally: os.close(fd)


def write_private(path,raw):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:
        with os.fdopen(fd,'wb',closefd=False) as stream:
            stream.write(raw);stream.flush();os.fsync(fd)
    finally: os.close(fd)


def sync_directory(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try: os.fsync(fd)
    finally: os.close(fd)


def outcome(ident,engine,digest,entries,report,*,reused=False,origin_attempt=None):
    return dict(artifact_id=ident,source_digest=digest,test_status=report['status'],engine=engine,
                code_draft_created=True,published=False,
                independent_acceptance=report.get('independent_acceptance',{}).get('status','not_configured'),
                test_elapsed_seconds=report['elapsed_seconds'],backend=report['backend'],
                writable_tmp=report['writable_tmp'],files=entries,tests_reused=reused,
                recovered_from_attempt=origin_attempt if reused else None)


def restore(conn,job,root,files,engine,profile,provenance):
    """No candidate code or tests run during recovery; unknown remnants stop the task."""
    entries,digest=manifest(files)
    rows=conn.execute('SELECT id,attempt,source_digest,engine,manifest,test_status,test_report,path,created_at FROM code_artifacts WHERE job_id=? ORDER BY attempt DESC',(job['id'],)).fetchall()
    targets=list(root.glob('job-'+str(job['id'])+'-attempt-*'))
    require(len(rows)<=1 and len(targets)<=1,'multiple artifact attempts require review')
    if not rows and not targets: return None
    row=rows[0] if rows else None
    if row:
        ident,attempt,saved_digest,saved_engine,saved_manifest,saved_status,saved_report,saved_path,created=row
        require(saved_digest==digest and saved_engine==engine,'artifact source changed')
        target=Path(saved_path)
        require(target==root/('job-'+str(job['id'])+'-attempt-'+str(attempt)),'artifact path changed')
        require(targets==[target],'artifact directory missing or ambiguous')
    else:
        target=targets[0]
        match=re.fullmatch('job-'+str(job['id'])+r'-attempt-([1-5])',target.name)
        require(match is not None,'unknown artifact directory')
        attempt=int(match[1]);ident=None
    require(type(attempt) is int and 1<=attempt<=job['attempt'],'artifact attempt is not owned by this retry')
    try:
        private_directory(target)
        saved_entries=json.loads(private_read(target/'manifest.json',64000))
        report=json.loads(private_read(target/'test-report.json',256000))
        require(saved_entries==entries,'artifact manifest changed')
        require(isinstance(report,dict) and report.get('source_digest')==digest,'artifact report source changed')
        require(report.get('status') in ('passed','failed','timeout','output_limit'),'artifact report status invalid')
        elapsed=report.get('elapsed_seconds')
        require(type(elapsed) in (int,float) and math.isfinite(elapsed) and elapsed>=0,'artifact report timing missing')
        require(isinstance(report.get('backend'),str) and bool(report['backend']) and type(report.get('writable_tmp')) is bool and isinstance(report.get('output'),str),'artifact execution evidence incomplete')
        for name,body in files.items():
            path=target/name
            for parent in path.parents:
                if parent==target: break
                private_directory(parent)
            require(private_read(path,len(body.encode()))==body.encode(),'artifact source bytes changed')
        checks=report.get('independent_acceptance',{})
        require(isinstance(checks,dict) and checks.get('profile')==profile,'artifact acceptance contract changed')
        if profile:
            require(checks.get('harness_sha256')==acceptance_checks.harness_sha256(profile),'artifact acceptance harness changed')
            require(checks.get('candidate_source_digest')==digest,'artifact acceptance candidate changed')
            if report['status']=='passed': require(checks.get('status')=='passed','artifact acceptance verdict changed')
        require(report.get('provenance')==provenance,'artifact provenance changed')
        identity=dict(format='uac-artifact-v1',job_id=job['id'],attempt=attempt,project='control',engine=engine,source_digest=digest)
        if row:
            require(json.loads(saved_manifest)==entries and json.loads(saved_report)==report and saved_status==report['status'],'artifact database and files disagree')
            if 'artifact_identity' in report: require(report['artifact_identity']==identity,'artifact identity changed')
        else:
            require(report.get('artifact_identity')==identity,'unregistered artifact identity missing or changed')
            created=report.get('artifact_created_at')
            require(type(created) in (int,float) and math.isfinite(created) and created>0,'artifact creation time missing')
            # A worker may have exited after rename but before the original directory sync.
            # Finish that durability step before committing the recovered SQLite receipt.
            sync_directory(target)
            sync_directory(root)
            cur=conn.execute('INSERT INTO code_artifacts(job_id,attempt,project,engine,source_digest,manifest,test_status,test_report,path,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)',
                (job['id'],attempt,'control',engine,digest,json.dumps(entries),report['status'],json.dumps(report,ensure_ascii=False),str(target),created))
            conn.commit();ident=cur.lastrowid
        return outcome(ident,engine,digest,entries,report,reused=True,origin_attempt=attempt)
    except (OSError,ValueError,KeyError,TypeError) as exc:
        if isinstance(exc,ArtifactRecoveryBlocked): raise
        raise ArtifactRecoveryBlocked('artifact recovery evidence incomplete') from None
