"""Credential-free test child; exact local HTML, intercepted APIs, one engine."""
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import sys
import unittest
import contract

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'nova-browser-candidate'))
import browser_candidate as candidate
suite=candidate.base


def main():
    source,output,engine,revision=sys.argv[1:]
    if engine not in contract.ENGINES: raise ValueError('Unknown engine')
    class CrossBrowserTests(candidate.CandidateTests):
        ENGINE=engine
    suite.SOURCE=Path(source);suite.OUTPUT=Path(output)
    tests=unittest.defaultTestLoader.loadTestsFromTestCase(CrossBrowserTests)
    if tests.countTestCases()!=34: raise ValueError('Unexpected test discovery')
    result=unittest.TextTestRunner(verbosity=2).run(tests)
    shots=[]
    for path in sorted(suite.OUTPUT.glob('*.png')):
        raw=path.read_bytes()
        shots.append({'path':path.name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    report={'schema':contract.SCHEMA,'source_revision':contract.REVISION,
            'source_manifest_sha256':hashlib.sha256(Path(__file__).with_name('source-pins.json').read_bytes()).hexdigest(),
            'harness_revision':revision,'harness_sha256':contract.harness_hashes(Path(__file__).resolve().parents[2]),
            'engine':engine,'browser_version':suite.BROWSER_VERSION,'playwright_version':version('playwright'),
            'counts':{'tests':result.testsRun,'pass':result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),
                      'fail':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped)},
            'viewports':contract.VIEWPORTS,'screenshots':shots,'advisories':sorted(suite.ADVISORIES),
            'backend_mocked':True,'production_access':False,'page_network_intercepted':True,
            'physical_device_test':False,'pixel_baseline_test':False,'published':False,
            'mobile_emulation':engine!='firefox'}
    (suite.OUTPUT/'report.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__': raise SystemExit(main())
