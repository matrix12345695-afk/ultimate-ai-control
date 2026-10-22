"""Read-only GitHub repository metadata. Never writes, runs code, or fetches secrets."""
import json
import os
import re
import urllib.request
from urllib.parse import quote

REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
DEFAULT_REPOS = {"control": "matrix12345695-afk/ultimate-ai-control"}

def allowed_repos():
    configured = os.getenv("GITHUB_READONLY_REPOS", "").strip()
    if not configured:
        return DEFAULT_REPOS.copy()
    result = {}
    for item in configured.split(","):
        if "=" not in item:
            continue
        label, name = (x.strip() for x in item.split("=", 1))
        if re.fullmatch(r"[a-z][a-z0-9_-]{0,30}", label) and REPO_PATTERN.fullmatch(name):
            result[label] = name
    return result

def repository_summary(label, opener=None):
    mapping = allowed_repos()
    if label not in mapping:
        return "Unknown repository. Use /repos."
    name = mapping[label]
    url = "https://api.github.com/repos/" + "/".join(quote(x, safe="") for x in name.split("/"))
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "UltimateAIControl-readonly"}
    token = os.getenv("GITHUB_READ_TOKEN", "").strip()
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(url, headers=headers, method="GET")
    opener = opener or urllib.request.urlopen
    try:
        with opener(request, timeout=12) as response:
            data = json.load(response)
        return (
            f"Repository: {data.get('full_name', name)}\n"
            f"Visibility: {'private' if data.get('private') else 'public'}\n"
            f"Default branch: {data.get('default_branch', '?')}\n"
            f"Open issues: {data.get('open_issues_count', '?')}\n"
            f"Last push: {data.get('pushed_at', '?')}\n"
            f"URL: {data.get('html_url', url)}"
        )
    except Exception as exc:
        return f"GitHub read failed ({type(exc).__name__}). Check access/token."

def command(text):
    parts = text.split()
    op = parts[0].split("@")[0].lower() if parts else ""
    if op == "/repos":
        return "\n".join(f"{k}: {v}" for k, v in allowed_repos().items()) or "No repositories configured."
    if op == "/repo":
        return repository_summary(parts[1]) if len(parts) == 2 else "Usage: /repo <label>"
    return None
