"""Russian Telegram menu: display only, no privileged automatic operations."""
import json

BUTTONS = [
    ["📊 Статус", "🗂 Проекты"],
    ["📋 Задачи", "🌐 Проверить сайт"],
    ["📝 Черновики", "✅ Согласования"],
    ["🔎 Проверка PR"],
    ["🧠 AI-статус", "📖 Помощь"],
]
ROUTES = {
    "📊 Статус": "/status",
    "🗂 Проекты": "/projects",
    "📋 Задачи": "/tasks",
    "🌐 Проверить сайт": "/check",
    "📝 Черновики": "/proposals",
    "✅ Согласования": "/approvals",
    "🧠 AI-статус": "/ai_status",
    "📖 Помощь": "/help",
    "🔎 Проверка PR": "/review",
}
WELCOME = (
    "🧠 ULTIMATE AI CONTROL v2.0 REVIEW (пилот)\n"
    "Центр управления проектами\n\n"
    "📡 Telegram: подключён\n"
    "🛡 Режим: v2.0 согласования, только проверка\n"
    "🤖 AI-модель: пока отключена\n\n"
    "Выбери раздел с помощью кнопок ниже. "
    "Изменения рабочих систем без подтверждения запрещены."
)
HELP = (
    "📖 Команды ULTIMATE AI CONTROL\n\n"
    "/task nova Описание — сохранить задачу\n"
    "/plan nova Описание — получить офлайн-план\n"
    "/draft nova Описание — создать черновик\n"
    "/taskstatus 1 — статус задачи\n"
    "/cancel 1 — отменить ожидающую задачу\n"
    "/proposal ID — посмотреть черновик\n"
    "/approve ID или /reject ID — решение по запросу\n"
    "/audit — журнал действий\n"
    "/repos — разрешённые репозитории\n\n"
    "/review — безопасные запросы на черновые PR\n"
    "/review_new control Описание — создать заявку на проверку\n"
    "/review_status 1 — статус заявки\n\n"
    "⚠️ Задачи сохраняются, но ещё не исполняются автономно."
)
def keyboard():
    return json.dumps({"keyboard":BUTTONS, "resize_keyboard":True, "is_persistent":True}, ensure_ascii=False)
def route(text):
    return ROUTES.get(text, text)
