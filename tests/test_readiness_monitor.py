import copy
import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import urllib.error
import health_incidents as health
import main
from owner_notifications import create
import queue_worker
import readiness_monitor as readiness
import scheduler
import task_queue as queue
import telegram_menu


class Response:
    status=200
    def __init__(self,raw,headers=None,url=readiness.URL):
        self.raw=raw;self.headers=headers or {'Content-Type':'application/json'};self.url=url
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def geturl(self): return self.url
    def read(self,limit):
        if limit!=8193: raise AssertionError('unbounded readiness read')
        return self.raw[:limit]


def response_bytes(**changes):
    data={'ok':True,'storage':'postgres','version':readiness.EXPECTED_VERSION}
    data.update(changes);return json.dumps(data).encode()


class ReadinessProbeTests(unittest.TestCase):
    def probe(self,raw=None,**response):
        def opener(request,timeout):
            self.assertEqual(request.full_url,readiness.URL)
            self.assertEqual(request.get_method(),'GET');self.assertEqual(timeout,12)
            self.assertIsNone(request.get_header('Authorization'));self.assertIsNone(request.get_header('Range'))
            return Response(response_bytes() if raw is None else raw,**response)
        return readiness.probe({'target':readiness.TARGET},opener)

    def test_ready_contract_is_bounded_and_records_only_checks_and_hash(self):
        raw=response_bytes(private_connection='do-not-copy-this')
        result=self.probe(raw)
        self.assertTrue(result['healthy']);self.assertTrue(readiness.valid_result(result))
        self.assertEqual(result['body_sha256'],hashlib.sha256(raw).hexdigest())
        self.assertNotIn('do-not-copy-this',json.dumps(result))

    def test_http_200_alone_does_not_prove_application_or_database_ready(self):
        for changes in ({'ok':False},{'ok':'true'},{'ok':1},{'storage':'temporary_file'},
                        {'storage':'postgres_unavailable'},{'version':'unexpected'}):
            with self.subTest(changes=changes):
                result=self.probe(response_bytes(**changes))
                self.assertFalse(result['healthy']);self.assertTrue(readiness.valid_result(result))
                self.assertEqual(result['http_status'],200)

    def test_invalid_ambiguous_deep_or_nonstandard_json_cannot_pass(self):
        for raw in (b'<html>not JSON</html>',b'[]',b'{"ok":false,"ok":true}',b'{"x":NaN}',
                    b'['*2000+b'0'+b']'*2000,b'\xff'):
            result=self.probe(raw);self.assertFalse(result['healthy']);self.assertTrue(readiness.valid_result(result))

    def test_content_type_encoding_and_body_limit_are_enforced(self):
        for kwargs in ({'headers':{'Content-Type':'text/html'}},
                       {'headers':{'Content-Type':'application/json','Content-Encoding':'gzip'}},
                       {'raw':b'x'*8193}):
            result=self.probe(**kwargs)
            self.assertFalse(result['healthy']);self.assertTrue(readiness.valid_result(result))
            self.assertIsNone(result['body_sha256'])

    def test_fixed_endpoint_rejects_redirects_and_arbitrary_paths(self):
        result=self.probe(url='https://other.invalid/private')
        self.assertEqual(result['detail'],'redirect_denied');self.assertFalse(result['healthy'])
        with self.assertRaises(readiness.RedirectDenied):
            readiness.NoRedirect().redirect_request(None,None,302,'',{},readiness.URL+'?new=1')
        for payload in ({'target':'inventory'},{'target':readiness.TARGET,'url':'https://other.invalid/'},{}):
            with self.assertRaises(ValueError): readiness.probe(payload,lambda *a,**k:None)

    def test_http_and_network_errors_are_safe_failure_observations(self):
        for error in (urllib.error.HTTPError(readiness.URL,503,'private server text',{},None),OSError('private connection string')):
            def opener(*args,**kwargs): raise error
            result=readiness.probe({'target':readiness.TARGET},opener)
            self.assertFalse(result['healthy']);self.assertTrue(readiness.valid_result(result))
            self.assertNotIn('private',json.dumps(result))

    def test_forged_healthy_evidence_missing_profile_and_extra_payload_are_rejected(self):
        result=self.probe()
        bad=copy.deepcopy(result);bad['checks']['database_ready']=False
        for changed in (bad,dict(result,contract='unknown'),dict(result,body_sha256=None),
                        dict(result,healthy='true'),dict(result,http_status=201),dict(result,raw_body='not allowed')):
            self.assertFalse(readiness.valid_result(changed))


class ReadinessIncidentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.db=Path(self.temp.name)/'control.db'
        self.conn=queue_worker.connect(self.db);queue_worker.initialize(self.conn)
    def tearDown(self): self.conn.close();self.temp.cleanup()
    def api_result(self,ready=True):
        return readiness.probe({'target':readiness.TARGET},lambda *a,**k:Response(response_bytes(ok=ready)))
    def sample(self,target=readiness.TARGET,good=True):
        ident=queue.enqueue(self.conn,'nova','check_site',{'target':target})
        result=self.api_result(good) if target==readiness.TARGET else {'target':'nova','url':health.TARGETS['nova'],'healthy':good,'detail':'HTTP 200' if good else 'HTTP 503'}
        outcome=queue_worker.run_once(self.db,site_checker=lambda _:result)
        self.assertEqual(outcome,{'id':ident,'state':'succeeded'});return ident

    def test_api_and_page_alarms_recover_independently_without_closing_other_decisions(self):
        api=self.sample(good=False);page=self.sample('nova',False)
        other=create(self.conn,'control','decision','Review publication','Exact release','Review',event_key='decision')
        self.sample('nova',True)
        self.assertEqual(self.conn.execute('SELECT state FROM agent_health_incidents WHERE opened_job_id=?',(api,)).fetchone()[0],'open')
        self.assertEqual(self.conn.execute('SELECT state FROM agent_health_incidents WHERE opened_job_id=?',(page,)).fetchone()[0],'recovered')
        self.sample(good=True)
        self.assertEqual(self.conn.execute('SELECT state FROM agent_health_incidents WHERE opened_job_id=?',(api,)).fetchone()[0],'recovered')
        self.assertEqual(self.conn.execute('SELECT state FROM owner_notifications WHERE id=?',(other,)).fetchone()[0],'pending')
        self.assertEqual(self.conn.execute("SELECT count(*) FROM owner_notifications WHERE title=?",(health.RECOVERIES[readiness.TARGET],)).fetchone()[0],1)

    def test_repeated_bad_api_is_one_incident_and_good_again_does_not_duplicate(self):
        self.sample(good=False);self.sample(good=False)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM agent_health_incidents').fetchone()[0],1)
        self.sample(good=True);before=self.conn.execute('SELECT count(*) FROM owner_notifications').fetchone()[0]
        self.sample(good=True)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM owner_notifications').fetchone()[0],before)

    def test_api_recovery_transaction_rolls_back_on_event_failure(self):
        self.sample(good=False)
        ident=queue.enqueue(self.conn,'nova','check_site',{'target':readiness.TARGET})
        job=queue.claim(self.conn,'test',queue.KINDS)
        with patch.object(queue,'_event',side_effect=RuntimeError('copy-only failure')):
            with self.assertRaises(RuntimeError): health.complete(self.conn,job,self.api_result())
        self.assertEqual(self.conn.execute('SELECT state FROM agent_jobs WHERE id=?',(ident,)).fetchone()[0],'running')
        self.assertEqual(self.conn.execute('SELECT state FROM agent_health_incidents').fetchone()[0],'open')
        health.complete(self.conn,job,self.api_result())
        self.assertEqual(self.conn.execute('SELECT state FROM agent_health_incidents').fetchone()[0],'recovered')

    def test_expired_lease_and_missing_api_evidence_cannot_resolve_an_alarm(self):
        self.sample(good=False)
        ident=queue.enqueue(self.conn,'nova','check_site',{'target':readiness.TARGET})
        job=queue.claim(self.conn,'test',queue.KINDS)
        fake=self.api_result();fake.pop('checks')
        with self.assertRaises(ValueError): health.complete(self.conn,job,fake)
        self.conn.execute('UPDATE agent_jobs SET lease_until=0 WHERE id=?',(ident,));self.conn.commit()
        with self.assertRaises(PermissionError): health.complete(self.conn,job,self.api_result())
        self.assertEqual(self.conn.execute('SELECT state FROM agent_health_incidents').fetchone()[0],'open')

    def test_command_is_deduplicated_and_monitor_shows_only_committed_check_details(self):
        with patch.object(main,'DB',self.db):
            main.command('/readiness4',source_key='telegram-api-check')
            main.command('/readiness4',source_key='telegram-api-check')
            self.assertIn('Использование',main.command('/readiness4 extra'))
        self.assertEqual(self.conn.execute('SELECT count(*) FROM agent_jobs').fetchone()[0],1)
        queue_worker.run_once(self.db,site_checker=lambda _:self.api_result())
        with patch.object(main,'DB',self.db):
            text=main.command('/monitor4')
        self.assertIn('nova-readiness: готов',text);self.assertIn('PostgreSQL ✅',text)
        self.assertEqual(telegram_menu.route('🩺 Проверить API'),'/readiness4')


if __name__=='__main__': unittest.main()
