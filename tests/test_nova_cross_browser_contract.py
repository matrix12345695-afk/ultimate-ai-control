"""Reject promoted, incomplete or tampered cross-engine evidence without browsers."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('nova_cross_browser_contract',ROOT/'ci/nova-cross-browser/contract.py')
contract=importlib.util.module_from_spec(spec);spec.loader.exec_module(contract)


class CrossBrowserContractTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.folder=Path(self.temp.name)
        self.manifest_sha=hashlib.sha256((ROOT/'ci/nova-cross-browser/source-pins.json').read_bytes()).hexdigest()
        self.hashes=contract.harness_hashes(ROOT)
        self.report={'schema':contract.SCHEMA,'source_revision':contract.REVISION,
                     'source_manifest_sha256':self.manifest_sha,'harness_revision':'a'*40,
                     'harness_sha256':self.hashes,'engine':'chromium','browser_version':contract.ENGINES['chromium'],
                     'playwright_version':'1.62.0','counts':{'tests':34,'pass':34,'fail':0,'errors':0,'skipped':0},
                     'viewports':contract.VIEWPORTS,'screenshots':[], 'advisories':[],
                     'backend_mocked':True,'production_access':False,'page_network_intercepted':True,
                     'physical_device_test':False,'pixel_baseline_test':False,'published':False,'mobile_emulation':True}
        for name in contract.SHOTS:
            v=next(v for v in contract.VIEWPORTS if v in name);width,height=contract.VIEWPORTS[v]
            def chunk(kind,raw):
                return struct.pack('!I',len(raw))+kind+raw+struct.pack('!I',zlib.crc32(kind+raw))
            raw=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!IIBBBBB',width,height,8,2,0,0,0))
            raw+=chunk(b'IDAT',zlib.compress((b'\0'+b'\x80\x80\x80'*width)*height))+chunk(b'IEND',b'')
            (self.folder/name).write_bytes(raw)
            self.report['screenshots'].append({'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
        (self.folder/'report.json').write_text(json.dumps(self.report))

    def tearDown(self): self.temp.cleanup()

    def validate(self,report=None,engine='chromium'):
        return contract.validate(self.report if report is None else report,engine,self.manifest_sha,'a'*40,self.hashes)

    def test_each_engine_is_distinct_and_firefox_does_not_claim_mobile_emulation(self):
        for engine,version in contract.ENGINES.items():
            report=dict(self.report,engine=engine,browser_version=version,mobile_emulation=engine!='firefox')
            self.assertTrue(self.validate(report,engine))
            if engine=='firefox':
                with self.assertRaises(ValueError): self.validate(dict(report,mobile_emulation=True),engine)
        with self.assertRaises(ValueError): self.validate(engine='safari')

    def test_wrong_source_harness_engine_and_versions_are_rejected(self):
        for change in ({'source_revision':'b'*40},{'harness_revision':'b'*40},
                       {'source_manifest_sha256':'b'*64},{'harness_sha256':{}},
                       {'engine':'webkit'},{'browser_version':'unverified'},{'playwright_version':'latest'}):
            with self.subTest(change=change),self.assertRaises(ValueError): self.validate(dict(self.report,**change))

    def test_failure_skip_and_missing_counts_cannot_satisfy_gate(self):
        for counts in ({'tests':34,'pass':33,'fail':1,'errors':0,'skipped':0},
                       {'tests':34,'pass':33,'fail':0,'errors':0,'skipped':1},
                       {'tests':34,'pass':34,'fail':False,'errors':0,'skipped':0},{}):
            with self.subTest(counts=counts),self.assertRaises(ValueError): self.validate(dict(self.report,counts=counts))

    def test_scope_cannot_be_promoted_to_production_or_real_device(self):
        for key in ('production_access','published','physical_device_test','pixel_baseline_test'):
            with self.subTest(key=key),self.assertRaises(ValueError): self.validate(dict(self.report,**{key:True}))
        for key in ('backend_mocked','page_network_intercepted'):
            with self.subTest(key=key),self.assertRaises(ValueError): self.validate(dict(self.report,**{key:False}))

    def test_incomplete_malformed_or_changed_coverage_fails_closed(self):
        for shots in (None,[None],self.report['screenshots'][:-1],list(reversed(self.report['screenshots'])),
                      [dict(self.report['screenshots'][0],path='../escape')]+self.report['screenshots'][1:]):
            with self.subTest(shots=str(shots)[:60]),self.assertRaises(ValueError): self.validate(dict(self.report,screenshots=shots))
        for change in ({'viewports':{}},{'advisories':['known issue']}):
            with self.assertRaises(ValueError): self.validate(dict(self.report,**change))

    def test_exact_screenshots_pass_and_modified_missing_extra_or_symlink_files_fail(self):
        self.assertTrue(self.validate());contract.files(self.report,self.folder)
        target=self.folder/contract.SHOTS[0];original=target.read_bytes()
        target.write_bytes(original[:-1]+bytes([original[-1]^1]))
        with self.assertRaises(ValueError): contract.files(self.report,self.folder)
        target.unlink()
        with self.assertRaises(ValueError): contract.files(self.report,self.folder)
        target.write_bytes(original);extra=self.folder/'unexpected.txt';extra.write_text('extra')
        with self.assertRaises(ValueError): contract.files(self.report,self.folder)
        extra.unlink();target.unlink();target.symlink_to(self.folder/contract.SHOTS[1])
        with self.assertRaises(ValueError): contract.files(self.report,self.folder)

    def test_rehashed_wrong_dimensions_are_rejected(self):
        target=self.folder/contract.SHOTS[0];raw=bytearray(target.read_bytes());raw[16:20]=struct.pack('!I',1)
        target.write_bytes(raw);report=copy.deepcopy(self.report);report['screenshots'][0]['sha256']=hashlib.sha256(raw).hexdigest()
        with self.assertRaises(ValueError): contract.files(report,self.folder)

    def test_source_manifest_matches_reviewed_candidate_html_bytes(self):
        candidate=json.loads((ROOT/'ci/nova-browser-candidate/source-pins.json').read_text())
        self.assertEqual(json.loads((ROOT/'ci/nova-cross-browser/source-pins.json').read_text()),candidate)
        self.assertEqual(set(self.hashes),set(contract.HARNESS_FILES))


if __name__=='__main__': unittest.main()
