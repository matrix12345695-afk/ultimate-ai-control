"""Reuse15 real HTTP/PG transition checks, with explicit approved build config diff."""
from pathlib import Path
import importlib.util,json,sys,unittest
spec=importlib.util.spec_from_file_location('original_rehearsal',Path(__file__).resolve().parents[1]/'nova-release/execute.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)


class LockedRehearsal(base.Rehearsal):
    def test_01_exact_source_difference(self):
        pins=json.loads(Path(__file__).with_name('source-pins.json').read_text())
        paths=set(row[0] for row in pins['baseline'])|set(row[0] for row in pins['candidate'])
        changed=[]
        for name in sorted(paths):
            left,right=base.BASE/name,base.CANDIDATE/name
            if not left.exists() or not right.exists() or left.read_bytes()!=right.read_bytes(): changed.append(name)
        self.assertEqual(changed,['.github/workflows/checks.yml','.node-version','.npmrc','index.html','package-lock.json','package.json','render.yaml'])
        base.PROOF['source_diff_only_approved_build_config']=True


def main():
    base.BASE,base.CANDIDATE,base.OUTPUT=map(Path,sys.argv[1:4]);base.NODE=sys.argv[4]
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(LockedRehearsal);assert suite.countTestCases()==15
    result=unittest.TextTestRunner(verbosity=2,failfast=True).run(suite)
    report={'schema':'nova-locked-rehearsal-v1','candidate_revision':'a3c3e77e0e74d33241935d25dd3bdfdd306ccd90',
            'counts':{'tests':result.testsRun,'pass':result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),'fail':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped)},
            'proof':base.PROOF,'postgres_major':16,'real_http':True,'fixture_data_only':True,'loopback_only':True,
            'Render_rollback_executed':False,'production_access':False,'published':False,'database_restored':False}
    base.OUTPUT.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps(report,sort_keys=True))
    return not result.wasSuccessful()


if __name__=='__main__': raise SystemExit(main())
