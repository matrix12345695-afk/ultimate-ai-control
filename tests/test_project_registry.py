import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import urllib.error

import main
import project_registry as registry
import queue_worker
import roadmap
import task_queue as queue
import telegram_menu


class Response:
    def __init__(self,url,raw,**kwargs):
        self.url=url;self.raw=raw;self.status=kwargs.get('status',200)
        self.headers=kwargs.get('headers',{})
    def geturl(self): return self.url
    def read(self,limit): return self.raw[:limit]
    def __enter__(self): return self
    def __exit__(self,*args): pass


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.db=Path(self.temp.name)/'control.db'
        self.conn=queue_worker.connect(self.db);queue_worker.initialize(self.conn)
        self.scope=copy.deepcopy(registry.REPOSITORIES['nova'])
        self.files={'package.json':b'{"name":"nova-web-agency","scripts":{"test":"do not execute this"},"dependencies":{"pg":"1"}}',
                    'server.js':b'throw new Error("must never execute");'}
        self.scope['files']=tuple((path,len(raw),registry.blob_id(raw)) for path,raw in self.files.items())
        self.policy=patch.dict(registry.REPOSITORIES,{'nova':self.scope})
        self.policy.start();self.requests=[];self.metadata_change={};self.response_change=None
    def tearDown(self):
        self.policy.stop();self.conn.close();self.temp.cleanup()
    def payload(self): return {'target':'nova','source':registry.METHOD}
    def opener(self,request,timeout):
        self.requests.append(request)
        self.assertGreater(timeout,0);self.assertLessEqual(timeout,5)
        url=request.full_url
        self.assertEqual(request.get_method(),'GET')
        self.assertIsNone(request.get_header('Authorization'))
        if url.startswith('https://api.github.com/'):
            meta={'id':self.scope['repository_id'],'full_name':registry.OWNER+'/'+self.scope['repository'],
                  'owner':{'login':registry.OWNER,'id':registry.OWNER_ID},'private':False,'fork':False}
            meta.update(self.metadata_change);raw=json.dumps(meta).encode()
        else:
            prefix='https://raw.githubusercontent.com/'+registry.OWNER+'/'+self.scope['repository']+'/'+self.scope['revision']+'/'
            self.assertTrue(url.startswith(prefix));raw=self.files[url[len(prefix):]]
        response=Response(url,raw)
        return self.response_change(response) if self.response_change else response
    def inspect(self): return registry.inspect_remote('nova',self.payload(),opener=self.opener)

    def test_exact_pinned_reads_never_execute_or_inherit_tokens_and_report_only_fingerprints(self):
        with patch.dict(os.environ,{'GITHUB_TOKEN':'test-only-token','GITHUB_READ_TOKEN':'test-only-read-token'}):
            result=self.inspect()
        self.assertEqual(len(self.requests),3)
        self.assertTrue(registry.valid_result('nova',result))
        self.assertEqual(result['facts']['dependency_names'],['pg'])
        for name in ('tests_executed','code_executed','published','complete_project_audit'):
            self.assertIs(result[name],False)
        encoded=json.dumps(result)
        self.assertNotIn('must never execute',encoded)
        self.assertNotIn('do not execute this',encoded)
        self.assertNotIn('test-only',encoded)

    def test_scope_rejects_foreign_projects_paths_refs_and_protected_inventory_before_network(self):
        cases=[('inventory',{}),('inventory-mini-app',{}),('qualisift',{}),('nova',{'target':'kinder','source':registry.METHOD}),
               ('nova',dict(self.payload(),path='.env')),('nova',dict(self.payload(),revision='main')),
               ('nova',dict(self.payload(),url='http://169.254.169.254/')),('nova',[])]
        for project,payload in cases:
            with self.subTest(project=project,payload=payload),self.assertRaises(registry.RepositoryScopeError):
                registry.inspect_remote(project,payload,opener=self.opener)
        self.assertEqual(self.requests,[])

    def test_changed_repository_identity_visibility_and_fork_stop_before_source_read(self):
        for change in ({'id':1},{'id':True},{'private':True},{'fork':True},{'full_name':'attacker/renamed'},
                       {'owner':{'login':registry.OWNER,'id':999}}):
            self.metadata_change=change;self.requests=[]
            with self.assertRaises(registry.RepositoryScopeError): self.inspect()
            self.assertEqual(len(self.requests),1)

    def test_changed_or_oversized_source_is_permanent_policy_failure(self):
        for raw in (b'x'*len(self.files['package.json']),b'x'*(len(self.files['package.json'])+1)):
            self.files['package.json']=raw;self.requests=[]
            with self.assertRaises(registry.RepositoryScopeError): self.inspect()
            self.assertEqual(len(self.requests),2)

    def test_redirect_encoding_metadata_size_and_total_deadline_are_bounded(self):
        for modify in (lambda r:Response('https://other.invalid/',r.raw),
                       lambda r:Response(r.url,r.raw,headers={'Content-Encoding':'gzip'}),
                       lambda r:Response(r.url,b'x'*65537)):
            self.response_change=modify
            with self.assertRaises(registry.RepositoryScopeError): self.inspect()
        with self.assertRaises(registry.RepositoryScopeError):
            registry.NoRedirect().redirect_request(None,None,302,'',{},'https://api.github.com/elsewhere')
        self.response_change=None
        with patch.object(registry.time,'monotonic',side_effect=(0,0,19)):
            with self.assertRaises(registry.RepositoryReadUnavailable): self.inspect()

    def test_http_errors_have_no_private_payload_and_are_retryable(self):
        def failing(request,timeout):
            raise urllib.error.HTTPError(request.full_url,429,'private response',{},None)
        with self.assertRaisesRegex(registry.RepositoryReadUnavailable,'^github_http_429$'):
            registry.inspect_remote('nova',self.payload(),opener=failing)

    def test_kinder_documentation_does_not_claim_android_or_backend_execution(self):
        self.scope=copy.deepcopy(registry.REPOSITORIES['kinder'])
        self.files={'README.md':b'# Kinder Spa scaffold','SECURITY.md':b'No customer data in source'}
        self.scope['files']=tuple((p,len(raw),registry.blob_id(raw)) for p,raw in self.files.items())
        with patch.dict(registry.REPOSITORIES,{'kinder':self.scope}):
            result=registry.inspect_remote('kinder',{'target':'kinder','source':registry.METHOD},opener=self.opener)
            self.assertTrue(registry.valid_result('kinder',result))
        self.assertEqual(result['facts'],{'stack':'documentation_scaffold','android_build_verified':False,'backend_verified':False})
        self.assertEqual(len(self.requests),3)

    def test_lease_checked_result_is_saved_with_work_span_and_project_projection(self):
        ident=queue.enqueue(self.conn,'nova','inspect_repository',self.payload())
        result=queue_worker.run_once(self.db,repository_inspector=lambda project,payload:self.inspect())
        self.assertEqual(result,{'id':ident,'state':'succeeded'})
        saved=json.loads(self.conn.execute('SELECT result FROM agent_jobs WHERE id=?',(ident,)).fetchone()[0])
        self.assertTrue(registry.valid_result('nova',saved))
        self.assertEqual(self.conn.execute('SELECT count(*) FROM agent_work_spans WHERE job_id=?',(ident,)).fetchone()[0],1)
        self.assertIn('Файлы и хеши проверены: 2',registry.describe(self.conn))
        self.assertEqual(registry.verified(self.conn)['nova']['job_id'],ident)
        roadmap.mark(self.conn,7,'active','read-only inspected source; execution remains disabled')
        self.assertIn('7. Несколько проектов — в работе',roadmap.describe(self.conn))
        self.assertIn('Репозиториев с проверенными файлами и хешами: 1',roadmap.describe(self.conn))

    def test_worker_scope_violation_is_not_retried_or_reported_as_success(self):
        ident=queue.enqueue(self.conn,'nova','inspect_repository',dict(self.payload(),path='.env'))
        with patch.object(registry,'inspect_remote') as inspect:
            outcome=queue_worker.run_once(self.db,repository_inspector=inspect)
            inspect.assert_not_called()
        self.assertEqual(outcome['state'],'failed')
        self.assertEqual(self.conn.execute('SELECT state,attempts FROM agent_jobs WHERE id=?',(ident,)).fetchone(),('failed',1))
        self.assertFalse(registry.verified(self.conn))
        self.assertEqual(self.conn.execute("SELECT kind FROM owner_notifications WHERE event_key=?",('repository-scope-'+str(ident),)).fetchone(),('critical',))

    def test_invalid_report_and_expired_lease_never_appear_verified(self):
        report=self.inspect()
        for changed in (dict(report,published=True),dict(report,repository_id=1),dict(report,source_digest='0'*64),dict(report,files=[])):
            self.assertFalse(registry.valid_result('nova',changed))
        ident=queue.enqueue(self.conn,'nova','inspect_repository',self.payload())
        def expired(project,payload):
            with queue_worker.connect(self.db) as c:
                c.execute('UPDATE agent_jobs SET lease_until=0 WHERE id=?',(ident,));c.commit()
            return report
        with self.assertRaises(PermissionError): queue_worker.run_once(self.db,repository_inspector=expired)
        self.assertIsNone(self.conn.execute('SELECT result FROM agent_jobs WHERE id=?',(ident,)).fetchone()[0])
        self.assertFalse(registry.verified(self.conn))

    def test_commands_are_scoped_idempotent_and_project_menu_is_read_only(self):
        with patch.object(main,'DB',self.db):
            self.assertIn('доступ ULTIMATE',main.command('/projects4'))
            for text in ('/repo_check inventory','/repo_check qualisift','/repo_check nova extra'):
                self.assertTrue(any(word in main.command(text) for word in ('Отклонено','Использование')))
            self.assertIn('поставлена в очередь',main.command('/repo_check nova',source_key='telegram-update-test'))
            main.command('/repo_check nova',source_key='telegram-update-test')
        self.assertEqual(self.conn.execute('SELECT count(*) FROM agent_jobs').fetchone()[0],1)
        self.assertEqual(telegram_menu.route('🗂 Проекты'),'/projects4')
        self.assertLessEqual(len(registry.describe(self.conn)),3900)

    def test_history_rejects_unverified_success_records_and_survives_reopen(self):
        ident=queue.enqueue(self.conn,'nova','inspect_repository',self.payload())
        job=queue.claim(self.conn,'test',queue.KINDS)
        queue.finish(self.conn,ident,job['lease_token'],{'method':registry.METHOD,'published':True})
        self.assertFalse(registry.verified(self.conn))
        queue.enqueue(self.conn,'nova','inspect_repository',self.payload())
        queue_worker.run_once(self.db,repository_inspector=lambda p,v:self.inspect())
        with queue_worker.connect(self.db) as reopened:
            self.assertIn('nova',registry.verified(reopened))


if __name__=='__main__': unittest.main()
