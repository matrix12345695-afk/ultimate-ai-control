"""Browser-only child: receives fixture HTML paths and an empty output directory."""
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import sys
import unittest
import browser_candidate as candidate
suite=candidate.base


def main():
    suite.SOURCE=Path(sys.argv[1]);suite.OUTPUT=Path(sys.argv[2]);suite.OUTPUT.mkdir(exist_ok=True)
    tests=unittest.defaultTestLoader.loadTestsFromTestCase(candidate.CandidateTests)
    assert tests.countTestCases()==candidate.EXPECTED_TESTS
    result=unittest.TextTestRunner(verbosity=2).run(tests)
    screenshots=[]
    for path in sorted(suite.OUTPUT.glob('*.png')):
        raw=path.read_bytes()
        screenshots.append({'path':path.name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    report={'schema':'nova-browser-candidate-v1','source_revision':'90f60bdaead95b65857dd0a19a905f43cf8658ef',
            'source_manifest_sha256':hashlib.sha256(Path(__file__).with_name('source-pins.json').read_bytes()).hexdigest(),
            'engine':'chromium','browser_version':suite.BROWSER_VERSION,'playwright_version':version('playwright'),
            'counts':{'tests':result.testsRun,'pass':result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),
                      'fail':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped)},
            'viewports':{key:list(value) for key,value in suite.VIEWPORTS.items()},'screenshots':screenshots,
            'advisories':sorted(suite.ADVISORIES),'backend_mocked':True,'production_access':False,
            'page_network_intercepted':True,'physical_device_test':False,'pixel_baseline_test':False,'published':False}
    (suite.OUTPUT/'report.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__': raise SystemExit(main())
