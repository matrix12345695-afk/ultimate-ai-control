import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch
import acceptance_checks as acceptance
import artifact_recovery
import main
import offline_developer
import queue_worker
import recipe_acceptance as recipes
import task_queue as queue
import telegram_menu
from isolated_python import manifest,run_bundle


def report(files,status='passed'):
    return {'status':status,'source_digest':manifest(files)[1],'elapsed_seconds':0.01,
            'backend':'fake-test-only','writable_tmp':False,'output':'artificial fixture'}


class RecipeAcceptanceTests(unittest.TestCase):
    def files(self,recipe='safe-paths'): return offline_developer.recipe_files(recipe,1)

    def test_only_selected_source_and_first_party_harness_enter_acceptance_namespace(self):
        for recipe,profile in recipes.RECIPE_PROFILES.items():
            files=self.files(recipe)
            files.update({'unittest.py':'raise RuntimeError("candidate shadow")','proposals/__init__.py':'raise RuntimeError("candidate initializer")'})
            calls=[]
            def runner(bundle,policy,**kwargs): calls.append((bundle,kwargs));return report(bundle)
            result=acceptance.check(files,'unused',profile,runner=runner)
            self.assertEqual(result['status'],'passed')
            self.assertEqual(set(calls[0][0]),{'acceptance_candidate.py','tests/test_owner_acceptance.py'})
            self.assertEqual(calls[0][0]['tests/test_owner_acceptance.py'],recipes.spec(profile)['tests'])
            self.assertEqual(calls[0][1],{'timeout':8})
            self.assertEqual(result['candidate_source_digest'],manifest(files)[1])
            self.assertEqual(result['harness_sha256'],recipes.harness_sha256(profile))

    def test_import_side_effect_assignment_dunder_wrong_signature_and_ambiguous_source_never_run(self):
        profile=recipes.RECIPE_PROFILES['safe-paths'];files=self.files();path=next(name for name in files if name.startswith('proposals/'))
        original=files[path]
        bad=[original+'\nimport os\n',original+'\nprint("side effect")\n',original.replace('value.split("/")','value.__class__()'),
             original.replace('safe_review_path(value)','safe_review_path(value=None)'),
             original.replace('    if not isinstance','    re = None\n    if not isinstance'),
             original.replace('import re','import re as unittest')]
        runner=Mock(side_effect=AssertionError('unreviewed source must not execute'))
        for source in bad:
            self.assertEqual(acceptance.check(dict(files,**{path:source}),'unused',profile,runner=runner)['status'],'failed')
        files['proposals/review_safe_paths_'+'0'*16+'.py']=original
        self.assertEqual(acceptance.check(files,'unused',profile,runner=runner)['status'],'failed')
        runner.assert_not_called()

    def test_profiles_cannot_be_chosen_by_general_model_output_or_interchanged(self):
        self.assertFalse(acceptance.allowed_profile('openai_broker',recipes.RECIPE_PROFILES['safe-paths']))
        self.assertFalse(acceptance.allowed_profile('offline_broker_demo',recipes.RECIPE_PROFILES['sha-check']))
        result=acceptance.check(self.files('sha-check'),'unused',recipes.RECIPE_PROFILES['safe-paths'],runner=Mock(side_effect=AssertionError()))
        self.assertEqual(result['status'],'failed')
        with self.assertRaises(ValueError): acceptance.harness_sha256('unknown')

    def test_both_reports_bind_their_own_digests_and_failed_acceptance_keeps_worker_failed(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);db=root/'control.db';calls=[]
            with queue_worker.connect(db) as conn:
                queue_worker.initialize(conn);ident=queue.enqueue(conn,'control','review_change',{'recipe':'sha-check'})
            original=offline_developer.prepare
            def runner(files,policy,**kwargs):
                calls.append(files);return report(files,'passed' if len(calls)==1 else 'failed')
            with patch.object(offline_developer,'prepare',side_effect=lambda c,j,*a:original(c,j,*a,runner=runner)):
                self.assertEqual(queue_worker.run_once(db),{'id':ident,'state':'failed'})
            with queue_worker.connect(db) as conn:
                saved=json.loads(conn.execute('SELECT test_report FROM code_artifacts').fetchone()[0])
                self.assertEqual(saved['candidate_test_status'],'passed')
                self.assertEqual(saved['independent_acceptance']['status'],'failed')
                self.assertEqual(conn.execute('SELECT kind FROM owner_notifications').fetchone()[0],'critical')
                self.assertEqual(conn.execute('SELECT count(*) FROM provider_costs').fetchone()[0],0)

    def test_candidate_failure_skips_acceptance_and_unknown_test_digest_is_rejected(self):
        with tempfile.TemporaryDirectory() as name,queue_worker.connect(Path(name)/'control.db') as conn:
            queue_worker.initialize(conn);job={'id':1,'attempt':1,'project':'control','payload':{'recipe':'safe-paths'}};calls=[]
            def runner(files,policy,**kwargs): calls.append(files);return report(files,'failed')
            result=offline_developer.prepare(conn,job,Path(name)/'artifacts','unused',runner=runner)
            self.assertEqual(result['test_status'],'failed');self.assertEqual(len(calls),1)
            saved=json.loads(conn.execute('SELECT test_report FROM code_artifacts').fetchone()[0])
            self.assertEqual(saved['independent_acceptance']['status'],'not_run')
        def wrong(files,policy,**kwargs): return dict(report(files),source_digest='0'*64)
        with self.assertRaises(ValueError): acceptance.check(self.files(),'unused',recipes.RECIPE_PROFILES['safe-paths'],runner=wrong)

    def test_recovery_reuses_complete_contract_and_refuses_changed_harness_without_retesting(self):
        with tempfile.TemporaryDirectory() as name,queue_worker.connect(Path(name)/'control.db') as conn:
            queue_worker.initialize(conn);job={'id':1,'attempt':1,'project':'control','payload':{'recipe':'sha-check'}};root=Path(name)/'artifacts'
            first=offline_developer.prepare(conn,job,root,'unused',runner=lambda f,p,**k:report(f))
            replay=offline_developer.prepare(conn,dict(job,attempt=2),root,'unused',runner=Mock(side_effect=AssertionError()))
            self.assertEqual(first['artifact_id'],replay['artifact_id']);self.assertTrue(replay['tests_reused'])
            profile=recipes.RECIPE_PROFILES['sha-check'];changed=dict(recipes.SPECS[profile],tests=recipes.COMMIT_TESTS+'\n# changed requirements\n')
            with patch.dict(recipes.SPECS,{profile:changed}):
                with self.assertRaisesRegex(artifact_recovery.ArtifactRecoveryBlocked,'harness changed'):
                    offline_developer.prepare(conn,dict(job,attempt=3),root,'unused',runner=Mock(side_effect=AssertionError()))

    def test_legacy_artifacts_are_not_retroactively_assigned_contracts_and_catalog_is_read_only(self):
        with tempfile.TemporaryDirectory() as name,queue_worker.connect(Path(name)/'control.db') as conn:
            queue_worker.initialize(conn);job={'id':1,'attempt':1,'project':'control','payload':{'recipe':'safe-paths'}}
            files=self.files();root=Path(name)/'artifacts'
            offline_developer.prepare_files(conn,job,root,'unused',files,engine='deterministic_recipe',runner=lambda f,p:report(f))
            before=conn.total_changes;text=acceptance.describe(conn)
            self.assertIn('Прошли артефактов: 0',text);self.assertEqual(conn.total_changes,before)
            with self.assertRaisesRegex(artifact_recovery.ArtifactRecoveryBlocked,'contract changed'):
                offline_developer.prepare(conn,dict(job,attempt=2),root,'unused',runner=Mock(side_effect=AssertionError()))
            with patch.object(main,'DB',Path(name)/'control.db'):
                self.assertIn('Независимая приёмка',main.command('/acceptance4'))
            self.assertEqual(telegram_menu.route('🧪 Приёмка'),'/acceptance4')


@unittest.skipUnless(os.getenv('UAC_SANDBOX_TEST_BINARY'),'explicit sandbox integration binary required')
class RealRecipeContracts(unittest.TestCase):
    def run_contract(self,recipe,wrong_expression):
        binary=Path(os.environ['UAC_SANDBOX_TEST_BINARY']).resolve()
        with tempfile.TemporaryDirectory() as name:
            policy=Path(name)/'policy.json';policy.write_text(json.dumps({'enabled':True,'backend':'bubblewrap-v1','binary':str(binary),'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest()}));policy.chmod(0o600)
            files=offline_developer.recipe_files(recipe,1);profile=recipes.RECIPE_PROFILES[recipe]
            good=acceptance.check(files,policy,profile)
            self.assertEqual(good['status'],'passed',good.get('output'));self.assertIn('Ran 8 tests',good['output'])
            path=next(name for name in files if name.startswith('proposals/'));source=files[path]
            head=source.split('def ',1)[0];signature=source.split('def ',1)[1].split(':',1)[0]
            mutants=[head+'def '+signature+':\n    return '+wrong_expression+'\n']
            mutants.append(source.replace('return not any(part in value.lower() for part in _BLOCKED)','return True') if recipe=='safe-paths' else source.replace('[0-9a-f]','[0-9a-fA-F]'))
            for mutant in mutants:
                self.assertNotEqual(mutant,source)
                changed={path:mutant,'tests/test_lying.py':'import unittest\nclass LyingTests(unittest.TestCase):\n    def test_claim(self): self.assertTrue(True)\n'}
                self.assertEqual(run_bundle(changed,policy,timeout=8)['status'],'passed')
                bad=acceptance.check(changed,policy,profile)
                self.assertEqual(bad['status'],'failed',bad.get('output'));self.assertIn('FAILED',bad['output'])
    def test_safe_path_contract_rejects_always_allow_with_passing_candidate_tests(self): self.run_contract('safe-paths','True')
    def test_git_commit_contract_rejects_nonhex_length_only_with_passing_candidate_tests(self): self.run_contract('sha-check','isinstance(value, str) and bool(value)')
