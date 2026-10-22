"""ULTIMATE AI CONTROL: Telegram dispatcher, no paid APIs or external write actions."""
import os, json, time, sqlite3, urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime, timezone
from telegram_pro import initialize, handle, record
from github_readonly import command as github_command
from planner import plan, format_plan
from ai_provider import status as ai_status, propose as ai_propose
from control_v08 import setup as setup_v08, save_proposal, list_proposals, proposal_detail, budget_status

BASE=Path(__file__).parent
DB=Path(os.getenv("DB_PATH",str(BASE/"data"/"control.db")))
TOKEN=os.getenv("TELEGRAM_BOT_TOKEN","")
ADMIN=os.getenv("ADMIN_TELEGRAM_ID","")
URL=os.getenv("MONITOR_URLS","https://novaweb.uz/").split(",")
PROJECTS={"nova":"NOVA WEB","inventory":"Inventory","sap":"SAP / iiko","kinder":"Kinder Spa","qualisift":"QualiSift"}
def db():
    DB.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY, project TEXT, description TEXT, created_at TEXT)")
    initialize(c)
    setup_v08(c)
    c.commit()
    return c
def api(method,**kwargs):
    data=urllib.parse.urlencode(kwargs).encode()
    with urllib.request.urlopen(f"https://api.telegram.org/bot{TOKEN}/{method}",data=data,timeout=35) as response:
        return json.load(response)["result"]
def reply(chat,msg): api("sendMessage",chat_id=chat,text=msg[:4000])
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
    github_result=github_command(text)
    if github_result is not None:
        return github_result
    extra=handle(text, db, ADMIN)
    if extra is not None: return extra
    parts=text.split(maxsplit=2)
    c=parts[0].split("@")[0].lower()
    if c in ("/start","/help"): return "ULTIMATE AI CONTROL v0.8\n/plan <project> <task> /repos /repo <label> /status /projects /tasks /task <project> <description> /check /taskstatus <id> /cancel <id> /approvals /approve <id> /reject <id> /audit\nAI disabled. No production changes."
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
                if text.startswith("/"): reply(chat["id"],command(text))
            if time.monotonic()>=next_check:
                result=check()
                if "unavailable" in result: reply(ADMIN,result)
                next_check=time.monotonic()+3600
        except Exception as exc:
            print("Polling error:",type(exc).__name__,flush=True)
            time.sleep(5)
if __name__=="__main__": main()
