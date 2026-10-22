"""AI developer v1.3: deterministic review-only change packages.

No GitHub writes, shell execution, deployment or paid model usage.
"""
import hashlib
import json
import re
from datetime import datetime, timezone

PROJECTS={"nova","inventory","sap","kinder","qualisift","control"}
MAX_TASK=1000
BRANCH_RE=re.compile(r"^[a-z][a-z0-9-]{0,50}$")

def prepare(project,task):
    if project not in PROJECTS:
        raise ValueError("Project not allowlisted")
    if not task or len(task)>MAX_TASK:
        raise ValueError("Invalid task length")
    if any(c in task for c in ("\x00","\r")):
        raise ValueError("Invalid characters")
    safe=re.sub(r"[^a-z0-9]+","-",task.lower()).strip("-")[:32].strip("-") or "task"
    digest=hashlib.sha256((project+"\x00"+task).encode()).hexdigest()[:10]
    branch=f"ai-review/{project}-{safe}-{digest}"
    return {
        "project":project,"task":task,"proposed_branch":branch,
        "steps":["Inspect allowlisted project sources, read-only",
                 "Draft minimal isolated change with file-level diff",
                 "Review source and dependency risks",
                 "Run tests only inside separate nonprivileged CI container",
                 "Open draft pull request for human inspection"],
        "gates":["No repository write without explicit approved scope",
                 "No execution inside the production worker",
                 "No merge, release, deploy or purchase without owner approval"],
        "execution_status":"NOT_EXECUTED",
        "ai_model":"DISABLED"
    }

def render(package):
    return ("🛠 План AI-разработчика (без исполнения)\n"
            f"Проект: {package['project']}\n"
            f"Предложенная ветка: {package['proposed_branch']}\n"
            "Дальнейшие действия: проверка исходников, подготовка diff, "
            "изолированные CI-тесты, черновой PR.\n"
            "Никаких изменений кода пока не выполнено.")
