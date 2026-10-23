"""Stage 3.1: deterministic, offline review pipeline for Python proposals.

Produces a manifest and unified diff for review. Does not execute untrusted code,
contact GitHub, access environment secrets or write to production directories.
Tests must run separately in an isolated, nonprivileged CI job.
"""
import ast
import difflib
import hashlib
import json
import re
from code_recipes_v48 import build_files, is_recipe_task
from execution_gate import stage

SAFE=re.compile(r"^(proposals/review_[a-z0-9_]+\.py|tests/test_review_[a-z0-9_]+\.py)$")
MAX_FILES=4
MAX_BYTES=16000

def prepare(project, task):
    if project!="control" or not is_recipe_task(task):
        raise PermissionError("Stage 3.1 restricted to reviewed control recipes")
    files=build_files(task)
    if not 1 <= len(files) <= MAX_FILES:
        raise ValueError("Unexpected file count")
    summary=[]
    patches=[]
    for name,content in sorted(files.items()):
        if not SAFE.fullmatch(name) or ".." in name or len(content.encode())>MAX_BYTES:
            raise PermissionError("Unsupported output path or size")
        ast.parse(content,filename=name)
        digest=hashlib.sha256(content.encode()).hexdigest()
        summary.append({"path":name,"sha256":digest,"bytes":len(content.encode()),"syntax":"passed"})
        patches.extend(difflib.unified_diff([],content.splitlines(keepends=True),
                       fromfile="/dev/null",tofile="b/"+name))
    manifest=stage(project,task,files)
    if manifest["files"]!=[{"path":x["path"],"sha256":x["sha256"],"bytes":x["bytes"]} for x in summary]:
        raise ValueError("Manifest mismatch")
    return {"project":project,"task":task,"branch":manifest["proposed_branch"],
            "manifest":manifest,"files":summary,"diff":"".join(patches),
            "tests":"required_in_isolated_CI","approval":"required_before_draft_PR",
            "merge":False,"deploy":False,"provider":"none"}

def format_report(bundle,max_chars=3500):
    if not isinstance(bundle,dict) or not bundle.get("files"):
        raise ValueError("Invalid review bundle")
    rows=["🛠 ULTIMATE 3.1 · изолированный пакет изменений",
          "Ветка: "+bundle["branch"],
          "Подготовлено файлов: "+str(len(bundle["files"]))]
    for item in bundle["files"]:
        rows.append("• "+item["path"]+" SHA256 "+item["sha256"][:12])
    rows+=["Синтаксис Python проверен без исполнения.",
           "Тесты выполняются отдельно в GitHub CI.",
           "Создание Draft PR: только после одобрения.",
           "Merge/Deploy: запрещены.",
           "Diff: "+str(len(bundle["diff"].encode()))+" байт (полный diff хранится в пакете)."]
    return "\n".join(rows)[:max_chars]
