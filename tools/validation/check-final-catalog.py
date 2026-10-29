"""Accept wheel, sdist and immutable remote installs through the real catalog.

Run on GitHub Actions only. Reuses the existing installed-package inventory and
qualification worker; acquisition uses the published URLs, without fixtures.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import venv

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location('final_package_inventory',ROOT/'tools/validation/check-built-packages.py')
packages=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packages)


def run(command,work,env,timeout=240):
    result=subprocess.run([str(x) for x in command],cwd=work,env=env,
        stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
    if len(result.stdout)+len(result.stderr)>8*1024**2:
        raise ValueError('Acceptance command output exceeded limit')
    if result.returncode:
        raise RuntimeError(result.stderr.decode('utf-8',errors='replace')[-8000:])
    return result


def collect(dist,wheelhouse,abi):
    if os.environ.get('GITHUB_ACTIONS')!='true':
        raise ValueError('Run final acceptance in GitHub Actions')
    revision=os.environ['GITHUB_SHA']
    wheels=list(dist.glob('*.whl'));sources=list(dist.glob('*.tar.gz'))
    if len(wheels)!=1 or len(sources)!=1:raise ValueError('One wheel and one sdist required')
    expected=packages.package_inventory(wheels[0],sources[0])
    system={'Windows':'windows','Darwin':'darwin','Linux':'linux'}[platform.system()]
    arch={'AMD64':'x86_64','arm64':'aarch64'}.get(platform.machine(),platform.machine())
    targets=json.loads((ROOT/'tools/runtime/abi-targets.json').read_bytes())['targets']
    selected=[t for t in targets if (t['os'],t['arch'],t['abi'])==(system,arch,abi)]
    if len(selected)!=1:raise ValueError('Unknown final ABI slot')
    target=selected[0]
    catalog=json.loads((ROOT/'src/twine_edge_overlap/runtime-catalog.json').read_bytes())
    descriptors=[d for d in catalog['artifacts'] if (d['os'],d['arch'],d['abi'])==
                 (system,arch,'windows' if abi=='win32' else abi)]
    if len(descriptors)!=1:raise ValueError('Missing or ambiguous installed catalog artifact')
    descriptor=descriptors[0]
    facts=dict(system=system,arch=arch,abi=abi,python=platform.python_version(),kernel=platform.release(),
        image=os.environ.get('TWINE_CI_IMAGE',os.environ.get('ImageOS','')+'/'+os.environ.get('ImageVersion','')),
        runner_arch=os.environ.get('RUNNER_ARCH'),fingerprint_scope='Observed environment facts; not a root-filesystem digest')
    image_digest=hashlib.sha256(json.dumps(facts,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    url='https://github.com/Extremois/desembaraca-twine/archive/'+revision+'.zip'
    records=[]
    for mode,package in (('wheel',wheels[0]),('sdist',sources[0]),('remote',url)):
        with tempfile.TemporaryDirectory(prefix='twine final com acentos ação ') as temporary:
            work=Path(temporary).resolve()
            if work.is_relative_to(ROOT):raise ValueError('Use an external installation workspace')
            environment=work/'venv';venv.EnvBuilder(with_pip=True).create(environment)
            scripts=environment/('Scripts' if os.name=='nt' else 'bin')
            python=scripts/('python.exe' if os.name=='nt' else 'python')
            env=dict(os.environ)
            for key in ('PYTHONPATH','PYTHONHOME','VIRTUAL_ENV','PIP_TARGET','PIP_PREFIX'):
                env.pop(key,None)
            env.update(PATH=str(scripts),PYTHONUTF8='1',PYTHONNOUSERSITE='1',PIP_CONFIG_FILE=os.devnull,
                PIP_DISABLE_PIP_VERSION_CHECK='1',LOCALAPPDATA=str(work/'cache'),XDG_CACHE_HOME=str(work/'cache'))
            (work/'home').mkdir()
            if system=='darwin':env['HOME']=str(work/'home')
            run([python,'-m','pip','install','--no-index','--find-links',wheelhouse,'setuptools','wheel','packaging'],work,env)
            run([python,'-m','pip','install','--no-index','--no-deps','--no-build-isolation',package],work,env)
            installed=json.loads(run([python,'-c',packages.FACTS],work,env).stdout)
            if installed['files']!=expected['files'] or installed['licenses']!=expected['licenses']:
                differences={group:[name for name in set(installed[group])|set(expected[group])
                    if installed[group].get(name)!=expected[group].get(name)] for group in ('files','licenses')}
                raise ValueError('Installed '+mode+' differs from final distributions: '+json.dumps(differences))
            if (not Path(installed.pop('package_path')).resolve().is_relative_to(environment)
                    or installed['git_available'] or installed['graphviz_available']):
                raise ValueError('Final installation escaped its isolated venv/PATH')
            if mode=='remote' and installed['direct_url']['url']!=url:
                raise ValueError('Remote package did not come from the immutable commit URL')
            for module in ('twine_edge_overlap','twine_edge_overlap.cli'):
                run([python,'-m',module,'--help'],work,env,30)
            run([scripts/('desembaraca-twine.exe' if os.name=='nt' else 'desembaraca-twine'),'--help'],work,env,30)
            package_sha=(installed['direct_url']['archive_info']['hashes']['sha256'] if mode=='remote'
                         else hashlib.sha256(package.read_bytes()).hexdigest())
            request=dict(target=target,artifact_id=descriptor['id'],application_revision=revision,
                source_state='committed',variant_required=False,package_sha256=package_sha,
                package_mode=mode,python_minor='.'.join(map(str,sys.version_info[:2])),
                python_origin='GitHub Actions native CPython; exact patch recorded',image_id=facts['image'],
                image_digest=image_digest,environment_kind='github-actions',
                github_actions=dict(repository=os.environ['GITHUB_REPOSITORY'],run_id=os.environ['GITHUB_RUN_ID'],
                    run_sha=revision,run_url='https://github.com/'+os.environ['GITHUB_REPOSITORY']+'/actions/runs/'+os.environ['GITHUB_RUN_ID'],
                    execution_kind='container' if Path('/.dockerenv').exists() else 'runner'),
                fixture_root=str(ROOT/'tests/fixtures'),work=str(work),retain_review=False)
            request_path=work/'request.json';request_path.write_text(json.dumps(request),encoding='utf-8')
            result_path=work/'result.json'
            run([python,ROOT/'tools/runtime/qualification-worker.py',request_path,result_path],work,env,900)
            result=json.loads(result_path.read_bytes())
            if not result['passed'] or len(result['corpus'])!=13 or result['network']['attempts']!=0:
                raise ValueError('Final public runtime/corpus/offline acceptance failed')
            result['installation'].update(console=True,module=True,outside_checkout=True)
            result['log_text']=result['log_text'].replace(str(work),'<test-work>')
            records.append(dict(mode=mode,archive_sha256=package_sha,installed_files=installed['files'],
                licenses=installed['licenses'],outside_checkout=True,git_and_global_graphviz_absent=True,
                real_catalog=True,public_acquisition=True,worker=result))
    return dict(kind='final-public-catalog-installed-acceptance',passed=True,qualified=False,
        application_revision=revision,environment=facts,environment_digest=image_digest,
        python=platform.python_version(),artifact_id=descriptor['id'],target_id=target['id'],records=records,
        scope='Real published catalog with wheel/sdist/remote acquisition, corpus and offline reuse; support promotion is a reviewed separate step')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('dist-dir','wheelhouse','report'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--abi',choices=('win32','darwin','glibc','musl'),required=True)
    args=parser.parse_args()
    if args.report.exists():parser.error('Preserve existing reports')
    report=collect(args.dist_dir.resolve(),args.wheelhouse.resolve(),args.abi)
    with args.report.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
