"""Commands are called only after main.py authenticates the private Telegram owner."""
import json
import time
import task_queue as queue
import roadmap
import health_incidents
import owner_followups
import project_registry
import work_analytics
import readiness_monitor
import acceptance_checks
import evidence_memory
import nova_project_tests
import artifact_prs
import release_preflight
import vps_resources
import nova_ci
import browser_ci
import browser_candidate_ci
import nova_release_ci
import locked_build_ci
import nova_deploy
import chat_binding
import budget_gate
import offline_developer
import metered_provider
import model_broker
from isolated_python import load_policy, SandboxUnavailable
from pathlib import Path
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
    known={"/roadmap","/queue","/job","/work","/project","/agents","/daily","/memory","/budget4","/pause","/resume","/chat_link","/chat_bind","/job_cancel","/sandbox","/recipe","/selftest","/artifact","/artifact_code","/provider4","/broker4","/develop","/developer_demo"}
    known.add('/monitor4')
    known.update(('/owner_later','/owner_item'))
    known.update(('/projects4','/repo_check'))
    known.update(('/analytics4','/weekly','/cost4'))
    known.add('/readiness4')
    known.add('/acceptance4')
    known.update(('/memory_log','/memory_item'))
    known.update(('/test_nova','/nova_tests'))
    known.update(('/nova_build','/test_nova_build','/nova_deploy','/test_nova_deploy'))
    known.update(('/test_nova_browser','/nova_browser','/nova_candidate','/test_nova_candidate','/nova_release','/test_nova_release'))
    known.update(('/test_nova_pg','/nova_pg'))
    known.update(('/vps4','/vps_check'))
    known.update(('/release_check','/release_checks'))
    known.update(('/artifact_pr','/artifact_prs','/artifact_pr_status','/artifact_pr_refresh','/artifact_release'))
    if op not in known: return None
    with connect() as conn:
        try:
            if op=='/nova_deploy': return nova_deploy.describe(conn)
            if op=='/test_nova_deploy':
                if len(args)!=1: return 'Использование: /test_nova_deploy'
                ident=queue.enqueue(conn,'nova','test_release',{'target':nova_deploy.PROFILE},max_attempts=5,event_key=source_key)
                return f'Проверка плана выпуска #{ident} в очереди. /nova_deploy. Только чтение CI и симулятор; сайт/Render не изменяются.'
            if op=='/nova_build': return locked_build_ci.describe(conn)
            if op=='/test_nova_build':
                if len(args)!=1: return 'Использование: /test_nova_build'
                ident=queue.enqueue(conn,'nova','test_release',{'target':locked_build_ci.PROFILE},max_attempts=5,event_key=source_key)
                return f'Сверка закреплённой сборки NOVA #{ident} в очереди. /nova_build. Чтение CI, без публикации и изменения Render.'
            if op=='/nova_release': return nova_release_ci.describe(conn)
            if op=='/test_nova_release':
                if len(args)!=1: return 'Использование: /test_nova_release'
                ident=queue.enqueue(conn,'nova','test_release',{'target':nova_release_ci.PROFILE},max_attempts=5,event_key=source_key)
                return f'Сверка репетиции выпуска NOVA #{ident} в очереди. /nova_release. Чтение CI; Render и сайт не изменяются.'
            if op=='/nova_candidate': return browser_candidate_ci.describe(conn)
            if op=='/test_nova_candidate':
                if len(args)!=1: return 'Использование: /test_nova_candidate'
                ident=queue.enqueue(conn,'nova','test_release',{'target':browser_candidate_ci.PROFILE},max_attempts=5,event_key=source_key)
                return f'Сверка черновика NOVA #{ident} в очереди. /nova_candidate. Только чтение CI, публикации нет.'
            if op=='/nova_browser': return browser_ci.describe(conn)
            if op=='/test_nova_browser':
                if len(args)!=1: return 'Использование: /test_nova_browser'
                ident=queue.enqueue(conn,'nova','test_release',{'target':browser_ci.PROFILE},max_attempts=5,event_key=source_key)
                return f'Сверка браузерного CI #{ident} в очереди. /nova_browser. Только чтение результата; браузер на VPS не запускается.'
            if op=='/nova_pg': return nova_ci.describe(conn)
            if op=='/test_nova_pg':
                if len(args)!=1: return 'Использование: /test_nova_pg'
                ident=queue.enqueue(conn,'nova','test_release',{'target':nova_ci.PROFILE},max_attempts=5,event_key=source_key)
                return f'Сверка PostgreSQL CI #{ident} в очереди. /nova_pg. Только чтение CI; новая БД на VPS не запускается.'
            if op=='/vps4': return vps_resources.describe(conn)
            if op=='/vps_check':
                if len(args)!=1: return 'Использование: /vps_check'
                ident=queue.enqueue(conn,'control','inspect_repository',{'target':vps_resources.TARGET},event_key=source_key)
                return f'Замер ресурсов VPS #{ident} в очереди. /vps4. Только чтение; сервисы и файлы не изменяются.'
            if op=='/release_checks': return release_preflight.describe(conn)
            if op=='/release_check':
                if len(args)!=2: return 'Использование: /release_check ID_заявки_PR'
                ident=owner_followups.number(args[1]);identity,_,_=artifact_prs.record(conn,ident)
                job=queue.enqueue(conn,'control','review_change',{'artifact_pr':identity['artifact_id'],'refresh':True,'release_check':True},max_attempts=5,event_key=source_key)
                return f'Проверка перед выпуском #{job} в очереди. Чтение GitHub и локальная сверка; согласование не создаётся, публикация отключена. /release_checks'
            if op=='/artifact_prs': return artifact_prs.describe(conn)
            if op=='/artifact_pr_status':
                if len(args)!=2: return 'Использование: /artifact_pr_status ID'
                return artifact_prs.describe(conn,owner_followups.number(args[1]))
            if op=='/artifact_release':
                if len(args)!=2: return 'Использование: /artifact_release ID'
                ident,aid,scope=artifact_prs.request_release(conn,owner_followups.number(args[1]))
                return (f'Согласование версии #{ident}\nПроект: control\nCommit: {scope["head_sha"]}\n'
                        +f'Артефакт SHA-256: {scope["artifact_sha256"]}\nОдобрить: /approve {aid}\nОтклонить: /reject {aid}'
                        +'\nДействует 60 минут только для этой версии. Решение сохраняется; исполнитель публикации ещё не подключён. Изменение PR/CI требует нового согласования.')
            if op in ('/artifact_pr','/artifact_pr_refresh'):
                if len(args)!=2: return 'Использование: '+op+' ID'
                ident=owner_followups.number(args[1]);payload={'artifact_pr':ident}
                if op=='/artifact_pr_refresh':
                    identity,_,_=artifact_prs.record(conn,ident);payload={'artifact_pr':identity['artifact_id'],'refresh':True}
                else: artifact_prs.material(conn,ident,Path(conn.execute('PRAGMA database_list').fetchone()[2]).parent)
                job=queue.enqueue(conn,'control','review_change',payload,max_attempts=5,
                                  event_key=source_key if op=='/artifact_pr_refresh' else 'artifact-pr-v1:'+str(ident))
                return f'Задание #{job} сохранено. Только отдельная ветка/Draft PR или проверка существующего PR. Merge и deploy запрещены. /artifact_prs'
            if op=='/nova_tests': return nova_project_tests.describe(conn)
            if op=='/test_nova':
                if len(args)!=1: return 'Использование: /test_nova'
                ident=queue.enqueue(conn,'nova','test_release',{'target':nova_project_tests.PROFILE},event_key=source_key)
                return f'Закреплённые проверки NOVA WEB #{ident} в очереди. Без npm, PostgreSQL, сети и публикации. Результат: /nova_tests и /job {ident}.'
            if op=='/memory_log':
                project=args[1] if len(args)>1 else roadmap.setting(conn,'active_project','control')
                page=owner_followups.number(args[2]) if len(args)==3 else 1
                return evidence_memory.summary(conn,project,page)
            if op=='/memory_item':
                if len(args)!=2: return 'Использование: /memory_item <номер>'
                return evidence_memory.detail(conn,owner_followups.number(args[1]))
            if op=='/monitor4': return health_incidents.describe(conn)
            if op=='/acceptance4': return acceptance_checks.describe(conn)
            if op=='/readiness4':
                if len(args)!=1: return 'Использование: /readiness4'
                ident=queue.enqueue(conn,'nova','check_site',{'target':readiness_monitor.TARGET},event_key=source_key)
                return f'Проверка API и готовности хранилища NOVA WEB #{ident} в очереди. Только GET /health, без записи в приложение. Результат: /job {ident} и /monitor4.'
            if op in ('/analytics4','/weekly','/daily'):
                if op=='/analytics4' and (len(args)>2 or (len(args)==2 and args[1] not in ('24h','7d'))):
                    return 'Использование: /analytics4 24h или /analytics4 7d'
                return work_analytics.describe(conn,7 if op=='/weekly' or (len(args)==2 and args[1]=='7d') else 1)
            if op=='/cost4':
                if len(args)!=2: return 'Использование: /cost4 <номер задачи>'
                return work_analytics.job_cost(conn,owner_followups.number(args[1]))
            if op=='/projects4': return project_registry.describe(conn)
            if op=='/repo_check':
                if len(args)!=2: return 'Использование: /repo_check nova или /repo_check kinder'
                payload={'target':args[1],'source':project_registry.METHOD}
                project_registry.check_scope(args[1],payload)
                ident=queue.enqueue(conn,args[1],'inspect_repository',payload,event_key=source_key)
                return f'Проверка файлов #{ident} поставлена в очередь. Только чтение закреплённой версии и сверка хешей; установки, запуска кода и публикации нет. /job {ident}'
            if op=='/owner_later':
                if len(args)>2: return 'Использование: /owner_later [страница]'
                return owner_followups.describe(conn,owner_followups.number(args[1]) if len(args)==2 else 1)
            if op=='/owner_item':
                if len(args)!=2: return 'Использование: /owner_item <номер>'
                return owner_followups.detail(conn,owner_followups.number(args[1]))
            if op=='/broker4':
                folder=Path(conn.execute('PRAGMA database_list').fetchone()[2]).parent
                result=model_broker.status(conn,folder)
                return ('Посредник модели: отдельный короткоживущий процесс.\n'
                        +'Генерация через OpenAI: '+('разрешена политикой' if result['enabled'] and result['allow_paid'] else 'выключена')
                        +'\nДемонстрация без LLM: '+('разрешена' if result['allow_demo'] else 'выключена')
                        +'\nСохранённые пакеты: '+json.dumps(result['bundles'],ensure_ascii=False)
                        +'\nКлюч здесь не читается. Черновики проходят отдельное задание изолированных тестов; публикации требуют согласования.')
            if op in ('/develop','/developer_demo'):
                if op=='/developer_demo':
                    if len(args)!=1: return 'Использование: /developer_demo'
                    payload={'ai_task':model_broker.DEMO_TASK,'broker_demo':True,'source':'telegram'}
                else:
                    if len(args)!=3 or args[1]!='control': return 'Использование: /develop control Описание. Пока разрешены только отдельные Python-черновики ULTIMATE.'
                    if not 1<=len(args[2])<=2500 or SECRET.search(args[2]): raise ValueError('invalid_or_sensitive_developer_task')
                    payload={'ai_task':args[2],'source':'telegram'}
                ident=queue.enqueue(conn,'control','review_change',payload,event_key=source_key)
                return f'Задание разработчика #{ident} сохранено. Генерация и изолированные тесты — отдельные этапы. Демонстрация не вызывает LLM; платная модель требует приватной настройки. /job {ident}'
            if op=='/provider4':
                folder=Path(conn.execute('PRAGMA database_list').fetchone()[2]).parent
                result=metered_provider.status(conn,folder/'provider-policy.json')
                return ('OpenAI: транспорт с учётом расходов подготовлен.\n'
                        +'Политика: '+('включена' if result['policy_enabled'] else 'выключена/не настроена')
                        +'\nМодель: '+result['model']
                        +'\nНеразрешённых резервов: '+str(result['unresolved_reservations'])
                        +'\nУчтено/зарезервировано: $'+f"{result['accounted_usd']:.4f}"
                        +'\nОчередь разработчика: /broker4. Ключ настраивается приватно на VPS; не отправляй его сюда.')
            if op=='/sandbox':
                try: cfg=load_policy(Path(conn.execute('PRAGMA database_list').fetchone()[2]).parent/'sandbox-policy.json')
                except (OSError,ValueError,SandboxUnavailable): return 'Изолированный исполнитель не настроен или проверка целостности не прошла.'
                return 'Bubblewrap: настроен. Сеть, новые процессы и потоки запрещены. Один CPU, 320 MiB, максимум 20 сек.\n'+('Scratch: 32 MiB.' if cfg['writable_tmp'] else 'Файловая система только для чтения; файловые тесты пока не поддерживаются.')
            if op=='/recipe':
                if len(args)!=2 or args[1] not in ('safe-paths','sha-check'): return 'Использование: /recipe safe-paths или /recipe sha-check. Это детерминированный генератор, не LLM.'
                ident=queue.enqueue(conn,'control','review_change',{'recipe':args[1]},event_key=source_key)
                return f'Кодовый рецепт #{ident} поставлен в очередь. Генерация → изолированные тесты → артефакт. Публикации нет.'
            if op=='/selftest':
                ident=queue.enqueue(conn,'control','test_release',{'target':'sandbox-smoke'},event_key=source_key)
                return f'Проверка изоляции #{ident} поставлена в очередь. /job {ident}'
            if op=='/artifact':
                if len(args)!=2 or not args[1].isdigit(): return 'Использование: /artifact <номер>'
                return offline_developer.describe(conn,int(args[1]))
            if op=='/artifact_code':
                if len(args)<2 or not args[1].isdigit() or (len(args)==3 and not args[2].isdigit()): return 'Использование: /artifact_code <номер> [номер файла]'
                return offline_developer.source_preview(conn,int(args[1]),int(args[2]) if len(args)==3 else 1)
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
            if op=="/memory":
                if len(args)>2: return 'Использование: /memory [проект]'
                project=args[1] if len(args)==2 else roadmap.setting(conn,"active_project","control")
                row=conn.execute("SELECT content,source FROM project_memory WHERE project=?",(project,)).fetchone()
                return (json.dumps(json.loads(row[0]),ensure_ascii=False,indent=2)+"\nИсточник: "+row[1])[:3400]+'\nПроверяемая история: /memory_log '+project if row else "Память проекта не найдена."
            if op=="/budget4":
                result=budget_gate.summary(conn)
                return f"Месячный предел: $30.\nУчтено/зарезервировано: ${result['accounted_usd']:.4f}.\nОстаток: ${result['remaining_usd']:.4f}.\nПлатный провайдер отключён; это локальный реестр, не счёт OpenAI."
        except (ValueError,PermissionError) as exc:
            return "Отклонено: "+str(exc)[:500]
