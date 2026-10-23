import unittest
import main
from ai_gateway_v30 import validate_task
from local_model_adapter_v30 import environment_ready

class AIV30CommandTests(unittest.TestCase):
    def test_offline_commands(self):
        self.assertIn("AI-провайдер: отключён",main.command("/ai30"))
        result=main.command("/ai30_plan control Проверить безопасность кода")
        self.assertIn("offline",result)
        self.assertIn("Код и PR не созданы",result)
    def test_reject_unknown_projects(self):
        self.assertIn("Задание отклонено",main.command("/ai30_plan unknown Исправить код"))
        with self.assertRaises(ValueError):
            validate_task("unknown","task")
    def test_paid_ai_stays_off(self):
        self.assertFalse(environment_ready({"LOCAL_AI_ENABLED":"false"})["ready"])
if __name__=="__main__": unittest.main()
