"""Build development packages and measure cache notices in a pinned, non-root Alpine userland."""
import argparse
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]


def validate_environment(lock,image,arch,minor,facts):
    pin=lock['images'][minor]['platforms'][arch]
    if (not re.fullmatch(r'python@sha256:[0-9a-f]{64}',image) or image!=pin['reference']
            or facts['arch']!=arch or facts['python_minor']!=minor or facts['distribution']!='alpine'
            or not facts['version'].startswith('3.22.') or facts['uid']==0):
        raise ValueError('Cache userland differs from pinned native CPU/Python/Alpine/non-root environment')


def collect(artifact,work,arch,minor,image):
    facts={}
    for line in Path('/etc/os-release').read_text().splitlines():
        key,sep,value=line.partition('=')
        if sep:facts[key]=value.strip('"')
    environment=dict(arch=platform.machine(),python_minor='.'.join(map(str,sys.version_info[:2])),
        distribution=facts.get('ID'),version=facts.get('VERSION_ID'),uid=os.geteuid())
    validate_environment(json.loads((ROOT/'tools/runtime/alpine-ci-images.json').read_bytes()),image,arch,minor,environment)
    if shutil.which('dot'):raise ValueError('Container unexpectedly has global Graphviz')
    work.mkdir(exist_ok=False)
    project=work/'project';project.mkdir()
    for name in ('pyproject.toml','MANIFEST.in','LICENSE','NOTICE','README.md'):
        shutil.copyfile(ROOT/name,project/name)
    shutil.copytree(ROOT/'src',project/'src',ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.egg-info'))
    builder=work/'builder'
    def run(argv):subprocess.run([str(x) for x in argv],cwd=work,check=True,timeout=240)
    run([sys.executable,'-m','venv',builder])
    python=builder/'bin/python'
    run([python,'-m','pip','install','--disable-pip-version-check','build'])
    run([python,'-m','build','--outdir',work/'dist',project])
    run([python,'-m','pip','download','--only-binary=:all:','--no-deps','--dest',work/'wheels','setuptools','wheel','packaging'])
    report_path=work/'cache-notices.json'
    run([python,ROOT/'tools/validation/check-built-packages.py','--dist-dir',work/'dist',
        '--wheelhouse',work/'wheels','--engine-artifact',artifact,'--engine-id','linux-musl-'+arch,
        '--engine-check','notices','--report',report_path])
    report=json.loads(report_path.read_bytes())
    report['execution_environment']=dict(environment,environment_kind='container',image=image,
        kernel=platform.release(),native_cpu=True,
        limitation='Alpine userland on Ubuntu hosted kernel; no native Alpine cell qualification')
    report_path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('artifact','work'):parser.add_argument('--'+name,type=Path,required=True)
    for name in ('arch','minor','image'):parser.add_argument('--'+name,required=True)
    args=parser.parse_args()
    collect(args.artifact.resolve(),args.work.resolve(),args.arch,args.minor,args.image)
