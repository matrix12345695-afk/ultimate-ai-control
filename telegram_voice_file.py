"""Bot credential stays in the authenticated dispatcher. No redirect or arbitrary URL."""
import json
import base64
import ctypes
import os
import re
import resource
import signal
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from voice_native import MAX_BYTES,VoiceError

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None

def _read(response,limit,deadline):
    # read1 makes at most one underlying read; read(n) can hide a slow stream loop.
    data=bytearray()
    while True:
        if time.monotonic()>=deadline:raise VoiceError('voice_download_timeout')
        part=response.read1(min(16384,limit+1-len(data)))
        if not part:break
        data.extend(part)
        if len(data)>limit:raise VoiceError('voice_download_size')
    if time.monotonic()>deadline:raise VoiceError('voice_download_timeout')
    return bytes(data)

def fetch(token,file_id,*,opener=None):
    if not isinstance(token,str) or not re.fullmatch(r'[0-9]+:[A-Za-z0-9_-]{20,150}',token): raise VoiceError('voice_bot_unavailable')
    if not isinstance(file_id,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,200}',file_id): raise VoiceError('voice_file_id')
    opener=opener or urllib.request.build_opener(NoRedirect()).open
    deadline=time.monotonic()+6
    try:
        request=urllib.request.Request('https://api.telegram.org/bot'+token+'/getFile',data=urllib.parse.urlencode({'file_id':file_id}).encode())
        with opener(request,timeout=2) as response: raw=_read(response,32768,deadline)
        doc=json.loads(raw);result=doc.get('result')
        if doc.get('ok') is not True or not isinstance(result,dict): raise VoiceError('voice_file_metadata')
        path=result.get('file_path');size=result.get('file_size')
        if (not isinstance(path,str) or not re.fullmatch(r'voice/[A-Za-z0-9_-]{1,160}\.(?:oga|ogg|opus)',path)
            or (size is not None and (type(size) is not int or not 1<=size<=MAX_BYTES))): raise VoiceError('voice_file_path_or_size')
        if time.monotonic()>=deadline: raise VoiceError('voice_download_timeout')
        request=urllib.request.Request('https://api.telegram.org/file/bot'+token+'/'+path)
        with opener(request,timeout=2) as response:
            data=_read(response,MAX_BYTES,deadline)
        if size is not None and len(data)!=size: raise VoiceError('voice_download_truncated')
        return data
    except VoiceError: raise
    except Exception: raise VoiceError('voice_download_unavailable') from None

def _limits():
    parent=os.getppid()
    if parent==1 or ctypes.CDLL(None,use_errno=True).prctl(1,signal.SIGKILL,0,0,0)!=0:os._exit(1)
    if os.getppid()!=parent:os._exit(1)
    resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,256*1024*1024))
    resource.setrlimit(resource.RLIMIT_CPU,(4,4));resource.setrlimit(resource.RLIMIT_NOFILE,(32,32))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))

def fetch_bounded(token,file_id):
    # A separate trusted transport process provides a hard deadline including DNS.
    # The token is stdin-only, never argv, worker environment or a temporary file.
    env={k:v for k,v in os.environ.items() if k in ('PATH','LANG','HTTP_PROXY','HTTPS_PROXY','NO_PROXY','http_proxy','https_proxy','no_proxy','SSL_CERT_FILE','SSL_CERT_DIR','REQUESTS_CA_BUNDLE')}
    proc=subprocess.Popen([sys.executable,__file__],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                          env=env,preexec_fn=_limits,start_new_session=True)
    try:
        output,_=proc.communicate(json.dumps({'token':token,'file_id':file_id}).encode(),timeout=8)
        if proc.returncode or len(output)>MAX_BYTES*2:raise VoiceError('voice_download_unavailable')
        body=json.loads(output)
        if body.get('ok') is not True:raise VoiceError('voice_download_unavailable')
        data=base64.b64decode(body['data'],validate=True)
        if len(data)>MAX_BYTES:raise VoiceError('voice_download_size')
        return data
    except subprocess.TimeoutExpired:raise VoiceError('voice_download_timeout') from None
    except VoiceError:raise
    except Exception:raise VoiceError('voice_download_unavailable') from None
    finally:
        if proc.poll() is None:os.killpg(proc.pid,signal.SIGKILL)
        proc.wait(timeout=2)
        for stream in (proc.stdin,proc.stdout):
            if stream:stream.close()

if __name__=='__main__':
    try:
        raw=sys.stdin.buffer.read(1025)
        if len(raw)>1024:raise VoiceError('voice_file_metadata')
        value=json.loads(raw)
        if set(value)!={'token','file_id'}:raise VoiceError('voice_file_metadata')
        data=fetch(value['token'],value['file_id'])
        print(json.dumps({'ok':True,'data':base64.b64encode(data).decode()}))
    except Exception:print(json.dumps({'ok':False,'code':'voice_download_unavailable'}))
