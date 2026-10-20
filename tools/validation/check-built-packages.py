"""Check current wheel/sdist bytes and isolated offline installations.

Build tools are supplied as wheels, never installed globally. This checks the
Python distribution and help only; it neither acquires nor qualifies an engine.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import sys
import tarfile
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = 'twine_edge_overlap/'
MAXIMUM = 128 * 1024**2


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def package_inventory(wheel, sdist, checkout=ROOT):
    """Reject omitted/changed package files before running an installer."""
    expected = {}
    for path in (checkout / 'src/twine_edge_overlap').rglob('*'):
        if (path.is_file() and '__pycache__' not in path.parts
                and (path.suffix in ('.py', '.json') or 'third_party' in path.parts)):
            expected[path.relative_to(checkout / 'src').as_posix()] = digest(path.read_bytes())
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or sum(i.file_size for i in archive.infolist()) > MAXIMUM:
            raise ValueError('Ambiguous or excessive wheel')
        actual = {name: digest(archive.read(name)) for name in names
                  if name.startswith(PACKAGE) and not name.endswith('/')}
        if actual != expected:
            raise ValueError('Wheel package files differ from current source/data/notices')
        licenses = {}
        for name in ('LICENSE', 'NOTICE'):
            matches = [p for p in names if '.dist-info/' in p and p.endswith('/' + name)]
            if len(matches) != 1 or archive.read(matches[0]) != (checkout / name).read_bytes():
                raise ValueError('Wheel license/notice missing or changed')
            licenses[name] = digest(archive.read(matches[0]))
    with tarfile.open(sdist, 'r:gz') as archive:
        members = archive.getmembers()
        names = [item.name for item in members]
        roots = {PurePosixPath(name).parts[0] for name in names if PurePosixPath(name).parts}
        if len(roots) != 1 or len(names) != len(set(names)) or len(names) > 10000:
            raise ValueError('Ambiguous sdist structure')
        if sum(item.size for item in members) > MAXIMUM:
            raise ValueError('Excessive sdist expansion')
        prefix = next(iter(roots)) + '/'
        found = {}
        source_licenses = {}
        for item in members:
            path = PurePosixPath(item.name)
            if (path.is_absolute() or '..' in path.parts or '\\' in item.name
                    or not (item.isfile() or item.isdir())):
                raise ValueError('Unsafe sdist member')
            if not item.isfile():
                continue
            name = item.name.removeprefix(prefix)
            if name.startswith('src/' + PACKAGE):
                found[name.removeprefix('src/')] = digest(archive.extractfile(item).read())
            if name in licenses:
                source_licenses[name] = digest(archive.extractfile(item).read())
        if found != expected or source_licenses != licenses:
            raise ValueError('Sdist package files/license/notices differ from wheel/source')
    return dict(files=expected, licenses=licenses)


FACTS = '''import hashlib,importlib.metadata as m,json,pathlib,shutil,sys
import twine_edge_overlap
d=m.distribution('twine-edge-overlap')
files={str(p).replace('\\\\','/'):hashlib.sha256(pathlib.Path(d.locate_file(p)).read_bytes()).hexdigest()
       for p in d.files if str(p).replace('\\\\','/').startswith('twine_edge_overlap/') and not str(p).endswith('.pyc')}
licenses={pathlib.Path(p).name:hashlib.sha256(pathlib.Path(d.locate_file(p)).read_bytes()).hexdigest()
          for p in d.files if str(p).endswith(('/LICENSE','/NOTICE'))}
print(json.dumps(dict(files=files,licenses=licenses,direct_url=json.loads(d.read_text('direct_url.json')),
    package_path=str(pathlib.Path(twine_edge_overlap.__file__).resolve()),
    git_available=shutil.which('git') is not None,graphviz_available=shutil.which('dot') is not None)))
'''


def validate_installation(facts, inventory, environment, archive_sha256):
    if facts['files'] != inventory['files'] or facts['licenses'] != inventory['licenses']:
        raise ValueError('Installed package differs from reviewed distribution bytes')
    if not Path(facts['package_path']).is_relative_to(environment.resolve()):
        raise ValueError('Application imported outside isolated venv')
    if facts['git_available'] or facts['graphviz_available']:
        raise ValueError('Application PATH exposes Git or global Graphviz')
    if facts['direct_url'].get('archive_info', {}).get('hashes', {}).get('sha256') != archive_sha256:
        raise ValueError('Installer recorded another input archive')


def collect(wheel, sdist, wheelhouse):
    import venv
    for path in (wheel, sdist):
        if not path.is_file() or not 0 < path.stat().st_size <= MAXIMUM:
            raise ValueError('Invalid distribution archive size')
    inventory = package_inventory(wheel, sdist)
    wheels = sorted(wheelhouse.glob('*.whl'))
    if not wheels:
        raise ValueError('Offline build-tool wheelhouse is empty')
    spec = importlib.util.spec_from_file_location('package_process', ROOT / 'src/twine_edge_overlap/engines/process.py')
    process = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = process
    spec.loader.exec_module(process)
    records = []
    with tempfile.TemporaryDirectory(prefix='twine-packages-') as folder:
        work = Path(folder).resolve()
        if work.is_relative_to(ROOT):
            raise ValueError('Installation workspace must be outside checkout')
        staged = work / 'inputs'
        staged.mkdir()
        for path in (wheel, sdist, *wheels):
            shutil.copyfile(path, staged / path.name)
        profile = work / 'profile'
        profile.mkdir()
        for mode, package in (('wheel', wheel), ('sdist', sdist)):
            environment = work / ('venv com acentos ação ' + mode)
            venv.EnvBuilder(with_pip=True).create(environment)
            scripts = environment / ('Scripts' if os.name == 'nt' else 'bin')
            python = scripts / ('python.exe' if os.name == 'nt' else 'python')
            console = scripts / ('desembaraca-twine.exe' if os.name == 'nt' else 'desembaraca-twine')
            env = {key: os.environ[key] for key in ('SystemRoot', 'WINDIR', 'TEMP', 'TMP') if key in os.environ}
            env.update(PATH=str(scripts), HOME=str(profile), USERPROFILE=str(profile),
                LOCALAPPDATA=str(profile / 'local'), XDG_CACHE_HOME=str(profile / 'cache'),
                PIP_NO_INDEX='1', PIP_CONFIG_FILE=os.devnull, PIP_DISABLE_PIP_VERSION_CHECK='1',
                PIP_NO_CACHE_DIR='1', PYTHONNOUSERSITE='1', PYTHONUTF8='1', LANG='C.UTF-8')
            commands = []
            def run(argv):
                result = process.run_bounded([str(x) for x in argv], cwd=profile, env=env,
                    timeout=120, max_output=8 * 1024**2)
                commands.append(dict(returncode=result.returncode,
                    stdout_sha256=digest(result.stdout), stderr_sha256=digest(result.stderr)))
                if result.returncode:
                    message = result.stderr.decode('utf-8', errors='replace')[-4000:].replace(str(work), '<work>')
                    raise RuntimeError('Isolated package command failed: ' + message)
                return result.stdout
            if mode == 'sdist':
                run([python, '-I', '-m', 'pip', 'install', '--no-index', '--no-deps',
                     '--find-links', staged, 'setuptools>=68', 'wheel', 'packaging'])
            run([python, '-I', '-m', 'pip', 'install', '--no-index', '--no-deps',
                 '--no-build-isolation', staged / package.name])
            for argv in ([console, '--help'], [python, '-I', '-m', 'twine_edge_overlap', '--help'],
                         [python, '-I', '-m', 'twine_edge_overlap.cli', '--help']):
                help_text = run(argv)
                if b'--prepare-runtime' not in help_text or b'--repair-runtime' not in help_text:
                    raise ValueError('Installed entrypoint options missing')
            facts = json.loads(run([python, '-I', '-c', FACTS]))
            validate_installation(facts, inventory, environment, digest(package.read_bytes()))
            if list(profile.rglob('active.json')) or list(profile.rglob('ready.json')):
                raise ValueError('Help unexpectedly prepared an engine')
            records.append(dict(mode=mode, archive_sha256=digest(package.read_bytes()),
                package_files_verified=len(inventory['files']), licenses_verified=inventory['licenses'],
                installed_file_hashes=facts['files'], entrypoints_verified=3,
                import_from_venv=True, git_and_global_graphviz_absent=True,
                outside_checkout=True, engine_prepared=False, commands=commands))
    return dict(kind='current-wheel-sdist-offline-installation-not-support-qualification',
        passed=True, qualified=False, captured_at=datetime.now(timezone.utc).isoformat(),
        application_revision=os.environ.get('GITHUB_SHA'), source_state='current-source-content-addressed',
        tool_sha256=digest(Path(__file__).read_bytes()),
        python=platform.python_version(), system=platform.system(),
        arch=platform.machine(), records=records,
        build_tools=[dict(name=p.name, sha256=digest(p.read_bytes())) for p in wheels],
        limitations=['Current development packages, not final remotely distributed candidates',
            'Installation and help only; no native engine, runtime acquisition or per-cell qualification'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('wheel', 'sdist', 'dist-dir'):
        parser.add_argument('--' + name, type=Path)
    for name in ('wheelhouse', 'report'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    if args.dist_dir:
        if args.wheel or args.sdist:
            parser.error('Use --dist-dir or explicit --wheel/--sdist')
        wheels = list(args.dist_dir.glob('*.whl'))
        sources = list(args.dist_dir.glob('*.tar.gz'))
        if len(wheels) != 1 or len(sources) != 1:
            parser.error('Expected exactly one wheel and one sdist in --dist-dir')
        args.wheel, args.sdist = wheels[0], sources[0]
    elif not args.wheel or not args.sdist:
        parser.error('Supply both --wheel/--sdist or --dist-dir')
    if args.report.exists():
        parser.error('Preserve existing reports; choose a new file')
    result = collect(args.wheel.resolve(), args.sdist.resolve(), args.wheelhouse.resolve())
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print('Current wheel/sdist installed and verified outside checkout; no native support qualification.')
