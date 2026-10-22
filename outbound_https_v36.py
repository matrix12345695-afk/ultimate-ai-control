"""Outbound-only HTTPS channel adapter.

An independently provisioned HTTPS mailbox is required; no endpoint is
created by this module. Never send private keys or GitHub credentials.
"""
import json
import ssl
import urllib.request
from urllib.parse import urlsplit

def validate_endpoint(url):
    if not isinstance(url,str):raise ValueError("Endpoint required")
    p=urlsplit(url)
    if p.scheme!="https" or not p.hostname or p.username or p.password or p.fragment:
        raise ValueError("HTTPS endpoint without embedded credentials required")
    if p.port not in (None,443):
        raise ValueError("Nonstandard port not allowed")
    return url

class OutboundChannel:
    def __init__(self,url,transport=None,enabled=False):
        if enabled is not True:raise PermissionError("Network exchange disabled")
        self.url=validate_endpoint(url)
        self.transport=transport or urllib.request.urlopen
    def exchange(self,message):
        if not isinstance(message,dict):raise ValueError("JSON object expected")
        body=json.dumps(message,separators=(",",":"),sort_keys=True).encode("utf-8")
        if len(body)>65536:raise ValueError("Payload too large")
        request=urllib.request.Request(self.url,data=body,method="POST",headers={
            "Content-Type":"application/json","Accept":"application/json",
            "User-Agent":"ultimate-control-outbound"})
        with self.transport(request,timeout=15) as response:
            if response.status!=200:raise RuntimeError("Unexpected response status")
            raw=response.read(65537)
        if len(raw)>65536:raise ValueError("Response too large")
        parsed=json.loads(raw)
        if not isinstance(parsed,dict):raise ValueError("Invalid response")
        return parsed
