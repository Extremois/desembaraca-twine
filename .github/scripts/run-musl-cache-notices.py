"""Exercise installed packages, corpus, recovery and notices in pinned musl CI."""
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
    repository=os.environ.get('GITHUB_REPOSITORY','')
    run_id=os.environ.get('GITHUB_RUN_ID','')
    revision=os.environ.get('GITHUB_SHA','')
    if (os.environ.get('GITHUB_ACTIONS')!='true' or not re.fullmatch(r'[\w.-]+/[\w.-]+',repository)
            or not run_id.isdigit() or int(run_id)<=0 or not re.fullmatch(r'[0-9a-f]{40}',revision)):
        raise ValueError('Musl ABI receipts require an identified GitHub Actions execution')
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
    for check,name in (('notices','cache-notices.json'),('runtime','installed-runtime.json')):
        report_path=work/name
        command=[python,ROOT/'tools/validation/check-built-packages.py','--dist-dir',work/'dist',
            '--wheelhouse',work/'wheels','--engine-artifact',artifact,'--engine-id','linux-musl-'+arch,
            '--engine-check',check,'--report',report_path]
        if check=='runtime':command.extend(['--review-directory',work/'runtime-review'])
        run(command)
        report=json.loads(report_path.read_bytes())
        report['execution_environment']=dict(environment,environment_kind='github-actions',execution_kind='container',image=image,
            kernel=platform.release(),native_cpu=True,
            limitation='Musl ABI execution on a hosted kernel; not individual Alpine release certification')
        report['github_actions']=dict(repository=repository,run_id=run_id,revision=revision,
            run_url='https://github.com/'+repository+'/actions/runs/'+run_id)
        report_path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    run([python,ROOT/'tools/validation/check-installation-docs.py','--work',work/'remote-installation',
         '--report',work/'remote-installation.json'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('artifact','work'):parser.add_argument('--'+name,type=Path,required=True)
    for name in ('arch','minor','image'):parser.add_argument('--'+name,required=True)
    args=parser.parse_args()
    collect(args.artifact.resolve(),args.work.resolve(),args.arch,args.minor,args.image)
