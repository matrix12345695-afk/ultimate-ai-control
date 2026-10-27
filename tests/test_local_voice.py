import base64
import copy
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch
import evidence_memory as memory
import local_voice as voice
import main
import queue_worker
import roadmap
import task_queue as q
import voice_assets as assets


def report():
    c=assets.contract()
    return {'schema':voice.PROFILE,'status':'passed','checks':{'asset_pins_verified':True,'opus_decode_verified':True,'english_fixture_transcribed':True},
            'counts':{'tests':3,'pass':3,'fail':0},'fixture_sha256':c['fixture_sha256'],'contract_sha256':assets.contract_sha(),
            'manifest_sha256':'a'*64,'model_sha256':c['downloads'][2]['sha256'],'source_commit':c['whisper_commit'],
            'fixture_language':'en','fixture_seconds':8.0,'decode_seconds':.02,'recognize_seconds':2.0,'transcript_sha256':'b'*64,
            'checked_at':time.time(),'network':False,'paid_calls':0,'owner_voice_enabled':False,'acceptance_only':True,'published':False,
            'address_space_mib':768,'cpu_count':1}


class LocalVoiceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.path=self.root/'db'
        self.conn=sqlite3.connect(self.path);queue_worker.initialize(self.conn)
    def tearDown(self): self.conn.close();self.temp.cleanup()
    def job(self):
        q.enqueue(self.conn,'control','test_release',{'target':voice.PROFILE})
        return q.claim(self.conn,'fixture',q.KINDS)

    def test_public_fixture_is_small_pinned_ogg_opus_and_not_owner_audio(self):
        data=base64.b64decode((voice.ROOT/'fixtures/voice-jfk8.ogg.b64').read_text().strip(),validate=True)
        self.assertLess(len(data),64000);self.assertTrue(data.startswith(b'OggS'));self.assertIn(b'OpusHead',data[:100])
        self.assertEqual(assets.digest(data),assets.contract()['fixture_sha256'])

    def test_report_cannot_claim_owner_enablement_paid_calls_or_publication(self):
        self.assertTrue(voice.valid(report()))
        for field,value in [('owner_voice_enabled',True),('paid_calls',1),('published',True),('network',True),('acceptance_only',False),('cpu_count',2),('address_space_mib',1024)]:
            self.assertFalse(voice.valid(dict(report(),**{field:value})))

    def test_unpinned_models_sources_and_contracts_are_rejected(self):
        for field in ('model_sha256','source_commit','contract_sha256','fixture_sha256'):
            self.assertFalse(voice.valid(dict(report(),**{field:'0'*64})))

    def test_incomplete_forged_and_invalid_time_reports_are_rejected(self):
        for field,value in [('decode_seconds',float('nan')),('recognize_seconds',19),('fixture_seconds',20),('checked_at',float('inf')),('manifest_sha256','bad')]:
            self.assertFalse(voice.valid(dict(report(),**{field:value})))
        bad=report();bad['checks']['opus_decode_verified']=False;self.assertFalse(voice.valid(bad))
        bad=report();bad['counts']['pass']=True;self.assertFalse(voice.valid(bad))
        bad=report();del bad['checks'];self.assertFalse(voice.valid(bad))

    def test_hash_pinned_download_rejects_truncation_or_changed_bytes(self):
        class Reply:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,size):return b'changed'
        with patch.object(assets.urllib.request,'urlopen',return_value=Reply()):
            with self.assertRaisesRegex(ValueError,'voice_download_pin'):
                assets._download({'url':'https://example.invalid','bytes':7,'sha256':'a'*64},self.root/'bad')
        self.assertFalse((self.root/'bad').exists())

    def test_policy_wrong_mode_missing_hash_or_permissions_never_runs_native_code(self):
        path=self.root/'voice-policy.json';path.write_text(json.dumps({'enabled':True,'mode':'live','runtime':'/tmp','contract_sha256':assets.contract_sha()}));path.chmod(0o600)
        with self.assertRaises(Exception): voice.policy(path)
        path.chmod(0o644)
        with self.assertRaises(PermissionError): voice.policy(path)
        link=self.root/'link';link.symlink_to(path)
        with self.assertRaises(PermissionError): voice.policy(link)

    def test_manifest_missing_or_extra_executables_and_model_changes_fail_closed(self):
        root=self.root/'runtime';root.mkdir(mode=0o700)
        (root/'manifest.json').write_text(json.dumps({'schema':'voice-runtime-v1','contract_sha256':assets.contract_sha(),'files':{'extra':{}}}));(root/'manifest.json').chmod(0o600)
        with self.assertRaisesRegex(ValueError,'manifest_scope'): assets.verify(root)

    def test_immutable_saved_report_and_hash_source_are_verified(self):
        job=self.job();r=report();first=voice.save(self.conn,job,r)
        self.assertEqual(voice.save(self.conn,job,report()),first)
        self.conn.execute("UPDATE voice_local_runs SET report='{}'");self.conn.commit()
        with self.assertRaises(ValueError): voice.save(self.conn,job,report())
        self.assertIn('изменился',voice.describe(self.conn))

    def test_report_cannot_be_attached_to_other_project_or_stale_lease(self):
        job=self.job()
        with self.assertRaises(PermissionError): voice.save(self.conn,dict(job,project='nova'),report())
        with self.assertRaises(PermissionError): voice.save(self.conn,dict(job,lease_token='x'*48),report())
        self.conn.execute("UPDATE agent_jobs SET payload='{}' WHERE id=?",(job['id'],));self.conn.commit()
        with self.assertRaises(PermissionError): voice.save(self.conn,job,report())

    def test_verified_worker_result_reaches_memory_and_partial_plan(self):
        ident=q.enqueue(self.conn,'control','test_release',{'target':voice.PROFILE})
        roadmap.mark(self.conn,10,'active','local pilot only; owner ingestion pending')
        with patch.object(voice,'observe',side_effect=lambda path:report()):
            self.assertEqual(queue_worker.run_once(self.path)['state'],'succeeded')
        while memory.sync(self.conn)['scanned']:pass
        mid=self.conn.execute("SELECT id FROM project_evidence_memory WHERE event_id IN(SELECT id FROM agent_job_events WHERE job_id=? AND event='succeeded')",(ident,)).fetchone()[0]
        self.assertIn('local_voice',memory.detail(self.conn,mid))
        text=roadmap.describe(self.conn);self.assertIn('10. Голосовое управление — в работе',text);self.assertIn('✅ Локальный OGG/Opus-пилот',text)
        self.conn.execute("UPDATE voice_local_runs SET report_sha256=?",('0'*64,));self.conn.commit()
        self.assertIn('повторной проверки',memory.detail(self.conn,mid));self.assertNotIn('✅ Локальный OGG/Opus-пилот',roadmap.describe(self.conn))

    def test_owner_commands_show_limits_and_deduplicate_test_requests(self):
        with patch.object(main,'DB',self.path):
            self.assertIn('ещё не принимаются',main.command('🎙 Голос 4.0'))
            main.command('/test_voice4',source_key='fixture-voice-123');main.command('/test_voice4',source_key='fixture-voice-123')
        self.assertEqual(self.conn.execute('SELECT count(*) FROM agent_jobs').fetchone()[0],1)

    def test_sandbox_mounts_no_home_credentials_db_shell_or_network(self):
        args=voice._arguments({'bwrap':'/bwrap','runtime':'/private/speech'},None,Path('/private/public-fixture'))
        self.assertIn('--unshare-all',args);self.assertIn('--clearenv',args);self.assertIn('--remount-ro',args)
        for entry in ('/home/maksim','/workspace','/usr/bin','/bin','/etc/ssl','/home/maksim/.config'):
            self.assertNotIn(entry,args)
        self.assertNotIn('TELEGRAM_BOT_TOKEN',' '.join(args))


@unittest.skipUnless(os.environ.get('UAC_VOICE_TEST_POLICY'),'prepared offline voice runtime required')
class RealVoiceSandboxTests(unittest.TestCase):
    def test_real_ogg_opus_decode_and_native_transcription_without_network(self):
        result=voice.observe(Path(os.environ['UAC_VOICE_TEST_POLICY']))
        self.assertTrue(voice.valid(result));self.assertLess(result['recognize_seconds'],18)

    def test_native_guard_denies_host_files_network_forks_and_writes(self):
        cfg=voice.policy(Path(os.environ['UAC_VOICE_TEST_POLICY']))
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);source=root/'probe.c';binary=root/'whisper-cli';canary=root/'outside'
            canary.write_text('fixture-secret-never-visible')
            source.write_text('#include <unistd.h>\n#include <sys/socket.h>\n#include <sys/resource.h>\n#include <fcntl.h>\n#include <stdio.h>\n#include <stdlib.h>\nint main(){if(socket(AF_INET,SOCK_STREAM,0)!=-1)return 1;if(fork()!=-1)return 2;if(open("'+str(canary)+'",O_RDONLY)!=-1)return 3;if(open("/tmp/write",O_CREAT|O_WRONLY,0600)!=-1)return 4;if(getenv("TELEGRAM_BOT_TOKEN"))return 5;struct rlimit r;getrlimit(RLIMIT_AS,&r);if(r.rlim_cur!=768ULL*1024*1024)return 6;getrlimit(RLIMIT_FSIZE,&r);if(r.rlim_cur!=0||r.rlim_max!=0)return 7;puts("isolated");return 0;}')
            subprocess.run(['gcc',str(source),'-o',str(binary)],check=True,capture_output=True,timeout=15)
            (root/'lib').mkdir()
            for name in assets.FILES:
                if name!='whisper-cli': (root/name).write_bytes(b'fixture-not-loaded')
            output,_=voice._execute(dict(cfg,runtime=str(root)),canary,['/runtime/whisper-cli'],limit=100,seconds=2)
            self.assertEqual(output.strip(),b'isolated')
            import voice_native
            with voice_native._sealed_input(b'public-fixture') as fd:
                output,_=voice._execute(dict(cfg,runtime=str(root)),Path('/unused'),['/runtime/whisper-cli'],limit=100,seconds=2,input_fd=fd)
            self.assertEqual(output.strip(),b'isolated')
