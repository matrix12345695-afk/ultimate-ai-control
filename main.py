"""ULTIMATE AI CONTROL: Telegram dispatcher, no paid APIs or external write actions."""
import os, json, time, sqlite3, urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime, timezone
from telegram_pro import initialize, handle, record
from github_readonly import command as github_command
from planner import plan, format_plan
from ai_provider import status as ai_status, propose as ai_propose
from control_v08 import setup as setup_v08, save_proposal, list_proposals, proposal_detail, budget_status
from telegram_menu import WELCOME, HELP, keyboard, route
from diagnostics import snapshot, format_snapshot
from operations import snapshot_once, backup_status, AlertLimiter
from monitoring import transitions, format_report
from github_watch import scan as github_scan
from project_reports import project_report
from developer_v13 import prepare as developer_prepare, render as developer_render
from execution_gate import stage as stage_changes
from github_requests import initialize as init_github_requests, create_request as create_github_request, describe as describe_github_request
from handoff_v16 import prepare_handoff
from review_bot_v45 import handle as review_handle
from code_reviews_v48 import handle as code_review_handle

BASE=Path(__file__).parent
DB=Path(os.getenv("DB_PATH",str(BASE/"data"/"control.db")))
TOKEN=os.getenv("TELEGRAM_BOT_TOKEN","")
ADMIN=os.getenv("ADMIN_TELEGRAM_ID","")
URL=os.getenv("MONITOR_URLS","https://novaweb.uz/").split(",")
class ManagedConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()

PROJECTS={"nova":"NOVA WEB","inventory":"Inventory","sap":"SAP / iiko","kinder":"Kinder Spa","qualisift":"QualiSift"}
def db():
    DB.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(DB, factory=ManagedConnection)
    c.execute("CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY, project TEXT, description TEXT, created_at TEXT)")
    initialize(c)
    setup_v08(c)
    init_github_requests(c)
    c.commit()
    return c
def api(method,**kwargs):
    data=urllib.parse.urlencode(kwargs).encode()
    with urllib.request.urlopen(f"https://api.telegram.org/bot{TOKEN}/{method}",data=data,timeout=35) as response:
        return json.load(response)["result"]
def reply(chat,msg,show_keyboard=False):
    args={"chat_id":chat,"text":msg[:4000]}
    if show_keyboard: args["reply_markup"]=keyboard()
    api("sendMessage",**args)
def check():
    results=[]
    for url in URL:
        url=url.strip()
        if not url.startswith("https://"): continue
        try:
            with urllib.request.urlopen(urllib.request.Request(url,method="HEAD"),timeout=12) as r:
                results.append(f"{url}: HTTP {r.status}")
        except Exception as e: results.append(f"{url}: unavailable ({type(e).__name__})")
    return "\n".join(results) or "No HTTPS monitoring URLs configured."
def command(text):
    text=route(text)
    if text == "/start": return WELCOME
    if text == "/help": return HELP
    github_result=github_command(text)
    if github_result is not None:
        return github_result
    extra=handle(text, db, ADMIN)
    if extra is not None: return extra
    review_response=review_handle(text, db)
    if review_response is not None: return review_response
    code_response=code_review_handle(text, db)
    if code_response is not None: return code_response
    parts=text.split(maxsplit=2)
    c=parts[0].split("@")[0].lower()
    if c in ("/start","/help"): return "ULTIMATE AI CONTROL v0.9\n/plan <project> <task> /repos /repo <label> /status /projects /tasks /task <project> <description> /check /taskstatus <id> /cancel <id> /approvals /approve <id> /reject <id> /audit\nAI disabled. No production changes."
    if c=="/github_handoff":
        args=text.split()
        if len(args)!=3 or not args[1].isdigit(): return "Использование: /github_handoff <request_id> <full_40_char_base_sha>"
        try:
            with db() as conn: package=prepare_handoff(conn,int(args[1]),args[2])
            return ("🔐 Пакет передачи подготовлен (без исполнения)\\n"
                    +"Request: "+str(package["request_id"])+"\\n"
                    +"Base: "+package["base_sha"]+"\\n"
                    +"Digest: "+package["handoff_sha256"]+"\\n"
                    +"Только черновой PR. Изменений в GitHub не сделано.")
        except (ValueError,PermissionError) as exc:
            return "Передача заблокирована: "+str(exc)
    if c=="/github_request":
        if len(parts)<3: return "Использование: /github_request control Описание задачи"
        try:
            with db() as conn:
                task_id,approval_id,manifest=create_github_request(conn,parts[1],parts[2],{"docs/review.md":"Требуется ручная проверка"})
            return f"Заявка #{task_id} создана. Одобрение: {approval_id}\\nПросмотр: /github_request_status {task_id}\\nЭто заявка на проверку, код не создан."
        except ValueError: return "Недопустимый проект или текст запроса."
    if c=="/github_request_status":
        if len(parts)<2 or not parts[1].isdigit(): return "Использование: /github_request_status <id>"
        with db() as conn: return describe_github_request(conn,int(parts[1]))
    if c=="/changegate":
        if len(parts)<3: return "Использование: /changegate control Описание"
        try:
            item=stage_changes(parts[1], parts[2], {"docs/review.md": "Требуется ручная проверка"})
            return "🔒 Черновик проверки: "+item["proposed_branch"]+"\nСтатус: AWAITING_REVIEW. Ветка и PR ещё не созданы."
        except ValueError:
            return "Недопустимые параметры запроса."
    if c=="/devplan":
        if len(parts)<3: return "Usage: /devplan nova Describe change"
        try: return developer_render(developer_prepare(parts[1],parts[2]))
        except ValueError: return "Недопустимый проект или текст задачи."
    if c=="/github_check":
        return format_report(github_scan())
    if c=="/report":
        with db() as conn:
            return project_report(conn, PROJECTS)
    if c=="/backups":
        return backup_status(DB.parent / "backups")
    if c=="/diagnostics":
        with db() as conn:
            return format_snapshot(snapshot(conn,ai_status()["enabled"]))
    if c=="/budget":
        with db() as conn: return budget_status(conn,0)
    if c=="/proposals":
        with db() as conn: return list_proposals(conn)
    if c=="/proposal":
        if len(parts)<2: return "Usage: /proposal <id>"
        with db() as conn: return proposal_detail(conn,parts[1])
    if c=="/draft":
        if len(parts)<3 or parts[1] not in PROJECTS: return "Usage: /draft nova Improve SEO"
        offline_plan=format_plan(plan(parts[1],parts[2]))
        with db() as conn:
            proposal_id=save_proposal(conn,parts[1],parts[2],offline_plan)
            record(conn,"draft_created",proposal_id)
            conn.commit()
        return f"Draft {proposal_id} saved. No code was changed. /proposal {proposal_id}"
    if c=="/ai_status":
        state=ai_status()
        return f"AI enabled: {state['enabled']}\nProvider: {state['provider']}\nModel: {state['model']}\nBudget gate USD: {state['budget_usd']}"
    if c=="/ai_plan":
        if len(parts)<3 or parts[1] not in PROJECTS: return "Usage: /ai_plan nova Improve SEO"
        return ai_propose(parts[1],parts[2])
    if c=="/plan":
        if len(parts)<3 or parts[1] not in PROJECTS: return "Usage: /plan nova Improve website"
        return format_plan(plan(parts[1],parts[2]))
    if c=="/status": return "Dispatcher online. AI: disabled. Production changes: prohibited."
    if c=="/projects": return "\n".join(f"{k}: {v}" for k,v in PROJECTS.items())
    if c=="/check": return check()
    if c=="/tasks":
        with db() as conn: rows=conn.execute("SELECT id,project,description,status FROM tasks ORDER BY id DESC LIMIT 10").fetchall()
        return "\n".join(f"#{i} [{state}] {p}: {d}" for i,p,d,state in rows) or "No tasks yet."
    if c=="/task":
        if len(parts)<3 or parts[1] not in PROJECTS: return "Usage: /task nova Check website"
        with db() as conn:
            conn.execute("INSERT INTO tasks(project,description,created_at) VALUES(?,?,?)",(parts[1],parts[2][:1000],datetime.now(timezone.utc).isoformat()))
            record(conn,"task_created",f"{parts[1]}: {parts[2][:300]}")
            conn.commit()
        return "Task queued (not executed)."
    return "Unknown command. Use /help"
def main():
    if not TOKEN or not ADMIN.isdecimal(): raise SystemExit("Configure TELEGRAM_BOT_TOKEN and ADMIN_TELEGRAM_ID")
    db().close()
    offset=0
    next_check=time.monotonic()+3600
    next_backup=time.monotonic()+60
    alerts=AlertLimiter(3600)
    previous_monitor={}
    previous_github={}
    next_github=time.monotonic()+120
    while True:
        try:
            updates=api("getUpdates",offset=offset,timeout=20,allowed_updates=json.dumps(["message"]))
            for update in updates:
                offset=update["update_id"]+1
                message=update.get("message",{})
                sender=message.get("from",{})
                chat=message.get("chat",{})
                if str(sender.get("id"))!=ADMIN or chat.get("type")!="private": continue
                text=message.get("text","")
                if text.startswith("/") or text in __import__("telegram_menu").ROUTES:
                    reply(chat["id"],command(text),show_keyboard=text in ("/start", "📖 Помощь"))
            if time.monotonic()>=next_github:
                try:
                    current_github=github_scan()
                    for alert in transitions(previous_github,current_github):
                        reply(ADMIN,alert)
                    previous_github=current_github
                except Exception as exc:
                    print('GitHub monitor failed:',type(exc).__name__,flush=True)
                next_github=time.monotonic()+3600
            if time.monotonic()>=next_backup:
                try:
                    created=snapshot_once(DB, DB.parent / 'backups')
                    if created: print('Local SQLite snapshot verified',flush=True)
                except Exception as exc:
                    print('Backup failed:',type(exc).__name__,flush=True)
                    if alerts.should_send('backup'): reply(ADMIN,'⚠️ Резервное копирование не выполнено. Проверь журнал Render.')
                next_backup=time.monotonic()+3600
            if time.monotonic()>=next_check:
                result=check()
                current_monitor={}
                for line in result.splitlines():
                    target, separator, detail=line.partition(': ')
                    if separator:
                        current_monitor[target]=(not detail.startswith('unavailable'),detail)
                for alert in transitions(previous_monitor,current_monitor):
                    reply(ADMIN,alert)
                previous_monitor=current_monitor
                next_check=time.monotonic()+3600
        except Exception as exc:
            print("Polling error:",type(exc).__name__,flush=True)
            if alerts.should_send('polling'):
                try: reply(ADMIN,'⚠️ Ошибка Telegram-подключения. Проверь Render.')
                except Exception: pass
            time.sleep(5)
if __name__=="__main__": main()
