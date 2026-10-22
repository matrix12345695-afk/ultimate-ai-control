"""Minimal read-only project status summary from local task records."""
def project_report(connection, projects):
    rows=connection.execute("SELECT project,status,COUNT(*) FROM tasks GROUP BY project,status").fetchall()
    counts={}
    for project,state,number in rows:
        counts.setdefault(project,{})[state]=number
    lines=["📊 Отчёт по проектам",""]
    for code,name in projects.items():
        statuses=counts.get(code,{})
        detail=", ".join(f"{state}: {amount}" for state,amount in sorted(statuses.items()))
        lines.append(f"{name}: {detail or 'задач пока нет'}")
    lines.append("")
    lines.append("Учтены только локальные задачи. Состояние внешних проектов пока не подключено.")
    return "\n".join(lines)
