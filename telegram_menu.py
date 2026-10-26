"""Russian Telegram menu: display only, no privileged automatic operations."""
import json

BUTTONS = [
    ["🔐 Посредник модели", "🧩 Демо разработчика"],
    ["🧮 Провайдер API"],
    ["🔒 Изоляция", "🧪 Самопроверка"],
    ["🧪 Приёмка"],
    ["🗺 План 4.0", "🔔 Уведомления"],
    ["📌 Для владельца"],
    ["🛠 Очередь 4.0", "🤖 Агенты"],
    ["📈 Работа за сутки", "💰 Бюджет 4.0"],
    ["📆 Работа за неделю"],
    ["📚 Память", "💬 Этот чат"],
    ["🧾 История проектов"],
    ["🧪 NOVA WEB", "🐘 PostgreSQL NOVA"],
    ["📝 PR из артефактов"],
    ["🖥 VPS", "🖼 Браузер NOVA"],
    ["🎨 Черновик NOVA", "🚦 Выпуск NOVA"],
    ["📦 Сборка NOVA", "🧭 План выпуска"],
    ["🛑 Пауза", "▶️ Продолжить"],
    ["📊 Статус", "🗂 Проекты"],
    ["📋 Задачи", "🌐 Проверить сайт"],
    ["📡 Мониторинг 4.0", "🩺 Проверить API"],
    ["📝 Черновики", "✅ Согласования"],
    ["🔎 Проверка PR"],
    ["🧪 Код / PR"],
    ["🧠 AI-статус", "📖 Помощь"],
]
ROUTES = {
    "🖼 Браузер NOVA":"/nova_browser",
    "🎨 Черновик NOVA":"/nova_candidate",
    "🚦 Выпуск NOVA":"/nova_release",
    "📦 Сборка NOVA":"/nova_build",
    "🧭 План выпуска":"/nova_deploy",
    "🐘 PostgreSQL NOVA":"/nova_pg",
    "🖥 VPS":"/vps4",
    "📝 PR из артефактов":"/artifact_prs",
    "🧪 NOVA WEB":"/test_nova",
    "🧾 История проектов":"/memory_log",
    "🧪 Приёмка":"/acceptance4",
    "🩺 Проверить API":"/readiness4",
    "📆 Работа за неделю":"/weekly",
    "📌 Для владельца":"/owner_later",
    "📡 Мониторинг 4.0":"/monitor4",
    "🔐 Посредник модели":"/broker4", "🧩 Демо разработчика":"/developer_demo",
    "🧮 Провайдер API":"/provider4",
    "🔒 Изоляция":"/sandbox", "🧪 Самопроверка":"/selftest",
    "🗺 План 4.0":"/roadmap", "🔔 Уведомления":"/owner_inbox",
    "🛠 Очередь 4.0":"/queue", "🤖 Агенты":"/agents", "📈 Работа за сутки":"/daily",
    "💰 Бюджет 4.0":"/budget4", "📚 Память":"/memory", "💬 Этот чат":"/chat_link",
    "🛑 Пауза":"/pause", "▶️ Продолжить":"/resume",
    "📊 Статус": "/status",
    "🗂 Проекты": "/projects4",
    "📋 Задачи": "/tasks",
    "🌐 Проверить сайт": "/check",
    "📝 Черновики": "/proposals",
    "✅ Согласования": "/approvals",
    "🧠 AI-статус": "/ai_status",
    "📖 Помощь": "/help",
    "🔎 Проверка PR": "/review",
    "🧪 Код / PR": "/code",
}
WELCOME = (
    "🧠 ULTIMATE AI CONTROL 4.0 · OPS\n"
    "Центр управления проектами\n\n"
    "📡 Telegram: подключён\n"
    "🛡 Режим: планировщик безопасных проверок и очередь\n"
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
    "/review_status 1 — статус заявки\n"
    "/code — генерация проверенных Python-рецептов и тестов\n\n"
    "/roadmap /queue /agents /daily /budget4 /memory\n"
    "/memory_log [проект] [страница] /memory_item ID — история со сверкой оснований\n"
    "/test_nova /nova_tests — закреплённые тесты NOVA без сети и базы данных\n"
    "/artifact_pr ID /artifact_prs /artifact_pr_status ID /artifact_pr_refresh ID — Draft PR из рецепта\n"
    "/artifact_release ID — запрос согласования точной версии, без исполнения публикации\n"
    "/monitor4 — доступность сайтов и история восстановления тревог\n"
    "/readiness4 — проверить API и готовность PostgreSQL через публичный /health\n"
    "/owner_later [страница] — сохранённые действия владельца\n"
    "/owner_item ID — полный запрос, статус и запись доставки\n"
    "/projects4 /repo_check nova /repo_check kinder — реестр и проверка исходников\n"
    "/analytics4 24h /analytics4 7d /cost4 ID — измерения, ожидание и квитанции API\n"
    "/provider4 — состояние транспорта API и неразрешённых резервов\n"
    "/broker4 /developer_demo — посредник и проверка пути без LLM\n"
    "/develop control Описание — отдельный Python-черновик через модель\n"
    "/work nova Описание — новая задача\n"
    "/job 1 /job_cancel 1 — состояние и отмена\n"
    "/project nova — проект для обычных текстовых сообщений\n"
    "/chat_link /chat_bind URL — ссылка возврата в Codex\n"
    "/pause /resume — безопасная пауза очереди\n\n"
    "/sandbox /selftest — состояние и проверка изоляции\n"
    "/acceptance4 — независимые проверки требований и проверенные артефакты\n"
    "/recipe safe-paths или /recipe sha-check — кодовый черновик без LLM\n"
    "/artifact 1 — сведения и отчёт черновика\n"
    "/artifact_code 1 1 — показать файл черновика\n\n"
    "Мониторинг и проверка исходников работают по расписанию. AI-разработка кода ожидает отдельного исполнителя."
)
def keyboard():
    return json.dumps({"keyboard":BUTTONS, "resize_keyboard":True, "is_persistent":True}, ensure_ascii=False)
def route(text):
    return ROUTES.get(text, text)
