import copy
import json
import sqlite3
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from pathlib import Path
import approval
import nova_deploy_machine as m
from nova_deploy_fixture import FixtureRender,prepared,finish,acceptance


class PublicationMachineTests(unittest.TestCase):
    def setUp(self):
        self.conn=sqlite3.connect(':memory:');self.now=time.time();self.ident,self.scope,self.api=prepared(self.conn,self.now)
    def tearDown(self): self.conn.close()
    def state(self): return m.load(self.conn,self.ident)[1]['state']
    def to(self,target):
        for _ in range(15):
            if self.state()==target: return
            m.advance(self.conn,self.ident,self.api,self.now)
        self.fail('State not reached:'+target)
    def test_three_acceptance_scenarios_are_fixture_only(self):
        result=acceptance();self.assertEqual((result['cases'],result['pass'],result['real_Render_calls'],result['production_mutations']),(3,3,0,0));self.assertFalse(result['published'])
    def test_scope_rejects_other_project_service_version_settings_or_unverified_prerequisite(self):
        for field,value in [('project','inventory'),('service','srv-other'),('workspace','tea-other'),('repository','owner/other'),('candidate','a'*40),('base_deploy','dep-other'),('backup_verified',False),('provider_access_verified',1),('after',dict(m.AFTER,auto_deploy='commit'))]:
            with self.subTest(field=field),self.assertRaises(m.Blocked): m.create(self.conn,dict(self.scope,**{field:value}),self.now)
    def test_no_owner_approval_or_wrong_owner_cannot_mutate(self):
        ident=m.create(self.conn,self.scope,self.now)
        with self.assertRaises(m.Blocked): m.advance(self.conn,ident,self.api,self.now)
        aid=m.request_approval(self.conn,ident,self.now)
        with self.assertRaises(PermissionError): approval.decide(self.conn,aid,'intruder','fixture-owner',True)
        with self.assertRaises(m.Blocked): m.advance(self.conn,ident,self.api,self.now)
        self.assertEqual(self.api.calls,[])
    def test_approval_for_another_run_cannot_authorize_this_run(self):
        other=m.create(self.conn,self.scope,self.now)
        aid=m.load(self.conn,self.ident)[1]['approval_id']
        self.conn.execute('UPDATE nova_deploy_simulations SET approval_id=? WHERE id=?',(aid,other));self.conn.commit()
        with self.assertRaises(m.Blocked): m.advance(self.conn,other,self.api,self.now)
        self.assertEqual(self.api.calls,[])
    def test_tampered_scope_or_digest_fails_closed(self):
        self.conn.execute("UPDATE nova_deploy_simulations SET scope_sha256='changed'");self.conn.commit()
        with self.assertRaises(m.Blocked): m.advance(self.conn,self.ident,self.api,self.now)
        self.assertEqual(self.api.calls,[])
    def test_expired_scope_or_approval_cannot_start_publication(self):
        with self.assertRaises(m.Blocked): m.advance(self.conn,self.ident,self.api,self.now+901)
        self.conn.execute("UPDATE approvals SET expires_at='2000-01-01T00:00:00+00:00'");self.conn.commit()
        with self.assertRaises(m.Blocked): m.advance(self.conn,self.ident,self.api,self.now)
        self.assertEqual(self.api.calls,[])
    def test_foreign_live_config_branch_or_stale_snapshot_blocks_before_write(self):
        for change in ({'live_id':'dep-foreign'},{'main':'b'*40},{'candidate':'b'*40},{'service':'srv-other'},{'queue_empty':False},{'settings':dict(m.BEFORE,health='/other')}):
            self.api.frame_changes=change
            with self.subTest(change=change),self.assertRaises(m.Blocked): m.advance(self.conn,self.ident,self.api,self.now)
        self.api.frame_changes={};self.api.stale=True
        with self.assertRaises(m.Blocked): m.advance(self.conn,self.ident,self.api,self.now)
        self.assertEqual(self.api.calls,[])
    def test_known_deploy_id_is_polled_until_live_and_verified_without_duplicate_post(self):
        self.to('deploying');self.api.pending=2
        for _ in range(2): self.assertEqual(m.advance(self.conn,self.ident,self.api,self.now),'deploying')
        self.assertEqual(finish(self.conn,self.ident,self.api,self.now),'succeeded')
        self.assertEqual([x[0] for x in self.api.calls],['configure','deploy'])
        for _ in range(3): self.assertEqual(m.advance(self.conn,self.ident,self.api,self.now),'succeeded')
        self.assertEqual(len(self.api.calls),2)
    def test_bad_candidate_requires_three_failed_verifications_then_exact_rollback(self):
        self.api.bad_candidate=True;self.to('verify_candidate')
        for _ in range(2): self.assertEqual(m.advance(self.conn,self.ident,self.api,self.now),'verify_candidate')
        self.assertEqual(m.advance(self.conn,self.ident,self.api,self.now),'rollback_ready')
        self.assertEqual(finish(self.conn,self.ident,self.api,self.now),'rolled_back')
        self.assertEqual(self.api.calls[-1][3],{'deployId':m.BASE_DEPLOY});self.assertEqual(self.api.settings,m.AFTER)
    def test_build_failure_with_healthy_baseline_needs_no_rollback_post(self):
        self.api.build_failed=True;self.assertEqual(finish(self.conn,self.ident,self.api,self.now),'failed_no_cutover')
        self.assertEqual([x[0] for x in self.api.calls],['configure','deploy'])
    def test_lost_deploy_response_never_repeats_even_after_restart(self):
        self.api.timeout_action='deploy';self.assertEqual(finish(self.conn,self.ident,self.api,self.now),'ambiguous')
        for _ in range(4): self.assertEqual(m.advance(self.conn,self.ident,self.api,self.now+40),'ambiguous')
        self.assertEqual([x[0] for x in self.api.calls],['configure','deploy'])
    def test_lost_configuration_response_stops_before_deploy(self):
        self.api.timeout_action='configure';self.assertEqual(m.advance(self.conn,self.ident,self.api,self.now),'ambiguous')
        self.assertEqual(self.api.settings,m.AFTER);self.assertEqual(len(self.api.calls),1)
    def test_durable_intent_survives_crash_without_auto_retry(self):
        self.conn.execute("UPDATE nova_deploy_simulations SET state='deploy_intent',nonce='fixture',lease_until=?",(self.now+10,));self.conn.commit()
        self.assertEqual(m.advance(self.conn,self.ident,self.api,self.now),'busy')
        self.assertEqual(m.advance(self.conn,self.ident,self.api,self.now+11),'ambiguous');self.assertEqual(self.api.calls,[])
    def test_two_workers_cannot_send_two_configuration_requests(self):
        with tempfile.TemporaryDirectory() as name:
            path=Path(name)/'simulation.db'
            with sqlite3.connect(path) as setup: ident,scope,api=prepared(setup)
            api.configure_started=threading.Event();api.configure_gate=threading.Event();out=[]
            def first():
                with sqlite3.connect(path) as conn: out.append(m.advance(conn,ident,api))
            thread=threading.Thread(target=first);thread.start();self.assertTrue(api.configure_started.wait(2))
            try:
                with sqlite3.connect(path) as second: self.assertEqual(m.advance(second,ident,api),'busy')
            finally: api.configure_gate.set();thread.join(3)
            self.assertFalse(thread.is_alive());self.assertEqual(out,['configure_verify']);self.assertEqual(len(api.calls),1)
    def test_read_failures_are_bounded_and_do_not_retry_writes(self):
        self.to('deploying');self.api.read_errors=5
        for _ in range(5): state=m.advance(self.conn,self.ident,self.api,self.now)
        self.assertEqual(state,'blocked');self.assertEqual(len(self.api.calls),2)
    def test_real_or_unrecognized_transport_is_disabled_before_any_method(self):
        class RealProvider:
            environment='production'
            def observe(self,*a): raise AssertionError('Must not contact provider')
        with self.assertRaisesRegex(m.Blocked,'live_transport_disabled'): m.advance(self.conn,self.ident,RealProvider(),self.now)
        self.assertFalse(m.LIVE_PUBLICATION_ENABLED)
    def test_configuration_ack_is_not_readback_verification(self):
        self.assertEqual(m.advance(self.conn,self.ident,self.api,self.now),'configure_verify')
        self.api.settings=dict(m.BEFORE)
        self.assertEqual(m.advance(self.conn,self.ident,self.api,self.now),'blocked');self.assertEqual(len(self.api.calls),1)
    def test_foreign_deployment_blocks_rollback(self):
        self.api.bad_candidate=True;self.to('rollback_ready');self.api.live_id='dep-someoneelse'
        with self.assertRaises(m.Blocked): m.advance(self.conn,self.ident,self.api,self.now)
        self.assertEqual(len(self.api.calls),2)
    def test_conditional_rollback_uses_bounded_operation_window_after_initial_approval_expiry(self):
        self.api.bad_candidate=True;self.to('rollback_ready')
        self.assertEqual(m.advance(self.conn,self.ident,self.api,self.now+901),'rolling_back')
        self.assertEqual(finish(self.conn,self.ident,self.api,self.now+902),'rolled_back')
    def test_operation_deadline_or_revocation_blocks_future_mutation(self):
        self.api.bad_candidate=True;self.to('rollback_ready')
        with self.assertRaises(m.Blocked): m.advance(self.conn,self.ident,self.api,self.now+3601)
        self.conn.execute("UPDATE approvals SET status='revoked'");self.conn.commit()
        with self.assertRaises(m.Blocked): m.advance(self.conn,self.ident,self.api,self.now)
        self.assertEqual(len(self.api.calls),2)
    def test_bad_rollback_verification_stops_without_recursive_rollback(self):
        self.api.bad_candidate=True;self.api.bad_rollback=True
        self.assertEqual(finish(self.conn,self.ident,self.api,self.now),'blocked');self.assertEqual([x[0] for x in self.api.calls],['configure','deploy','rollback'])
    def test_write_intent_commit_failure_cannot_send_request(self):
        self.conn.execute("CREATE TRIGGER deny_intent BEFORE UPDATE ON nova_deploy_simulations BEGIN SELECT RAISE(FAIL,'fixture commit gap'); END");self.conn.commit()
        with self.assertRaises(sqlite3.IntegrityError): m.advance(self.conn,self.ident,self.api,self.now)
        self.assertEqual(self.api.calls,[])
    def test_only_documented_three_payloads_are_generated_no_data_or_budget_changes(self):
        self.assertEqual(m.request(self.scope,'deploy'),('POST','/services/'+m.SERVICE+'/deploys',{'commitId':m.CANDIDATE}))
        method,path,body=m.request(self.scope,'configure');self.assertEqual(method,'PATCH');self.assertEqual(set(body),{'autoDeployTrigger','serviceDetails'})
        self.assertEqual(set(body['serviceDetails']),{'healthCheckPath','envSpecificDetails'})
        with self.assertRaises(m.Blocked): m.request(self.scope,'restore_database')
        proof=self.api.http(False);proof['health']['ok']=1;self.assertFalse(m.verify_http(proof,self.scope))

    def test_lost_reply_survives_new_database_connection_without_another_write(self):
        with tempfile.TemporaryDirectory() as name:
            path=Path(name)/'journal.db'
            with sqlite3.connect(path) as first:
                ident,scope,api=prepared(first);api.timeout_action='deploy'
                self.assertEqual(finish(first,ident,api),'ambiguous')
            restarted=FixtureRender()
            with sqlite3.connect(path) as second:
                self.assertEqual(m.advance(second,ident,restarted),'ambiguous')
                self.assertEqual(restarted.calls,[])
                self.assertGreater(second.execute('SELECT count(*) FROM nova_deploy_simulation_events').fetchone()[0],0)
