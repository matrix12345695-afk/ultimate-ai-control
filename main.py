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
from owner_notifications import initialize as initialize_owner_inbox, format_pending as format_owner_inbox, create as notify_owner
from owner_delivery import deliver_one
from queue_worker import initialize as initialize_runtime
from runtime_commands import handle as runtime_handle, submit_text
from roadmap import setting, set_setting
from chat_binding import current as bound_chat
from review_bot_v45 import handle as review_handle
from code_reviews_v48 import handle as code_review_handle
from ai_commands_v30 import handle as ai30_handle
from isolated_development_v31 import prepare as prepare_v31, format_report as report_v31
from ai_commands_v30 import handle as ai30_handle

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
    initialize_owner_inbox(c)
    initialize_runtime(c)
    c.commit()
    return c
def api(method,**kwargs):
    data=urllib.parse.urlencode(kwargs).encode()
    with urllib.request.urlopen(f"https://api.telegram.org/bot{TOKEN}/{method}",data=data,timeout=35) as response:
        payload=json.load(response)
        if payload.get("ok") is not True:
            raise ValueError("Telegram request rejected")
        return payload["result"]
def reply(chat,msg,show_keyboard=False):
    args={"chat_id":chat,"text":msg[:4000]}
    if show_keyboard: args["reply_markup"]=keyboard()
    elif msg.startswith("🔔 ULTIMATE AI CONTROL"):
        with db() as conn: link=bound_chat(conn)["url"]
        if link: args["reply_markup"]=json.dumps({"inline_keyboard":[[{"text":"Открыть чат Codex","url":link}]]})
    return api("sendMessage",**args)
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
def owner_event(project, kind, title, reason, next_action):
    import hashlib
    # The same condition produces at most one inbox item per UTC hour, including restarts.
    hour=datetime.now(timezone.utc).strftime("%Y%m%d%H")
    key=hashlib.sha256((project+kind+title+reason+hour).encode()).hexdigest()
    with db() as conn:
        ident=notify_owner(conn,project,kind,title,reason[:500],next_action,event_key=key)
        record(conn,"owner_notification",str(ident))
        conn.commit()
    return ident
def command(text,source_key=None):
    text=route(text)
    runtime_result=runtime_handle(text,db,source_key)
    if runtime_result is not None: return runtime_result
    if text.split("@")[0] == "/owner_inbox":
        with db() as conn: return format_owner_inbox(conn)
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
    ai30_response=ai30_handle(text)
    if ai30_response is not None: return ai30_response
    ai30_response=ai30_handle(text)
    if ai30_response is not None: return ai30_response
    parts=text.split(maxsplit=2)
    c=parts[0].split("@")[0].lower()
    if c in ("/start","/help"): return "ULTIMATE AI CONTROL v0.9\n/plan <project> <task> /repos /repo <label> /status /projects /tasks /task <project> <description> /check /taskstatus <id> /cancel <id> /approvals /approve <id> /reject <id> /audit\nAI disabled. No production changes."
    if c=="/dev31":
        if len(parts)!=2 or not parts[1].isdigit() or int(parts[1])<=0:
            return "Использование: /dev31 <номер_кодовой_заявки>"
        try:
            with db() as conn:
                row=conn.execute("SELECT project,task,manifest_json FROM github_change_requests WHERE id=?",(int(parts[1]),)).fetchone()
                if not row: return "Заявка не найдена."
                import json as _json
                bundle=prepare_v31(row[0],row[1])
                if bundle["manifest"]!=_json.loads(row[2]):
                    return "Заявка изменена: пакет не прошёл SHA-256 проверку."
                return report_v31(bundle)
        except (ValueError,PermissionError,SyntaxError) as exc:
            return "Изолированная подготовка отклонена: "+str(exc)
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
    with db() as conn: offset=int(setting(conn,"telegram_offset","0"))
    next_check=time.monotonic()+3600
    next_backup=time.monotonic()+60
    alerts=AlertLimiter(3600)
    previous_monitor={}
    previous_github={}
    next_github=time.monotonic()+120
    next_owner_delivery=time.monotonic()+1
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
                    reply(chat["id"],command(text,source_key="telegram:"+str(update["update_id"])),show_keyboard=text in ("/start", "📖 Помощь"))
                elif text.strip():
                    try:
                        with db() as conn: ident=submit_text(conn,text,event_key="telegram:"+str(update["update_id"]))
                        reply(chat["id"],f"Текстовая задача #{ident} сохранена. /job {ident}. Если потребуется решение, придёт уведомление.")
                    except ValueError as exc: reply(chat["id"],str(exc))
                elif message.get("voice"):
                    reply(chat["id"],"Распознавание голоса ещё не подключено. Отправь задачу текстом; этап есть в /roadmap.")
                with db() as conn: set_setting(conn,"telegram_offset",str(offset))
            if time.monotonic()>=next_owner_delivery:
                deliver_one(db, reply, ADMIN)
                next_owner_delivery=time.monotonic()+5
            if time.monotonic()>=next_github:
                try:
                    current_github=github_scan()
                    for alert in transitions(previous_github,current_github):
                        owner_event("control","info","Изменилось состояние GitHub",alert,"Открой /github_check в этом боте.")
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
                    if alerts.should_send('backup'):
                        owner_event("control","critical","Ошибка резервного копирования",type(exc).__name__,"Проверь /backups и журнал ULTIMATE на VPS.")
                next_backup=time.monotonic()+3600
            if time.monotonic()>=next_check:
                result=check()
                current_monitor={}
                for line in result.splitlines():
                    target, separator, detail=line.partition(': ')
                    if separator:
                        current_monitor[target]=(not detail.startswith('unavailable'),detail)
                for alert in transitions(previous_monitor,current_monitor):
                    owner_event("monitoring","info" if alert.startswith("RECOVERED") else "critical",
                                "Изменилось состояние сайта",alert,"Проверь /check. Исправления и публикации требуют отдельного согласования.")
                previous_monitor=current_monitor
                next_check=time.monotonic()+3600
        except Exception as exc:
            print("Polling error:",type(exc).__name__,flush=True)
            if alerts.should_send('polling'):
                try: reply(ADMIN,'⚠️ Ошибка Telegram-подключения. Проверь Render.')
                except Exception: pass
            time.sleep(5)
if __name__=="__main__": main()
