"""Same34 browser regressions, exact locked-build HTML; fixture API only."""
from pathlib import Path
import sys,hashlib,json,unittest
from importlib.metadata import version
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'nova-browser-candidate'))
import browser_candidate as candidate
import browser_suite as base


def main():
    base.SOURCE=Path(sys.argv[1]);base.OUTPUT=Path(sys.argv[2]);base.OUTPUT.mkdir()
    tests=unittest.defaultTestLoader.loadTestsFromTestCase(candidate.CandidateTests);assert tests.countTestCases()==34
    result=unittest.TextTestRunner(verbosity=2).run(tests)
    rows=[]
    for path in sorted(base.OUTPUT.glob('*.png')):
        raw=path.read_bytes();rows.append({'path':path.name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    report={'schema':'nova-locked-browser-v1','source_revision':'a3c3e77e0e74d33241935d25dd3bdfdd306ccd90',
            'browser_version':base.BROWSER_VERSION,'playwright_version':version('playwright'),
            'counts':{'tests':result.testsRun,'pass':result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),'fail':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped)},
            'viewports':{k:list(v) for k,v in base.VIEWPORTS.items()},'screenshots':rows,'advisories':sorted(base.ADVISORIES),
            'backend_mocked':True,'production_access':False,'published':False}
    (base.OUTPUT/'report.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'counts':report['counts'],'browser':base.BROWSER_VERSION,'screenshots':len(rows),'advisories':report['advisories']}))
    return not result.wasSuccessful()


if __name__=='__main__': raise SystemExit(main())
