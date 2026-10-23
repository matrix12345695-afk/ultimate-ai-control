import concurrent.futures
import sqlite3
import tempfile
from pathlib import Path
import unittest
import task_queue as queue


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/'queue.db'
        self.conn=sqlite3.connect(self.path,timeout=10)
        queue.initialize(self.conn)

    def tearDown(self):
        self.conn.close()
        self.temp.cleanup()

    def enqueue(self,**kwargs):
        return queue.enqueue(self.conn,'nova','check_site',{'url':'https://novaweb.uz/'},now=100,**kwargs)

    def claim(self,worker='monitor',**kwargs):
        return queue.claim(self.conn,worker,{'check_site'},now=101,**kwargs)

    def test_protected_project_and_unknown_kind(self):
        for project in ('inventory','inventory-mini-app','../../inventory-bot'):
            with self.assertRaises(ValueError): queue.enqueue(self.conn,project,'check_site',{})
        with self.assertRaises(ValueError): queue.enqueue(self.conn,'nova','shell',{'cmd':'echo bad'})

    def test_idempotent_enqueue_and_mismatch_rejection(self):
        ident=self.enqueue(event_key='incident-1')
        self.assertEqual(self.enqueue(event_key='incident-1'),ident)
        with self.assertRaises(ValueError):
            queue.enqueue(self.conn,'nova','check_site',{'different':True},event_key='incident-1')

    def test_persisted_queue_and_default_single_worker(self):
        self.enqueue()
        self.enqueue()
        job=self.claim()
        with sqlite3.connect(self.path) as other:
            self.assertIsNone(queue.claim(other,'second',{'check_site'},now=102))
            self.assertEqual(other.execute('SELECT state FROM agent_jobs WHERE id=?',(job['id'],)).fetchone()[0],'running')

    def test_priority_and_capability_selection(self):
        low=self.enqueue(priority=1)
        high=self.enqueue(priority=90)
        queue.enqueue(self.conn,'control','test_release',{},priority=100,now=100)
        self.assertEqual(self.claim()['id'],high)
        self.assertNotEqual(high,low)

    def test_concurrent_claims_never_duplicate(self):
        self.enqueue()
        def attempt(index):
            conn=sqlite3.connect(self.path,timeout=10)
            try: return queue.claim(conn,'worker-'+str(index),{'check_site'},now=101)
            finally: conn.close()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            results=list(pool.map(attempt,range(4)))
        self.assertEqual(sum(result is not None for result in results),1)

    def test_paused_queue_retains_jobs_and_heartbeat_requests_pause(self):
        self.enqueue()
        job=self.claim()
        queue.configure(self.conn,paused=True,reason='owner emergency stop',now=102)
        self.assertTrue(queue.heartbeat(self.conn,job['id'],job['lease_token'],now=103)['paused'])
        self.assertIsNone(queue.claim(self.conn,'other',{'check_site'},now=104))
        queue.finish(self.conn,job['id'],job['lease_token'],{'safe_stop':True},now=105)
        self.enqueue()
        queue.configure(self.conn,paused=False,now=106)
        self.assertIsNotNone(queue.claim(self.conn,'other',{'check_site'},now=107))

    def test_expired_worker_cannot_finish_reclaimed_job(self):
        self.enqueue()
        old=self.claim(lease_seconds=5)
        new=queue.claim(self.conn,'replacement',{'check_site'},now=107)
        self.assertEqual(new['attempt'],2)
        self.assertNotEqual(old['lease_token'],new['lease_token'])
        with self.assertRaises(PermissionError): queue.finish(self.conn,old['id'],old['lease_token'],{},now=108)
        queue.finish(self.conn,new['id'],new['lease_token'],{'ok':True},now=108)

    def test_expired_final_attempt_fails_permanently(self):
        self.enqueue(max_attempts=1)
        self.claim(lease_seconds=5)
        self.assertIsNone(queue.claim(self.conn,'replacement',{'check_site'},now=110))
        self.assertEqual(self.conn.execute('SELECT state FROM agent_jobs').fetchone()[0],'failed')

    def test_retry_backoff_and_bounded_attempts(self):
        self.enqueue(max_attempts=2)
        first=self.claim()
        queue.fail(self.conn,first['id'],first['lease_token'],'timeout',now=102)
        self.assertIsNone(queue.claim(self.conn,'second',{'check_site'},now=103))
        second=queue.claim(self.conn,'second',{'check_site'},now=163)
        queue.fail(self.conn,second['id'],second['lease_token'],'timeout',now=164)
        self.assertIsNone(queue.claim(self.conn,'third',{'check_site'},now=10000))

    def test_wrong_lease_cannot_change_job(self):
        self.enqueue()
        job=self.claim()
        with self.assertRaises(PermissionError): queue.heartbeat(self.conn,job['id'],'wrong',now=102)
        with self.assertRaises(PermissionError): queue.fail(self.conn,job['id'],'wrong','failure',now=102)

    def test_awaiting_owner_frees_slot_for_independent_work(self):
        self.enqueue()
        self.enqueue()
        job=self.claim()
        queue.finish(self.conn,job['id'],job['lease_token'],{'release':'abc','approval':'required'},awaiting_owner=True,now=102)
        other=queue.claim(self.conn,'monitor',{'check_site'},now=103)
        self.assertIsNotNone(other)
        self.assertNotEqual(other['id'],job['id'])

    def test_max_concurrency_and_single_job_per_worker(self):
        for _ in range(4): self.enqueue()
        queue.configure(self.conn,concurrency=2,now=100)
        self.assertIsNotNone(self.claim('worker-1'))
        self.assertIsNone(self.claim('worker-1'))
        self.assertIsNotNone(self.claim('worker-2'))
        self.assertIsNone(self.claim('worker-3'))
        with self.assertRaises(ValueError): queue.configure(self.conn,concurrency=4)

    def test_cancel_never_kills_running_worker(self):
        waiting=self.enqueue()
        self.assertTrue(queue.cancel(self.conn,waiting,now=101))
        ident=self.enqueue()
        job=self.claim()
        self.assertEqual(job['id'],ident)
        self.assertFalse(queue.cancel(self.conn,ident,now=102))

    def test_measured_time_clipped_to_window_without_guessing(self):
        self.enqueue()
        job=self.claim(lease_seconds=120)
        queue.add_work_span(self.conn,job['id'],job['lease_token'],'active',102,112,now=113)
        queue.add_work_span(self.conn,job['id'],job['lease_token'],'testing',112,122,now=123)
        report=queue.report(self.conn,107,117)
        totals={r['category']:r['seconds'] for r in report['measured_seconds']}
        self.assertEqual(totals,{'active':5,'testing':5})
        self.assertIn('unknown',report['unmeasured_time'])

    def test_overlapping_and_future_spans_rejected(self):
        self.enqueue()
        job=self.claim()
        queue.add_work_span(self.conn,job['id'],job['lease_token'],'active',102,112,now=113)
        with self.assertRaises(ValueError): queue.add_work_span(self.conn,job['id'],job['lease_token'],'testing',110,115,now=116)
        with self.assertRaises(ValueError): queue.add_work_span(self.conn,job['id'],job['lease_token'],'active',113,125,now=120)

    def test_no_work_time_is_reported_without_worker_measurements(self):
        self.enqueue()
        self.claim()
        self.assertEqual(queue.report(self.conn,0,1000)['measured_seconds'],[])

    def test_invalid_inputs_and_transactions(self):
        for value in (True,-1,101):
            with self.assertRaises(ValueError): self.enqueue(priority=value)
        with self.assertRaises(ValueError): queue.enqueue(self.conn,'nova','check_site',{'x':float('nan')})
        with self.assertRaises(ValueError): queue.claim(self.conn,'worker',{'shell'},now=101)
        with self.assertRaises(ValueError): queue.claim(self.conn,'worker',{'check_site'},lease_seconds=0)
        with self.assertRaises(ValueError): queue.report(self.conn,100,99)
        self.conn.execute("INSERT INTO agent_job_events(at,event,detail) VALUES(100,'x','x')")
        with self.assertRaises(RuntimeError): self.enqueue()
        self.conn.rollback()


if __name__=='__main__': unittest.main()
