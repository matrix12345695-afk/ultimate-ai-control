"""Reviewed acceptance contracts for the offline demo and two fixed code recipes.

Candidate tests never enter this second sandbox. A narrow pure-function AST contract
prevents the candidate from replacing unittest or the harness. This is not a general grader.
"""
import ast
import hashlib
import recipe_acceptance
from isolated_python import manifest,run_bundle

PROFILE='bounded-percent-v1'
TESTS='''import unittest
from draft_component import bounded_percent

class OwnerProgressContract(unittest.TestCase):
    def test_zero(self):
        for total in (1,3,7,1000): self.assertEqual(bounded_percent(0,total),0)
    def test_exact_and_floor(self):
        for done,total,want in ((1,3,33),(2,3,66),(1,8,12),(7,8,87),(1,1000,0),(999,1000,99)):
            self.assertEqual(bounded_percent(done,total),want)
    def test_complete_and_cap(self):
        for done,total in ((1,1),(7,7),(8,7),(1000,1)):
            self.assertEqual(bounded_percent(done,total),100)
    def test_large_integers(self):
        self.assertEqual(bounded_percent(10**60,3*10**60),33)
    def test_negative_or_zero_bounds(self):
        for done,total in ((-1,3),(1,0),(1,-3),(0,0)):
            with self.assertRaises(ValueError): bounded_percent(done,total)
    def test_strict_integer_inputs(self):
        for value in (True,False,None,'1',1.0,[],{}):
            for pair in ((value,3),(1,value)):
                with self.assertRaises(ValueError): bounded_percent(*pair)
    def test_range_and_monotonicity(self):
        for total in (1,2,7,31):
            values=[bounded_percent(done,total) for done in range(2*total+1)]
            self.assertEqual(values,sorted(values))
            self.assertTrue(all(type(value) is int and 0<=value<=100 for value in values))
'''
HARNESS_SHA256=hashlib.sha256(TESTS.encode()).hexdigest()
RECIPE_PROFILES=recipe_acceptance.RECIPE_PROFILES


def harness_sha256(profile):
    return HARNESS_SHA256 if profile==PROFILE else recipe_acceptance.harness_sha256(profile)


def allowed_profile(engine,profile):
    return (profile is None or (engine=='offline_broker_demo' and profile==PROFILE) or
            (engine=='deterministic_recipe' and profile in RECIPE_PROFILES.values()))


def describe(conn):
    import json
    profiles={PROFILE:('Расчёт процентов · демонстрация',7),
              RECIPE_PROFILES['safe-paths']:('Безопасные пути файлов',8),
              RECIPE_PROFILES['sha-check']:('Полный Git commit SHA',8)}
    counts={name:0 for name in profiles}
    for raw, in conn.execute("SELECT test_report FROM code_artifacts WHERE test_status='passed'"):
        try: checks=json.loads(raw).get('independent_acceptance',{})
        except (TypeError,ValueError,AttributeError): continue
        if not isinstance(checks,dict): continue
        profile=checks.get('profile')
        if (profile in profiles and checks.get('status')=='passed' and
                checks.get('harness_sha256')==harness_sha256(profile)):
            counts[profile]+=1
    lines=['🧪 Независимая приёмка ULTIMATE']
    for profile,(label,tests) in profiles.items():
        lines.append(f'{label}: {profile}\nПроверок требований: {tests}. Прошли артефактов: {counts[profile]}.\nSHA-256 набора: {harness_sha256(profile)}')
    lines.append('Тесты черновика и требования проверяются раздельно. Ошибка любого обязательного этапа блокирует готовность. Старым артефактам новые проверки не приписываются.')
    lines.append('Это проверенные контракты отдельных Python-рецептов, не приёмка произвольной задачи. Публикация требует отдельного согласования.')
    return '\n\n'.join(lines)


def candidate_source(files):
    source=files.get('draft_component.py')
    if not isinstance(source,str): raise ValueError('acceptance_component_missing')
    tree=ast.parse(source)
    if len(tree.body)!=1 or not isinstance(tree.body[0],ast.FunctionDef):
        raise ValueError('acceptance_requires_one_pure_function')
    fn=tree.body[0];args=fn.args
    if (fn.name!='bounded_percent' or [a.arg for a in args.args]!=['done','total'] or
        args.posonlyargs or args.kwonlyargs or args.vararg or args.kwarg or args.defaults or args.kw_defaults or
        fn.decorator_list or fn.returns or fn.type_comment or getattr(fn,'type_params',[]) or
        any(a.annotation for a in args.args)):
        raise ValueError('acceptance_function_signature')
    allowed=(ast.Module,ast.FunctionDef,ast.arguments,ast.arg,ast.If,ast.Compare,ast.Name,ast.Load,
             ast.IsNot,ast.Is,ast.Lt,ast.LtE,ast.Gt,ast.GtE,ast.Eq,ast.NotEq,ast.Or,ast.And,
             ast.BoolOp,ast.Raise,ast.Call,ast.Constant,ast.Return,ast.BinOp,ast.Mult,ast.FloorDiv,
             ast.Add,ast.Sub,ast.Mod,ast.UnaryOp,ast.USub,ast.Not)
    for node in ast.walk(tree):
        if not isinstance(node,allowed): raise ValueError('acceptance_source_outside_contract')
        if isinstance(node,ast.FunctionDef) and node is not fn: raise ValueError('acceptance_nested_function')
        if isinstance(node,ast.Name) and node.id not in {'done','total','type','int','ValueError','min','max'}:
            raise ValueError('acceptance_source_name')
        if isinstance(node,ast.Call) and (not isinstance(node.func,ast.Name) or node.func.id not in {'type','ValueError','min','max'} or node.keywords):
            raise ValueError('acceptance_source_call')
    return source


def check(files,policy,profile,runner=run_bundle):
    digest=harness_sha256(profile)
    result={'profile':profile,'harness_sha256':digest,'candidate_source_digest':manifest(files)[1]}
    try: source=candidate_source(files) if profile==PROFILE else recipe_acceptance.candidate_source(files,profile)
    except (ValueError,SyntaxError) as exc:
        return dict(result,status='failed',reason=str(exc) if isinstance(exc,ValueError) else 'acceptance_source_syntax',elapsed_seconds=0)
    bundle=({'draft_component.py':source,'tests/test_owner_acceptance.py':TESTS} if profile==PROFILE else
            {'acceptance_candidate.py':source,'tests/test_owner_acceptance.py':recipe_acceptance.spec(profile)['tests']})
    report=runner(bundle,policy,timeout=8)
    if report.get('source_digest')!=manifest(bundle)[1]: raise ValueError('acceptance_report_digest_mismatch')
    return dict(report,**result)
