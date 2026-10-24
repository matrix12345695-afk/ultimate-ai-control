import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import evidence_memory as memory
import isolated_node as node
import main
import nova_project_tests as nova
import queue_worker
import task_queue as q


class NovaProjectTests(unittest.TestCase):
    def setUp(self):
        self.conn=sqlite3.connect(':memory:');queue_worker.initialize(self.conn)
        self.job={'id':q.enqueue(self.conn,'nova','test_release',{'target':nova.PROFILE},now=100),
                  'attempt':1,'kind':'test_release','project':'nova','payload':{'target':nova.PROFILE}}

    def tearDown(self): self.conn.close()

    def report(self,files):
        return {'source_digest':node.source_manifest(files)[1],'status':'passed','exit_code':0,
                'output':'\n'.join('# '+k+' '+str(v) for k,v in {'tests':24,'pass':24,'fail':0,'skipped':0,'cancelled':0,'todo':0}.items()),
                'backend':node.BACKEND,'driver_sha256':nova.DRIVER_SHA256,'network':False,
                'process_forks':False,'new_threads_after_guard':False,'writable_filesystem':False}

    def test_only_exact_nova_scope_can_execute(self):
        nova.check_scope(self.job)
        for field,value in [('project','inventory'),('project','kinder'),('kind','review_change'),
                            ('payload',{'target':nova.PROFILE,'url':'https://example.test'}),('attempt',True)]:
            with self.assertRaises(PermissionError): nova.check_scope(dict(self.job,**{field:value}))

    def test_tap_counts_cannot_hide_skips_failures_or_missing_summary(self):
        report=self.report({'x.js':'0'})
        self.assertEqual(nova.verdict(report)['status'],'passed')
        for output in (report['output'].replace('# skipped 0','# skipped 1'),'',report['output']+'\n# tests 24',
                       report['output'].replace('# pass 24','# pass 23')):
            self.assertEqual(nova.verdict(dict(report,output=output))['status'],'failed')

    def test_source_scope_requires_every_exact_blob(self):
        with self.assertRaises(ValueError): nova.check_sources({})
        with self.assertRaises(ValueError): nova.check_sources({p:'0' for p,_,_ in nova.PINS})
        for files in ({'../x.js':'0'},{'x.node':'0'},{'/x.js':'0'},{'x.js':'x'*256001}):
            with self.assertRaises(ValueError): node.source_manifest(files)

    def test_recovery_reuses_same_report_after_completion_crash_and_rejects_tampering(self):
        files={'x.js':'0'};report=self.report(files)
        with patch.object(nova,'load_sources',return_value=files),patch.object(nova,'check_sources',return_value=node.source_manifest(files)):
            first=nova.execute(self.conn,self.job,'unused',runner=lambda *args:report)
            again=nova.execute(self.conn,dict(self.job,attempt=2),'unused',runner=lambda *args:self.fail('reran tests'))
            self.assertEqual(first['project_test_id'],again['project_test_id']);self.assertTrue(again['tests_reused'])
            self.conn.execute("UPDATE project_test_runs SET report='{}'");self.conn.commit()
            with self.assertRaises(ValueError): nova.execute(self.conn,dict(self.job,attempt=2),'unused')
            self.assertIn('нужна повторная проверка',nova.describe(self.conn))

    def test_failed_evidence_is_saved_as_failed_and_not_published(self):
        files={'x.js':'0'};report=dict(self.report(files),status='failed',exit_code=1)
        with patch.object(nova,'load_sources',return_value=files),patch.object(nova,'check_sources',return_value=node.source_manifest(files)):
            result=nova.execute(self.conn,self.job,'unused',runner=lambda *args:report)
        self.assertEqual(result['test_status'],'failed');self.assertFalse(result['published'])

    def test_project_test_is_linked_into_memory_and_report_changes_invalidate_it(self):
        files={'x.js':'0'};report=self.report(files)
        job=q.claim(self.conn,'unit-test',q.KINDS,now=101)
        with patch.object(nova,'load_sources',return_value=files),patch.object(nova,'check_sources',return_value=node.source_manifest(files)):
            result=nova.execute(self.conn,self.job,'unused',runner=lambda *args:report)
        q.finish(self.conn,job['id'],job['lease_token'],result,now=102)
        memory.sync(self.conn)
        self.assertIn('набор тестов Node',memory.summary(self.conn,'nova'))
        ident=self.conn.execute('SELECT id FROM project_evidence_memory').fetchone()[0]
        self.assertIn(nova.PROFILE,memory.detail(self.conn,ident))
        self.conn.execute("UPDATE project_test_runs SET report_sha256='changed'");self.conn.commit()
        self.assertIn('повторной проверки',memory.detail(self.conn,ident))

    def test_runtime_commands_queue_fixed_scope_without_model_or_permission_changes(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(main,'DB',Path(folder)/'control.db'):
            self.assertIn('не подтверждён',main.command('/nova_tests'))
            self.assertIn('в очереди',main.command('/test_nova',source_key='unit-nova-test'))
            self.assertIn('в очереди',main.command('🧪 NOVA WEB',source_key='unit-nova-test'))
            with main.db() as conn:
                row=conn.execute('SELECT project,kind,payload FROM agent_jobs').fetchone()
                self.assertEqual(row[:2],('nova','test_release'));self.assertEqual(json.loads(row[2]),{'target':nova.PROFILE})
                self.assertEqual(conn.execute('SELECT count(*) FROM agent_jobs').fetchone()[0],1)

    def test_worker_preserves_soft_cap_and_python_limits_while_allowing_reviewed_node_child(self):
        import resource
        with patch.object(resource,'setrlimit') as cap,patch.object(os,'nice'):
            queue_worker.apply_limits()
        self.assertEqual(cap.call_args_list[0].args,(resource.RLIMIT_AS,(384*1024*1024,768*1024*1024)))


@unittest.skipUnless(os.getenv('UAC_NODE_TEST_POLICY') and os.getenv('UAC_NODE_TEST_DATA'),'real Node sandbox needs reviewed policy and pinned public sources')
class RealNodeSandboxTests(unittest.TestCase):
    def setUp(self):
        self.policy=Path(os.environ['UAC_NODE_TEST_POLICY'])
        self.data=Path(os.environ['UAC_NODE_TEST_DATA'])

    def test_real_pinned_nova_subset_and_mutated_readiness(self):
        files=nova.load_sources(self.data)
        report=nova.verdict(node.run(files,self.policy,nova.DRIVER))
        self.assertTrue(nova.valid_report(report,nova.check_sources(files)[1]))
        self.assertEqual(report['status'],'passed');self.assertEqual(report['test_counts']['pass'],24)
        files=dict(files);files['health.js']="module.exports={checkReadiness:async()=>({ok:true,storage:'postgres'})};"
        with self.assertRaises(ValueError): nova.check_sources(files)
        bad=node.run(files,self.policy,nova.DRIVER)
        self.assertEqual(bad['status'],'failed');self.assertGreater(nova.counts(bad['output'])['fail'],0)

    def test_real_boundary_blocks_host_files_writes_network_processes_and_new_threads(self):
        driver='''const fs=require('node:fs'),cp=require('node:child_process'),net=require('node:net'),assert=require('node:assert/strict');
assert.equal(process.env.OPENAI_API_KEY,undefined);assert.equal(process.env.BOT_TOKEN,undefined);
assert.throws(()=>fs.readFileSync('/etc/passwd'));assert.throws(()=>fs.writeFileSync('/tmp/forbidden','x'));
assert.throws(()=>new (require('node:worker_threads').Worker)('0',{eval:true}));
assert.equal(cp.spawnSync('/runtime/node',['-e','0']).error.code,'EPERM');
const server=net.createServer();server.on('error',e=>{assert.equal(e.code,'EPERM');console.log('node-boundary-pass')});server.listen(0,'127.0.0.1');'''
        report=node.run({'fixture.js':'0'},self.policy,driver)
        self.assertEqual(report['status'],'passed');self.assertIn('node-boundary-pass',report['output'])

    def test_real_timeout_and_output_limit(self):
        self.assertEqual(node.run({'fixture.js':'0'},self.policy,'while(true){}',timeout=1)['status'],'timeout')
        self.assertEqual(node.run({'fixture.js':'0'},self.policy,"const fs=require('node:fs');while(true)fs.writeSync(1,'x'.repeat(16384));")['status'],'output_limit')
