import sqlite3
import unittest
from owner_notifications import initialize, create, pending, resolve, format_pending

class OwnerInboxTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        initialize(self.db)

    def tearDown(self):
        self.db.close()

    def test_priority_and_isolation(self):
        create(self.db, "nova", "decision", "Публикация", "Нужен владелец", "Проверить версию", "t1")
        create(self.db, "kinder", "critical", "Ошибка", "Сбой", "Посмотреть отчёт", "t2")
        self.assertEqual([r[1] for r in pending(self.db)], ["kinder", "nova"])
        self.assertTrue(resolve(self.db, 1))
        self.assertFalse(resolve(self.db, 1))
        self.assertEqual(len(pending(self.db)), 1)

    def test_reject_bad_data(self):
        with self.assertRaises(ValueError):
            create(self.db, "nova", "deploy", "Title", "Reason", "Action")
        with self.assertRaises(ValueError):
            create(self.db, "nova", "decision", "", "Reason", "Action")

    def test_empty_report(self):
        self.assertIn("Нет запросов", format_pending(self.db))

if __name__ == "__main__":
    unittest.main()
