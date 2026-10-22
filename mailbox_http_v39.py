"""Minimal WSGI mailbox API. Not mounted or listening until explicitly deployed.

TLS termination, IP restrictions and rate limits must be configured outside
this component. The handler never accepts identity from request JSON.
"""
import json
from mailbox_api_v38 import MailboxAPI

class MailboxHTTP:
    def __init__(self,api): self.api=api

    def __call__(self,environ,start_response):
        def respond(status,data):
            blob=json.dumps(data,separators=(",",":"),ensure_ascii=False).encode()
            start_response(status,[("Content-Type","application/json"),("Content-Length",str(len(blob))),
                                   ("Cache-Control","no-store")])
            return [blob]
        try:
            method=environ.get("REQUEST_METHOD","")
            path=environ.get("PATH_INFO","")
            header=environ.get("HTTP_AUTHORIZATION","")
            if not header.startswith("Bearer ") or len(header)>300:
                raise PermissionError("Bearer authorization required")
            token=header[7:]
            if method=="POST" and path in ("/v1/submit","/v1/confirm"):
                rawlen=environ.get("CONTENT_LENGTH","")
                if not rawlen.isdigit() or int(rawlen)>65536:
                    return respond("413 Payload Too Large",{"error":"size"})
                body=environ["wsgi.input"].read(int(rawlen))
                payload=json.loads(body)
                if not isinstance(payload,dict):raise ValueError("Object required")
                if path=="/v1/submit":
                    self.api.submit(token,payload["message_id"],payload["envelope"])
                    return respond("201 Created",{"state":"pending"})
                self.api.confirm(token,payload["message_id"],payload["receipt"])
                return respond("200 OK",{"state":"acknowledged"})
            if method=="POST" and path=="/v1/acquire":
                row=self.api.acquire(token)
                return respond("200 OK",{"item":{"message_id":row[0],"envelope":row[1]} if row else None})
            if method=="POST" and path=="/v1/receipt":
                rawlen=environ.get("CONTENT_LENGTH","")
                if not rawlen.isdigit() or int(rawlen)>1024:
                    return respond("413 Payload Too Large",{"error":"size"})
                payload=json.loads(environ["wsgi.input"].read(int(rawlen)))
                if not isinstance(payload,dict):raise ValueError("Object required")
                row=self.api.receipt(token,payload["message_id"])
                return respond("200 OK",{"receipt":row})
            return respond("404 Not Found",{"error":"route"})
        except PermissionError:
            return respond("403 Forbidden",{"error":"access denied"})
        except (ValueError,TypeError,KeyError,UnicodeDecodeError,json.JSONDecodeError):
            return respond("400 Bad Request",{"error":"invalid request"})
        except Exception:
            return respond("500 Internal Server Error",{"error":"internal error"})
