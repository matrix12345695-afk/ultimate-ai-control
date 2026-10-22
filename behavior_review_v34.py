"""Stage 3.1 behavioral checks and immutable review evidence.

Only predetermined source fixtures are evaluated by an AST-based interpreter
for literal assignments, with no exec/eval/import or model-generated execution.
"""
import ast
import hashlib
import json
from autofix_preview_v32 import preview

CASES = {
    "proposals/review_example.py": {"answer": 42},
    "tests/test_review_example.py": {"answer": 42},
}

def _literal_bindings(source):
    tree=ast.parse(source)
    result={}
    for node in tree.body:
        if not isinstance(node,ast.Assign) or len(node.targets)!=1 or not isinstance(node.targets[0],ast.Name):
            raise PermissionError("Only literal assignments permitted in behavioral harness")
        value=ast.literal_eval(node.value)
        if type(value) not in (str,int,float,bool,type(None)):
            raise PermissionError("Only primitive literals permitted")
        result[node.targets[0].id]=value
    return result

def evidence(path,source,rule):
    if path not in CASES:
        raise PermissionError("Fixture not allowlisted")
    original=_literal_bindings(source)
    proposed=preview(path,source,hashlib.sha256(source.encode()).hexdigest(),rule)
    if not proposed["changed"]:
        raise ValueError("No change to validate")
    after=_literal_bindings(proposed["proposed_content"])
    expected=CASES[path]
    tests={
      "expected_bindings_before":original==expected,
      "expected_bindings_after":after==expected,
      "semantics_preserved":original==after,
      "diff_nonempty":bool(proposed["diff"]),
    }
    if not all(tests.values()):
        raise ValueError("Behavioral contract failed")
    report={
      "schema":"ultimate.review.v34","path":path,"rule":rule,
      "before_sha256":proposed["before_sha256"],
      "after_sha256":proposed["after_sha256"],
      "diff_sha256":hashlib.sha256(proposed["diff"].encode()).hexdigest(),
      "tests":tests,"passed":True,
      "approval_required":True,"git_write":False,"merge":False,"deploy":False,
    }
    payload=json.dumps(report,sort_keys=True,separators=(",",":"),ensure_ascii=False)
    report["evidence_sha256"]=hashlib.sha256(payload.encode()).hexdigest()
    return report

def review_message(report):
    if report.get("schema")!="ultimate.review.v34" or report.get("passed") is not True:
        raise ValueError("Invalid review evidence")
    return ("🧪 Проверенный пакет 3.1\n"
            "Файл: "+report["path"]+"\n"
            "Правило: "+report["rule"]+"\n"
            "Поведенческие проверки: "+str(len(report["tests"]))+"/"+str(len(report["tests"]))+"\n"
            "SHA-256 отчёта: "+report["evidence_sha256"]+"\n"
            "Это предварительный отчёт. Отдельное согласование Draft PR обязательно.\n"
            "Merge и Deploy запрещены.")
