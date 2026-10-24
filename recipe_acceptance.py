"""First-party behavioral contracts for the two reviewed offline code recipes.

Only one AST-checked helper enters the acceptance namespace. Candidate tests,
package initializers and shadow modules never enter it. This is not a general grader.
"""
import ast
import hashlib
import re

RECIPE_PROFILES={'safe-paths':'review-path-v1','sha-check':'git-commit-v1'}
PATH_TESTS='''import unittest
from acceptance_candidate import safe_review_path

class ReviewPathContract(unittest.TestCase):
    def test_allowed_namespaces(self):
        for value in ('docs/a.md','tests/test_case_9.py','proposals/nested/new-feature.py','docs/a_b/c.d'):
            self.assertIs(safe_review_path(value),True,value)
    def test_forbidden_roots(self):
        for value in ('src/main.py','/etc/passwd','README.md','../docs/a.md','Docs/a.md','C:/docs/a.md'):
            self.assertIs(safe_review_path(value),False,value)
    def test_traversal_components(self):
        for value in ('docs/../a.md','tests/a/../../b.py','proposals/./a.py','docs/.','docs/..'):
            self.assertIs(safe_review_path(value),False,value)
    def test_empty_components_and_windows_separators(self):
        for value in ('docs//a.md','tests/a/','proposals/','docs/a\\\\b.py'):
            self.assertIs(safe_review_path(value),False,value)
    def test_sensitive_substrings_case_insensitive(self):
        for value in ('docs/.env','tests/CREDENTIALS.py','proposals/Secret.txt','docs/tokenizer.md','docs/a/.ENV.local'):
            self.assertIs(safe_review_path(value),False,value)
    def test_suffix_length_bound(self):
        for prefix in ('docs/','tests/','proposals/'):
            self.assertIs(safe_review_path(prefix+'a'*120),True)
            self.assertIs(safe_review_path(prefix+'a'*121),False)
    def test_wrong_types(self):
        for value in (None,True,False,0,3.1,[],{},b'docs/a.md'):
            self.assertIs(safe_review_path(value),False)
    def test_ascii_and_full_string_boundary(self):
        for value in ('docs/a.md\\n','docs/a b.md','docs/%2e%2e/a','docs/файл.md','docs/a\\x00.md','docs/a?b.md'):
            self.assertIs(safe_review_path(value),False,value)
'''
COMMIT_TESTS='''import unittest
from acceptance_candidate import is_git_commit

class GitCommitContract(unittest.TestCase):
    def test_full_canonical_sha(self):
        self.assertIs(is_git_commit('0123456789abcdef'*2+'12345678'),True)
    def test_each_hex_character(self):
        for value in '0123456789abcdef': self.assertIs(is_git_commit(value*40),True)
    def test_exact_length(self):
        for size in (0,1,7,39,41,64): self.assertIs(is_git_commit('a'*size),False)
    def test_lowercase_only(self):
        for value in ('A'*40,'a'*39+'B','G'*40): self.assertIs(is_git_commit(value),False)
    def test_no_whitespace(self):
        for value in ('a'*40+'\\n',' '+'a'*40,'a'*39+'\\t','\\r'+'a'*40): self.assertIs(is_git_commit(value),False)
    def test_non_hex_and_unicode(self):
        for value in ('z'*40,'0'*39+'x','０'*40,'٠'*40,'-1'*20): self.assertIs(is_git_commit(value),False)
    def test_wrong_types(self):
        for value in (None,True,False,40,1.2,[],{},b'a'*40): self.assertIs(is_git_commit(value),False)
    def test_not_a_path_or_ref(self):
        for value in ('../'+'a'*40,'refs/heads/main','sha:'+'a'*40,'a'*20+'/'+ 'a'*20): self.assertIs(is_git_commit(value),False)
'''
SPECS={
    'review-path-v1':{'function':'safe_review_path','module':'review_safe_paths',
                      'globals':{'_PATH','_BLOCKED'},'regex':'_PATH','tests':PATH_TESTS},
    'git-commit-v1':{'function':'is_git_commit','module':'review_sha_check',
                     'globals':{'_COMMIT'},'regex':'_COMMIT','tests':COMMIT_TESTS}}


def spec(profile):
    if profile not in SPECS: raise ValueError('unknown_acceptance_profile')
    return SPECS[profile]


def harness_sha256(profile):
    return hashlib.sha256(spec(profile)['tests'].encode()).hexdigest()


def candidate_source(files,profile):
    cfg=spec(profile)
    candidates=[name for name in files if re.fullmatch(r'proposals/'+cfg['module']+r'_[0-9a-f]{16}\.py',name)]
    if len(candidates)!=1: raise ValueError('acceptance_recipe_component_missing_or_ambiguous')
    source=files[candidates[0]]
    if not isinstance(source,str): raise ValueError('acceptance_recipe_source_type')
    tree=ast.parse(source)
    body=list(tree.body)
    if body and isinstance(body[0],ast.Expr) and isinstance(body[0].value,ast.Constant) and isinstance(body[0].value.value,str): body.pop(0)
    imports=[node for node in body if isinstance(node,ast.Import)]
    functions=[node for node in body if isinstance(node,ast.FunctionDef)]
    assignments=[node for node in body if isinstance(node,ast.Assign)]
    if (len(body)!=len(cfg['globals'])+2 or len(imports)!=1 or len(functions)!=1 or len(assignments)!=len(cfg['globals']) or
            len(imports[0].names)!=1 or imports[0].names[0].name!='re' or imports[0].names[0].asname):
        raise ValueError('acceptance_recipe_module_shape')
    names=set()
    for assignment in assignments:
        if len(assignment.targets)!=1 or not isinstance(assignment.targets[0],ast.Name): raise ValueError('acceptance_recipe_globals')
        name=assignment.targets[0].id;names.add(name);value=assignment.value
        if name==cfg['regex']:
            if (not isinstance(value,ast.Call) or not isinstance(value.func,ast.Attribute) or
                    not isinstance(value.func.value,ast.Name) or value.func.value.id!='re' or value.func.attr!='compile' or
                    len(value.args)!=1 or value.keywords or not isinstance(value.args[0],ast.Constant) or
                    not isinstance(value.args[0].value,str) or not 1<=len(value.args[0].value)<=512):
                raise ValueError('acceptance_recipe_regex')
        elif name=='_BLOCKED':
            if not isinstance(value,ast.Tuple) or not 1<=len(value.elts)<=8 or any(not isinstance(v,ast.Constant) or not isinstance(v.value,str) or not 1<=len(v.value)<=40 for v in value.elts):
                raise ValueError('acceptance_recipe_blocked_words')
        else: raise ValueError('acceptance_recipe_globals')
    if names!=cfg['globals']: raise ValueError('acceptance_recipe_globals')
    fn=functions[0];args=fn.args
    if (fn.name!=cfg['function'] or [a.arg for a in args.args]!=['value'] or
            args.posonlyargs or args.kwonlyargs or args.vararg or args.kwarg or args.defaults or args.kw_defaults or
            fn.decorator_list or fn.returns or fn.type_comment or getattr(fn,'type_params',[]) or args.args[0].annotation):
        raise ValueError('acceptance_recipe_signature')
    allowed=(ast.Module,ast.Expr,ast.Constant,ast.Import,ast.alias,ast.Assign,ast.Name,ast.Load,ast.Store,
             ast.FunctionDef,ast.arguments,ast.arg,ast.If,ast.Return,ast.BoolOp,ast.And,ast.Or,
             ast.UnaryOp,ast.Not,ast.Compare,ast.In,ast.NotIn,ast.Eq,ast.NotEq,ast.Tuple,
             ast.Call,ast.Attribute,ast.GeneratorExp,ast.comprehension)
    known={'re','value','part','str','isinstance','bool','any'}|cfg['globals']
    for node in ast.walk(tree):
        if not isinstance(node,allowed): raise ValueError('acceptance_recipe_source_outside_contract')
        if isinstance(node,ast.FunctionDef) and node is not fn: raise ValueError('acceptance_recipe_nested_function')
        if isinstance(node,ast.Import) and node is not imports[0]: raise ValueError('acceptance_recipe_import')
        if isinstance(node,ast.Assign) and node not in assignments: raise ValueError('acceptance_recipe_assignment')
        if isinstance(node,ast.Name) and node.id not in known: raise ValueError('acceptance_recipe_name')
        if isinstance(node,ast.Attribute):
            if not isinstance(node.value,ast.Name): raise ValueError('acceptance_recipe_attribute')
            if (node.value.id,node.attr) not in {('re','compile'),(cfg['regex'],'fullmatch'),('value','split'),('value','lower')}:
                raise ValueError('acceptance_recipe_attribute')
        if isinstance(node,ast.GeneratorExp) and len(node.generators)!=1: raise ValueError('acceptance_recipe_generator')
        if isinstance(node,ast.comprehension) and (node.is_async or node.ifs or not isinstance(node.target,ast.Name) or node.target.id!='part'):
            raise ValueError('acceptance_recipe_generator')
        if isinstance(node,ast.Call):
            if node.keywords: raise ValueError('acceptance_recipe_call')
            if isinstance(node.func,ast.Name):
                if node.func.id not in ('isinstance','bool','any'): raise ValueError('acceptance_recipe_call')
            elif isinstance(node.func,ast.Attribute):
                if node.func.attr=='compile' and node not in [a.value for a in assignments]: raise ValueError('acceptance_recipe_call')
            else: raise ValueError('acceptance_recipe_call')
    return source
