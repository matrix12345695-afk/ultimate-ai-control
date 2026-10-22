import io
import json
import sqlite3
import unittest
from github_watch import inspect
from project_reports import project_report

class Response(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self,*args):
        self.close()

class Version12Tests(unittest.TestCase):
    def test_reject_unknown_repository(self):
        self.assertFalse(inspect("unknown")[0])
    def test_github_response(self):
        def fake(request,timeout):
            return Response(json.dumps({"full_name":"matrix12345695-afk/ultimate-ai-control","pushed_at":"2026-10-22T00:00:00Z"}).encode())
        self.assertTrue(inspect("control",fake)[0])
    def test_project_report(self):
        with sqlite3.connect(":memory:") as db:
            db.execute("CREATE TABLE tasks(project TEXT,status TEXT)")
            db.execute("INSERT INTO tasks VALUES ('nova','queued')")
            report=project_report(db,{"nova":"NOVA WEB","kinder":"Kinder Spa"})
            self.assertIn("queued: 1",report)
            self.assertIn("задач пока нет",report)
if __name__=="__main__":
    unittest.main()
