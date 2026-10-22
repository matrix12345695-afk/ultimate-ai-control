import concurrent.futures
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch
import budget_gate
import metered_provider as api


class MeteredProviderTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.path=self.root/'db.sqlite'
        self.conn=sqlite3.connect(self.path)
        api.initialize(self.conn)
        self.policy=self.root/'policy.json'
        self.key=self.root/'private.key'
        self.key.write_text('sk-test-only-not-real-'+'a'*40)
        self.key.chmod(0o600)
        self.configure(enabled=True)
        # Deterministic tariff/date tests remain reproducible after the review expires.
        self.clock=patch.object(api,'datetime')
        clock=self.clock.start()
        clock.now.return_value=datetime(2026,10,22,12,tzinfo=timezone.utc)

    def tearDown(self):
        self.clock.stop()
        self.conn.close()
        self.temp.cleanup()

    def configure(self,**values):
        cfg=dict(api.DEFAULT_POLICY,**values)
        self.policy.write_text(json.dumps(cfg))
        self.policy.chmod(0o600)
        return cfg

    def body(self):
        return {'id':'resp_test_only','model':api.DEFAULT_POLICY['model'],'service_tier':'default','status':'completed',
                'usage':{'input_tokens':1000,'output_tokens':100,'total_tokens':1100,'input_tokens_details':{'cached_tokens':100}},
                'output':[{'type':'reasoning'},{'type':'message','role':'assistant','content':[{'type':'output_text','text':'Prepare a draft and run tests.'}]}]}

    def call(self,key='test:one',prompt='Prepare a safe draft',transport=None):
        return api.generate(self.conn,self.policy,self.key,key,prompt,transport=transport or (lambda *args:self.body()))

    def test_disabled_missing_key_bad_policy_and_expired_prices_never_send(self):
        from unittest.mock import Mock
        transport=Mock()
        self.configure(enabled=False)
        with self.assertRaisesRegex(api.ProviderBlocked,'provider_disabled'): self.call(transport=transport)
        self.configure(enabled=True,monthly_limit_microusd=31000000)
        with self.assertRaisesRegex(api.ProviderBlocked,'owner_budget'): self.call(transport=transport)
        self.configure(enabled=True,model='unknown-model')
        with self.assertRaises(api.ProviderBlocked): self.call(transport=transport)
        self.configure(enabled=True)
        with patch.object(api,'PRICING_EXPIRES','2026-10-21'):
            with self.assertRaisesRegex(api.ProviderBlocked,'pricing_review_expired'): self.call(transport=transport)
        self.key.unlink()
        with self.assertRaises(FileNotFoundError): self.call(transport=transport)
        transport.assert_not_called()
        self.assertEqual(budget_gate.charged(self.conn),0)

    def test_private_files_symlink_permissions_and_secret_prompt_rejected(self):
        self.key.chmod(0o644)
        with self.assertRaises(api.ProviderBlocked): self.call()
        self.key.chmod(0o600)
        link=self.root/'key-link';link.symlink_to(self.key)
        with self.assertRaises(api.ProviderBlocked): api.private_read(link,512)
        with self.assertRaisesRegex(api.ProviderBlocked,'sensitive_prompt'): self.call(prompt='password=do-not-send')
        with self.assertRaises(api.ProviderBlocked): api.generate(self.conn,self.policy,self.key,'x','task',project='inventory')
        self.assertEqual(budget_gate.charged(self.conn),0)

    def test_reservation_precedes_io_cached_usage_and_durable_replay(self):
        sent=[]
        def transport(payload,key,request_id):
            with sqlite3.connect(self.path) as read:
                self.assertEqual(read.execute("SELECT state FROM provider_costs WHERE id=?",(request_id,)).fetchone()[0],'reserved')
                self.assertEqual(read.execute('SELECT state FROM metered_requests').fetchone()[0],'pending')
            self.assertEqual(payload['tools'],[])
            self.assertFalse(payload['store'])
            self.assertEqual(payload['service_tier'],'default')
            self.assertEqual(payload['max_output_tokens'],2048)
            sent.append(request_id)
            return self.body()
        result=self.call(transport=transport)
        self.assertEqual(result['cost_microusd'],428)
        self.assertFalse(result['published'])
        self.assertTrue(result['usable'])
        self.assertEqual(budget_gate.charged(self.conn),428)
        again=self.call(transport=transport)
        self.assertTrue(again['replayed'])
        self.assertEqual(len(sent),1)
        with self.assertRaisesRegex(api.ProviderBlocked,'request_key_conflict'): self.call(prompt='different task',transport=transport)
        raw=self.conn.execute('SELECT result FROM metered_requests').fetchone()[0]
        self.assertNotIn(self.key.read_text(),raw)

    def test_timeout_ambiguity_freezes_other_keys_after_restart_and_month_rollover(self):
        calls=[]
        def timeout(*args): calls.append(1);raise TimeoutError('never-log-raw-secrets')
        with self.assertRaisesRegex(api.ProviderBlocked,'ambiguous_send'): self.call(transport=timeout)
        held=api.quote(api.policy(self.policy))
        self.assertEqual(budget_gate.charged(self.conn),held)
        self.conn.close();self.conn=sqlite3.connect(self.path)
        with self.assertRaisesRegex(api.ProviderBlocked,'request_unresolved'): self.call(transport=timeout)
        with patch.object(budget_gate,'month',return_value='2026-11'):
            self.assertEqual(budget_gate.charged(self.conn),held)
            with self.assertRaisesRegex(api.ProviderBlocked,'unresolved_usage'): self.call(key='test:new',transport=timeout)
        self.assertEqual(len(calls),1)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM owner_notifications').fetchone()[0],1)
        self.assertEqual(self.conn.execute('SELECT state FROM provider_costs').fetchone()[0],'unknown')

    def test_unpriced_missing_or_excessive_usage_never_releases_hold(self):
        for mutate in ('missing','tokens','model','tier','cache'):
            with self.subTest(mutate=mutate):
                conn=sqlite3.connect(':memory:')
                body=self.body()
                if mutate=='missing': del body['usage']
                if mutate=='tokens': body['usage']['output_tokens']=9000;body['usage']['total_tokens']=10000
                if mutate=='model': body['model']='different-model'
                if mutate=='tier': body['service_tier']='priority'
                if mutate=='cache': body['usage']['input_tokens_details']['cache_write_tokens']=100
                with self.assertRaises(api.ProviderBlocked):
                    api.generate(conn,self.policy,self.key,'test:'+mutate,'task',transport=lambda *a:body)
                self.assertEqual(conn.execute('SELECT state FROM provider_costs').fetchone()[0],'unknown')
                self.assertEqual(budget_gate.charged(conn),api.quote(api.policy(self.policy)))
                conn.close()

    def test_incomplete_refusal_tool_and_sensitive_outputs_are_billed_without_execution(self):
        for kind in ('incomplete','tool','refusal','secret'):
            body=self.body()
            if kind=='incomplete': body['status']='incomplete'
            if kind=='tool': body['output']=[{'type':'function_call','name':'run_shell'}]
            if kind=='refusal': body['output'][1]['content']=[{'type':'refusal','refusal':'no'}]
            if kind=='secret': body['output'][1]['content'][0]['text']='api_key=never-store-this'
            result=self.call(key='test:'+kind,transport=lambda *a:body)
            self.assertFalse(result['usable'])
            self.assertEqual(result['text'],'')
        self.assertEqual(budget_gate.charged(self.conn),4*428)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM provider_costs WHERE state='settled'").fetchone()[0],4)

    def test_budget_cap_stops_before_send_and_notification_is_deduplicated(self):
        from unittest.mock import Mock
        reserve=budget_gate.reserve(self.conn,'control','planner','old',29999000)
        budget_gate.settle(self.conn,reserve,29999000,1,1)
        transport=Mock()
        for _ in range(2):
            with self.assertRaisesRegex(api.ProviderBlocked,'budget_exhausted'): self.call(transport=transport)
        transport.assert_not_called()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM owner_notifications').fetchone()[0],1)
        self.assertEqual(budget_gate.charged(self.conn),29999000)

    def test_concurrent_duplicate_dispatch_has_only_one_reservation_and_send(self):
        started=threading.Event();finish=threading.Event();calls=[]
        def transport(*args):
            calls.append(1);started.set();finish.wait(5);return self.body()
        def attempt():
            with sqlite3.connect(self.path,timeout=10) as conn:
                return api.generate(conn,self.policy,self.key,'test:race','task',transport=transport)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            first=pool.submit(attempt)
            self.assertTrue(started.wait(5))
            with self.assertRaisesRegex(api.ProviderBlocked,'request_unresolved'): pool.submit(attempt).result()
            finish.set();self.assertTrue(first.result()['usable'])
        self.assertEqual(len(calls),1)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM provider_costs').fetchone()[0],1)

    def test_rollover_guard_and_80_percent_notification(self):
        with patch.object(api,'datetime') as clock:
            clock.now.return_value=datetime(2026,10,31,23,59,30,tzinfo=timezone.utc)
            with self.assertRaisesRegex(api.ProviderBlocked,'month_boundary'): self.call()
        ident=budget_gate.reserve(self.conn,'control','planner','old',24000000)
        budget_gate.settle(self.conn,ident,24000000,1,1)
        self.call(key='test:one');self.call(key='test:two')
        self.assertEqual(self.conn.execute("SELECT count(*) FROM owner_notifications WHERE event_key LIKE 'provider-budget-warning-%'").fetchone()[0],1)

    def test_redirect_never_forwards_credentials(self):
        import urllib.request
        req=urllib.request.Request(api.ENDPOINT,headers={'Authorization':'Bearer test-only'})
        with self.assertRaisesRegex(api.ProviderBlocked,'redirect_rejected'):
            api.NoRedirect().redirect_request(req,None,307,'redirect',{},'https://evil.invalid/')

    def test_slow_request_crossing_utc_month_keeps_hold_for_new_month(self):
        with patch.object(budget_gate,'month',return_value='2026-10') as month:
            def slow_response(*args):
                month.return_value='2026-11'
                return self.body()
            with self.assertRaisesRegex(api.ProviderBlocked,'ambiguous_send'):
                self.call(transport=slow_response)
            self.assertEqual(self.conn.execute('SELECT month,state FROM provider_costs').fetchone(),('2026-10','unknown'))
            self.assertEqual(budget_gate.charged(self.conn),api.quote(api.policy(self.policy)))
            with self.assertRaisesRegex(api.ProviderBlocked,'unresolved_usage'): self.call(key='test:next-month')


if __name__=='__main__': unittest.main()
