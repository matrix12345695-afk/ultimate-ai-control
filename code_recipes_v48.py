"""v2.1 offline, bounded code recipes: real Python plus runnable unit tests.

This is intentionally NOT an LLM. A new nonce permits repeated approvals while
the recipe names and file content remain strictly allowlisted. Only test and
proposal files are created, never active production Python modules.
"""
import hashlib
import re
import secrets

TASK = re.compile(r"^CODE_RECIPE:(safe-paths|sha-check):([0-9a-f]{8})$")
RECIPES = {
    "safe-paths": "Валидатор безопасных путей для файлов GitHub review",
    "sha-check": "Проверка 40-символьных Git commit SHA",
}


def new_recipe_task(recipe):
    if recipe not in RECIPES:
        raise ValueError("Recipe is not allowlisted")
    return "CODE_RECIPE:" + recipe + ":" + secrets.token_hex(4)


def is_recipe_task(task):
    return isinstance(task, str) and TASK.fullmatch(task) is not None


def build_files(task):
    matched = TASK.fullmatch(task) if isinstance(task, str) else None
    if not matched:
        raise ValueError("Untrusted code recipe task")
    recipe = matched.group(1)
    fingerprint = hashlib.sha256(task.encode("ascii")).hexdigest()[:16]
    module = "review_" + recipe.replace("-", "_") + "_" + fingerprint
    source_path = "proposals/" + module + ".py"
    tests_path = "tests/test_" + module + ".py"
    if recipe == "safe-paths":
        source = (
            '"""Review-only path safety helper; not imported by production. """\n'
            'import re\n\n'
            '_PATH = re.compile(r"^(docs|tests|proposals)/[A-Za-z0-9_./-]{1,120}$")\n'
            '_BLOCKED = (".env", "credentials", "secret", "token")\n\n'
            'def safe_review_path(value):\n'
            '    """Reject traversal, unusual separators and sensitive destinations."""\n'
            '    if not isinstance(value, str) or not _PATH.fullmatch(value):\n'
            '        return False\n'
            '    if any(part in ("", ".", "..") for part in value.split("/")):\n'
            '        return False\n'
            '    return not any(part in value.lower() for part in _BLOCKED)\n'
        )
        tests = (
            '"""Generated offline recipe smoke tests; review before adoption."""\n'
            'import unittest\n'
            'from proposals.' + module + ' import safe_review_path\n\n'
            'class ReviewPathTests(unittest.TestCase):\n'
            '    def test_allowed(self):\n'
            '        self.assertTrue(safe_review_path("tests/review_case.py"))\n'
            '        self.assertTrue(safe_review_path("proposals/new_feature.py"))\n'
            '    def test_reject_parent_and_hidden(self):\n'
            '        for path in ("../readme.md", "docs/../a.md", "docs//a.md",\n'
            '                     "tests/.env", "docs/private-secret.txt",\n'
            '                     "docs\\\\file.py", "/etc/passwd", "src/app.py"):\n'
            '            self.assertFalse(safe_review_path(path), path)\n'
            '    def test_reject_wrong_types(self):\n'
            '        self.assertFalse(safe_review_path(None))\n'
            '        self.assertFalse(safe_review_path(13))\n\n'
            'if __name__ == "__main__":\n'
            '    unittest.main()\n'
        )
    else:
        source = (
            '"""Review-only Git SHA validator; not imported by production."""\n'
            'import re\n\n'
            '_COMMIT = re.compile(r"^[0-9a-f]{40}$")\n\n'
            'def is_git_commit(value):\n'
            '    """Allow only canonical, full lower-case SHA-1 Git identifiers."""\n'
            '    return isinstance(value, str) and bool(_COMMIT.fullmatch(value))\n'
        )
        tests = (
            '"""Generated offline recipe smoke tests; review before adoption."""\n'
            'import unittest\n'
            'from proposals.' + module + ' import is_git_commit\n\n'
            'class ReviewCommitTests(unittest.TestCase):\n'
            '    def test_valid(self):\n'
            '        self.assertTrue(is_git_commit("a" * 40))\n'
            '        self.assertTrue(is_git_commit("0123456789abcdef" * 2 + "12345678"))\n'
            '    def test_invalid(self):\n'
            '        for value in (None, 123, "", "a" * 39, "a" * 41,\n'
            '                      "G" * 40, "A" * 40, "a" * 39 + "\\n"):\n'
            '            self.assertFalse(is_git_commit(value), value)\n\n'
            'if __name__ == "__main__":\n'
            '    unittest.main()\n'
        )
    return {source_path: source, tests_path: tests}
