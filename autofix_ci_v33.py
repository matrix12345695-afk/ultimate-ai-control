"""CI-only autofix validation for preapproved, small Python fixtures.

Operates entirely in temporary files. No credentials, git writes or network.
This is a smoke-test harness, not a security boundary for arbitrary code.
"""
import hashlib
import pathlib
import subprocess
import sys
import tempfile

from autofix_preview_v32 import preview

def validate_fixture(path, source, rule):
    digest=hashlib.sha256(source.encode()).hexdigest()
    result=preview(path,source,digest,rule)
    if not result["changed"]:
        return {"status":"unchanged","path":path,"diff":result["diff"],
                "tests_passed":False,"reason":"no change to validate"}
    with tempfile.TemporaryDirectory(prefix="ultimate31-") as tmp:
        root=pathlib.Path(tmp)
        target=root/path
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(result["proposed_content"],encoding="utf-8")
        proc=subprocess.run(
            [sys.executable,"-I","-m","py_compile",str(target)],
            cwd=root,env={"PATH":"/usr/bin:/bin","PYTHONNOUSERSITE":"1"},
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            text=True,timeout=8,check=False,
        )
    return {"status":"passed" if proc.returncode==0 else "failed",
            "path":path,"before_sha256":digest,
            "after_sha256":result["after_sha256"],
            "diff":result["diff"],"tests_passed":proc.returncode==0,
            "check":"isolated_python_compile_only",
            "reason":"syntax verified; behavioral tests still required",
            "git_write":False,"merge":False,"deploy":False}
