"""Stage 3.1 bounded autofix preview for already-known Python source.

Never executes edited code or writes to production. Exact SHA binding prevents
changing a different revision. Intended for ephemeral CI checkout only.
"""
import ast
import difflib
import hashlib
from pathlib import PurePosixPath

MAX_BYTES=16000
ALLOW={"proposals/review_example.py","tests/test_review_example.py"}
RULES={
 "missing-final-newline":lambda source:source if source.endswith("\n") else source+"\n",
 "trim-trailing-whitespace":lambda source:"".join(
    line.rstrip(" \t\r\n")+("\n" if line.endswith("\n") else "")
    for line in source.splitlines(keepends=True)),
}
def preview(path,original,expected_sha256,rule):
    if path not in ALLOW or str(PurePosixPath(path))!=path:
        raise PermissionError("Only allowlisted offline fixture paths")
    if not isinstance(original,str) or not 0<len(original.encode())<=MAX_BYTES:
        raise ValueError("Invalid source size")
    if hashlib.sha256(original.encode()).hexdigest()!=expected_sha256:
        raise PermissionError("Source revision mismatch")
    if rule not in RULES:
        raise PermissionError("Fix rule not approved")
    ast.parse(original,filename=path)
    edited=RULES[rule](original)
    ast.parse(edited,filename=path)
    diff="".join(difflib.unified_diff(original.splitlines(keepends=True),
       edited.splitlines(keepends=True),fromfile="a/"+path,tofile="b/"+path))
    return {"path":path,"rule":rule,"before_sha256":expected_sha256,
            "after_sha256":hashlib.sha256(edited.encode()).hexdigest(),
            "changed":edited!=original,"diff":diff,"proposed_content":edited,
            "tests":"not_run_requires_isolated_CI","git_write":False,
            "merge":False,"deploy":False}
