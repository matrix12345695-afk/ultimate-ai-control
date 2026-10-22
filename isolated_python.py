"""Rootless Bubblewrap runner for bounded Python unittest bundles on Linux x86_64.

Untrusted code never runs on the host interpreter. Only runtime libraries and a materialized
read-only bundle enter the namespace. Network, process forks, namespace creation and affinity
changes are denied. Threads share one bounded address space and one CPU. Older Bubblewrap
without sized tmpfs support gets a read-only /tmp, never an unlimited writable scratch mount.
"""
import errno
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import resource
import selectors
import signal
import stat
import struct
import subprocess
import sys
import sysconfig
import tempfile
import time

MAX_FILES=64
MAX_BUNDLE_BYTES=2*1024*1024
MAX_OUTPUT=64000
OUTPUT_BUDGET=256000
MAX_SECONDS=20


class SandboxUnavailable(RuntimeError): pass


def validate_files(files):
    if not isinstance(files,dict) or not 1<=len(files)<=MAX_FILES: raise ValueError("invalid bundle size")
    total=0
    for name,body in files.items():
        if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9_./-]{1,160}',name): raise ValueError("invalid bundle path")
        path=PurePosixPath(name)
        if path.is_absolute() or any(p in ('','.','..') for p in name.split('/')): raise ValueError("path traversal")
        if path.suffix!='.py' or any(p.startswith('.') for p in path.parts): raise ValueError("only Python source is enabled")
        if not isinstance(body,str): raise ValueError("source must be text")
        total+=len(body.encode())
    if total>MAX_BUNDLE_BYTES or not any(name.startswith('tests/test_') for name in files):
        raise ValueError("oversized bundle or no tests")
    return files


def manifest(files):
    validate_files(files)
    entries=[{'path':name,'sha256':hashlib.sha256(body.encode()).hexdigest(),'bytes':len(body.encode())} for name,body in sorted(files.items())]
    digest=hashlib.sha256(json.dumps(entries,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return entries,digest


def load_policy(path):
    p=Path(path)
    info=p.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)!=0o600:
        raise SandboxUnavailable("sandbox policy must be owner-private")
    cfg=json.loads(p.read_text())
    if cfg.get('enabled') is not True or cfg.get('backend')!='bubblewrap-v1': raise SandboxUnavailable("sandbox not enabled")
    binary=Path(cfg.get('binary','')).resolve(strict=True)
    details=binary.stat()
    if not stat.S_ISREG(details.st_mode) or details.st_uid not in (0,os.getuid()) or details.st_mode & (stat.S_IWGRP|stat.S_IWOTH|stat.S_ISUID|stat.S_ISGID):
        raise SandboxUnavailable("unsafe sandbox binary permissions")
    if hashlib.sha256(binary.read_bytes()).hexdigest()!=cfg.get('binary_sha256'): raise SandboxUnavailable("sandbox binary hash mismatch")
    if platform.machine() not in ('x86_64','amd64'): raise SandboxUnavailable("seccomp policy supports Linux x86_64 only")
    help_text=subprocess.run([str(binary),'--help'],capture_output=True,text=True,timeout=5).stdout
    needed=('--seccomp','--clearenv','--remount-ro','--cap-drop','--unshare-all')
    if not all(flag in help_text for flag in needed): raise SandboxUnavailable("sandbox flags unavailable")
    cfg['binary']=str(binary)
    cfg['writable_tmp']='--size ' in help_text
    return cfg


def seccomp_filter():
    # Classic BPF, struct seccomp_data: nr at 0, arch at 4, argument[0] at 16.
    LD=0x20; JEQ=0x15; JGE=0x35; JSET=0x45; RET=0x06
    KILL=0x80000000; ALLOW=0x7fff0000; DENY=0x00050000|errno.EPERM
    code=[(LD,0,0,4),(JEQ,1,0,0xc000003e),(RET,0,0,KILL),
          (LD,0,0,0),(JGE,0,1,0x40000000),(RET,0,0,KILL)]
    # No network, new processes, tracing, new namespaces, mounts, kernel control or CPU escape.
    blocked=(41,42,44,46,57,58,101,155,161,165,166,167,168,169,172,173,203,
             246,248,249,250,272,298,303,304,308,310,311,321,323,425,426,427,428,429,430,431,432,438,442)
    for number in blocked: code.extend([(JEQ,0,1,number),(RET,0,0,DENY)])
    # glibc falls back from clone3 to clone when ENOSYS is returned.
    code.extend([(JEQ,0,1,435),(RET,0,0,0x00050000|errno.ENOSYS)])
    # clone is permitted for threads only, with no namespace flags. Threads share memory/CPU.
    code.extend([(JEQ,0,4,56),(LD,0,0,16),(JSET,1,0,0x7e020000),
                 (JSET,1,0,0x00010000),(RET,0,0,DENY),(RET,0,0,ALLOW)])
    return b''.join(struct.pack('HBBI',*insn) for insn in code)


def _limits():
    resource.setrlimit(resource.RLIMIT_AS,(320*1024*1024,320*1024*1024))
    resource.setrlimit(resource.RLIMIT_CPU,(15,15))
    resource.setrlimit(resource.RLIMIT_NPROC,(128,128))
    resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    resource.setrlimit(resource.RLIMIT_FSIZE,(8*1024*1024,8*1024*1024))
    available=os.sched_getaffinity(0)
    os.sched_setaffinity(0,{min(available)})


def _arguments(cfg,source,filter_fd):
    version=f'python{sys.version_info.major}.{sys.version_info.minor}'
    stdlib=Path(sysconfig.get_path('stdlib')).resolve()
    executable=Path(sys.executable).resolve()
    args=[cfg['binary'],'--unshare-all','--die-with-parent','--new-session','--cap-drop','ALL','--clearenv',
          '--ro-bind',str(executable),'/runtime/bin/python3',
          '--ro-bind',str(stdlib),'/runtime/lib/'+version]
    # Dynamic loader and standard native libraries only; no /home, /root, /etc or host /tmp.
    for name in ('/lib/x86_64-linux-gnu','/usr/lib/x86_64-linux-gnu','/lib64'):
        if Path(name).exists(): args+=['--ro-bind',name,name]
    libdirs={Path(sys.base_prefix)/'lib',executable.parent.parent/'lib',Path(sysconfig.get_config_var('LIBDIR') or '/nonexistent')}
    for libdir in sorted(libdirs):
        lib=libdir/f'libpython{sys.version_info.major}.{sys.version_info.minor}.so.1.0'
        if lib.is_file():
            args+=['--ro-bind',str(lib.resolve()),'/runtime/lib/'+lib.name]
            break
    for folder in ('site-packages','dist-packages'):
        if (stdlib/folder).is_dir():
            args+=['--tmpfs','/runtime/lib/'+version+'/'+folder,'--remount-ro','/runtime/lib/'+version+'/'+folder]
    args+=['--proc','/proc','--dev','/dev','--remount-ro','/dev','--dir','/home','--dir','/etc']
    if cfg['writable_tmp']:
        args+=['--size',str(32*1024*1024),'--tmpfs','/tmp']
    else:
        args+=['--tmpfs','/tmp','--remount-ro','/tmp']
    args+=['--ro-bind',str(source),'/workspace','--chdir','/workspace',
           '--setenv','HOME','/tmp','--setenv','LANG','C.UTF-8',
           '--setenv','PYTHONHOME','/runtime','--setenv','PYTHONPATH','/workspace',
           '--setenv','PYTHONDONTWRITEBYTECODE','1',
           '--setenv','LD_LIBRARY_PATH','/runtime/lib:/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu',
           '--remount-ro','/','--seccomp',str(filter_fd),
           '--','/runtime/bin/python3','-S','-B','-m','unittest','discover','-s','tests','-q']
    return args


def run_bundle(files,policy_path,timeout=MAX_SECONDS):
    validate_files(files)
    if type(timeout) is not int or not 1<=timeout<=MAX_SECONDS: raise ValueError("invalid sandbox timeout")
    cfg=load_policy(policy_path)
    entries,digest=manifest(files)
    started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='uac-sandbox-') as folder:
        root=Path(folder)
        source=root/'bundle'
        source.mkdir()
        for name,body in files.items():
            p=source/name
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(body)
            p.chmod(0o444)
        with tempfile.TemporaryFile() as policy:
            policy.write(seccomp_filter())
            policy.flush()
            policy.seek(0)
            args=_arguments(cfg,source,policy.fileno())
            proc=None
            tail=b''
            count=0
            status=None
            try:
                proc=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                                      env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8'},pass_fds=(policy.fileno(),),
                                      preexec_fn=_limits,start_new_session=True)
                sel=selectors.DefaultSelector()
                sel.register(proc.stdout,selectors.EVENT_READ)
                deadline=time.monotonic()+timeout
                while sel.get_map():
                    if time.monotonic()>=deadline:
                        status='timeout'
                        break
                    for key,_ in sel.select(min(0.1,max(0,deadline-time.monotonic()))):
                        chunk=os.read(key.fileobj.fileno(),8192)
                        if not chunk:
                            sel.unregister(key.fileobj)
                            continue
                        count+=len(chunk)
                        tail=(tail+chunk)[-MAX_OUTPUT:]
                        if count>OUTPUT_BUDGET:
                            status='output_limit'
                            break
                    if status: break
                sel.close()
                if status and proc.poll() is None:
                    os.killpg(proc.pid,signal.SIGKILL)
                code=proc.wait(timeout=3)
                status=status or ('passed' if code==0 else 'failed')
            finally:
                if proc is not None:
                    if proc.poll() is None:
                        os.killpg(proc.pid,signal.SIGKILL)
                    proc.wait(timeout=3)
                    proc.stdout.close()
        if status=='failed' and tail.startswith(b'bwrap:'):
            raise SandboxUnavailable('namespace setup failed; no host execution fallback')
        return {'status':status,'exit_code':code,'elapsed_seconds':round(time.monotonic()-started,4),
                'output':tail.decode(errors='replace'),'source_digest':digest,'files':entries,
                'backend':'bubblewrap-v1','writable_tmp':cfg['writable_tmp'],
                'network':False,'process_forks':False,'cpu_count':1,'address_space_mib':320}
