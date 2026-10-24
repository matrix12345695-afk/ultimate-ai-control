"""Read-only Node sandbox. Startup threads are locked before any project code loads.

NAPI guard uses TSYNC to deny clone/fork across all startup threads. The outer filter
permits only the exact pthread clone flags during trusted runtime initialization.
There is no host fallback, network, writable scratch, package install or external key.
"""
import errno
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import resource
import selectors
import signal
import stat
import struct
import subprocess
import tempfile
import time
import isolated_python as python

BACKEND='bubblewrap-node-locked-v1'
GUARD_SOURCE=Path(__file__).with_name('node_thread_guard.c')
FLAGS=['--test-reporter=tap','--jitless','--single-threaded','--no-node-snapshot',
       '--max-old-space-size=32','--v8-pool-size=1']


def source_manifest(files):
    if not isinstance(files,dict) or not 1<=len(files)<=64: raise ValueError('invalid Node bundle')
    for name,body in files.items():
        if (not isinstance(name,str) or not re.fullmatch('[A-Za-z0-9_./-]{1,160}',name)
                or any(part in ('','.','..') or part.startswith('.') for part in name.split('/'))
                or PurePosixPath(name).suffix not in {'.js','.cjs','.json','.html','.xml','.txt'}
                or not isinstance(body,str)):
            raise ValueError('invalid Node source path or body')
    entries=[{'path':p,'bytes':len(body.encode()),'sha256':hashlib.sha256(body.encode()).hexdigest()}
             for p,body in sorted(files.items())]
    if sum(item['bytes'] for item in entries)>256000: raise ValueError('Node bundle too large')
    digest=hashlib.sha256(json.dumps(entries,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return entries,digest


def checked_file(path,expected,private=False):
    path=Path(path)
    if path.absolute()!=path.resolve(): raise python.SandboxUnavailable('Node runtime symlink denied')
    info=path.stat()
    if (not stat.S_ISREG(info.st_mode) or info.st_uid not in (0,os.getuid()) or
            info.st_mode & (stat.S_IWGRP|stat.S_IWOTH|stat.S_ISUID|stat.S_ISGID) or
            (private and (info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)!=0o600)) or
            hashlib.sha256(path.read_bytes()).hexdigest()!=expected):
        raise python.SandboxUnavailable('Node runtime integrity check failed')
    return path


def load_policy(path):
    path=Path(path)
    info=path.lstat()
    if path.absolute()!=path.resolve() or not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)!=0o600:
        raise python.SandboxUnavailable('Node policy must be private')
    cfg=json.loads(path.read_bytes())
    if cfg.get('enabled') is not True or cfg.get('backend')!=BACKEND:
        raise python.SandboxUnavailable('Node sandbox is disabled')
    cfg['binary']=str(checked_file(cfg.get('binary',''),cfg.get('binary_sha256')))
    cfg['guard']=str(checked_file(cfg.get('guard',''),cfg.get('guard_sha256'),private=True))
    if cfg.get('guard_source_sha256')!=hashlib.sha256(GUARD_SOURCE.read_bytes()).hexdigest():
        raise python.SandboxUnavailable('Node guard source version mismatch')
    cfg['bwrap']=python.load_policy(path.with_name('sandbox-policy.json'))['binary']
    return cfg


def seccomp_filter():
    base=python.seccomp_filter()
    instructions=[struct.unpack('HBBI',base[i:i+8]) for i in range(0,len(base),8)]
    if instructions[:6]!=[(0x20,0,0,4),(0x15,1,0,0xc000003e),(0x06,0,0,0x80000000),
                           (0x20,0,0,0),(0x35,0,1,0x40000000),(0x06,0,0,0x80000000)]:
        raise python.SandboxUnavailable('Node filter architecture prefix changed')
    # Retain the architecture/x32 checks. glibc falls back from clone3 ENOSYS to
    # clone with exact pthread flags (no new process or namespace). The NAPI guard
    # permanently denies both variants using TSYNC before loading project files.
    prefix=[(0x20,0,0,0),(0x15,0,4,56),(0x20,0,0,16),(0x15,0,1,0x3d0f00),
            (0x06,0,0,0x7fff0000),(0x06,0,0,0x00050000|errno.EPERM),
            (0x15,0,1,435),(0x06,0,0,0x00050000|errno.ENOSYS)]
    return b''.join(struct.pack('HBBI',*x) for x in instructions[:6]+prefix+instructions[6:])


def limits():
    # Node/V8 needs virtual reservations above the Python cap. RSS is much smaller;
    # this 768MiB address-space ceiling remains enforced on the whole process.
    resource.setrlimit(resource.RLIMIT_AS,(768*1024*1024,768*1024*1024))
    resource.setrlimit(resource.RLIMIT_CPU,(8,8))
    resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    resource.setrlimit(resource.RLIMIT_FSIZE,(0,0))
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})


def run(files,policy_path,driver,timeout=8):
    if type(timeout) is not int or not 1<=timeout<=10: raise ValueError('invalid Node timeout')
    entries,digest=source_manifest(files)
    cfg=load_policy(policy_path)
    started=time.monotonic();tail=b'';count=0;status=None;proc=None
    with tempfile.TemporaryDirectory(prefix='uac-node-') as name:
        root=Path(name);bundle=root/'bundle';bundle.mkdir()
        for path,body in files.items():
            p=bundle/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body.encode());p.chmod(0o444)
        runner=root/'runner.cjs'
        runner.write_text("'use strict';\nrequire('/guard.node');\n"+driver)
        args=[cfg['bwrap'],'--unshare-all','--die-with-parent','--new-session','--cap-drop','ALL','--clearenv',
              '--ro-bind',cfg['binary'],'/runtime/node','--ro-bind',cfg['guard'],'/guard.node']
        for path in ('/lib/x86_64-linux-gnu','/usr/lib/x86_64-linux-gnu','/lib64'):
            if Path(path).exists(): args+=['--ro-bind',path,path]
        args+=['--proc','/proc','--dev','/dev','--remount-ro','/dev','--dir','/home','--dir','/etc',
               '--tmpfs','/tmp','--remount-ro','/tmp','--ro-bind',str(bundle),'/workspace',
               '--ro-bind',str(runner),'/runner.cjs','--chdir','/workspace',
               '--setenv','HOME','/tmp','--setenv','LANG','C.UTF-8','--setenv','UV_THREADPOOL_SIZE','1',
               '--remount-ro','/']
        with tempfile.TemporaryFile() as filt:
            filt.write(seccomp_filter());filt.flush();filt.seek(0)
            args+=['--seccomp',str(filt.fileno()),'--','/runtime/node',*FLAGS,'/runner.cjs']
            try:
                proc=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                                      env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8'},pass_fds=(filt.fileno(),),
                                      preexec_fn=limits,start_new_session=True)
                with selectors.DefaultSelector() as selector:
                    selector.register(proc.stdout,selectors.EVENT_READ)
                    deadline=time.monotonic()+timeout
                    while selector.get_map() and not status:
                        if time.monotonic()>=deadline: status='timeout';break
                        for key,_ in selector.select(.05):
                            chunk=os.read(key.fileobj.fileno(),8192)
                            if not chunk: selector.unregister(key.fileobj);continue
                            count+=len(chunk);tail=(tail+chunk)[-64000:]
                            if count>256000: status='output_limit';break
                if status and proc.poll() is None: os.killpg(proc.pid,signal.SIGKILL)
                code=proc.wait(timeout=2)
                status=status or ('passed' if code==0 else 'failed')
            finally:
                if proc is not None:
                    if proc.poll() is None: os.killpg(proc.pid,signal.SIGKILL)
                    proc.wait(timeout=2);proc.stdout.close()
    if status=='failed' and tail.startswith(b'bwrap:'):
        raise python.SandboxUnavailable('Node namespace setup failed; no host fallback')
    return {'status':status,'exit_code':code,'source_digest':digest,'files':entries,
            'elapsed_seconds':round(time.monotonic()-started,4),'output':tail.decode(errors='replace'),
            'output_sha256':hashlib.sha256(tail).hexdigest(),'backend':BACKEND,
            'node_sha256':cfg['binary_sha256'],'guard_sha256':cfg['guard_sha256'],
            'driver_sha256':hashlib.sha256(driver.encode()).hexdigest(),
            'network':False,'process_forks':False,'new_threads_after_guard':False,
            'writable_filesystem':False,'address_space_mib':768,'cpu_count':1}
