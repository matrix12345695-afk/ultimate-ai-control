"""Read-only allowlisted GitHub checks; no repository modifications."""
import json
import os
import urllib.request
from urllib.parse import quote
from github_readonly import allowed_repos

def inspect(label, opener=None):
    repositories=allowed_repos()
    if label not in repositories:
        return False, "не разрешён"
    name=repositories[label]
    url="https://api.github.com/repos/"+"/".join(quote(part,safe="") for part in name.split("/"))
    headers={"Accept":"application/vnd.github+json","User-Agent":"UltimateAIControl-watch"}
    token=os.getenv("GITHUB_READ_TOKEN","").strip()
    if token:
        headers["Authorization"]="Bearer "+token
    try:
        request=urllib.request.Request(url,headers=headers,method="GET")
        with (opener or urllib.request.urlopen)(request,timeout=12) as response:
            data=json.load(response)
        if data.get("full_name")!=name:
            return False, "некорректный ответ GitHub"
        return True, "доступен; обновлено "+str(data.get("pushed_at","неизвестно"))[:19]
    except Exception as error:
        return False, "ошибка "+type(error).__name__

def scan(opener=None,*,excluded=()):
    from project_retirement import canonical
    return {"GitHub "+label:inspect(label,opener) for label,name in allowed_repos().items()
            if canonical(label) not in excluded and canonical(name.rsplit('/',1)[-1]) not in excluded}
