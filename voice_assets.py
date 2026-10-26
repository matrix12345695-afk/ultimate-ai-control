"""Explicit rootless preparation of a pinned, acceptance-only speech runtime.

Never called by a Telegram handler or worker. No global installs, credentials or services.
"""
import hashlib
import json
import os
import resource
from pathlib import Path
import shutil
import stat
import subprocess
import tarfile
import tempfile
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parent
FILES=('whisper-cli','opusdec','model.bin','lib/libopus.so.0','lib/libopusfile.so.0','lib/libopusurl.so.0','lib/libogg.so.0')

def digest(data): return hashlib.sha256(data).hexdigest()
def contract(): return json.loads((ROOT/'voice_assets_contract.json').read_text())
def contract_sha(): return digest((ROOT/'voice_assets_contract.json').read_bytes())

def regular(path,private=False):
    path=Path(path);info=path.lstat()
    if (path.resolve()!=path or not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid()
        or info.st_mode&0o022 or (private and stat.S_IMODE(info.st_mode)!=0o600)):
        raise PermissionError('unsafe_voice_asset')
    return path

def verify(root):
    root=Path(root)
    if root.resolve()!=root or root.stat().st_uid!=os.getuid() or root.stat().st_mode&0o077:
        raise PermissionError('unsafe_voice_runtime')
    manifest=json.loads(regular(root/'manifest.json',True).read_text())
    if (set(manifest)!={'schema','contract_sha256','files'} or manifest['schema']!='voice-runtime-v1'
        or manifest['contract_sha256']!=contract_sha() or set(manifest['files'])!=set(FILES)):
        raise ValueError('voice_manifest_scope')
    for name in FILES:
        path=regular(root/name);data=path.read_bytes();saved=manifest['files'][name]
        if saved!={'bytes':len(data),'sha256':digest(data)}: raise ValueError('voice_asset_changed')
    if manifest['files']['model.bin']['sha256']!=contract()['downloads'][2]['sha256']:
        raise ValueError('voice_model_pin')
    return manifest

def _download(item,destination):
    with urllib.request.urlopen(item['url'],timeout=60) as response:
        data=response.read(item['bytes']+1)
    if len(data)!=item['bytes'] or digest(data)!=item['sha256']: raise ValueError('voice_download_pin')
    destination.write_bytes(data)

def _run(args,cwd=None):
    # This builder executes only reviewed hash-pinned build tools, outside the worker.
    env={k:v for k,v in os.environ.items() if k in ('PATH','HOME','LANG','HTTP_PROXY','HTTPS_PROXY','NO_PROXY','http_proxy','https_proxy','no_proxy','SSL_CERT_FILE','SSL_CERT_DIR','REQUESTS_CA_BUNDLE')}
    def limited():
        resource.setrlimit(resource.RLIMIT_AS,(1536*1024*1024,1536*1024*1024))
        resource.setrlimit(resource.RLIMIT_CPU,(240,240));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
        os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});os.nice(15)
    result=subprocess.run(args,cwd=cwd,env=env,capture_output=True,text=True,timeout=300,preexec_fn=limited)
    if result.returncode: raise RuntimeError('voice_build_failed_'+Path(args[0]).name)

def prepare(destination):
    destination=Path(destination)
    if destination.exists(): return verify(destination)
    if destination.parent.resolve()!=destination.parent or not destination.parent.is_dir(): raise ValueError('voice_parent_missing')
    if shutil.disk_usage(destination.parent).free<1024**3: raise RuntimeError('voice_disk_headroom')
    for executable in ('g++','make','dpkg-deb'):
        if not shutil.which(executable): raise RuntimeError('voice_build_tool_missing_'+executable)
    with tempfile.TemporaryDirectory(prefix='.voice-prepare-',dir=destination.parent) as name:
        temp=Path(name);out=temp/'runtime';out.mkdir(mode=0o700);(out/'lib').mkdir(mode=0o700)
        for item in contract()['downloads']: _download(item,temp/item['name'])
        source=temp/'source';source.mkdir();cmake=temp/'cmake';cmake.mkdir()
        with tarfile.open(temp/'source.tar.gz') as archive:
            for member in archive.getmembers():
                p=Path(member.name)
                if p.is_absolute() or '..' in p.parts or not (member.isfile() or member.isdir()): raise ValueError('voice_source_archive_path')
            archive.extractall(source)
        with zipfile.ZipFile(temp/'cmake.whl') as archive:
            for name in archive.namelist():
                p=Path(name)
                if p.is_absolute() or '..' in p.parts: raise ValueError('voice_build_archive_path')
            archive.extractall(cmake)
        binary=cmake/'cmake/data/bin/cmake';binary.chmod(0o700)
        folder=source/('whisper.cpp-'+contract()['whisper_commit']);build=temp/'build'
        flags=['-DCMAKE_BUILD_TYPE=Release','-DBUILD_SHARED_LIBS=OFF','-DGGML_OPENMP=OFF','-DGGML_NATIVE=OFF','-DGGML_BLAS=OFF','-DWHISPER_CURL=OFF','-DWHISPER_BUILD_TESTS=OFF','-DWHISPER_BUILD_SERVER=OFF',
               '-DGGML_AVX=OFF','-DGGML_AVX2=OFF','-DGGML_FMA=OFF','-DGGML_F16C=OFF','-DGGML_SSE42=OFF']
        _run([str(binary),'-S',str(folder),'-B',str(build),*flags])
        _run([str(binary),'--build',str(build),'--target','whisper-cli','-j1'])
        shutil.copyfile(build/'bin/whisper-cli',out/'whisper-cli');shutil.copyfile(temp/'model.bin',out/'model.bin')
        extracted=temp/'debs';extracted.mkdir()
        for item in contract()['downloads'][3:]: _run(['dpkg-deb','-x',str(temp/item['name']),str(extracted)])
        shutil.copyfile(extracted/'usr/bin/opusdec',out/'opusdec')
        for name in FILES[3:]:
            matches=list(extracted.rglob(Path(name).name))
            if len(matches)!=1: raise ValueError('voice_decoder_library_scope')
            resolved=matches[0].resolve()
            if extracted not in resolved.parents: raise ValueError('voice_decoder_library_escape')
            shutil.copyfile(resolved,out/name)
        for name in FILES: (out/name).chmod(0o500 if name in ('whisper-cli','opusdec') else 0o400)
        # Preserve notices with the private distribution; these are never executable.
        notices=(folder/'LICENSE').read_text()
        notices+='\nOpenAI Whisper model: Copyright (c) 2022 OpenAI; MIT license.\n'+(folder/'LICENSE').read_text().split('\n',2)[-1]
        for copyright_file in sorted(extracted.glob('usr/share/doc/*/copyright')):
            notices+='\n\n'+str(copyright_file.relative_to(extracted))+'\n'+copyright_file.read_text()
        (out/'LICENSES.txt').write_text(notices);(out/'LICENSES.txt').chmod(0o400)
        manifest={'schema':'voice-runtime-v1','contract_sha256':contract_sha(),
                  'files':{name:{'bytes':(out/name).stat().st_size,'sha256':digest((out/name).read_bytes())} for name in FILES}}
        (out/'manifest.json').write_text(json.dumps(manifest,sort_keys=True)+'\n');(out/'manifest.json').chmod(0o600)
        verify(out);out.rename(destination)
    return verify(destination)

if __name__=='__main__':
    import sys
    if len(sys.argv)!=3 or sys.argv[1]!='prepare': raise SystemExit('Usage: voice_assets.py prepare ABSOLUTE_DIRECTORY')
    os.umask(0o077);prepare(Path(sys.argv[2]));print('voice_assets_prepared_hashes_verified=PASS')
