import unittest
from telegram_menu import route, keyboard, WELCOME, HELP
import main
class MenuTest(unittest.TestCase):
    def test_routes(self):
        self.assertEqual(route("📊 Статус"), "/status")
        self.assertEqual(route("🌐 Проверить сайт"), "/check")
    def test_keyboard(self):
        self.assertIn("resize_keyboard", keyboard())
    def test_start(self):
        self.assertIn("ULTIMATE AI CONTROL", main.command("/start"))
        self.assertIn("отключена", main.command("/start"))
    def test_help(self):
        self.assertIn("/task", main.command("/help"))
if __name__=="__main__": unittest.main()
