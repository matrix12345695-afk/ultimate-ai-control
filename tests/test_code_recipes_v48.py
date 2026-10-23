"""v2.1 recipe outputs are real, compilable Python and require exact approval."""
import json
import os
import pathlib
import re
import sqlite3
import subprocess
import sys
import tempfile
import unittest

import main
from code_recipes_v48 import RECIPES, build_files, is_recipe_task, new_recipe_task
from execution_gate import stage
from review_executor_v46 import exact_files


class CodeRecipeTests(unittest.TestCase):
    def test_each_recipe_generates_python_that_passes_real_tests(self):
        for recipe in RECIPES:
            with self.subTest(recipe=recipe):
                task = new_recipe_task(recipe)
                self.assertTrue(is_recipe_task(task))
                files = build_files(task)
                self.assertEqual(len(files), 2)
                self.assertTrue(any(p.startswith("tests/test_") for p in files))
                self.assertTrue(any(p.startswith("proposals/") for p in files))
                for body in files.values():
                    compile(body, "<review code>", "exec")
                with tempfile.TemporaryDirectory() as dirname:
                    root = pathlib.Path(dirname)
                    for name, content in files.items():
                        path = root / name
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_text(content, encoding="utf-8")
                    result = subprocess.run(
                        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                        cwd=root, capture_output=True, text=True, timeout=15,
                    )
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn("OK", result.stderr)
                manifest = stage("control", task, files)
                self.assertEqual(exact_files("control", task, json.dumps(manifest)), files)

    def test_only_allowlisted_recipes(self):
        for invalid in ("", "prompt:write-keys", "safe-paths; rm -rf",
                        "sha-check/../../", "../sha-check", 12):
            with self.assertRaises(ValueError):
                new_recipe_task(invalid)
        for invalid in ("CODE_RECIPE:safe-paths:;rm",
                        "CODE_RECIPE:whatever:11111111",
                        "CODE_RECIPE:safe-paths:ABCD1234",
                        "CODE_RECIPE:safe-paths:1234", None, ""):
            self.assertFalse(is_recipe_task(invalid))
            with self.assertRaises(ValueError):
                build_files(invalid)

    def test_tampered_code_manifest_fails_closed(self):
        task = new_recipe_task("sha-check")
        files = build_files(task)
        manifest = stage("control", task, files)
        self.assertEqual(exact_files("control", task, json.dumps(manifest)), files)
        manifest["files"][0]["sha256"] = "e" * 64
        with self.assertRaises(PermissionError):
            exact_files("control", task, json.dumps(manifest))
        with self.assertRaises(PermissionError):
            exact_files("nova", task, json.dumps(manifest))

    def test_different_nonces_produce_independent_hashes_and_branches(self):
        a, b = new_recipe_task("safe-paths"), new_recipe_task("safe-paths")
        self.assertNotEqual(a, b)
        first, second = build_files(a), build_files(b)
        self.assertNotEqual(set(first), set(second))
        self.assertNotEqual(stage("control", a, first)["proposed_branch"],
                            stage("control", b, second)["proposed_branch"])

    def test_old_document_proposals_continue_to_work(self):
        import hashlib
        from review_bot_v45 import _document
        task = "Review docs"
        path = "proposals/review-" + hashlib.sha256(task.encode()).hexdigest()[:16] + ".md"
        original = {path: _document(task)}
        manifest = stage("control", task, original)
        self.assertEqual(exact_files("control", task, json.dumps(manifest)), original)


class CodeTelegramTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_db, self.old_admin = main.DB, main.ADMIN
        main.DB = pathlib.Path(self.temp.name) / "control.db"
        main.ADMIN = "502438855"

    def tearDown(self):
        main.DB, main.ADMIN = self.old_db, self.old_admin
        self.temp.cleanup()

    def test_preview_approval_gate_for_real_python(self):
        self.assertIn("/code_new", main.command("/code"))
        self.assertIn("/code_new", main.command("🧪 Код / PR"))
        response = main.command("/code_new control safe-paths")
        self.assertIn("Кодовая заявка #1", response)
        approval = re.search(r"Одобрение: ([A-Za-z0-9_-]+)", response).group(1)
        preview = main.command("/code_preview 1")
        self.assertIn("def safe_review_path(", preview)
        self.assertIn("class ReviewPathTests", preview)
        self.assertIn("перед одобрением", preview)
        with main.db() as conn:
            self.assertEqual(conn.execute(
                "SELECT status FROM approvals WHERE id=?", (approval,)
            ).fetchone()[0], "pending")
        self.assertIn("Recorded: approved", main.command("/approve " + approval))
        with main.db() as conn:
            project,task,raw = conn.execute(
                "SELECT project,task,manifest_json FROM github_change_requests WHERE id=1"
            ).fetchone()
            self.assertEqual(exact_files(project,task,raw), build_files(task))
        self.assertIn("Готово к передаче на ручную проверку: да",
                      main.command("/review_status 1"))

    def test_bad_recipe_and_tampered_preview(self):
        self.assertIn("Использование", main.command("/code_new control exploit"))
        self.assertIn("Использование", main.command("/code_new inventory safe-paths"))
        self.assertIn("Использование", main.command("/code_preview 0"))
        self.assertIn("не найдена", main.command("/code_preview 1"))
        main.command("/code_new control sha-check")
        with main.db() as conn:
            conn.execute("UPDATE github_change_requests SET manifest_json='{}' WHERE id=1")
            conn.commit()
        self.assertIn("заблокировано", main.command("/code_preview 1"))


if __name__ == "__main__":
    unittest.main()
