"""Python 3.6-compatible engine probe, executed only inside the CI baseline guest."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess


def digest(data):return hashlib.sha256(data).hexdigest()


def probe(source,output):
    output.mkdir(exist_ok=False)
    pin=json.loads((source/'inputs.json').read_text(encoding='utf-8'))
    binary=(source/'dot').read_bytes()
    if digest(binary)!=pin['engine_sha256']:raise ValueError('Guest engine differs from pin')
    relocated=output/'engine com espaços ação';relocated.mkdir()
    engine=relocated/'dot';engine.write_bytes(binary);engine.chmod(0o755)
    if shutil.which('dot'):raise ValueError('Unexpected global Graphviz')
    env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','HOME':str(output),'GVBINDIR':str(relocated)}
    version=subprocess.run([str(engine),'-V'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                           cwd=str(relocated),env=env,timeout=10,check=True)
    if b'16.1.0' not in version.stdout+version.stderr:raise ValueError('Version probe failed')
    rows=[]
    for item in pin['cases']:
        dot=source/item['dot_file'];raw=dot.read_bytes()
        if digest(raw)!=item['dot_sha256']:raise ValueError('Guest DOT input differs from pin')
        result=subprocess.run([str(engine),'-Tjson0',str(dot)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                              cwd=str(relocated),env=env,timeout=30,check=True)
        if len(result.stdout)+len(result.stderr)>8*1024**2:raise ValueError('Engine output exceeds bound')
        filename=item['case']+'.json';(output/filename).write_bytes(result.stdout)
        rows.append(dict(case=item['case'],dot_sha256=digest(raw),output=filename,
                         output_sha256=digest(result.stdout),output_bytes=len(result.stdout)))
    identity={}
    for line in Path('/etc/os-release').read_text().splitlines():
        key,separator,value=line.partition('=')
        if separator and key in ('ID','VERSION_ID','PRETTY_NAME'):identity[key]=value.strip('"')
    cpu={}
    with open('/proc/cpuinfo','rb') as stream:raw_cpu=stream.read(1024**2+1)
    if len(raw_cpu)>1024**2:raise ValueError('CPU evidence exceeds bound')
    for line in raw_cpu.decode().splitlines():
        key,separator,value=line.partition(':');key=key.strip()
        if separator and key in ('model name','flags','CPU architecture','Features') and key not in cpu:cpu[key]=value.strip()
    loader=Path('/lib64/ld-linux-x86-64.so.2').resolve(strict=True)
    ldd=subprocess.run(['/usr/bin/ldd',str(engine)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,check=True)
    if len(ldd.stdout)>65536 or b'not found' in ldd.stdout:raise ValueError('Guest dynamic dependency failure')
    (output/'ldd.txt').write_bytes(ldd.stdout)
    report=dict(kind='ubuntu1804-native-kernel-engine-baseline',passed=True,qualified=False,
        identity=identity,arch=platform.machine(),kernel=platform.release(),glibc=os.confstr('CS_GNU_LIBC_VERSION'),
        python=platform.python_version(),python_role='Image system Python for engine probe only; not a supported application slot',
        engine_sha256=digest(binary),inputs_sha256=digest((source/'inputs.json').read_bytes()),
        cpu=cpu,loader=str(loader),loader_sha256=digest(loader.read_bytes()),ldd_sha256=digest(ldd.stdout),
        relocated_unicode_path=True,global_graphviz_absent=True,cases=rows,
        scope='Native guest kernel, glibc and real engine only; no application/Python-slot, Pro eligibility, Twine or support qualification')
    (output/'guest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();probe(args.input,args.output)
