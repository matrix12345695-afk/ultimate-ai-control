"""ULTIMATE v3.0: no-cost, local-only AI planning contract.

No network requests or code execution. A local HTTP inference transport must
be supplied by a separate unprivileged process; no paid API is provisioned.
This module validates tasks and model responses, then produces review-only plans.
"""
import json
import re

PROJECTS = frozenset(("control", "nova", "inventory", "sap", "kinder", "qualisift"))
FORBIDDEN = re.compile(r"(?i)(sk-[a-z0-9_-]{12,}|(password|api[_-]?key|secret|token)\s*[:=]\s*\S+)")
MAX_TASK = 1200
MAX_RESPONSE = 10000

def prepare_task(project, task):
    if project not in PROJECTS:
        raise ValueError("Project not allowlisted")
    if not isinstance(task, str) or not 1 <= len(task) <= MAX_TASK:
        raise ValueError("Invalid task")
    if any(ch in task for ch in ("\x00", "\r")) or FORBIDDEN.search(task):
        raise ValueError("Unsafe task content")
    return {
        "project": project,
        "task": task,
        "system": (
            "Prepare a code review proposal. Do not claim changes were made. "
            "Return JSON with summary, affected_files, implementation_steps, "
            "tests, risks. Never request secrets or deployment credentials."
        ),
        "mode": "REVIEW_ONLY",
    }

def validate_response(raw, allowed_paths=None):
    if not isinstance(raw, str) or len(raw.encode("utf-8")) > MAX_RESPONSE:
        raise ValueError("Response oversized or invalid")
    proposal = json.loads(raw)
    required = ("summary", "affected_files", "implementation_steps", "tests", "risks")
    if not isinstance(proposal, dict) or set(proposal) != set(required):
        raise ValueError("Response schema mismatch")
    if not isinstance(proposal["summary"], str) or not 1 <= len(proposal["summary"]) <= 1200:
        raise ValueError("Invalid summary")
    for field in required[1:]:
        items = proposal[field]
        if not isinstance(items, list) or not 1 <= len(items) <= 12:
            raise ValueError("Invalid " + field)
        if not all(isinstance(x, str) and 1 <= len(x) <= 300 for x in items):
            raise ValueError("Invalid item in " + field)
    if FORBIDDEN.search(raw):
        raise ValueError("Potential secret in model output")
    paths = proposal["affected_files"]
    if allowed_paths is not None and not set(paths).issubset(set(allowed_paths)):
        raise PermissionError("Model suggested unapproved paths")
    return proposal

def format_plan(plan):
    parts = ["🧠 AI-план (только проверка)", plan["summary"]]
    for field,label in (("affected_files","Файлы"), ("implementation_steps","Шаги"),
                        ("tests","Тесты"), ("risks","Риски")):
        parts.append(label+": "+ "; ".join(plan[field]))
    parts.append("Код не изменён. Запуск, PR, merge и deploy не разрешены.")
    return "\n".join(parts)[:3500]
