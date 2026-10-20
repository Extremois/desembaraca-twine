"""Exercise a private musl bundle in a pinned Alpine userland, without qualifying a cell."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from twine_edge_overlap.runtime_platform import parse_os_release


def validate_slot(lock,release,arch,minor,image,facts):
    if lock.get('schema_version')!=1 or release not in ('3.21','3.22','3.23','3.24'):
        raise ValueError('Unknown Alpine compatibility release')
    rows=[row for row in lock['images'] if (row['alpine'],row['python'])==(release,minor)]
    if len(rows)!=1 or arch not in ('x86_64','aarch64') or minor not in ('3.12','3.14'):
        raise ValueError('Missing or ambiguous Alpine/Python/CPU slot')
    pin=rows[0]['platforms'][arch]
    identity=facts['identity']
    if (not re.fullmatch(r'python@sha256:[0-9a-f]{64}',pin['reference']) or image!=pin['reference']
            or identity.get('ID')!='alpine'
            or not re.fullmatch(re.escape(release)+r'\.[0-9]+',identity.get('VERSION_ID',''))
            or facts['implementation']!='CPython' or facts['python_minor']!=minor or facts['machine']!=arch):
        raise ValueError('Image, distribution, CPython or CPU differs from requested slot')
    return pin


def read_bounded(path,maximum=8*1024**2):
    with path.open('rb') as stream:data=stream.read(maximum+1)
    if len(data)>maximum:raise ValueError('Userland evidence input exceeds bound')
    return data


def check(package,work,release,arch,minor,image):
    work.mkdir(parents=True,exist_ok=False)
    lock_raw=read_bounded(ROOT/'tools/runtime/alpine-compatibility-images.json',65536)
    os_release=read_bounded(Path('/etc/os-release'),65536)
    facts=dict(identity=parse_os_release(os_release.decode('utf-8')),implementation=platform.python_implementation(),
               python_minor='.'.join(map(str,sys.version_info[:2])),machine=platform.machine())
    validate_slot(json.loads(lock_raw),release,arch,minor,image,facts)
    if sys.platform!='linux' or shutil.which('dot'):
        raise ValueError('Requires isolated Linux userland without global Graphviz')
    candidate_raw=read_bounded(package/'candidate.json');candidate=json.loads(candidate_raw)
    provenance_raw=read_bounded(package/'provenance.json');provenance=json.loads(provenance_raw)
    digest=lambda raw:hashlib.sha256(raw).hexdigest()
    if (candidate['artifact_id']!='linux-musl-'+arch or candidate['qualified'] is not False
            or digest(provenance_raw)!=candidate['provenance_sha256']
            or provenance['recipe']['abi']!='musl' or provenance['native_arch']!=arch):
        raise ValueError('Candidate does not match the requested musl architecture')
    environment=dict(kind='alpine-private-bundle-userland-compatibility',passed=False,qualified=False,approved=False,
        environment_kind='container',alpine=release,python=platform.python_version(),arch=arch,
        kernel=platform.release(),image=image,identity=facts['identity'],os_release_sha256=digest(os_release),
        image_lock_sha256=digest(lock_raw),candidate_sha256=digest(candidate_raw),
        provenance_sha256=digest(provenance_raw),engine_sha256=provenance['executable_sha256'],
        application_revision=os.environ.get('GITHUB_SHA'),global_graphviz_absent=True,
        scope='Matching CPU, container userland and controlled acquisition; no native Alpine kernel/cell qualification')
    # Preserve the identified slot even when a later venv or integration step fails.
    report=work/'environment.json'
    report.write_text(json.dumps(environment,indent=2)+'\n',encoding='utf-8')
    venv=work/'venv com espaços ação'
    subprocess.run([sys.executable,'-m','venv',str(venv)],check=True,timeout=60)
    python=venv/'bin/python'
    pip=subprocess.run([str(python),'-m','pip','--version'],check=True,capture_output=True,timeout=30)
    (work/'pip-version.txt').write_bytes(pip.stdout)
    subprocess.run([str(python),str(ROOT/'tools/runtime/observe-linux-network.py'),
        '--build-output',str(package),'--private-package',str(package),'--environment-kind','container',
        '--report',str(work/'runtime-network.json'),'--corpus-report',str(work/'runtime-corpus.json')],
        check=True,timeout=210)
    network_raw=read_bounded(work/'runtime-network.json');network=json.loads(network_raw)
    if (not network['passed'] or network['corpus']['network_syscalls']!={}
            or network['corpus']['cases']!=13 or network['corpus']['engine_sha256']!=environment['engine_sha256']):
        raise ValueError('Private runtime/corpus/network evidence is incomplete')
    environment.update(passed=True,venv_and_pip_verified=True,pip_version_sha256=digest(pip.stdout),
                       runtime_network_sha256=digest(network_raw))
    report.write_text(json.dumps(environment,indent=2)+'\n',encoding='utf-8')
    print('Pinned Alpine '+release+' '+arch+' CPython '+minor+': venv, private runtime and offline corpus passed')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package',type=Path,required=True)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--alpine',required=True)
    parser.add_argument('--arch',required=True)
    parser.add_argument('--python',required=True)
    parser.add_argument('--image',required=True)
    args=parser.parse_args()
    check(args.package,args.work,args.alpine,args.arch,args.python,args.image)
