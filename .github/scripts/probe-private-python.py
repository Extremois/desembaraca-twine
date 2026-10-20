"""Python 3.6-compatible private CPython prerequisite probe for the CI guest."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import shutil
import subprocess
import tarfile


def validate_members(members):
    names=set();links=set();total=0
    if len(members)>30000:raise ValueError('Too many interpreter archive entries')
    for item in members:
        path=PurePosixPath(item.name)
        if (path.is_absolute() or not path.parts or path.parts[0]!='python' or '..' in path.parts
                or '\\' in item.name or str(path) in names or item.mode & 0o6000
                or not (item.isfile() or item.isdir() or item.issym() or item.islnk())):
            raise ValueError('Unsafe interpreter archive member')
        names.add(str(path));total+=item.size
        if not 0<=item.size<=64*1024**2 or total>512*1024**2:raise ValueError('Interpreter expansion exceeds bound')
        if item.issym() or item.islnk():
            links.add(str(path))
            target=posixpath.normpath(posixpath.join(str(path.parent),item.linkname) if item.issym() else item.linkname)
            if '\\' in item.linkname or target.startswith('/') or not target.startswith('python/'):
                raise ValueError('Interpreter link escapes private root')
    for name in names:
        if any(str(parent) in links for parent in PurePosixPath(name).parents):
            raise ValueError('Interpreter archive writes through a link')
    return members


def extract_private(archive,destination):
    destination.mkdir(mode=0o700,exist_ok=False)
    with tarfile.open(str(archive),'r:gz') as stream:
        members=validate_members(stream.getmembers())
        # Create regular files first, then links; never traverse archive-controlled links.
        for item in members:
            target=destination/item.name
            if item.isdir():target.mkdir(parents=True,exist_ok=True)
            elif item.isfile():
                target.parent.mkdir(parents=True,exist_ok=True)
                with stream.extractfile(item) as source,target.open('xb') as output:shutil.copyfileobj(source,output)
                target.chmod(item.mode & 0o777)
        for item in members:
            target=destination/item.name
            if item.issym():
                target.parent.mkdir(parents=True,exist_ok=True);target.symlink_to(item.linkname)
            elif item.islnk():
                origin=destination/item.linkname
                if origin.is_symlink() or not origin.is_file():raise ValueError('Invalid private hardlink')
                target.parent.mkdir(parents=True,exist_ok=True);os.link(str(origin),str(target))


FACTS='''import ctypes,ensurepip,json,pip,platform,sqlite3,ssl,struct,sys,sysconfig,venv,zlib
print(json.dumps(dict(python=platform.python_version(),implementation=platform.python_implementation(),
arch=platform.machine(),bits=struct.calcsize("P")*8,pip=pip.__version__,ensurepip=ensurepip.version(),
ssl=ssl.OPENSSL_VERSION,venv_active=sys.prefix!=sys.base_prefix,
gil_disabled=bool(sysconfig.get_config_var("Py_GIL_DISABLED")),ssl_context=bool(ssl.create_default_context()))))'''


def probe(source,output):
    output.mkdir(exist_ok=False)
    pins=json.loads((source/'private-python.json').read_text())['interpreters']
    system=Path('/usr/bin/python3').resolve(strict=True)
    digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    before=digest(system);rows=[]
    env=dict(PATH='/usr/bin:/bin',LANG='C.UTF-8',HOME=str(output),PIP_NO_INDEX='1',PIP_DISABLE_PIP_VERSION_CHECK='1')
    for pin in pins:
        archive=source/('python-'+pin['minor']+'.tar.gz')
        if archive.stat().st_size!=pin['size'] or digest(archive)!=pin['sha256']:raise ValueError('Interpreter archive changed')
        private=output/('private-'+pin['minor']);extract_private(archive,private)
        python=private/'python/bin/python3';venv=output/('venv com espaços ação '+pin['minor'])
        subprocess.run([str(python),'-I','-m','venv','--copies',str(venv)],env=env,check=True,timeout=120)
        raw=subprocess.check_output([str(venv/'bin/python'),'-I','-c',FACTS],env=env,timeout=30)
        facts=json.loads(raw.decode('utf-8'))
        if (source/'application/wheel.json').exists():
            application=output/('application-'+pin['minor'])
            subprocess.run([str(venv/'bin/python'),'-I',str(source/'application/probe.py'),
                '--input',str(source),'--output',str(application)],env=env,check=True,timeout=240)
            shutil.copyfile(application/'runtime.json',output/('application-'+pin['minor']+'.json'))
        rows.append(dict(minor=pin['minor'],archive_sha256=pin['sha256'],archive_bytes=archive.stat().st_size,facts=facts))
    report=dict(kind='native-ubuntu1804-private-python-prerequisites',passed=True,qualified=False,
        system_python_before=before,system_python_after=digest(system),interpreters=rows,
        network='No guest internet; archives transferred from host after pinned HTTPS acquisition',
        scope='Private prerequisite toolchains only; no installed application, Pro eligibility or full cell qualification')
    (output/'private-python-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();probe(args.input,args.output)
