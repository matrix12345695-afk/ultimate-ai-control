"""v2.0 Telegram review pilot: typed commands, content-bound approvals, no writes.

This production-safe adapter presents pre-existing review primitives to the
administrator. It neither generates arbitrary code nor contacts GitHub.
GitHub draft PR execution remains isolated and opt-in.
"""
import hashlib
import re

from controller_v20 import initialize as initialize_review, verify_request
from github_requests import create_request, describe

MAX_TASK = 300
SUPPORTED = {"/review", "/review_new", "/review_status", "/review_prepare", "/review_ci"}

def help_text():
    return (
        "🔎 ULTIMATE v2.0: проверка изменений (пилот)\n"
        "/review_new control <описание> — создать документ-предложение и запрос одобрения\n"
        "/review_status <id> — сведения о заявке\n"
        "/approvals — запросы на согласование\n"
        "/approve <approval_id> или /reject <approval_id> — решение администратора\n"
        "/review_prepare <id> <40-символьный SHA main> — проверенный пакет передачи\n"
        "/review_ci <id> — записанный результат CI\n"
        "⚠️ Автогенерация кода, запись GitHub, слияние и публикация НЕ выполняются."
    )

def _document(task):
    safe_task = " ".join(task.split())
    return (
        "# ULTIMATE AI CONTROL: предложение к рассмотрению\n\n"
        "## Запрос\n\n" + safe_task + "\n\n"
        "## Действия перед PR\n\n"
        "1. Проверить соответствующие исходные файлы в разрешённом репозитории.\n"
        "2. Подготовить точное изменение и сопоставить его SHA-256 с одобрением.\n"
        "3. Прогнать изолированные CI-тесты.\n"
        "4. Создать только черновой PR и повторно проверить его свойства через GitHub.\n\n"
        "## Ограничения\n\n"
        "Это описание плана, а не готовое изменение кода.\n"
        "Запрещены автоматическое слияние, деплой, платежи и изменение production.\n"
    )

def handle(text, connect):
    if not isinstance(text, str) or not text:
        return None
    parts = text.strip().split(maxsplit=2)
    op = parts[0].split("@", 1)[0].lower()
    if op not in SUPPORTED:
        return None
    if op == "/review":
        return help_text()
    try:
        with connect() as conn:
            initialize_review(conn)
            if op == "/review_new":
                if len(parts) != 3 or parts[1] != "control":
                    return "Использование: /review_new control Описание задачи"
                task = parts[2].strip()
                if not task or len(task) > MAX_TASK or any(c in task for c in "\x00\r"):
                    return "Недопустимое описание: 1–300 символов."
                digest = hashlib.sha256(task.encode("utf-8")).hexdigest()[:16]
                path = "proposals/review-" + digest + ".md"
                ident, approval_id, package = create_request(
                    conn, "control", task, {path: _document(task)}
                )
                return (
                    f"📝 Заявка #{ident} создана (только документ-предложение).\n"
                    f"Файл: {path}\n"
                    f"Ветка: {package['proposed_branch']}\n"
                    f"Одобрение: {approval_id}\n"
                    f"Чтобы одобрить подготовку чернового PR: /approve {approval_id}\n"
                    f"После одобрения: /review_prepare {ident} <SHA main>\n"
                    "Одобрение действует 60 минут. Никаких изменений GitHub не сделано."
                )
            if len(parts) < 2 or not re.fullmatch(r"[1-9][0-9]*", parts[1]):
                return f"Использование: {op} <id>"
            ident = int(parts[1])
            if op == "/review_status":
                details = describe(conn, ident)
                report = conn.execute(
                    "SELECT ci_state,pr_url FROM github_ci_reports WHERE request_id=?",
                    (ident,),
                ).fetchone()
                if report:
                    details += "\nCI: " + report[0] + "\nDraft PR: " + report[1]
                return details
            if op == "/review_ci":
                row = conn.execute(
                    "SELECT ci_state,head_sha,pr_url FROM github_ci_reports WHERE request_id=?",
                    (ident,),
                ).fetchone()
                if row is None:
                    return "CI ещё не подтверждён. Черновой PR может быть не создан."
                return "CI: " + row[0] + "\nCommit: " + row[1] + "\nPR: " + row[2]
            if op == "/review_prepare":
                if len(parts) != 3 or not re.fullmatch(r"[0-9a-f]{40}", parts[2]):
                    return "Использование: /review_prepare <id> <40-символьный SHA main>"
                package = verify_request(conn, ident, parts[2])
                return (
                    f"🔐 Проверенный пакет заявки #{ident}\n"
                    f"Ветка: {package['branch']}\n"
                    f"База: {package['base_sha']}\n"
                    f"Контроль: {package['handoff_sha256']}\n"
                    "Пакет готов для отдельного доверенного исполнителя.\n"
                    "GitHub ещё не изменён. Merge и Deploy запрещены."
                )
    except (ValueError, PermissionError, KeyError) as exc:
        return "Отклонено: " + str(exc)
