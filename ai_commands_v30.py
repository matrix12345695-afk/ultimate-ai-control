"""3.0 guarded offline planning commands; no model network, PR or execution."""
import json
from ai_gateway_v30 import offline_review,validate_task

def handle(text):
    if not isinstance(text,str) or not text.strip(): return None
    args=text.strip().split(maxsplit=2)
    operation=args[0].split("@",1)[0].lower()
    if operation=="/ai30":
        return ("🧠 ULTIMATE 3.0: AI Gateway (подготовка)\n"
                "AI-провайдер: отключён; платные API не используются.\n"
                "/ai30_plan control Описание задачи — бесплатный план без AI\n"
                "Доступ: проекты control, nova, inventory, sap, kinder, qualisift.\n"
                "Режим: только план, без записи файлов, PR, merge и deploy.")
    if operation!="/ai30_plan":return None
    if len(args)!=3:
        return "Использование: /ai30_plan control Описание задачи"
    try:
        report=offline_review(args[1],args[2])
        lines=["🧠 ULTIMATE 3.0 · offline","Проект: "+report["project"],
               "Задание: "+report["task"],"Этапы:"]
        lines.extend(str(i)+". "+v for i,v in enumerate(report["steps"],1))
        lines.extend(["Проверки: "+", ".join(report["tests"]),
                      "AI-модель пока не подключена. Код и PR не созданы."])
        return "\n".join(lines)[:3900]
    except (ValueError,PermissionError) as exc:
        return "Задание отклонено: "+str(exc)
