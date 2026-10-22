"""Commands are called only after main.py authenticates the private Telegram owner."""
import json
import time
import task_queue as queue
import roadmap
import chat_binding
import budget_gate
from ai_gateway_v30 import SECRET


def submit_text(conn,text,*,project=None,source="telegram",event_key=None):
    project=project or roadmap.setting(conn,"active_project","control")
    if not isinstance(text,str) or not 1<=len(text.strip())<=2500 or SECRET.search(text):
        raise ValueError("Пустая/слишком длинная задача или возможный секрет. Секреты в задачах запрещены.")
    return queue.enqueue(conn,project,"plan_change",{"text":text.strip(),"source":source},event_key=event_key)


def handle(text,connect,source_key=None):
    args=text.split(maxsplit=2)
    if not args: return None
    op=args[0].split("@")[0].lower()
    known={"/roadmap","/queue","/job","/work","/project","/agents","/daily","/memory","/budget4","/pause","/resume","/chat_link","/chat_bind","/job_cancel"}
    if op not in known: return None
    with connect() as conn:
        try:
            if op=="/roadmap": return roadmap.describe(conn)
            if op=="/chat_bind":
                if len(args)!=2: return "Использование: /chat_bind https://chatgpt.com/c/..."
                chat_binding.bind(conn,args[1])
                return "Ссылка возврата в этот чат сохранена. Чтение сообщений ChatGPT автоматически не включено."
            if op=="/chat_link": return chat_binding.action(conn)+"\nПлан из текущего чата импортирован явно; автоматического доступа к его новым сообщениям нет."
            if op in ("/pause","/resume"):
                queue.configure(conn,paused=op=="/pause",reason="Telegram owner request")
                return "Новые задания приостановлены. Текущие безопасные проверки завершаются. Inventory не затрагивается." if op=="/pause" else "Очередь возобновлена."
            if op=="/project":
                if len(args)==1: return "Активный проект: "+roadmap.setting(conn,"active_project","control")+"\nВыбрать: /project nova"
                if len(args)!=2 or args[1] not in queue.PROJECTS: return "Проект не включён. Inventory защищён."
                roadmap.set_setting(conn,"active_project",args[1])
                return "Активный проект: "+args[1]
            if op=="/work":
                if len(args)!=3: return "Использование: /work nova Описание задачи"
                ident=submit_text(conn,args[2],project=args[1],event_key=source_key)
                return f"Задача #{ident} сохранена в исполняемой очереди. Статус: /job {ident}. Разработка кода ожидает подключения изолированного AI-исполнителя."
            if op=="/queue":
                rows=conn.execute("SELECT id,project,kind,state FROM agent_jobs ORDER BY id DESC LIMIT 15").fetchall()
                paused=conn.execute("SELECT paused FROM agent_queue_control WHERE singleton=1").fetchone()[0]
                return ("Очередь приостановлена\n" if paused else "Очередь активна\n")+("\n".join(f"#{i} {p} · {k} · {s}" for i,p,k,s in rows) or "Задач пока нет.")
            if op in ("/job","/job_cancel"):
                if len(args)!=2 or not args[1].isdigit(): return "Использование: "+op+" <номер>"
                ident=int(args[1])
                if op=="/job_cancel": return "Задача отменена." if queue.cancel(conn,ident) else "Задача не ожидает или отсутствует."
                row=conn.execute("SELECT project,kind,state,attempts,result,last_error FROM agent_jobs WHERE id=?",(ident,)).fetchone()
                return f"#{ident} · {row[0]} · {row[1]}\nСтатус: {row[2]} · попыток: {row[3]}\n{row[4] or row[5] or ''}"[:3900] if row else "Задача не найдена."
            if op=="/agents":
                rows=conn.execute("SELECT worker,heartbeat,state,detail FROM agent_worker_status").fetchall()
                if not rows: return "Исполнитель ещё не зарегистрировался."
                return "\n".join(f"{w}: {state}, heartbeat {max(0,time.time()-at):.0f} сек. назад, задача {detail or '—'}" for w,at,state,detail in rows)+"\nAI-разработчик, дизайнер и голосовой агент ещё не активированы."
            if op=="/daily":
                now=time.time()
                report=queue.report(conn,now-86400,now)
                rows=report["measured_seconds"]
                return "Реальные интервалы за 24 часа:\n"+("\n".join(f"{r['worker']} · {r['project']} · {r['category']}: {r['seconds']:.2f} сек." for r in rows) or "Измерений ещё нет.")+"\nСобытия: "+json.dumps(report["events"],ensure_ascii=False)+"\nНезаписанное время считается неизвестным."
            if op=="/memory":
                project=args[1] if len(args)==2 else roadmap.setting(conn,"active_project","control")
                row=conn.execute("SELECT content,source FROM project_memory WHERE project=?",(project,)).fetchone()
                return (json.dumps(json.loads(row[0]),ensure_ascii=False,indent=2)+"\nИсточник: "+row[1])[:3900] if row else "Память проекта не найдена."
            if op=="/budget4":
                result=budget_gate.summary(conn)
                return f"Месячный предел: $30.\nУчтено/зарезервировано: ${result['accounted_usd']:.4f}.\nОстаток: ${result['remaining_usd']:.4f}.\nПлатный провайдер отключён; это локальный реестр, не счёт OpenAI."
        except (ValueError,PermissionError) as exc:
            return "Отклонено: "+str(exc)[:500]
