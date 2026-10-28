"""Install one candidate in an external venv and collect explicitly partial evidence."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from twine_edge_overlap.runtime_catalog import read_json,abi_target_matches
from twine_edge_overlap.runtime_platform import detect_host


REVIEW_CASES = ('crossing', 'coincident', 'isolated_overlap',
                'connected_overlap', 'through_isolated', 'through_connected')


def export_review(work, record, destination):
    """Preserve only the six public corpus outputs, bound to observed hashes.

    Export is opt-in, exclusive and never records a visual review as completed.
    Validate every input before creating the destination; never copy whole work/cache.
    """
    destination=Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError('Review output already exists')
    corpus=record['corpus']
    if len({item['case'] for item in corpus})!=len(corpus):
        raise ValueError('Duplicate review corpus cases')
    observed={item['case']:item for item in corpus}
    if not set(REVIEW_CASES).issubset(observed):
        raise ValueError('Six public review cases are required')
    source=Path(work)/'review'
    if source.is_symlink():raise ValueError('Review source cannot be a link')
    payloads=[]
    outputs=[]
    for case in REVIEW_CASES:
        name=case+'.twee'
        path=source/name
        if path.is_symlink() or not path.is_file():
            raise ValueError('Missing or linked review output')
        with path.open('rb') as stream:data=stream.read(10*1024**2+1)
        sha=hashlib.sha256(data).hexdigest()
        if len(data)>10*1024**2 or sha!=observed[case]['output_sha256']:
            raise ValueError('Review output differs from verified corpus')
        payloads.append((name,data))
        outputs.append(dict(case=case,file=name,sha256=sha))
    manifest={key:record[key] for key in ('target_id','python_minor','application_revision','artifact_sha256','source_state')}
    manifest.update(schema='twine-public-review-v1',review_status='pending',outputs=outputs)
    encoded=(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n').encode('utf-8')
    destination.mkdir(exist_ok=False)
    for name,data in [*payloads,('manifest.json',encoded)]:
        with (destination/name).open('xb') as stream:stream.write(data)
    return dict(directory=destination.name,manifest='manifest.json',
                manifest_sha256=hashlib.sha256(encoded).hexdigest(),review_status='pending')


def host_matches(target,host):
    if target.get('qualification_scope')=='abi':return abi_target_matches(target,host)
    distro=host.distribution_id if host.os=='linux' else ('macos' if host.os=='darwin' else 'windows')
    version=host.distribution_version if host.os=='linux' else host.os_version
    return (not host.translated and host.bits==64 and host.os==target['os'] and host.arch==target['arch']
            and distro==target['distribution_id']
            and (target['version']=='rolling' or not host.channel or host.channel==target['channel'])
            and (target['version']=='rolling' or version==target['version'] or version.startswith(target['version']+'.')))


def interpreter(path,minor):
    command=[str(path),'-I','-c','import json,platform,struct,sys; print(json.dumps(dict(minor="%d.%d"%sys.version_info[:2],patch=platform.python_version(),implementation=platform.python_implementation(),arch=platform.machine(),bits=struct.calcsize("P")*8)))']
    value=json.loads(subprocess.check_output(command,text=True,timeout=10))
    if value['minor']!=minor or value['implementation']!='CPython' or value['bits']!=64:
        raise ValueError('Interpreter does not satisfy native CPython slot '+minor)
    return value


def execution_context(requested,env,kernel,in_container):
    observed='wsl' if 'microsoft' in kernel.lower() else ('container' if in_container else 'runner')
    if requested!='github-actions':
        return (observed if observed!='runner' else requested),None
    repository=env.get('GITHUB_REPOSITORY','');run_id=env.get('GITHUB_RUN_ID','')
    if (env.get('GITHUB_ACTIONS')!='true' or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repository)
            or not re.fullmatch(r'[1-9][0-9]*',run_id) or not re.fullmatch(r'[0-9a-f]{40}',env.get('GITHUB_SHA',''))):
        raise ValueError('GitHub Actions evidence requires a recorded workflow run')
    return 'github-actions',dict(repository=repository,run_id=run_id,run_sha=env['GITHUB_SHA'],
        run_url='https://github.com/'+repository+'/actions/runs/'+run_id,
        job=env.get('GITHUB_JOB',''),run_attempt=env.get('GITHUB_RUN_ATTEMPT','1'),execution_kind=observed)


def collect(args):
    registry=read_json(args.registry)
    targets=[target for target in registry['targets'] if target['id']==args.target]
    if len(targets)!=1:raise ValueError('Unknown or ambiguous target')
    target=targets[0]
    host=detect_host()
    if not host_matches(target,host):raise ValueError('Host differs from requested support cell')
    family=[item for item in registry['targets'] if all(item[key]==target[key] for key in ('os','distribution_id','version','channel','arch'))]
    variant_needed=target['cpu_variant']!='distribution-default' or len({item['cpu_variant'] for item in family})>1
    if variant_needed and host.cpu_variant!=target['cpu_variant']:raise ValueError('Installed image variant is unknown or differs from cell')
    if not re.fullmatch(r'[0-9a-f]{40,64}',args.application_revision):raise ValueError('Pinned application revision required')
    if not re.fullmatch(r'[0-9a-f]{64}',args.image_digest):raise ValueError('Source image/environment SHA-256 required')
    package=args.package.resolve()
    if hashlib.sha256(package.read_bytes()).hexdigest()!=args.package_sha256:raise ValueError('Candidate package hash mismatch')
    interpreters={'3.12':args.python_312.resolve(),'3.14':args.python_314.resolve()}
    facts={minor:interpreter(path,minor) for minor,path in interpreters.items()}
    # Both interpreters must already exist before any rolling snapshot is captured.
    from twine_edge_overlap.runtime_platform import normalize_arch
    if any(normalize_arch(item['arch'])!=target['arch'] for item in facts.values()):raise ValueError('Interpreter architecture differs from cell')
    kind,ci_context=execution_context(args.environment_kind,os.environ,platform.release(),Path('/.dockerenv').exists())
    base=tempfile.gettempdir()
    if os.name=='nt' and not base.startswith('\\\\?\\'):base='\\\\?\\'+base
    with tempfile.TemporaryDirectory(prefix='twine qualify '+chr(0xe7)+' ',dir=base) as folder:
        work=Path(folder)
        env=dict(os.environ)
        for key in ('PYTHONPATH','PYTHONHOME','VIRTUAL_ENV'):env.pop(key,None)
        env.update(PYTHONUTF8='1',PIP_NO_INDEX='1',PIP_DISABLE_PIP_VERSION_CHECK='1',LOCALAPPDATA=str(work/'cache'),XDG_CACHE_HOME=str(work/'cache'))
        if sys.platform=='darwin':env['HOME']=str(work/'home')
        environment=work/'venv'
        subprocess.run([str(interpreters[args.python_minor]),'-m','venv',str(environment)],check=True,cwd=work,env=env,timeout=120,capture_output=True)
        python=environment/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
        command=[str(python),'-m','pip','install','--no-index','--no-deps','--no-build-isolation']
        if args.wheelhouse:
            command.extend(['--find-links',str(args.wheelhouse.resolve())])
            subprocess.run([str(python),'-m','pip','install','--no-index','--find-links',str(args.wheelhouse.resolve()),'setuptools>=68','wheel'],check=True,cwd=work,env=env,timeout=120,capture_output=True)
        command.append(str(package))
        installed=subprocess.run(command,check=True,cwd=work,env=env,timeout=120,capture_output=True)
        console=environment/('Scripts/desembaraca-twine.exe' if os.name=='nt' else 'bin/desembaraca-twine')
        for invocation in ([str(console),'--help'],[str(python),'-m','twine_edge_overlap','--help']):
            subprocess.run(invocation,check=True,cwd=work,env=env,timeout=10,capture_output=True)
        # Worker deliberately imports only the installed package, never ROOT/src.
        request=dict(target=target,artifact_id=args.artifact_id,application_revision=args.application_revision,
                     source_state=args.source_state,
                     variant_required=variant_needed,
                     package_sha256=args.package_sha256,package_mode='wheel' if package.suffix=='.whl' else 'sdist',
                     python_minor=args.python_minor,python_origin=args.python_origin,interpreters=facts,
                     image_id=args.image_id,image_digest=args.image_digest,environment_kind=kind,github_actions=ci_context,
                     fixture_root=str(ROOT/'tests/fixtures'),work=str(work),
                     retain_review=bool(getattr(args,'review_output',None)))
        request_path=work/'request.json'
        request_path.write_text(json.dumps(request),encoding='utf-8')
        output=work/'result.json'
        subprocess.run([str(python),str(ROOT/'tools/runtime/qualification-worker.py'),str(request_path),str(output)],check=True,cwd=work,env=env,timeout=1200,capture_output=True)
        # Pretty-printed full rolling inventories are larger than raw query output.
        # This maintainer evidence limit does not change any runtime/query limit.
        record=read_json(output,maximum=32*1024**2)
        record['installation'].update(console=True,module=True)
        record['log_text']=installed.stdout.decode('utf-8',errors='replace')+'\n'+record.pop('log_text','')
        for private in (str(work),str(work).replace('\\\\?\\',''),str(package.parent),str(ROOT)):
            record['log_text']=record['log_text'].replace(private,'<test-path>')
        if getattr(args,'review_output',None):
            record['review_bundle']=export_review(work,record,args.review_output)
        return record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry',type=Path,default=ROOT/'tools/runtime/abi-targets.json')
    for name in ('target','artifact-id','application-revision','package-sha256','python-origin','image-id','image-digest'):
        parser.add_argument('--'+name,required=True)
    for name in ('package','python-312','python-314'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--wheelhouse',type=Path)
    parser.add_argument('--python-minor',choices=('3.12','3.14'),required=True)
    parser.add_argument('--source-state',choices=('committed','dirty','unverified'),default='unverified')
    parser.add_argument('--environment-kind',choices=('github-actions','native','wsl','container','emulated','simulated'),required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--review-output',type=Path,help='New directory for six public Twine outputs; visual review stays pending')
    args=parser.parse_args()
    try:
        if args.output.exists():raise ValueError('Evidence output already exists')
        if args.review_output and (args.review_output.exists() or args.review_output.is_symlink()):
            raise ValueError('Review output already exists')
        record=collect(args)
        log_folder=args.output.with_suffix('.logs')
        log_folder.mkdir(exist_ok=False)
        log=log_folder/'collection.txt'
        log.write_text(record.pop('log_text'),encoding='utf-8')
        record['logs']=[dict(path=log_folder.name+'/'+log.name,sha256=hashlib.sha256(log.read_bytes()).hexdigest())]
        with args.output.open('x',encoding='utf-8') as stream:json.dump(record,stream,indent=2,ensure_ascii=False);stream.write('\n')
        print('Evidence collected. Missing gates remain pending; no support was promoted.')
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as exc:
        detail=str(exc) if isinstance(exc,ValueError) else type(exc).__name__
        parser.exit(1,'Qualification collection failed: '+detail+'; no support promoted.\n')


if __name__=='__main__':main()
