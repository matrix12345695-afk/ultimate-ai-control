"""Archive/empty-target guard for the disposable PG18 recovery harness only."""
import hashlib
import json
import os
from pathlib import Path
import stat

TARGETS={'nova_recovery_target','nova_recovery_negative'}


def publish_archive(path,raw):
    path=Path(path)
    if not 1000<len(raw)<=32*1024**2: raise ValueError('archive_size')
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0),0o600)
    try:
        with os.fdopen(fd,'wb') as stream:
            stream.write(raw);stream.flush();os.fsync(stream.fileno())
        return {'format':'postgres-custom','scope':'application_public_schema','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'postgres_major':18}
    except BaseException:
        path.unlink(missing_ok=True);raise


def verified_bytes(path,manifest):
    path=Path(path);info=path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_mode&0o077: raise ValueError('archive_permissions')
    if set(manifest)!={'format','scope','bytes','sha256','postgres_major'} or manifest['format']!='postgres-custom' or manifest['scope']!='application_public_schema' or manifest['postgres_major']!=18: raise ValueError('manifest_scope')
    if type(manifest['bytes']) is not int or not 1000<manifest['bytes']<=32*1024**2 or info.st_size!=manifest['bytes']: raise ValueError('archive_size')
    with path.open('rb') as stream: raw=stream.read(32*1024**2+1)
    if hashlib.sha256(raw).hexdigest()!=manifest['sha256'] or not raw.startswith(b'PGDMP'): raise ValueError('archive_hash_or_format')
    return raw


def restore(executor,path,manifest,target):
    # Never accepts a URL, source database, production name or an arbitrary identifier.
    if target not in TARGETS: raise ValueError('fixture_target_only')
    raw=verified_bytes(path,manifest)
    info=executor('psql','--no-psqlrc','--tuples-only','--no-align','--dbname='+target,'--command=SELECT current_database(),(SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname !~ \'^pg_\' AND n.nspname<>\'information_schema\');').decode().strip().split('|')
    if info!=[target,'0']: raise ValueError('destination_not_empty')
    # Only a disposable fixture database, never --clean/drop or live DB replacement.
    return executor('pg_restore','--single-transaction','--exit-on-error','--no-owner','--no-privileges','--dbname='+target,input=raw)
