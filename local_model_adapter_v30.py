"""Opt-in localhost-only chat-completion adapter for v3.0 planning.

Calls only 127.0.0.1:PORT through a separately provided local inference server.
It never executes model output, writes files, sends secrets or talks to paid APIs.
Disabled unless explicitly enabled in the operator's private environment.
"""
import ipaddress
import json
import os
import urllib.request
from urllib.parse import urlsplit

from ai_review_contract_v30 import prepare_task, validate_response

MAX_BYTES = 12000

def local_endpoint(url):
    if not isinstance(url, str):
        raise ValueError("Endpoint invalid")
    parsed = urlsplit(url)
    if parsed.scheme != "http" or parsed.username or parsed.password:
        raise ValueError("Only plain HTTP on local loopback is allowed")
    try:
        host = ipaddress.ip_address(parsed.hostname or "")
    except ValueError as exc:
        raise ValueError("IP literal required") from exc
    if host != ipaddress.ip_address("127.0.0.1"):
        raise ValueError("Only 127.0.0.1 allowed")
    if parsed.port is None or not 1024 <= parsed.port <= 65535:
        raise ValueError("Explicit unprivileged port required")
    if parsed.path != "/v1/chat/completions" or parsed.query or parsed.fragment:
        raise ValueError("Unrecognized endpoint path")
    return url

def request_local_plan(project, task, model, endpoint, enabled=False, opener=None):
    if enabled is not True:
        raise PermissionError("Local model disabled")
    if not isinstance(model,str) or not 1 <= len(model) <= 100 or any(x in model for x in "/\\\n\r"):
        raise ValueError("Invalid model")
    endpoint = local_endpoint(endpoint)
    spec = prepare_task(project, task)
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": spec["system"]},
            {"role": "user", "content": "Project: "+project+"\nTask: "+task},
        ],
        "stream": False,
        "temperature": 0,
        "max_tokens": 900,
    }).encode("utf-8")
    req = urllib.request.Request(
        endpoint, data=body, method="POST",
        headers={"Content-Type": "application/json"},
    )
    with (opener or urllib.request.urlopen)(req, timeout=25) as response:
        if int(response.headers.get("Content-Length","0")) > MAX_BYTES:
            raise ValueError("Oversized response")
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("Oversized response")
    result = json.loads(raw)
    message = result["choices"][0]["message"]["content"]
    return validate_response(message)

def environment_ready(env=None):
    values = os.environ if env is None else env
    if values.get("LOCAL_AI_ENABLED") != "true":
        return {"ready": False, "reason": "disabled"}
    try:
        local_endpoint(values.get("LOCAL_AI_ENDPOINT",""))
    except ValueError:
        return {"ready": False, "reason": "endpoint_invalid"}
    if not values.get("LOCAL_AI_MODEL"):
        return {"ready": False, "reason": "model_missing"}
    return {"ready": True, "reason": "configured_not_tested"}
