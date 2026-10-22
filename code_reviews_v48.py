"""Telegram commands for opt-in, hash-bound Python code recipe reviews.

The polling bot saves only reviewed file hashes; isolated executor performs
any approved GitHub operation, never this module.
"""
import json

from code_recipes_v48 import RECIPES, build_files, is_recipe_task, new_recipe_task
from execution_gate import stage
from github_requests import create_request


def instructions():
    return (
        "🧪 Код v2.1 (без AI-модели, проверенные Python-рецепты)\n"
        "/code_new control safe-paths — проверка безопасных путей\n"
        "/code_new control sha-check — проверка Git SHA\n"
        "/code_preview <id> — увидеть исходный Python-код и тесты ДО одобрения\n"
        "/approve <approval_id> — разрешить создание только Draft PR\n"
        "/review_status <id> — PR и CI\n"
        "Каждый рецепт создаёт реальные файлы proposals/*.py и tests/test_*.py.\n"
        "Без произвольного AI-программирования, merge, deploy и платежей."
    )


def handle(text, connect):
    if not isinstance(text, str) or not text:
        return None
    parts = text.strip().split(maxsplit=2)
    op = parts[0].split("@", 1)[0].lower()
    if op not in ("/code", "/code_new", "/code_preview"):
        return None
    if op == "/code":
        return instructions()
    if op == "/code_new":
        if len(parts) != 3 or parts[1] != "control" or parts[2] not in RECIPES:
            return "Использование: /code_new control safe-paths или /code_new control sha-check"
        task = new_recipe_task(parts[2])
        files = build_files(task)
        with connect() as conn:
            ident, approval, manifest = create_request(conn, "control", task, files)
        return (
            f"🧪 Кодовая заявка #{ident} создана. Рецепт: {parts[2]}\n"
            f"Изменяемые файлы: {', '.join(sorted(files))}\n"
            f"Ветка: {manifest['proposed_branch']}\n"
            f"Одобрение: {approval}\n"
            f"СНАЧАЛА прочитай код: /code_preview {ident}\n"
            f"Если согласен: /approve {approval}\n"
            "После одобрения только Draft PR и CI. Продакшн не изменяется."
        )
    if len(parts) != 2 or not parts[1].isdigit() or int(parts[1]) <= 0:
        return "Использование: /code_preview <id>"
    with connect() as conn:
        row = conn.execute(
            "SELECT project,task,manifest_json FROM github_change_requests WHERE id=?",
            (int(parts[1]),),
        ).fetchone()
        if row is None or row[0] != "control" or not is_recipe_task(row[1]):
            return "Кодовая заявка не найдена."
        files = build_files(row[1])
        if stage(row[0], row[1], files) != json.loads(row[2]):
            return "Заявка не соответствует исходному коду. Одобрение заблокировано."
        preview = f"🧪 Исходники заявки #{parts[1]} (перед одобрением)\n"
        for path, body in sorted(files.items()):
            preview += "\n" + path + "\n" + body
        preview += "\n⚠️ Создание PR требует отдельного /approve."
        return preview[:3900]
