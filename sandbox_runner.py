"""Safe test runner: executes ONLY repository-maintained unittest suite.

This is not a sandbox for untrusted arbitrary code. Run it in an ephemeral,
non-privileged, network-restricted container without production secrets.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

MAX_SECONDS=90
MAX_OUTPUT=12000

def run_tests(workspace, timeout=MAX_SECONDS):
    root=Path(workspace).resolve()
    if not root.is_dir() or not (root/"tests").is_dir():
        raise ValueError("workspace must contain tests/")
    if not isinstance(timeout,int) or timeout<1 or timeout>MAX_SECONDS:
        raise ValueError("invalid timeout")
    started=time.monotonic()
    try:
        result=subprocess.run(
            [sys.executable,"-m","unittest","discover","-s","tests","-v"],
            cwd=root,env={"PATH":"/usr/bin:/bin","PYTHONUNBUFFERED":"1"},
            capture_output=True,text=True,timeout=timeout,check=False)
        return {"status":"passed" if result.returncode==0 else "failed",
                "exit_code":result.returncode,
                "elapsed_seconds":round(time.monotonic()-started,2),
                "output":(result.stdout+"\n"+result.stderr)[-MAX_OUTPUT:]}
    except subprocess.TimeoutExpired:
        return {"status":"timeout","exit_code":None,
                "elapsed_seconds":round(time.monotonic()-started,2),
                "output":"Unit tests exceeded time limit"}

if __name__=="__main__":
    print(json.dumps(run_tests(Path(__file__).resolve().parent),ensure_ascii=False,indent=2))
