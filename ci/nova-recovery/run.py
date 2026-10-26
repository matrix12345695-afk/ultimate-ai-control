"""Hosted-only PG18 application-schema backup/restore; synthetic data, no live access."""
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import shutil
import subprocess
import tempfile
import urllib.request
import backup_guard

HERE=Path(__file__).resolve().parent
REVISION='a3c3e77e0e74d33241935d25dd3bdfdd306ccd90'
IMAGE='postgres@sha256:9770878138a2e83abcb10856d30cc3f24dae0d317bb956db6ab9159de6c3c80d'
LABELS=['postgres18_client_and_server','exact_application_schema','legacy_json_export_5000_limit_reproduced','restricted_read_only_export_role','export_role_write_denied','private_custom_archive','existing_archive_not_overwritten','snapshot_excludes_later_write','all_four_tables_restored','more_than5000_leads_restored','operational_fields_preserved','sequence_continuity','telegram_dedup_preserved','daily_reminder_dedup_preserved','foreign_key_preserved','source_unchanged_by_export_restore','nonempty_target_refused','foreign_target_refused','corrupt_archive_refused','unsafe_file_permissions_refused','manifest_change_refused','missing_archive_refused','truncated_archive_refused','no_production_access']


def main():
    if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('RUNNER_ENVIRONMENT')!='github-hosted': raise RuntimeError('Disposable hosted runner only')
    container=os.environ.get('PG_FIXTURE_CONTAINER','')
    if not re.fullmatch('[0-9a-f]{64}',container): raise RuntimeError('fixture container missing')
    clean={'PATH':os.environ['PATH'],'LANG':'C.UTF-8'}
    def call(*args,input=None):
        p=subprocess.run(['docker','exec','-i',container,*args],input=input,capture_output=True,timeout=45,env=clean)
        if p.returncode: raise RuntimeError('fixture_command_failed')
        if len(p.stdout)>32*1024**2: raise RuntimeError('fixture_output_limit')
        return p.stdout
    inspect=subprocess.run(['docker','inspect','--format','{{.Config.Image}}',container],capture_output=True,timeout=15,check=True,env=clean).stdout.decode().strip();assert inspect==IMAGE
    version=call('psql','-U','postgres','-d','postgres','-Atqc',"SELECT current_setting('server_version_num')::int/10000").decode().strip();assert version=='18'
    assert call('pg_dump','--version').decode().startswith('pg_dump (PostgreSQL) 18.')
    evidence=Path.cwd()/'recovery-evidence';assert not evidence.exists();evidence.mkdir()
    pins=json.loads((HERE/'source-pins.json').read_text());node=shutil.which('node');npm=shutil.which('npm')
    with tempfile.TemporaryDirectory(prefix='nova-recovery-fixture-') as name:
        temp=Path(name);source=temp/'source';source.mkdir();home=temp/'home';home.mkdir()
        for path,size,blob in pins:
            url='https://raw.githubusercontent.com/matrix12345695-afk/nova-web-agency/'+REVISION+'/'+path
            with urllib.request.urlopen(url,timeout=15) as response:
                assert response.geturl()==url
                raw=response.read(size+1)
            assert len(raw)==size and hashlib.sha1(b'blob '+str(size).encode()+b'\0'+raw).hexdigest()==blob
            target=source/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        env={**clean,'HOME':str(home),'CI':'true','DATABASE_URL':'postgresql://postgres:postgres@127.0.0.1:15432/nova_recovery_source'}
        assert subprocess.run([node,'--version'],env=env,check=True,capture_output=True).stdout.strip()==b'v24.21.0'
        subprocess.run([npm,'ci','--omit=dev','--ignore-scripts','--no-audit','--no-fund'],cwd=source,env=env,check=True,timeout=90,stdout=subprocess.DEVNULL)
        for database in ('nova_recovery_source','nova_recovery_target','nova_recovery_negative'):
            call('createdb','-U','postgres',database)
            if database!='nova_recovery_source':
                # PG18 custom dumps include CREATE SCHEMA public. Remove only the
                # just-created empty fixture namespace, never any application object.
                call('psql','-U','postgres','-d',database,'-v','ON_ERROR_STOP=1','-c','DROP SCHEMA public RESTRICT')
        def fixture(action,database='nova_recovery_source'):
            local=dict(env,DATABASE_URL='postgresql://postgres:postgres@127.0.0.1:15432/'+database)
            proc=subprocess.run([node,str(HERE/'fixture.cjs'),action,database],cwd=source,env=local,capture_output=True,timeout=40)
            if proc.returncode: raise RuntimeError('node_fixture_failed: '+proc.stderr.decode()[-300:])
            return json.loads(proc.stdout.splitlines()[-1])
        seeded=fixture('init');assert seeded['legacy_export_count']==5000 and seeded['source_count']==5003
        tables=call('psql','-U','postgres','-d','nova_recovery_source','-Atqc',"SELECT relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND relkind='r' ORDER BY relname").decode().splitlines()
        assert tables==['nova_daily_reminders','nova_lead_events','nova_leads','nova_telegram_updates']
        sql="CREATE ROLE nova_backup LOGIN PASSWORD 'fixture' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION; ALTER ROLE nova_backup SET default_transaction_read_only=on; GRANT CONNECT ON DATABASE nova_recovery_source TO nova_backup; GRANT USAGE ON SCHEMA public TO nova_backup; GRANT SELECT ON ALL TABLES IN SCHEMA public TO nova_backup; GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO nova_backup;"
        call('psql','-U','postgres','-d','nova_recovery_source','-v','ON_ERROR_STOP=1','-c',sql)
        def reader(*args,input=None): return call('env','PGPASSWORD=fixture','PGUSER=nova_backup',*args,input=input)
        role=reader('psql','-h','127.0.0.1','-d','nova_recovery_source','-Atqc',"SELECT current_setting('default_transaction_read_only'),rolsuper,rolcreatedb,rolcreaterole,rolreplication FROM pg_roles WHERE rolname=current_user").decode().strip();assert role=='on|f|f|f|f'
        try: reader('psql','-h','127.0.0.1','-d','nova_recovery_source','-v','ON_ERROR_STOP=1','-c',"INSERT INTO nova_daily_reminders(day) VALUES('FORBIDDEN')")
        except RuntimeError: pass
        else: raise AssertionError('write allowed')
        hold=subprocess.Popen([node,str(HERE/'fixture.cjs'),'hold','nova_recovery_source'],cwd=source,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(hold.stdout,selectors.EVENT_READ);assert selector.select(15)
            snapshot=json.loads(hold.stdout.readline())['snapshot'];assert re.fullmatch('[0-9A-F]+-[0-9A-F]+-[0-9]+',snapshot)
            after_later=fixture('later');assert after_later['nova_leads']['n']==5004
            raw=reader('pg_dump','-h','127.0.0.1','--dbname=nova_recovery_source','--format=custom','--no-owner','--no-privileges','--schema=public','--strict-names','--lock-wait-timeout=5s','--snapshot='+snapshot)
        finally:
            hold.communicate(b'done\n',timeout=10);assert hold.returncode==0
        archive=temp/'application.dump';manifest=backup_guard.publish_archive(archive,raw)
        assert archive.stat().st_mode&0o777==0o600
        try: backup_guard.publish_archive(archive,raw)
        except FileExistsError: pass
        else: raise AssertionError('archive overwritten')
        def admin(*args,input=None): return call('env','PGUSER=postgres',*args,input=input)
        backup_guard.restore(admin,archive,manifest,'nova_recovery_target')
        restored=fixture('verify','nova_recovery_target');assert restored['tables']==seeded['tables']
        for key in ('sequence_preserved','dedup_preserved','reminder_preserved','foreign_key_preserved','operational_fields_preserved'): assert restored[key] is True
        assert fixture('snapshot')==after_later
        def denied(name,fn):
            try: fn()
            except (ValueError,OSError): return
            raise AssertionError(name+' accepted')
        denied('nonempty',lambda:backup_guard.restore(admin,archive,manifest,'nova_recovery_target'))
        denied('foreign',lambda:backup_guard.restore(admin,archive,manifest,'novaweb_crm_dev'))
        bad=temp/'corrupt.dump';bad.write_bytes(raw[:-1]+bytes([raw[-1]^1]));bad.chmod(0o600)
        denied('corruption',lambda:backup_guard.restore(admin,bad,manifest,'nova_recovery_negative'))
        archive.chmod(0o644);denied('mode',lambda:backup_guard.restore(admin,archive,manifest,'nova_recovery_negative'));archive.chmod(0o600)
        denied('manifest',lambda:backup_guard.restore(admin,archive,dict(manifest,scope='cluster'),'nova_recovery_negative'))
        denied('missing',lambda:backup_guard.restore(admin,temp/'missing',manifest,'nova_recovery_negative'))
        bad.write_bytes(raw[:1000]);denied('truncation',lambda:backup_guard.restore(admin,bad,manifest,'nova_recovery_negative'))
        assert admin('psql','-d','nova_recovery_negative','-Atqc',"SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public'").strip()==b'0'
        report={'schema':'nova-pg18-recovery-v1','candidate_revision':REVISION,'postgres_major':18,'image':IMAGE,'source_manifest_sha256':hashlib.sha256((HERE/'source-pins.json').read_bytes()).hexdigest(),'dependency_lock_sha256':hashlib.sha256((source/'package-lock.json').read_bytes()).hexdigest(),'archive_manifest':manifest,'table_snapshot':seeded['tables'],'source_fixture_rows':5003,'legacy_json_export_count':5000,'checks':{k:True for k in LABELS},'counts':{'tests':24,'pass':24,'fail':0,'errors':0,'skipped':0},'production_access':False,'production_backup_verified':False,'Render_rollback_executed':False,'published':False}
        assert len(LABELS)==24
        (evidence/'report.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
        (evidence/'source-pins.json').write_bytes((HERE/'source-pins.json').read_bytes())
        assert not list(evidence.glob('*.dump'))
    print(json.dumps(report,sort_keys=True),flush=True)


if __name__=='__main__': main()
