from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import health_incidents as health
import main
from owner_notifications import create,mark_delivered
import queue_worker
import task_queue as queue


class HealthIncidentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.db=Path(self.temp.name)/'control.db'
        self.conn=queue_worker.connect(self.db);queue_worker.initialize(self.conn)
    def tearDown(self): self.conn.close();self.temp.cleanup()
    def sample(self,healthy):
        ident=queue.enqueue(self.conn,'nova','check_site',{'target':'nova'})
        result=dict(target='nova',url=health.TARGETS['nova'],healthy=healthy,detail='HTTP 200' if healthy else 'HTTP 503')
        outcome=queue_worker.run_once(self.db,site_checker=lambda _:result)
        self.assertEqual(outcome,dict(id=ident,state='succeeded'))
        return ident
    def claim(self):
        ident=queue.enqueue(self.conn,'nova','check_site',{'target':'nova'})
        job=queue.claim(self.conn,'operations-1',queue.KINDS,lease_seconds=60)
        self.assertEqual(job['id'],ident);return job
    def good(self): return dict(target='nova',url=health.TARGETS['nova'],healthy=True,detail='HTTP 200')

    def test_recovery_resolves_only_its_alert_preserves_receipt_and_has_no_duplicate_good_notes(self):
        failed=self.sample(False)
        alarm=self.conn.execute("SELECT id FROM owner_notifications WHERE kind='critical'").fetchone()[0]
        mark_delivered(self.conn,alarm,message_id=999)
        decision=create(self.conn,'ULTIMATE AI CONTROL','decision','Publish','Version needs approval','Review',event_key='owner-publish')
        other=create(self.conn,'ULTIMATE AI CONTROL','critical','Sandbox failure','Failed','Review',event_key='sandbox-failure')
        recovered=self.sample(True)
        self.assertEqual(self.conn.execute('SELECT state,telegram_message_id FROM owner_notifications WHERE id=?',(alarm,)).fetchone(),('resolved',999))
        self.assertEqual(self.conn.execute('SELECT state,recovery_job_id FROM agent_health_incidents WHERE opened_job_id=?',(failed,)).fetchone(),('recovered',recovered))
        for ident in (decision,other): self.assertEqual(self.conn.execute('SELECT state FROM owner_notifications WHERE id=?',(ident,)).fetchone()[0],'pending')
        count=self.conn.execute('SELECT count(*) FROM owner_notifications').fetchone()[0]
        self.sample(True)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM owner_notifications').fetchone()[0],count)
        with patch.object(main,'DB',self.db): self.assertIn('Подтверждённых восстановлений: 1',main.command('/monitor4'))

    def test_repeated_failure_is_one_incident_and_next_outage_is_new(self):
        self.sample(False);self.sample(False)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM agent_health_incidents').fetchone()[0],1)
        self.sample(True);self.sample(False)
        self.assertEqual(dict(self.conn.execute('SELECT state,count(*) FROM agent_health_incidents GROUP BY state')),dict(open=1,recovered=1))
        self.assertEqual(self.conn.execute("SELECT count(*) FROM owner_notifications WHERE kind='critical' AND state='pending'").fetchone()[0],1)

    def test_committed_legacy_queue_alarm_is_reconciled_even_when_stored_health_already_good(self):
        bad=queue.enqueue(self.conn,'nova','check_site',{'target':'nova'})
        self.conn.execute("UPDATE agent_jobs SET state='succeeded',result=?,updated_at=? WHERE id=?",(json.dumps(dict(target='nova',url=health.TARGETS['nova'],healthy=False,detail='TimeoutError')),time.time()-2,bad))
        self.conn.execute('INSERT INTO agent_health VALUES(?,?,?,?)',('nova',1,'HTTP 200',time.time()-1));self.conn.commit()
        alarm=create(self.conn,health.PROJECT,'critical','Состояние NOVA WEB изменилось','Timeout','Review',task_id=str(bad),event_key='health-job-'+str(bad))
        self.sample(True)
        self.assertEqual(self.conn.execute('SELECT state FROM owner_notifications WHERE id=?',(alarm,)).fetchone()[0],'resolved')
        self.assertEqual(self.conn.execute('SELECT source FROM agent_health_incidents').fetchone()[0],'queue')

    def test_legacy_hourly_poller_requires_exact_format_and_event_fingerprint(self):
        title='Изменилось состояние сайта';reason='WARNING https://novaweb.uz/: unavailable (TimeoutError)'
        stamp=datetime.now(timezone.utc);key=hashlib.sha256(('monitoring'+'critical'+title+reason+stamp.strftime('%Y%m%d%H')).encode()).hexdigest()
        alarm=create(self.conn,'monitoring','critical',title,reason,'Review',event_key=key)
        forged=create(self.conn,'monitoring','critical',title,reason,'Review',event_key='arbitrary-event')
        self.sample(True)
        self.assertEqual(self.conn.execute('SELECT state FROM owner_notifications WHERE id=?',(alarm,)).fetchone()[0],'resolved')
        self.assertEqual(self.conn.execute('SELECT state FROM owner_notifications WHERE id=?',(forged,)).fetchone()[0],'pending')
        self.assertEqual(self.conn.execute('SELECT source FROM agent_health_incidents').fetchone()[0],'legacy-poller')

    def test_fake_prefix_wrong_url_and_uncommitted_origin_are_never_resolved(self):
        notes=[]
        for state,url,healthy in (('queued',health.TARGETS['nova'],False),('succeeded','https://other.invalid/',False),('succeeded',health.TARGETS['nova'],True)):
            ident=queue.enqueue(self.conn,'nova','check_site',{'target':'nova'})
            self.conn.execute('UPDATE agent_jobs SET state=?,result=?,available_at=? WHERE id=?',(state,json.dumps(dict(target='nova',url=url,healthy=healthy)),time.time()+1000,ident));self.conn.commit()
            notes.append(create(self.conn,health.PROJECT,'critical','Состояние NOVA WEB изменилось','Unknown','Review',task_id=str(ident),event_key='health-job-'+str(ident)))
        self.sample(True)
        self.assertTrue(all(self.conn.execute('SELECT state FROM owner_notifications WHERE id=?',(n,)).fetchone()[0]=='pending' for n in notes))
        self.assertEqual(self.conn.execute('SELECT count(*) FROM agent_health_incidents').fetchone()[0],0)

    def test_transaction_failure_rolls_back_job_health_resolution_and_recovery_outbox(self):
        self.sample(False);job=self.claim();count=self.conn.execute('SELECT count(*) FROM owner_notifications').fetchone()[0]
        with patch.object(queue,'_event',side_effect=RuntimeError('artificial commit gap')):
            with self.assertRaises(RuntimeError): health.complete(self.conn,job,self.good())
        self.assertEqual(self.conn.execute('SELECT state FROM agent_jobs WHERE id=?',(job['id'],)).fetchone()[0],'running')
        self.assertEqual(self.conn.execute('SELECT healthy FROM agent_health').fetchone()[0],0)
        self.assertEqual(self.conn.execute('SELECT state FROM agent_health_incidents').fetchone()[0],'open')
        self.assertEqual(self.conn.execute('SELECT count(*) FROM owner_notifications').fetchone()[0],count)
        self.assertEqual(self.conn.execute('SELECT state FROM owner_notifications').fetchone()[0],'pending')
        health.complete(self.conn,job,self.good())
        self.assertEqual(self.conn.execute('SELECT state FROM agent_jobs WHERE id=?',(job['id'],)).fetchone()[0],'succeeded')

    def test_expired_or_superseded_sample_never_closes_current_alarm(self):
        self.sample(False);job=self.claim()
        self.conn.execute('UPDATE agent_jobs SET lease_until=0 WHERE id=?',(job['id'],));self.conn.commit()
        with self.assertRaises(PermissionError): health.complete(self.conn,job,self.good())
        self.assertEqual(self.conn.execute('SELECT state FROM agent_health_incidents').fetchone()[0],'open')
        self.conn.execute('UPDATE agent_jobs SET lease_until=? WHERE id=?',(time.time()+60,job['id']))
        self.conn.execute('UPDATE agent_health SET checked_at=?',(time.time()+10,));self.conn.commit()
        result=health.complete(self.conn,job,self.good())
        self.assertTrue(result['superseded'])
        self.assertEqual(self.conn.execute('SELECT state FROM agent_health_incidents').fetchone()[0],'open')

    def test_transactional_notifications_require_transaction_and_rollback_with_it(self):
        with self.assertRaises(ValueError): create(self.conn,'test','info','t','r','a',commit=False)
        self.conn.execute('BEGIN IMMEDIATE')
        create(self.conn,'test','info','t','r','a',commit=False)
        self.assertTrue(self.conn.in_transaction);self.conn.rollback()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM owner_notifications').fetchone()[0],0)

    def test_invalid_results_and_malformed_legacy_ids_do_not_change_health(self):
        job=self.claim()
        for changed in (dict(url='https://other.invalid/'),dict(healthy='true'),dict(healthy=True,detail='HTTP 503'),dict(healthy=False,detail='HTTP 200')):
            with self.assertRaises(ValueError): health.complete(self.conn,job,dict(self.good(),**changed))
        self.assertEqual(self.conn.execute('SELECT count(*) FROM agent_health').fetchone()[0],0)
        task='9'*19
        note=create(self.conn,health.PROJECT,'critical','Состояние NOVA WEB изменилось','Unknown','Review',task_id=task,event_key='health-job-'+task)
        health.complete(self.conn,job,self.good())
        self.assertEqual(self.conn.execute('SELECT state FROM owner_notifications WHERE id=?',(note,)).fetchone()[0],'pending')
