"""Opt-in AI planning adapter. Disabled by default. No auto execution.

Provider is explicitly configured by the operator; paid APIs are never invoked
unless AI_ENABLED=true AND a key and approved endpoint are configured.
"""
import json
import os
import re
import urllib.request
from urllib.parse import urlparse

REDACT_RE = re.compile(r"(?i)(sk-[A-Za-z0-9_-]{12,}|(?:token|password|api[_-]?key|secret)\s*[:=]\s*\S+)")
MAX_PROMPT_CHARS = 2500
MAX_RESPONSE_BYTES = 12000

def status():
    return {
        "enabled": os.getenv("AI_ENABLED","false").lower()=="true",
        "provider": os.getenv("AI_PROVIDER","none"),
        "model": os.getenv("AI_MODEL","unconfigured"),
        "budget_usd": os.getenv("AI_MONTHLY_BUDGET_USD","0"),
    }

def build_request(project, task):
    if not re.fullmatch(r"[a-z][a-z0-9_-]{0,30}",project):
        raise ValueError("Invalid project identifier")
    if not task or len(task)>MAX_PROMPT_CHARS:
        raise ValueError("Invalid task length")
    if REDACT_RE.search(task):
        raise ValueError("Request appears to contain a secret")
    return {
        "model": os.getenv("AI_MODEL",""),
        "messages": [
            {"role":"system","content":"You are a planning assistant. Return a short implementation plan, risk assessment and test checklist. Never claim code was changed. Never ask for credentials."},
            {"role":"user","content":f"Project: {project}\nTask: {task}"}
        ],
        "max_tokens": 450,
    }

def propose(project, task):
    cfg=status()
    if not cfg["enabled"]:
        return "AI is disabled. Use /plan for the free offline planner."
    # API billing protection: no call without an explicit positive monthly budget.
    try: budget=float(cfg["budget_usd"])
    except ValueError: budget=0
    if budget<=0:
        return "AI request blocked: no approved budget."
    if cfg["provider"]!="openai_compatible":
        return "AI request blocked: provider is not configured."
    key=os.getenv("AI_API_KEY","")
    endpoint=os.getenv("AI_ENDPOINT","")
    host=urlparse(endpoint)
    allow_hosts={h.strip() for h in os.getenv("AI_ALLOWED_HOSTS","").split(",") if h.strip()}
    if not key or not cfg["model"] or host.scheme!="https" or not host.hostname or host.hostname not in allow_hosts or host.username or host.password:
        return "AI request blocked: missing key/model or endpoint not allowlisted."
    body=json.dumps(build_request(project,task)).encode()
    req=urllib.request.Request(endpoint,data=body,method="POST",
        headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=20) as res:
            if int(res.headers.get("Content-Length","0"))>MAX_RESPONSE_BYTES:
                return "AI response blocked: too large."
            raw=res.read(MAX_RESPONSE_BYTES+1)
            if len(raw)>MAX_RESPONSE_BYTES: return "AI response blocked: too large."
        result=json.loads(raw)
        message=result["choices"][0]["message"]["content"]
        return str(message)[:3500]
    except Exception as exc:
        return f"AI request failed ({type(exc).__name__})."
