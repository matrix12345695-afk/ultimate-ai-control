"""Read-only owner follow-ups projected from the durable inbox and owner settings.

Deferred setup is not approval or completed provisioning. No delivery, resolution,
provider access or scheduling happens here; critical requests stay visible.
"""
import math
import roadmap

PAGE_SIZE = 4


def compact(value, limit):
    text = ' '.join(str(value).split())
    return text if len(text) <= limit else text[:limit-1] + '…'


def number(value):
    if (not isinstance(value, str) or not value.isascii() or not value.isdecimal()
            or not 1 <= len(value) <= 19 or value.startswith('0')):
        raise ValueError('Нужен положительный номер.')
    result = int(value)
    if result > 9223372036854775807:
        raise ValueError('Слишком большой номер.')
    return result


def describe(conn, page=1):
    if type(page) is not int or page < 1:
        raise ValueError('Нужен положительный номер страницы.')
    counts = dict(conn.execute("SELECT kind,count(*) FROM owner_notifications WHERE state='pending' AND kind IN ('critical','decision') GROUP BY kind"))
    total = sum(counts.values())
    pages = max(1, math.ceil(total/PAGE_SIZE))
    if page > pages:
        return f'Такой страницы нет. Страниц: {pages}. /owner_later 1'
    lines = ['📌 Для владельца · сохранено в журнале']
    if roadmap.setting(conn, 'provider_setup_deferred') == 'true':
        lines.append('Отложено тобой: подключение API. Пока ничего делать не нужно; платные вызовы остаются выключенными. Вернёмся к настройке, когда ты будешь готов.')
    if not roadmap.setting(conn, 'current_chat_url'):
        lines.append('Позже, по желанию: /chat_bind <ссылка на этот чат> для кнопки возврата. Отсутствие ссылки не мешает независимым задачам.')
    lines.append(f'Нерешённых критических запросов: {counts.get("critical",0)}. Требуют решения: {counts.get("decision",0)}. Страница {page}/{pages}.')
    rows = conn.execute("""SELECT id,kind,project,title,reason,next_action,delivered_at
        FROM owner_notifications WHERE state='pending' AND kind IN ('critical','decision')
        ORDER BY CASE kind WHEN 'critical' THEN 0 ELSE 1 END,id LIMIT ? OFFSET ?""",
        (PAGE_SIZE,(page-1)*PAGE_SIZE)).fetchall()
    for ident,kind,project,title,reason,action,delivered in rows:
        label = '🔴 Критическое' if kind == 'critical' else '🟡 Решение'
        lines.append(f'\n{label} #{ident} · {compact(project,45)}: {compact(title,90)}\nПричина: {compact(reason,140)}\nЧто сделать: {compact(action,230)}\nПодробности: /owner_item {ident}. Telegram: '+('доставка записана' if delivered else 'доставка не подтверждена'))
    if not rows:
        lines.append('Активных запросов на решение нет. Отложенные настройки сохраняются отдельно.')
    if page < pages:
        lines.append(f'\nДальше: /owner_later {page+1}')
    lines.append('\nПросмотр списка ничего не одобряет и не закрывает. Новые публикации согласуются отдельно по проекту и версии.')
    return '\n'.join(lines)


def detail(conn, ident):
    if type(ident) is not int or not 1 <= ident <= 9223372036854775807:
        raise ValueError('Нужен положительный номер запроса.')
    row = conn.execute('''SELECT project,kind,state,title,reason,next_action,task_id,
        created_at,resolved_at,delivered_at,telegram_message_id,event_key
        FROM owner_notifications WHERE id=?''',(ident,)).fetchone()
    if not row:
        return 'Запрос не найден. /owner_later'
    project,kind,state,title,reason,action,task,created,resolved,delivered,message,key = row
    status = 'ожидает решения' if state == 'pending' else 'закрыт в журнале'
    if state == 'resolved' and key in ('runtime-needs-ai-executor-v4','developer-private-key-setup-v1') and roadmap.setting(conn,'provider_setup_deferred') == 'true':
        status = 'отложено владельцем; подключение API не выполнено'
    lines = [f'Запрос #{ident} · {compact(kind,20)} · {compact(project,100)}',
             'Статус: '+status, 'Тема: '+compact(title,500),
             'Причина: '+compact(reason,500), ('Что сделать: ' if state == 'pending' else 'В исходном запросе: ')+compact(action,500),
             'Создан: '+compact(created,80)]
    if task: lines.append('Задача: '+compact(task,100))
    if resolved: lines.append('Закрыт: '+compact(resolved,80))
    lines.append('Telegram: '+(f'доставка записана, сообщение {message}' if delivered and message else 'доставка не подтверждена'))
    lines.append('Доставка не подтверждает прочтение. Просмотр и закрытие запроса не разрешают публикацию или оплату.')
    return '\n'.join(lines)
