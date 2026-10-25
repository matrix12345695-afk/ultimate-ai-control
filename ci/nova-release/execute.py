"""Real loopback HTTP restarts baseline -> candidate -> baseline, same disposable PG."""
import hashlib
import http.client
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

HERE=Path(__file__).resolve().parent
URL='postgresql://postgres:postgres@127.0.0.1:15432/novaweb_test'
EXPECTED=15
BASE=None;CANDIDATE=None;NODE=None;OUTPUT=None
PROOF={};LOGS=[]


def request(path='/',method='GET',body=None):
    conn=http.client.HTTPConnection('127.0.0.1',18765,timeout=3)
    try:
        conn.request(method,path,body=body,headers={'Content-Type':'application/json'})
        response=conn.getresponse();raw=response.read(100001)
        assert len(raw)<=100000
        return response.status,dict(response.getheaders()),raw
    finally: conn.close()


def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


class Rehearsal(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.current=None;cls.before=None;cls.after=None
    @classmethod
    def tearDownClass(cls): cls.stop()
    @classmethod
    def stop(cls):
        if cls.current:
            proc,log=cls.current
            if proc.poll() is None: os.killpg(proc.pid,signal.SIGTERM)
            try: proc.wait(timeout=3)
            except subprocess.TimeoutExpired: os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=2)
            log.close();cls.current=None
    def env(self,root,broken=False):
        return {'PATH':os.environ['PATH'],'HOME':os.environ['HOME'],'LANG':'C.UTF-8',
                'DATABASE_URL':URL.replace('15432','15434') if broken else URL,
                'PORT':'18766' if broken else '18765','DATA_DIR':str(root/'data')}
    def launch(self,root,broken=False):
        log=tempfile.TemporaryFile();LOGS.append(log)
        proc=subprocess.Popen([NODE,'--require',str(HERE/'loopback-guard.cjs'),str(root/'server.js')],cwd=root,
            env=self.env(root,broken),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        return proc,log
    def start(self,root):
        self.stop();self.__class__.current=self.launch(root);proc,log=self.current
        until=time.monotonic()+12
        while time.monotonic()<until:
            if proc.poll() is not None: self.fail('Pinned NOVA server failed to start')
            try:
                if request('/health')[0]==200: return
            except (OSError,http.client.HTTPException): pass
            time.sleep(.1)
        self.fail('Pinned NOVA readiness timeout')
    def fixture(self,action='snapshot'):
        proc=subprocess.run([NODE,'--require',str(HERE/'loopback-guard.cjs'),str(HERE/'fixture.cjs'),action],cwd=BASE,
             env=self.env(BASE),stdin=subprocess.DEVNULL,capture_output=True,timeout=10)
        self.assertEqual(proc.returncode,0,'Fixture SQL failed');self.assertLess(len(proc.stdout),100000)
        result=json.loads(proc.stdout);self.assertEqual(result['postgres_major'],16);return result
    def home(self,root):
        code,headers,raw=request();self.assertEqual(code,200);self.assertEqual(raw,(root/'index.html').read_bytes())
        self.assertEqual(headers['X-Frame-Options'],'DENY');self.assertIn("connect-src 'self'",headers['Content-Security-Policy'])
        return hashlib.sha256(raw).hexdigest()
    def healthy(self):
        code,_,raw=request('/health');self.assertEqual(code,200)
        self.assertEqual(json.loads(raw),{'ok':True,'storage':'postgres','version':'sales-funnel-v1'})
        code,_,raw=request('/api/status');self.assertEqual(code,200);self.assertEqual(json.loads(raw),{'ordersEnabled':False})
    def denied(self):
        for path,body in [('/api/lead',json.dumps({'name':'Fixture','contact':'TEST_ONLY_NO_DELIVERY','consent':True,'type':'START'})),('/api/telegram/webhook','{}')]:
            code,_,raw=request(path,'POST',body);self.assertEqual(code,503 if path=='/api/lead' else 403);self.assertIs(json.loads(raw)['ok'],False)
    def test_01_exact_source_difference(self):
        paths=[p.relative_to(BASE) for p in BASE.rglob('*') if p.is_file() and 'node_modules' not in p.parts]
        changed=[str(p) for p in paths if (BASE/p).read_bytes()!=(CANDIDATE/p).read_bytes()]
        self.assertEqual(changed,['index.html']);PROOF['source_diff_only_index']=True
    def test_02_baseline_boot_home(self):
        self.start(BASE);PROOF['baseline_home_sha256']=self.home(BASE)
    def test_03_baseline_readiness(self): self.healthy()
    def test_04_seed_postgres_fixture(self):
        self.__class__.before=self.fixture('baseline');self.assertTrue(any(row['id']=='NWREHEARSAL001' for row in self.before['rows']['nova_leads']))
        PROOF['before_data_sha256']=digest(self.before)
    def test_05_baseline_write_guards(self): self.denied();self.assertEqual(self.fixture(),self.before)
    def test_06_failed_candidate_keeps_baseline(self):
        proc,log=self.launch(CANDIDATE,broken=True)
        try:
            self.assertNotEqual(proc.wait(timeout=10),0)
            conn=http.client.HTTPConnection('127.0.0.1',18766,timeout=1)
            try:
                with self.assertRaises((OSError,http.client.HTTPException)): conn.request('GET','/health');conn.getresponse()
            finally: conn.close()
            self.assertEqual(self.home(BASE),PROOF['baseline_home_sha256']);self.healthy();self.assertEqual(self.fixture(),self.before)
            PROOF['failed_candidate_not_promoted']=True
        finally:
            if proc.poll() is None: os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=2)
            log.close()
    def test_07_candidate_boot_home(self):
        self.start(CANDIDATE);PROOF['candidate_home_sha256']=self.home(CANDIDATE)
        self.assertNotEqual(PROOF['baseline_home_sha256'],PROOF['candidate_home_sha256'])
    def test_08_candidate_readiness_and_static_routes(self):
        self.healthy()
        for path,name in [('/demo/beauty','showcase.html'),('/demo/estate','showcase.html'),('/demo/cafe','showcase.html'),('/robots.txt','robots.txt'),('/sitemap.xml','sitemap.xml')]:
            code,_,raw=request(path);self.assertEqual(code,200);self.assertEqual(raw,(CANDIDATE/name).read_bytes())
    def test_09_preserved_on_upgrade(self): self.assertEqual(self.fixture(),self.before);PROOF['upgrade_preserved_all_tables']=True
    def test_10_candidate_era_fixture_write(self):
        self.__class__.after=self.fixture('candidate')
        for table,old in self.before['rows'].items():
            self.assertEqual(len(self.after['rows'][table]),len(old)+1)
            for row in old: self.assertIn(row,self.after['rows'][table])
        PROOF['after_data_sha256']=digest(self.after)
    def test_11_candidate_write_guards(self): self.denied();self.assertEqual(self.fixture(),self.after)
    def test_12_rollback_home(self):
        self.start(BASE);self.assertEqual(self.home(BASE),PROOF['baseline_home_sha256']);PROOF['rollback_html_restored']=True
    def test_13_rollback_readiness(self): self.healthy()
    def test_14_rollback_preserves_candidate_era_data(self):
        self.assertEqual(self.fixture(),self.after);PROOF['rollback_preserved_all_tables']=True
        PROOF['final_table_counts']={key:len(value) for key,value in self.after['rows'].items()}
    def test_15_rollback_write_guards(self): self.denied();self.assertEqual(self.fixture(),self.after)


def main():
    global BASE,CANDIDATE,NODE,OUTPUT
    BASE,CANDIDATE,OUTPUT=map(Path,sys.argv[1:4]);NODE=sys.argv[4]
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Rehearsal);assert suite.countTestCases()==EXPECTED
    result=unittest.TextTestRunner(verbosity=2,failfast=True).run(suite)
    report={'schema':'nova-release-rehearsal-v1','base_revision':'1a23239a0a9c7d79905c91505a8741d8350d7e75',
            'candidate_revision':'495a7f1a1a3a25c45fd98101fffa9c02e58f3970','counts':{'tests':result.testsRun,'pass':result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),'fail':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped)},
            'proof':PROOF,'postgres_major':16,'real_http':True,'fixture_data_only':True,'loopback_only':True,
            'render_api_rollback_executed':False,'production_access':False,'published':False,'database_restored':False}
    OUTPUT.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps(report,sort_keys=True),flush=True)
    return 0 if result.wasSuccessful() and result.testsRun==EXPECTED else 1


if __name__=='__main__': raise SystemExit(main())
