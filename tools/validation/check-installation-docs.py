"""Exercise the documented immutable remote install in a disposable external venv.

This checks installation/help and packaged metadata, never native-engine support.
Run on an ephemeral CI runner; no engine acquisition or global installation.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import venv

REVISION = '40b3e38f3dc6bef2fe64b17f66e1f812460bd7f1'
URL = 'https://github.com/Extremois/desembaraca-twine/archive/' + REVISION + '.zip'


def collect(work):
    work = work.resolve()
    checkout = Path(__file__).resolve().parents[2]
    for relative in ('README.md', 'specs/003-add-cross-platform-support/quickstart.md'):
        if URL not in (checkout/relative).read_text(encoding='utf-8'):
            raise ValueError('Documented immutable URL differs from smoke-test source')
    if work.is_relative_to(checkout):
        raise ValueError('Use a new work directory outside the checkout')
    work.mkdir(parents=True, exist_ok=False)
    home = work / 'profile'
    home.mkdir()
    environment = dict(os.environ)
    for key in ('PYTHONPATH', 'PYTHONHOME', 'PIP_TARGET', 'PIP_PREFIX', 'PIP_USER'):
        environment.pop(key, None)
    environment.update(HOME=str(home), USERPROFILE=str(home), LOCALAPPDATA=str(home/'local'),
        XDG_CACHE_HOME=str(home/'cache'), PIP_CACHE_DIR=str(home/'pip'),
        PYTHONUTF8='1', PYTHONNOUSERSITE='1', PIP_CONFIG_FILE=os.devnull)
    root = work / 'venv com acentos á'
    venv.EnvBuilder(with_pip=True).create(root)
    scripts = root / ('Scripts' if os.name == 'nt' else 'bin')
    python = scripts / ('python.exe' if os.name == 'nt' else 'python')
    console = scripts / ('desembaraca-twine.exe' if os.name == 'nt' else 'desembaraca-twine')
    environment['PATH'] = str(scripts)
    commands = []

    def run(argv, timeout=60):
        result = subprocess.run([str(item) for item in argv], cwd=home, env=environment,
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        if len(result.stdout)+len(result.stderr)>8*1024**2:
            raise ValueError('Command output exceeded bound')
        commands.append(dict(arguments=[str(item).replace(str(root), '<venv>') for item in argv],
            returncode=result.returncode, stdout_sha256=hashlib.sha256(result.stdout).hexdigest(),
            stderr_sha256=hashlib.sha256(result.stderr).hexdigest()))
        if result.returncode:
            raise RuntimeError(result.stderr.decode('utf-8', errors='replace')[-8000:])
        return result.stdout

    run([python, '-m', 'pip', 'install', '--disable-pip-version-check', '--no-cache-dir', URL], 240)
    for argv in ([console, '--help'], [python, '-m', 'twine_edge_overlap', '--help'],
                 [python, '-m', 'twine_edge_overlap.cli', '--help']):
        help_text = run(argv).decode('utf-8')
        if '--prepare-runtime' not in help_text or '--repair-runtime' not in help_text:
            raise ValueError('Documented CLI options missing')
    raw = run([python, '-c', '''import hashlib,importlib.metadata as m,json,pathlib,shutil
d=m.distribution('twine-edge-overlap')
files={str(p):hashlib.sha256(pathlib.Path(d.locate_file(p)).read_bytes()).hexdigest()
       for p in d.files if str(p).endswith('.json') or '/third_party/' in str(p)}
import twine_edge_overlap
print(json.dumps(dict(direct_url=json.loads(d.read_text('direct_url.json')),
    package_path=str(pathlib.Path(twine_edge_overlap.__file__).resolve()),files=files,
    git_available=shutil.which('git') is not None,graphviz_available=shutil.which('dot') is not None)))'''])
    installed = json.loads(raw)
    if installed['direct_url']['url'] != URL or not installed['direct_url']['archive_info'].get('hashes', {}).get('sha256'):
        raise ValueError('Remote source identity not recorded')
    if not Path(installed.pop('package_path')).is_relative_to(root):
        raise ValueError('Imported package outside fresh venv')
    if installed['git_available'] or installed['graphviz_available']:
        raise ValueError('Restricted PATH unexpectedly contains Git or Graphviz')
    for name in ('runtime-catalog.json','support-matrix.json','runtime-manifest.json'):
        if 'twine_edge_overlap/'+name not in installed['files']:
            raise ValueError('Missing packaged metadata: '+name)
    if not any('/third_party/' in name for name in installed['files']):
        raise ValueError('Missing packaged notices')
    if any(home.rglob('ready.json')) or any(home.rglob('active.json')):
        raise ValueError('Help unexpectedly prepared an engine')
    return dict(kind='documented-remote-install-and-help-smoke',passed=True,qualified=False,
        revision=REVISION,url=URL,python=platform.python_version(),os=platform.system(),
        arch=platform.machine(),outside_checkout=True,path_contains_only_venv=True,
        engine_prepared=False,installed=installed,commands=commands,
        limitations=['Installation/help only; distributed catalog still Windows-only',
                    'No POSIX native-engine preparation, cell acceptance or support promotion'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        parser.error('Report already exists')
    result = collect(args.work)
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')
    print('Remote installation and three help invocations passed; no native support qualification.')
