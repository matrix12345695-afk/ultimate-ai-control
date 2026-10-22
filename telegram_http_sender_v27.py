"""Opt-in Telegram HTTPS sender for an isolated review process.

Never imported by the production polling entrypoint. Token is injected at
runtime, never logged or persisted. Default remains disabled.
"""
import json
import urllib.request

ENDPOINT="https://api.telegram.org"

def make_sender(token,enabled=False,opener=None):
    if enabled is not True:
        raise PermissionError("External Telegram delivery disabled")
    if not isinstance(token,str) or len(token)<20 or "/" in token:
        raise ValueError("Invalid bot credential")
    opener=opener or urllib.request.urlopen
    def send(chat_id,body):
        if not isinstance(chat_id,int) or chat_id<=0:
            raise ValueError("Invalid admin chat")
        if not isinstance(body,str) or not body or len(body)>4000:
            raise ValueError("Invalid message")
        data=json.dumps({"chat_id":chat_id,"text":body,"disable_web_page_preview":True}).encode()
        request=urllib.request.Request(ENDPOINT+"/bot"+token+"/sendMessage",
            data=data,headers={"Content-Type":"application/json"},method="POST")
        with opener(request,timeout=12) as response:
            result=json.load(response)
        return result.get("ok") is True and bool(result.get("result",{}).get("message_id"))
    return send
