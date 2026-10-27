import base64
import concurrent.futures
import copy
from email.message import Message
import io
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import Mock,patch
import urllib.error
import urllib.request
import urllib.response
import emergency_control as control
import evidence_memory as memory
import local_voice
import main
import owner_notifications as inbox
import queue_worker
import roadmap
import task_queue as q
import telegram_voice_file as transport
import voice_assets as assets
import voice_flow_test as flow
import voice_intake as voice
import voice_native as native

AUDIO=base64.b64decode((Path(__file__).resolve().parents[1]/'fixtures/voice-jfk8.ogg.b64').read_bytes().strip(),validate=True)

def recognition(data,language,path,text='Проверь мобильную версию сайта NOVA.'):
    return {'text':text,'receipt':{'schema':'voice-recognition-v1','status':'transcribed','audio_sha256':assets.digest(data),
        'audio_bytes':len(data),'language':language,'decoded_seconds':8.0,'decode_seconds':.02,'recognize_seconds':2.0,
        'transcript_sha256':assets.digest(text.encode()),'model_sha256':assets.contract()['downloads'][2]['sha256'],
        'contract_sha256':assets.contract_sha(),'manifest_sha256':'a'*64,'network':False,'paid_calls':0,'published':False}}

def owner_policy(root):
    doc={'enabled':True,'mode':'owner_preview','runtime':'/fixture-unused-native-runtime','contract_sha256':assets.contract_sha(),
         'max_bytes':native.MAX_BYTES,'max_seconds':native.MAX_SECONDS,'languages':list(native.LANGUAGES)}
    path=root/native.POLICY;path.write_text(json.dumps(doc));path.chmod(0o600)

def update(ident=1,**meta):
    value={'file_id':'fixture-file','file_unique_id':'fixture-unique','duration':8,'file_size':len(AUDIO),'mime_type':'audio/ogg'};value.update(meta)
    return {'update_id':ident,'message':{'from':{'id':101},'chat':{'id':101,'type':'private'},'voice':value}}

class VoiceIntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.path=self.root/'control.db'
        self.conn=sqlite3.connect(self.path);queue_worker.initialize(self.conn);owner_policy(self.root)
        roadmap.set_setting(self.conn,'active_project','nova')
        roadmap.set_setting(self.conn,'voice_intake_gate','enabled')
    def tearDown(self):self.conn.close();self.temp.cleanup()
    def capture(self,ident=1,fetch=None):return voice.capture(self.conn,self.root,update(ident),'101',fetch or (lambda _:AUDIO))
    def ready(self,text='Проверь мобильную версию сайта NOVA.'):
        ident=self.capture();job=q.claim(self.conn,'fixture-only',q.KINDS)
        result=voice.process(self.conn,self.root,job,transcriber=lambda *a:recognition(*a,text=text))
        self.assertEqual(result['voice_recognition'],'transcribed');q.finish(self.conn,job['id'],job['lease_token'],result)
        return ident
    def preview(self,ident):
        text=voice.preview(self.conn,self.root,ident,'101');return voice.get(self.conn,ident)['preview_code']

    def test_authentication_precedes_storage_policy_and_network(self):
        fetch=Mock()
        for sender,chat,typ in [(999,101,'private'),(101,999,'private'),(101,101,'group')]:
            doc=update();doc['message']['from']['id']=sender;doc['message']['chat'].update(id=chat,type=typ)
            with self.assertRaises(PermissionError):voice.capture(self.conn,self.root,doc,'101',fetch)
        fetch.assert_not_called();self.assertEqual(self.conn.execute('SELECT count(*) FROM voice_inputs').fetchone()[0],0)

    def test_duration_size_type_and_mime_fail_before_network(self):
        fetch=Mock()
        for patch_meta in ({'duration':True},{'duration':11},{'duration':0},{'file_size':native.MAX_BYTES+1},{'file_size':False},{'mime_type':'audio/mp3'},{'file_id':'../outside'}):
            with self.subTest(meta=patch_meta),self.assertRaises(native.VoiceError):voice.capture(self.conn,self.root,update(**patch_meta),'101',fetch)
        fetch.assert_not_called()

    def test_disabled_or_writable_policy_cannot_capture(self):
        path=self.root/native.POLICY;path.chmod(0o644);fetch=Mock()
        with self.assertRaises(PermissionError):self.capture(fetch=fetch)
        fetch.assert_not_called()

    def test_duplicate_update_never_redownloads_or_retargets(self):
        fetch=Mock(return_value=AUDIO);ident=self.capture(fetch=fetch)
        roadmap.set_setting(self.conn,'active_project','kinder');roadmap.set_setting(self.conn,'voice_language','uz')
        self.assertEqual(self.capture(fetch=fetch),ident);self.assertEqual(fetch.call_count,1)
        row=voice.get(self.conn,ident);self.assertEqual((row['project'],row['language']),('nova','ru'))
        self.assertEqual(self.conn.execute('SELECT count(*) FROM agent_jobs').fetchone()[0],1)

    def test_changed_update_identity_fails_without_second_download(self):
        self.capture();fetch=Mock()
        with self.assertRaises(native.VoiceError):voice.capture(self.conn,self.root,update(duration=7),'101',fetch)
        fetch.assert_not_called()

    def test_five_pending_and_rolling_daily_caps_are_enforced(self):
        for i in range(5):self.capture(i+1)
        with self.assertRaisesRegex(native.VoiceError,'five_pending'):self.capture(6)
        self.conn.execute("UPDATE voice_inputs SET state='rejected'");self.conn.commit();voice.cleanup(self.conn,self.root)
        for i in range(6,31):
            ident=self.capture(i);voice.reject(self.conn,self.root,ident,'101')
        with self.assertRaisesRegex(native.VoiceError,'daily_limit'):self.capture(31)

    def test_capture_is_blocked_by_emergency_before_download(self):
        control.stop(self.conn);fetch=Mock()
        with self.assertRaises(control.Stopped):self.capture(fetch=fetch)
        fetch.assert_not_called()

    def test_separate_gate_blocks_download_and_confirmation_and_survives_restart(self):
        ident=self.ready();code=self.preview(ident);roadmap.set_setting(self.conn,'voice_intake_gate','disabled')
        fetch=Mock()
        with self.assertRaises(native.VoiceError):self.capture(2,fetch=fetch)
        fetch.assert_not_called()
        with self.assertRaises(native.VoiceError):voice.confirm(self.conn,ident,'nova',code,'101')
        queue_worker.initialize(self.conn);self.assertEqual(roadmap.setting(self.conn,'voice_intake_gate'),'disabled')

    def test_gate_disable_during_download_never_queues_audio(self):
        def fetch(_):roadmap.set_setting(self.conn,'voice_intake_gate','disabled');return AUDIO
        ident=self.capture(fetch=fetch);self.assertEqual(voice.get(self.conn,ident)['state'],'failed')
        self.assertFalse((self.root/'voice-audio'/f'{ident}.ogg').exists())
        self.assertEqual(self.conn.execute('SELECT count(*) FROM agent_jobs').fetchone()[0],0)

    def test_stop_during_file_fetch_fails_capture_and_removes_input(self):
        def fetch(_):control.stop(self.conn);return AUDIO
        ident=self.capture(fetch=fetch)
        self.assertEqual(voice.get(self.conn,ident)['state'],'failed')
        self.assertEqual(self.conn.execute('SELECT count(*) FROM agent_jobs').fetchone()[0],0)
        self.assertFalse((self.root/'voice-audio'/f'{ident}.ogg').exists())

    def test_private_storage_and_no_audio_blob_in_main_database(self):
        ident=self.capture();row=voice.get(self.conn,ident);path=self.root/'voice-audio'/f'{ident}.ogg'
        self.assertEqual(path.stat().st_mode&0o777,0o600);self.assertEqual(path.parent.stat().st_mode&0o777,0o700)
        self.assertEqual(row['audio_sha256'],assets.digest(AUDIO));self.assertNotIn(AUDIO,list(row.values()))
        self.assertNotIn('file_id',row);self.assertNotIn('file_unique_id',row)

    def test_unexpected_storage_symlink_is_not_followed(self):
        other=self.root/'other';other.mkdir();(self.root/'voice-audio').symlink_to(other,target_is_directory=True)
        ident=self.capture();self.assertEqual(voice.get(self.conn,ident)['state'],'failed');self.assertEqual(list(other.iterdir()),[])

    def test_capture_job_link_failure_rolls_back_job_and_removes_audio(self):
        with patch.object(voice,'_enqueue_locked',side_effect=sqlite3.OperationalError('fixture write failure')):ident=self.capture()
        self.assertEqual(voice.get(self.conn,ident)['state'],'failed')
        self.assertFalse((self.root/'voice-audio'/f'{ident}.ogg').exists())
        self.assertEqual(self.conn.execute('SELECT count(*) FROM agent_jobs').fetchone()[0],0)

    def test_interrupted_receiving_is_recovered_without_retrying_network(self):
        with self.assertRaises(SystemExit):self.capture(fetch=lambda _:(_ for _ in ()).throw(SystemExit()))
        self.conn.execute('UPDATE voice_inputs SET received_at=?',(time.time()-31,));self.conn.commit();voice.cleanup(self.conn,self.root)
        self.assertEqual(voice.get(self.conn,1)['state'],'failed')
        fetch=Mock();self.capture(fetch=fetch);fetch.assert_not_called()

    def test_changed_raw_audio_is_rejected_without_native_execution(self):
        ident=self.capture();path=self.root/'voice-audio'/f'{ident}.ogg';path.write_bytes(b'changed')
        job=q.claim(self.conn,'fixture',q.KINDS);transcriber=Mock()
        result=voice.process(self.conn,self.root,job,transcriber=transcriber)
        self.assertEqual(result['voice_recognition'],'failed');transcriber.assert_not_called();self.assertFalse(path.exists())

    def test_lost_lease_cannot_publish_a_preview_or_failure_receipt(self):
        ident=self.capture();job=q.claim(self.conn,'fixture',q.KINDS)
        def changed(*args):
            self.conn.execute('UPDATE agent_jobs SET lease_token=? WHERE id=?',('f'*48,job['id']));self.conn.commit()
            return recognition(*args)
        with self.assertRaises(PermissionError):voice.process(self.conn,self.root,job,transcriber=changed)
        row=voice.get(self.conn,ident);self.assertEqual(row['state'],'queued');self.assertIsNone(row['receipt'])

    def test_rejection_during_recognition_never_resurrects_preview(self):
        ident=self.capture();job=q.claim(self.conn,'fixture',q.KINDS)
        def rejected(*args):voice.reject(self.conn,self.root,ident,'101');return recognition(*args)
        voice.process(self.conn,self.root,job,transcriber=rejected)
        row=voice.get(self.conn,ident);self.assertEqual(row['state'],'rejected');self.assertIsNone(row['transcript'])

    def test_receipt_audio_language_or_duration_mismatch_fails_closed(self):
        ident=self.capture();job=q.claim(self.conn,'fixture',q.KINDS)
        def mismatched(*args):
            result=recognition(*args);result['receipt']['decoded_seconds']=2;return result
        result=voice.process(self.conn,self.root,job,transcriber=mismatched)
        self.assertEqual(result['voice_recognition'],'failed');self.assertIsNone(voice.get(self.conn,ident)['transcript'])

    def test_silence_and_excessive_decoded_pcm_never_reach_recognizer(self):
        cfg={'manifest':{'files':{'model.bin':{'sha256':assets.contract()['downloads'][2]['sha256']}}}}
        for pcm in (b'\0'*32000,b'\0'*(native.MAX_SECONDS*32000+2)):
            with patch.object(native,'policy',return_value=cfg),patch.object(native.runner,'_execute',return_value=(pcm,.02)) as execute:
                with self.assertRaises(native.VoiceError):native.transcribe(AUDIO,'ru',self.root/native.POLICY)
                self.assertEqual(execute.call_count,1)

    def test_raw_file_symlink_is_not_read_or_deleted_as_a_regular_file(self):
        ident=self.capture();path=self.root/'voice-audio'/f'{ident}.ogg';path.unlink()
        outside=self.root/'outside';outside.write_text('fixture-secret');path.symlink_to(outside)
        job=q.claim(self.conn,'fixture',q.KINDS);transcriber=Mock()
        result=voice.process(self.conn,self.root,job,transcriber=transcriber)
        self.assertEqual(result['voice_recognition'],'failed');transcriber.assert_not_called()
        self.assertEqual(outside.read_text(),'fixture-secret');self.assertTrue(path.is_symlink())

    def test_recognition_is_not_a_task_and_requires_preview_then_confirmation(self):
        ident=self.ready();row=voice.get(self.conn,ident)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM agent_jobs').fetchone()[0],1)
        self.assertFalse((self.root/'voice-audio'/f'{ident}.ogg').exists())
        with self.assertRaises(native.VoiceError):voice.confirm(self.conn,ident,'nova',row['preview_code'],'101')
        code=self.preview(ident);task=voice.confirm(self.conn,ident,'nova',code,'101')
        self.assertEqual(voice.confirm(self.conn,ident,'nova',code,'101'),task)
        state,payload=self.conn.execute('SELECT state,payload FROM agent_jobs WHERE id=?',(task,)).fetchone()
        self.assertEqual(state,'queued');self.assertEqual(json.loads(payload)['source'],'voice_confirmed')
        self.assertEqual(voice.get(self.conn,ident)['transcript'],None)

    def test_confirmation_is_atomic_on_failure_and_retry_creates_one_task(self):
        ident=self.ready();code=self.preview(ident);original=q._event
        def event(conn,job,at,kind,detail=''):
            if kind=='voice_confirmed':raise sqlite3.OperationalError('fixture commit failure')
            return original(conn,job,at,kind,detail)
        with patch.object(q,'_event',side_effect=event),self.assertRaises(sqlite3.OperationalError):voice.confirm(self.conn,ident,'nova',code,'101')
        self.assertEqual(voice.get(self.conn,ident)['state'],'ready');self.assertEqual(self.conn.execute('SELECT count(*) FROM agent_jobs').fetchone()[0],1)
        voice.confirm(self.conn,ident,'nova',code,'101');self.assertEqual(self.conn.execute('SELECT count(*) FROM agent_jobs').fetchone()[0],2)

    def test_two_connections_confirmation_creates_one_task(self):
        ident=self.ready();code=self.preview(ident)
        def confirm():
            with sqlite3.connect(self.path,timeout=10) as conn:return voice.confirm(conn,ident,'nova',code,'101')
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda _:confirm(),range(2)))
        self.assertEqual(results[0],results[1]);self.assertEqual(self.conn.execute('SELECT count(*) FROM agent_jobs').fetchone()[0],2)

    def test_project_and_owner_are_explicit_and_old_project_code_is_invalidated(self):
        ident=self.ready();old=self.preview(ident)
        with self.assertRaises(PermissionError):voice.preview(self.conn,self.root,ident,'999')
        with self.assertRaises(native.VoiceError):voice.confirm(self.conn,ident,'kinder',old,'101')
        voice.change_project(self.conn,self.root,ident,'kinder','101');new=voice.get(self.conn,ident)['preview_code']
        self.assertNotEqual(new,old)
        with self.assertRaises(native.VoiceError):voice.confirm(self.conn,ident,'kinder',old,'101')
        task=voice.confirm(self.conn,ident,'kinder',new,'101')
        self.assertEqual(self.conn.execute('SELECT project FROM agent_jobs WHERE id=?',(task,)).fetchone()[0],'kinder')
        with self.assertRaises(native.VoiceError):voice.change_project(self.conn,self.root,ident,'inventory','101')

    def test_expiry_clears_preview_and_resolves_only_its_own_notification(self):
        keep=inbox.create(self.conn,'control','decision','Other task','Keep this request','No action',event_key='keep')
        ident=self.ready();row=voice.get(self.conn,ident);self.conn.execute('UPDATE voice_inputs SET expires_at=? WHERE id=?',(time.time()-1,ident));self.conn.commit()
        voice.cleanup(self.conn,self.root);self.assertEqual(voice.get(self.conn,ident)['state'],'expired')
        self.assertEqual(voice.get(self.conn,ident)['transcript'],None)
        self.assertEqual(self.conn.execute('SELECT state FROM owner_notifications WHERE id=?',(row['notice_id'],)).fetchone()[0],'resolved')
        self.assertEqual(self.conn.execute('SELECT state FROM owner_notifications WHERE id=?',(keep,)).fetchone()[0],'pending')

    def test_owner_cancels_queued_recognition_but_cannot_silently_cancel_confirmed_task(self):
        ident=self.capture();voice.reject(self.conn,self.root,ident,'101');row=voice.get(self.conn,ident)
        self.assertEqual(self.conn.execute('SELECT state FROM agent_jobs WHERE id=?',(row['job_id'],)).fetchone()[0],'cancelled')
        self.assertFalse((self.root/'voice-audio'/f'{ident}.ogg').exists())

    def test_rollback_cleanup_requires_disabled_gate_and_preserves_confirmed_text_tasks(self):
        ident=self.ready();task=voice.confirm(self.conn,ident,'nova',self.preview(ident),'101')
        pending=self.capture(2);row=voice.get(self.conn,pending)
        with self.assertRaises(PermissionError):voice.expire_pending_for_rollback(self.conn,self.root)
        roadmap.set_setting(self.conn,'voice_intake_gate','disabled');result=voice.expire_pending_for_rollback(self.conn,self.root)
        self.assertEqual(result,{'expired':1,'cleanup_pending':0})
        self.assertEqual(voice.get(self.conn,ident)['state'],'confirmed');self.assertEqual(voice.get(self.conn,pending)['state'],'expired')
        self.assertEqual(self.conn.execute('SELECT state FROM agent_jobs WHERE id=?',(task,)).fetchone()[0],'queued')
        self.assertEqual(self.conn.execute('SELECT state FROM agent_jobs WHERE id=?',(row['job_id'],)).fetchone()[0],'cancelled')

    def test_emergency_and_reset_never_restore_old_confirmation(self):
        ident=self.ready();code=self.preview(ident);control.stop(self.conn);control.reset(self.conn,1)
        with self.assertRaises(control.Stopped):voice.confirm(self.conn,ident,'nova',code,'101')
        voice.cleanup(self.conn,self.root);self.assertEqual(voice.get(self.conn,ident)['state'],'expired')

    def test_stop_during_recognition_discards_preview_but_keeps_receipt(self):
        ident=self.capture();job=q.claim(self.conn,'fixture',q.KINDS)
        def recognizer(*args):control.stop(self.conn);return recognition(*args)
        result=voice.process(self.conn,self.root,job,transcriber=recognizer)
        self.assertEqual(result['voice_recognition'],'transcribed');row=voice.get(self.conn,ident)
        self.assertEqual(row['state'],'expired');self.assertIsNone(row['transcript']);self.assertIsNotNone(row['receipt_sha256'])

    def test_transcript_tamper_and_secret_output_cannot_create_task(self):
        ident=self.ready();self.conn.execute("UPDATE voice_inputs SET transcript='changed' WHERE id=?",(ident,));self.conn.commit()
        with self.assertRaises(native.VoiceError):self.preview(ident)
        with self.assertRaises(native.VoiceError):native.clean_text('api_key=sk-test-only-not-real-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')

    def test_notification_resolution_is_not_a_voice_confirmation(self):
        ident=self.ready();row=voice.get(self.conn,ident);inbox.resolve(self.conn,row['notice_id'])
        self.assertEqual(voice.get(self.conn,ident)['state'],'ready');self.assertIsNone(voice.get(self.conn,ident)['task_id'])

    def test_slash_text_remains_plain_task_payload(self):
        ident=self.ready('/emergency_stop');code=self.preview(ident);task=voice.confirm(self.conn,ident,'nova',code,'101')
        with patch.object(main,'command',side_effect=AssertionError('dispatcher command invoked')):result=queue_worker.run_once(self.path)
        self.assertEqual(result['id'],task);self.assertEqual(result['state'],'awaiting_owner');self.assertFalse(control.state(self.conn)['latched'])

    def test_worker_failure_is_final_and_removes_raw_audio(self):
        ident=self.capture()
        with patch.object(native,'transcribe',side_effect=native.VoiceError('fixture failed')):result=queue_worker.run_once(self.path)
        self.assertEqual(result['state'],'failed');self.assertEqual(voice.get(self.conn,ident)['state'],'failed')
        self.assertFalse((self.root/'voice-audio'/f'{ident}.ogg').exists())

    def test_main_capture_and_commands_use_authenticated_owner_and_confirm_exact_text(self):
        with patch.object(main,'DB',self.path),patch.object(main,'ADMIN','101'),patch.object(transport,'fetch_bounded',return_value=AUDIO):
            response=main.accept_voice(update());self.assertIn('Голосовое #1',response)
            with patch.object(native,'transcribe',side_effect=recognition):queue_worker.run_once(self.path)
            self.assertIn('Проверь мобильную',main.command('/voice 1'))
            code=voice.get(self.conn,1)['preview_code'];self.assertIn('Подтверждённая текстовая задача',main.command('/voice_confirm 1 nova '+code))
            self.assertIn('confirmed',main.command('🗣 Мои голосовые'))

    def test_recognition_memory_is_private_and_stays_valid_after_confirmation(self):
        ident=self.capture()
        with patch.object(native,'transcribe',side_effect=recognition):queue_worker.run_once(self.path)
        while memory.sync(self.conn)['scanned']:pass
        mid=self.conn.execute("SELECT id FROM project_evidence_memory WHERE event_id IN(SELECT id FROM agent_job_events WHERE job_id=? AND event='succeeded')",(voice.get(self.conn,ident)['job_id'],)).fetchone()[0]
        text=memory.detail(self.conn,mid);self.assertIn('voice_input',text);self.assertNotIn('Проверь мобильную версию',text)
        voice.confirm(self.conn,ident,'nova',self.preview(ident),'101');self.assertIn('voice_input',memory.detail(self.conn,mid))
        self.conn.execute("UPDATE voice_inputs SET receipt='{}'");self.conn.commit();self.assertIn('повторной проверки',memory.detail(self.conn,mid))

    def test_mono_single_stream_and_actual_duration_are_guarded(self):
        self.assertEqual(native.validate_audio(AUDIO),AUDIO)
        stereo=bytearray(AUDIO);stereo[27+stereo[26]+9]=2
        for bad in (bytes(stereo),AUDIO+AUDIO,AUDIO[:-1],b'not audio',AUDIO+b'OggS',b'x'*(native.MAX_BYTES+1)):
            with self.assertRaises(native.VoiceError):native.validate_audio(bad)

    def fixture_flow_report(self):
        def public_fixture(*args):return recognition(*args,text='My fellow Americans ask what your country can do.')
        with patch.object(native,'transcribe',side_effect=public_fixture):return flow.observe(self.root)

    def test_flow_report_cannot_promote_synthetic_cases_to_owner_roundtrip(self):
        report=self.fixture_flow_report();self.assertTrue(flow.valid(report))
        for field,value in [('telegram_roundtrip_verified',True),('owner_confirmation_real',True),('live_inbox_changed',True),('paid_calls',1),('published',True)]:
            self.assertFalse(flow.valid(dict(report,**{field:value})))
        broken=copy.deepcopy(report);broken['checks']['confirmation_once_exact_project']=False;self.assertFalse(flow.valid(broken))

    def test_flow_report_saved_immutably_and_scoped_to_exact_job(self):
        q.enqueue(self.conn,'control','test_release',{'target':flow.PROFILE});job=q.claim(self.conn,'fixture',q.KINDS)
        report=self.fixture_flow_report();result=flow.save(self.conn,job,report)
        self.assertEqual(flow.save(self.conn,job,self.fixture_flow_report()),result)
        with self.assertRaises(PermissionError):flow.save(self.conn,dict(job,project='nova'),report)
        self.conn.execute("UPDATE voice_flow_runs SET report='{}'");self.conn.commit()
        with self.assertRaises(ValueError):flow.save(self.conn,job,report)

    def test_flow_memory_and_plan_revalidate_receipt_without_completing_stage(self):
        roadmap.mark(self.conn,10,'active','fixture-only acceptance')
        q.enqueue(self.conn,'control','test_release',{'target':flow.PROFILE})
        template=self.fixture_flow_report()
        with patch.object(flow,'observe',side_effect=lambda root:dict(template,checked_at=time.time())):result=queue_worker.run_once(self.path)
        self.assertEqual(result['state'],'succeeded')
        while memory.sync(self.conn)['scanned']:pass
        mid=self.conn.execute("SELECT id FROM project_evidence_memory WHERE event_id IN(SELECT id FROM agent_job_events WHERE job_id=? AND event='succeeded')",(result['id'],)).fetchone()[0]
        self.assertIn('voice_flow',memory.detail(self.conn,mid));self.assertIn('10. Голосовое управление — в работе',roadmap.describe(self.conn))
        self.conn.execute("UPDATE voice_flow_runs SET report_sha256=?",('0'*64,));self.conn.commit()
        self.assertIn('повторной проверки',memory.detail(self.conn,mid));self.assertNotIn('✅ Приём/подтверждение',roadmap.describe(self.conn))


class Response:
    def __init__(self,data):self.data=io.BytesIO(data)
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read1(self,size):return self.data.read(size)

class TelegramVoiceTransportTests(unittest.TestCase):
    TOKEN='123456:fixture_only_not_a_real_telegram_key_12345'
    def opener(self,path='voice/file_1.oga',size=None,data=AUDIO):
        replies=[Response(json.dumps({'ok':True,'result':{'file_path':path,'file_size':len(data) if size is None else size}}).encode()),Response(data)]
        calls=[]
        def opened(request,**kwargs):calls.append(request.full_url);return replies.pop(0)
        return opened,calls

    def test_only_telegram_api_and_private_file_endpoint_are_used(self):
        opened,calls=self.opener();self.assertEqual(transport.fetch(self.TOKEN,'fixture',opener=opened),AUDIO)
        self.assertEqual(len(calls),2);self.assertTrue(all(u.startswith('https://api.telegram.org/') for u in calls))

    def test_path_url_query_traversal_and_size_rejected_before_file_fetch(self):
        for path in ('../private','https://outside.invalid/','voice/a.oga?x=1','voice/../../env.oga','/voice/a.oga'):
            opened,calls=self.opener(path=path)
            with self.assertRaises(native.VoiceError):transport.fetch(self.TOKEN,'fixture',opener=opened)
            self.assertEqual(len(calls),1)
        opened,calls=self.opener(size=native.MAX_BYTES+1)
        with self.assertRaises(native.VoiceError):transport.fetch(self.TOKEN,'fixture',opener=opened)
        self.assertEqual(len(calls),1)

    def test_download_bytes_truncation_and_slow_stream_are_bounded(self):
        opened,_=self.opener(size=len(AUDIO)+1)
        with self.assertRaisesRegex(native.VoiceError,'truncated'):transport.fetch(self.TOKEN,'fixture',opener=opened)
        opened,_=self.opener(size=1,data=b'x'*(native.MAX_BYTES+1))
        with self.assertRaisesRegex(native.VoiceError,'size'):transport.fetch(self.TOKEN,'fixture',opener=opened)
        class Slow:
            def read1(self,size):return b'x'
        with patch.object(transport.time,'monotonic',side_effect=[0,1,2,3,4,5,6,7]),self.assertRaisesRegex(native.VoiceError,'timeout'):transport._read(Slow(),100,6)

    def test_redirect_is_not_followed_with_bot_credential(self):
        seen=[]
        def redirected(handler,request):
            seen.append(request.full_url);headers=Message();headers['Location']='https://outside.invalid/steal'
            reply=urllib.response.addinfourl(io.BytesIO(b''),headers,request.full_url,302);reply.msg='Found';return reply
        with patch.object(urllib.request.HTTPSHandler,'https_open',redirected):
            with self.assertRaises(native.VoiceError) as error:transport.fetch(self.TOKEN,'fixture')
        self.assertEqual(len(seen),1);self.assertNotIn(self.TOKEN,str(error.exception))

    def test_network_exception_never_exposes_key_or_url(self):
        opened=Mock(side_effect=OSError('https://api.telegram.org/bot'+self.TOKEN))
        with self.assertRaises(native.VoiceError) as error:transport.fetch(self.TOKEN,'fixture',opener=opened)
        self.assertEqual(str(error.exception),'voice_download_unavailable')

    def test_transport_child_uses_stdin_only_and_strips_other_service_keys(self):
        child=Mock();child.returncode=0;child.poll.return_value=0
        child.communicate.return_value=(json.dumps({'ok':True,'data':base64.b64encode(AUDIO).decode()}).encode(),None)
        with patch.dict(os.environ,{'TELEGRAM_BOT_TOKEN':'fixture-do-not-inherit','OPENAI_API_KEY':'fixture-do-not-inherit'}),patch.object(transport.subprocess,'Popen',return_value=child) as popen:
            self.assertEqual(transport.fetch_bounded(self.TOKEN,'fixture'),AUDIO)
        args,kwargs=popen.call_args
        self.assertNotIn(self.TOKEN,str(args));self.assertNotIn('TELEGRAM_BOT_TOKEN',kwargs['env']);self.assertNotIn('OPENAI_API_KEY',kwargs['env'])
        envelope=json.loads(child.communicate.call_args.args[0]);self.assertEqual(envelope['token'],self.TOKEN)

    def test_hard_download_timeout_kills_only_transport_process_group(self):
        child=Mock();child.pid=123456789;child.poll.return_value=None
        child.communicate.side_effect=transport.subprocess.TimeoutExpired(['fixture-transport'],8)
        with patch.object(transport.subprocess,'Popen',return_value=child),patch.object(transport.os,'killpg') as kill:
            with self.assertRaisesRegex(native.VoiceError,'timeout'):transport.fetch_bounded(self.TOKEN,'fixture')
        kill.assert_called_once_with(child.pid,transport.signal.SIGKILL)

    def test_real_transport_child_has_parent_death_signal_and_memory_cap(self):
        import subprocess,sys
        code='import ctypes,resource;v=ctypes.c_int();assert ctypes.CDLL(None).prctl(2,ctypes.byref(v),0,0,0)==0;print(v.value,resource.getrlimit(resource.RLIMIT_AS)[0])'
        result=subprocess.run([sys.executable,'-c',code],preexec_fn=transport._limits,capture_output=True,text=True,timeout=3)
        self.assertEqual(result.returncode,0);self.assertEqual(result.stdout.strip(),'9 268435456')


@unittest.skipUnless(os.environ.get('UAC_VOICE_OWNER_TEST_POLICY'),'prepared owner voice policy required')
class RealVoiceFlowTests(unittest.TestCase):
    def test_real_native_and_synthetic_state_cases_do_not_claim_owner_roundtrip(self):
        result=flow.observe(Path(os.environ['UAC_VOICE_OWNER_TEST_POLICY']).parent)
        self.assertTrue(flow.valid(result));self.assertFalse(result['telegram_roundtrip_verified'])
        self.assertFalse(flow.valid(dict(result,telegram_roundtrip_verified=True)))
