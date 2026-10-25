import copy
import json
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import evidence_memory as memory
from owner_notifications import create,mark_delivered
import queue_worker
import scheduler
import task_queue as q
import vps_resources as vps

GIB=1024**3


def fixture(at=1000,*,memory_free=6*GIB,disk_free=60*GIB,ticks=1000,busy=100,boot=10):
    return dict(schema=vps.TARGET,observed_at=at,cpu=[busy,0,0,ticks-busy,0,0,0,0],boot=boot,cores=4,
                memory=[10*GIB,memory_free],disk=[100*GIB,disk_free],inodes=[10000,8000],load=[.1,.2,.3],errors=[])


class VPSResourcesTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'test.db'
        self.conn=sqlite3.connect(self.path);queue_worker.initialize(self.conn)
    def tearDown(self): self.conn.close();self.tmp.cleanup()
    def job(self,at):
        ident=q.enqueue(self.conn,'control','inspect_repository',{'target':vps.TARGET},now=at)
        job=q.claim(self.conn,'unit',q.KINDS,now=at,lease_seconds=60)
        self.assertEqual(ident,job['id']);return job
    def sample(self,at=1000,**kw):
        job=self.job(at);result=vps.complete(self.conn,job,fixture(at+1,**kw),now=at+2)
        return job,result

    def test_first_cpu_unknown_then_counter_delta_and_guest_not_double_counted(self):
        self.sample()
        self.sample(1300,ticks=2000,busy=400)
        report=json.loads(self.conn.execute('SELECT report FROM vps_resource_samples ORDER BY id DESC LIMIT 1').fetchone()[0])
        self.assertEqual(report['values']['cpu'],30)
        self.assertEqual(report['cpu_interval_seconds'],300)
        self.assertIn('30.00%',vps.describe(self.conn,now=1302))
        self.assertIn('устарели',vps.describe(self.conn,now=2300))

    def test_two_samples_open_one_alarm_and_two_recover_resolve_only_exact_note(self):
        other=create(self.conn,'ULTIMATE AI CONTROL','critical','Other incident','Other','Review',event_key='other')
        self.sample(memory_free=100*1024**2)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM vps_resource_incidents').fetchone()[0],0)
        self.sample(1300,memory_free=100*1024**2)
        alarm=self.conn.execute('SELECT notification_id FROM vps_resource_incidents').fetchone()[0]
        mark_delivered(self.conn,alarm,message_id=99)
        self.sample(1600,memory_free=100*1024**2)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM vps_resource_incidents').fetchone()[0],1)
        self.sample(1900);self.sample(2200)
        self.assertEqual(self.conn.execute('SELECT state,telegram_message_id FROM owner_notifications WHERE id=?',(alarm,)).fetchone(),('resolved',99))
        self.assertEqual(self.conn.execute('SELECT state FROM owner_notifications WHERE id=?',(other,)).fetchone()[0],'pending')
        self.sample(2500,memory_free=100*1024**2);self.sample(2800,memory_free=100*1024**2)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM vps_resource_incidents WHERE state='open'").fetchone()[0],1)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM vps_resource_incidents').fetchone()[0],2)

    def test_manual_bursts_do_not_advance_debounce_and_gap_resets_streak(self):
        self.sample(memory_free=1);self.sample(1010,memory_free=1);self.sample(1020,memory_free=1)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM vps_resource_incidents').fetchone()[0],0)
        self.sample(2000,memory_free=1) # >15min from accepted qualification
        self.assertEqual(self.conn.execute('SELECT count(*) FROM vps_resource_incidents').fetchone()[0],0)
        self.sample(2300,memory_free=1)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM vps_resource_incidents').fetchone()[0],1)

    def test_hysteresis_unknown_and_reboot_cannot_falsely_recover(self):
        self.sample(memory_free=1);self.sample(1300,memory_free=1)
        self.sample(1600,memory_free=int(1.2*GIB));self.sample(1900,memory_free=int(1.2*GIB))
        self.assertEqual(self.conn.execute('SELECT state FROM vps_resource_incidents').fetchone()[0],'open')
        self.sample(2200,boot=11);self.sample(2500,boot=12)
        self.assertEqual(self.conn.execute('SELECT state FROM vps_resource_incidents').fetchone()[0],'open')
        sample=fixture(2801,boot=12);sample['memory']=None;sample['errors']=['memory']
        vps.complete(self.conn,self.job(2800),sample,now=2802)
        self.assertEqual(self.conn.execute('SELECT state FROM vps_resource_incidents').fetchone()[0],'open')
        _,grade,interval=vps.assess(fixture(2500,ticks=1,busy=1),fixture(2200,ticks=2000,busy=400))
        self.assertEqual(grade['cpu'],'unknown');self.assertIsNone(interval)

    def test_cpu_memory_disk_inode_thresholds_and_telemetry_are_separate(self):
        base=fixture(1000);new=fixture(1300,ticks=2000,busy=1050,memory_free=1,disk_free=1)
        new['inodes']=[10000,100]
        values,grades,_=vps.assess(new,base)
        self.assertEqual(values['cpu'],95)
        self.assertEqual(grades,dict(cpu='bad',memory='bad',disk='bad',inodes='bad',telemetry='good'))
        new['cpu']=None;new['boot']=None;new['cores']=None;new['errors']=['cpu']
        values,grades,_=vps.assess(new,base)
        self.assertIsNone(values['cpu']);self.assertEqual(grades['telemetry'],'bad')

    def test_bad_lease_wrong_scope_future_sample_and_atomic_failure_do_not_mutate(self):
        self.sample(memory_free=1);job=self.job(1300);sample=fixture(1301,memory_free=1)
        before=self.conn.execute('SELECT * FROM vps_resource_streaks').fetchall()
        with self.assertRaises(PermissionError): vps.complete(self.conn,dict(job,project='inventory'),sample,now=1302)
        with self.assertRaises(PermissionError): vps.complete(self.conn,job,dict(sample,observed_at=1400),now=1302)
        with patch.object(q,'_event',side_effect=RuntimeError('copy-only commit gap')):
            with self.assertRaises(RuntimeError): vps.complete(self.conn,job,sample,now=1302)
        self.assertEqual(self.conn.execute('SELECT * FROM vps_resource_streaks').fetchall(),before)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM vps_resource_incidents').fetchone()[0],0)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM owner_notifications').fetchone()[0],0)
        with self.assertRaises(PermissionError): vps.complete(self.conn,job,sample,now=1400)
        vps.complete(self.conn,job,sample,now=1302)

    def test_malformed_or_conflicting_measurements_are_not_recorded(self):
        sample=fixture();job=self.job(999)
        for change in (dict(observed_at=float('nan')),dict(memory=[10,-1]),dict(cpu=[0]*7),dict(load=[float('inf'),0,0]),dict(errors=['disk'])):
            with self.assertRaises(ValueError): vps.complete(self.conn,job,dict(sample,**change),now=1001)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM vps_resource_samples').fetchone()[0],0)

    def test_proc_read_is_bounded_unit_checked_and_missing_data_not_healthy(self):
        root=Path(self.tmp.name)/'proc';root.mkdir()
        (root/'stat').write_text('cpu 100 0 10 800 10 1 2 3 90 0\ncpu0 0\ncpu1 0\nbtime 10\n')
        (root/'meminfo').write_text('MemTotal: 1000000 kB\nMemAvailable: 500000 kB\n')
        (root/'loadavg').write_text('0.1 0.2 0.3 1/10 4\n')
        fs=SimpleNamespace(f_blocks=100,f_frsize=4096,f_bavail=50,f_files=1000,f_favail=900)
        sample=vps.collect(self.tmp.name,proc=root,statvfs=lambda _:fs,clock=lambda:1000)
        self.assertEqual(sample['cores'],2);self.assertEqual(sample['cpu'],[100,0,10,800,10,1,2,3])
        self.assertEqual(sample['memory'],[1024000000,512000000]);self.assertEqual(sample['errors'],[])
        (root/'meminfo').write_text('MemTotal: 1 MB\nMemAvailable: 1 MB\n')
        (root/'stat').write_text('x'*65537)
        sample=vps.collect(self.tmp.name,proc=root,statvfs=lambda _:fs,clock=lambda:1000)
        self.assertIsNone(sample['memory']);self.assertIsNone(sample['cpu']);self.assertIn('cpu',sample['errors'])
        self.assertEqual(vps.assess(sample,None)[1]['telemetry'],'bad')

    def test_worker_routes_fixed_resource_job_and_memory_detects_mutated_source(self):
        ident=q.enqueue(self.conn,'control','inspect_repository',{'target':vps.TARGET})
        result=queue_worker.run_once(self.path)
        self.assertEqual(result,dict(id=ident,state='succeeded'))
        memory.sync(self.conn)
        mid=self.conn.execute('SELECT id FROM project_evidence_memory WHERE event_id IN (SELECT id FROM agent_job_events WHERE job_id=?) ORDER BY id DESC LIMIT 1',(ident,)).fetchone()[0]
        self.assertIn('resource_sample',memory.detail(self.conn,mid))
        self.conn.execute("UPDATE vps_resource_samples SET sample='{}' WHERE job_id=?",(ident,));self.conn.commit()
        self.assertIn('повторной проверки',memory.detail(self.conn,mid))

    def test_schedule_respects_pause_and_is_idempotent(self):
        vps.seed(self.conn,now=1000);vps.seed(self.conn,now=1001)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM agent_schedules WHERE name=?',(vps.SCHEDULE,)).fetchone()[0],1)
        self.conn.execute('UPDATE agent_queue_control SET paused=1');self.conn.commit()
        self.assertEqual(scheduler.tick(self.conn,now=1300),[])
        self.conn.execute('UPDATE agent_queue_control SET paused=0');self.conn.commit()
        self.assertEqual(len(scheduler.tick(self.conn,now=1300)),1)
        self.assertEqual(scheduler.tick(self.conn,now=1300),[])

    def test_missing_telemetry_alerts_without_resolving_existing_memory_incident(self):
        self.sample(memory_free=1);self.sample(1300,memory_free=1)
        for at in (1600,1900):
            sample=fixture(at+1);sample['memory']=None;sample['errors']=['memory']
            vps.complete(self.conn,self.job(at),sample,now=at+2)
        self.assertEqual(set(row[0] for row in self.conn.execute("SELECT metric FROM vps_resource_incidents WHERE state='open'")),{'memory','telemetry'})
        self.sample(2200);self.sample(2500)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM vps_resource_incidents WHERE state='open'").fetchone()[0],0)

    def test_superseded_observation_is_retained_without_advancing_or_closing_alert(self):
        self.sample(memory_free=1);self.sample(1300,memory_free=1)
        before=self.conn.execute('SELECT * FROM vps_resource_streaks').fetchall()
        job=self.job(1100)
        result=vps.complete(self.conn,job,fixture(1101),now=1102)
        report=json.loads(self.conn.execute('SELECT report FROM vps_resource_samples WHERE id=?',(result['resource_sample_id'],)).fetchone()[0])
        self.assertTrue(report['superseded'])
        self.assertEqual(self.conn.execute('SELECT * FROM vps_resource_streaks').fetchall(),before)
        self.assertEqual(self.conn.execute('SELECT state FROM vps_resource_incidents').fetchone()[0],'open')
