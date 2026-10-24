import copy
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import patch
import approval
import artifact_prs as ledger
import artifact_pr_broker as broker
import evidence_memory as memory
import offline_developer
import queue_worker
import task_queue as q
from isolated_python import manifest


class FakeGitHub:
    def __init__(self):
        self.calls=[];self.branch=None;self.pr=None;self.files={};self.fail_pr_once=False
        self.base='a'*40;self.head='c'*40;self.ci='success';self.read_only=False

    def call(self,method,path,payload=None,missing=False):
        if self.read_only and method!='GET': raise AssertionError('refresh attempted a write')
        self.calls.append((method,path,copy.deepcopy(payload)))
        if path=='': return {'id':1429215344,'full_name':ledger.REPO,'owner':{'id':250530390},'private':False,'fork':False,'default_branch':'main'}
        if path=='/git/ref/heads/main': return {'object':{'sha':self.base}}
        if path.startswith('/git/trees/'):
            return {'sha':'d'*40,'truncated':False,'tree':[]}
        if path=='/git/trees':
            self.files={f['path']:f['content'] for f in payload['tree']};return {'sha':'b'*40}
        if path=='/git/commits': return {'sha':self.head}
        if path.startswith('/git/commits/'): return {'tree':{'sha':'b'*40},'parents':[{'sha':'a'*40}]}
        if path.startswith('/git/ref/heads/'):
            return {'object':{'sha':self.branch}} if self.branch else None
        if path=='/git/refs':
            self.branch=payload['sha'];self.ref=payload['ref'].removeprefix('refs/heads/');return {}
        if path.startswith('/pulls?'): return [self.pr] if self.pr else []
        if path=='/pulls':
            self.pr={'number':901,'html_url':'https://github.com/'+ledger.REPO+'/pull/901'}
            if self.fail_pr_once:
                self.fail_pr_once=False;raise broker.Pending('artificial_timeout_after_pr_created')
            return self.pr
        if path.startswith('/pulls/'):
            return dict(self.pr,state='open',draft=True,merged=False,
                head={'ref':self.ref,'sha':self.branch,'repo':{'full_name':ledger.REPO}},
                base={'ref':'main','sha':self.base,'repo':{'full_name':ledger.REPO}})
        if path.startswith('/compare/'):
            return {'total_commits':1,'ahead_by':1,'behind_by':0,'files':[
                {'filename':p,'status':'added','sha':hashlib.sha1(b'blob '+str(len(s.encode())).encode()+b'\0'+s.encode()).hexdigest()}
                for p,s in self.files.items()]}
        if path.startswith('/actions/runs?'):
            return {'workflow_runs':[{'id':999,'run_attempt':1,'head_sha':self.head,'name':'Safe unit tests',
                'event':'pull_request','path':'.github/workflows/tests.yml','repository':{'id':1429215344},
                'head_repository':{'id':1429215344},'status':'completed' if self.ci!='pending' else 'in_progress',
                'conclusion':self.ci if self.ci!='pending' else None}]}
        raise AssertionError((method,path))


class ArtifactPRTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.data=Path(self.temp.name)
        self.conn=sqlite3.connect(':memory:');queue_worker.initialize(self.conn)
        origin=q.enqueue(self.conn,'control','review_change',{'recipe':'safe-paths'})
        job=q.claim(self.conn,'unit',q.KINDS)
        def runner(files,*args,**kwargs):
            return {'status':'passed','source_digest':manifest(files)[1],'elapsed_seconds':.01,'backend':'bubblewrap-v1','writable_tmp':False,'output':'fixture tests'}
        result=offline_developer.prepare(self.conn,job,self.data/'artifacts',self.data/'policy',runner=runner)
        q.finish(self.conn,origin,job['lease_token'],result,awaiting_owner=True)
        self.artifact=result['artifact_id']
        ident=q.enqueue(self.conn,'control','review_change',{'artifact_pr':self.artifact})
        self.job=q.claim(self.conn,'unit',q.KINDS)
        self.assertEqual(ident,self.job['id']);self.github=FakeGitHub()
        for name,value in [('artifact-pr-policy.json',ledger.canonical({'enabled':True,'mode':'draft_only','repository':ledger.REPO,'recipes':['safe-paths','sha-check']})),
                           ('review-executor-activation-approved','approved')]:
            p=self.data/name;p.write_text(value);p.chmod(0o600)

    def tearDown(self): self.conn.close();self.temp.cleanup()

    def run_broker(self,job=None,issuer=None):
        job=job or self.job
        return broker.run(self.conn,{'job_id':job['id'],'lease_token':job['lease_token']},self.data,
                          client_factory=lambda *args:self.github,token_issuer=issuer or (lambda *args,**kwargs:'fixture-credential'))

    def test_exact_artifact_becomes_one_draft_and_main_is_never_written(self):
        result=self.run_broker()
        self.assertEqual(result['ci_state'],'success');self.assertTrue(result['draft']);self.assertFalse(result['published'])
        self.run_broker()
        self.assertEqual(sum(method=='POST' and path=='/pulls' for method,path,_ in self.github.calls),1)
        writes=[(method,path,payload) for method,path,payload in self.github.calls if method!='GET']
        self.assertTrue(all(method=='POST' for method,_,_ in writes))
        refs=[payload['ref'] for _,path,payload in writes if path=='/git/refs']
        self.assertEqual(len(refs),1);self.assertTrue(refs[0].startswith('refs/heads/ai-review/artifact-'))
        self.assertFalse(any('merge' in path or 'deploy' in path for _,path,_ in self.github.calls))

    def test_uncertain_pr_creation_is_reconciled_without_duplicates(self):
        self.github.fail_pr_once=True
        with self.assertRaises(broker.Pending): self.run_broker()
        result=self.run_broker()
        self.assertEqual(result['pr_url'],self.github.pr['html_url'])
        self.assertEqual(sum(m=='POST' and p=='/pulls' for m,p,_ in self.github.calls),1)

    def test_ci_pending_retains_pr_and_only_latest_exact_head_counts(self):
        self.github.ci='pending'
        with self.assertRaises(broker.Pending): self.run_broker()
        self.github.ci='success';self.run_broker()
        data=self.github.call('GET','/actions/runs?fixture')
        failed=copy.deepcopy(data['workflow_runs'][0]);failed.update(id=1000,conclusion='failure')
        self.assertEqual(broker.ci_evidence({'workflow_runs':data['workflow_runs']+[failed]},self.github.head)[0],'failure')
        for field,value in [('head_sha','e'*40),('event','push'),('path','other.yml')]:
            run=copy.deepcopy(failed);run[field]=value
            self.assertEqual(broker.ci_evidence({'workflow_runs':[run]},self.github.head),('pending',[]))

    def test_changed_diff_or_branch_invalidates_verification(self):
        self.run_broker();self.github.branch='e'*40
        with self.assertRaises(broker.Blocked): self.run_broker()
        self.assertFalse(ledger.record(self.conn,1)[1]['verified'])

    def test_modified_artifact_or_report_never_reaches_credentials(self):
        identity,files=ledger.material(self.conn,self.artifact,self.data)
        path=self.data/'artifacts'/('job-'+str(identity['generation_job_id'])+'-attempt-1')/next(iter(files))
        path.write_text('changed')
        with self.assertRaises(PermissionError):
            self.run_broker(issuer=lambda *args,**kwargs:self.fail('credential requested before source validation'))

    def test_policy_denies_before_credential_access_and_lease_is_required(self):
        (self.data/'artifact-pr-policy.json').write_text('{}')
        with self.assertRaises(broker.Blocked): self.run_broker(issuer=lambda *args,**kwargs:self.fail('issued credential'))
        with self.assertRaises(PermissionError): broker.run(self.conn,{'job_id':self.job['id'],'lease_token':'0'*48},self.data)

    def test_refresh_uses_only_get_and_can_invalidate_old_ci(self):
        result=self.run_broker()
        q.finish(self.conn,self.job['id'],self.job['lease_token'],result,awaiting_owner=True)
        q.enqueue(self.conn,'control','review_change',{'artifact_pr':self.artifact,'refresh':True})
        refresh=q.claim(self.conn,'unit',q.KINDS);self.github.calls=[]
        self.assertEqual(self.run_broker(refresh)['pr_url'],result['pr_url'])
        self.assertTrue(all(m=='GET' for m,_,_ in self.github.calls))

    def test_same_scope_approval_is_idempotent_and_cannot_authorize_other_head_or_project(self):
        self.run_broker();candidate,aid,scope=ledger.request_release(self.conn,1)
        self.assertEqual(ledger.request_release(self.conn,1)[:2],(candidate,aid))
        self.assertFalse(ledger.release_authorized(self.conn,candidate,scope))
        approval.decide(self.conn,aid,'owner','owner',True)
        self.assertTrue(ledger.release_authorized(self.conn,candidate,scope))
        for change in ({'project':'nova'},{'head_sha':'f'*40},{'artifact_sha256':'0'*64}):
            self.assertFalse(ledger.release_authorized(self.conn,candidate,dict(scope,**change)))
        remote=ledger.record(self.conn,1)[1];remote['verified']=False
        ledger.save_remote(self.conn,self.job,1,remote)
        self.assertFalse(ledger.release_authorized(self.conn,candidate,scope))

    def test_release_candidate_rolls_back_approval_if_link_insert_fails(self):
        self.run_broker()
        self.conn.execute("CREATE TEMP TRIGGER reject_candidate BEFORE INSERT ON artifact_release_candidates BEGIN SELECT RAISE(ABORT,'copy-only failure'); END")
        before=self.conn.execute('SELECT count(*) FROM approvals').fetchone()[0]
        with self.assertRaises(sqlite3.IntegrityError): ledger.request_release(self.conn,1)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM approvals').fetchone()[0],before)

    def test_expired_verification_and_ci_failure_cannot_request_publication(self):
        self.run_broker();remote=ledger.record(self.conn,1)[1];remote['checked_at']=time.time()-901
        ledger.save_remote(self.conn,self.job,1,remote)
        with self.assertRaises(PermissionError): ledger.request_release(self.conn,1)
        remote.update(checked_at=time.time(),ci_state='failure');ledger.save_remote(self.conn,self.job,1,remote)
        with self.assertRaises(PermissionError): ledger.request_release(self.conn,1)

    def test_memory_binds_pr_identity_and_ignores_only_refresh_timestamp(self):
        result=self.run_broker();q.finish(self.conn,self.job['id'],self.job['lease_token'],result,awaiting_owner=True)
        memory.sync(self.conn)
        row=self.conn.execute("SELECT id FROM project_evidence_memory WHERE event_id IN(SELECT id FROM agent_job_events WHERE job_id=? AND event='awaiting_owner')",(self.job['id'],)).fetchone()
        self.assertIn('Draft PR сверён',memory.summary(self.conn,'control'))
        remote=ledger.record(self.conn,1)[1];remote['checked_at']+=1
        self.conn.execute('UPDATE artifact_pr_requests SET remote=?',(ledger.canonical(remote),));self.conn.commit()
        self.assertIn(self.github.pr['html_url'],memory.detail(self.conn,row[0]))
        remote['head_sha']='e'*40
        self.conn.execute('UPDATE artifact_pr_requests SET remote=?',(ledger.canonical(remote),));self.conn.commit()
        self.assertIn('повторной проверки',memory.detail(self.conn,row[0]))

    def test_refresh_transport_rejects_all_write_methods_before_network(self):
        client=broker.Client('fixture',time.monotonic()+5);client.read_only=True
        for method in ('POST','PUT','PATCH','DELETE'):
            with self.assertRaises(broker.Blocked): client.call(method,'/git/refs',{})


if __name__=='__main__': unittest.main()
