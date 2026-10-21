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
    if not Path(facts['package_path']).resolve().is_relative_to(environment.resolve()):
        raise ValueError('Application imported outside isolated venv')
    if facts['git_available'] or facts['graphviz_available']:
        raise ValueError('Application PATH exposes Git or global Graphviz')
    if facts['direct_url'].get('archive_info', {}).get('hashes', {}).get('sha256') != archive_sha256:
        raise ValueError('Installer recorded another input archive')


def prepare_engine_fixture(artifact, destination, artifact_id):
    """Stage a byte-bound private bundle; never change the installed catalog."""
    def read(path, maximum=8 * 1024**2):
        if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= maximum:
            raise ValueError('Invalid private engine input')
        return path.read_bytes()
    candidates = list(artifact.rglob('candidate.json'))
    if len(candidates) != 1:
        raise ValueError('Expected one private engine candidate')
    candidate_raw = read(candidates[0])
    candidate = json.loads(candidate_raw)
    if candidate.get('artifact_id') != artifact_id or candidate.get('qualified') is not False:
        raise ValueError('Private engine candidate identity differs')
    package = candidates[0].parent
    inventory_raw = read(package / 'inventory.json')
    archive_raw = read(package / 'candidate.zip', MAXIMUM)
    if (digest(inventory_raw) != candidate['inventory_sha256']
            or digest(archive_raw) != candidate['archive_sha256']
            or len(archive_raw) != candidate['archive_bytes']):
        raise ValueError('Private engine inventory/archive changed')
    provenances = [read(p) for p in artifact.rglob('provenance.json')]
    matching = [raw for raw in provenances if digest(raw) == candidate['provenance_sha256']]
    if not matching:
        raise ValueError('Private engine provenance is missing')
    provenance_raw = matching[0]
    provenance = json.loads(provenance_raw)
    if (provenance.get('completed') is not True or provenance.get('artifact_id') != artifact_id
            or json.loads(inventory_raw)['provenance_sha256'] != digest(provenance_raw)):
        raise ValueError('Private engine provenance is incomplete or inconsistent')
    destination.mkdir(exist_ok=False)
    for name, raw in [('candidate.json', candidate_raw), ('inventory.json', inventory_raw),
                      ('candidate.zip', archive_raw), ('provenance.json', provenance_raw)]:
        (destination / name).write_bytes(raw)
    return dict(artifact_id=artifact_id, engine_sha256=provenance['executable_sha256'],
        candidate_archive_sha256=candidate['archive_sha256'], provenance_sha256=digest(provenance_raw))


def validate_engine_result(report, fixture, cases, system):
    if (report.get('passed') is not True or report.get('qualified') is not False
            or report.get('engine_sha256') != fixture['engine_sha256']
            or report.get('provenance_sha256') != fixture['provenance_sha256']):
        raise ValueError('Private installed-engine result differs from staged bundle')
    observations = report.get('observations', {})
    if set(observations) != {'automatic', 'explicit'}:
        raise ValueError('Private installed-engine first-use evidence is incomplete')
    for row in observations.values():
        if (row.get('acquisition_calls') != 1 or row.get('offline_acquisition_calls') != 0
                or any(row.get(key) is not True for key in ('real_engine', 'fixture_transport',
                    'healthy_generation_reused', 'final_destination_probe', 'probe_before_ready', 'external_unicode_paths'))
                or row.get('executable_mode') != 0o755 or row.get('generation_mode') != 0o700):
            raise ValueError('Private installed-engine preparation/offline invariant failed')
    rows = report.get('cases', [])
    expected = {item['case']: item for item in cases}
    actual = {item['case']: item for item in rows}
    if len(actual) != len(rows) or set(actual) != set(expected):
        raise ValueError('Private installed-engine corpus is incomplete or duplicated')
    for name, row in actual.items():
        if (len(row['before']) != 3 or len(row['after']) != 3
                or any(type(n) is not int or n < 0 for n in [*row['before'], *row['after']])
                or any(a > b for a, b in zip(row['after'], row['before']))):
            raise ValueError('Private installed-engine geometry regressed')
        if expected[name]['known_resolvable'] and row['after'] != [0, 0, 0]:
            raise ValueError('Known reference was not solved by installed engine')
    if system == 'darwin' and (report.get('security_before') is None
            or report['security_before'] != report.get('security_after')
            or observations['explicit'].get('native_inspection', {}).get('security_settings_unchanged') is not True):
        raise ValueError('macOS protection observations changed or are missing')


def validate_recovery_result(rows, cases):
    expected = {item['case'] for item in cases if item['known_resolvable']}
    if not isinstance(rows, dict) or set(rows) != {'transfer', 'disk-space', 'corrupt-archive', 'execution-denied'}:
        raise ValueError('Private engine failed-repair scenarios are incomplete')
    for row in rows.values():
        refs = row.get('references', [])
        if (row.get('selected_generation_preserved') is not True
                or row.get('previous_handle_usable') is not True
                or row.get('failed_repair_acquisition_calls') != 1
                or row.get('offline_acquisition_calls') != 0
                or len(refs) != len(expected) or {item['case'] for item in refs} != expected):
            raise ValueError('Previous generation or complete offline corpus not preserved after failed repair')
        for item in refs:
            if (item.get('after') != [0, 0, 0] or any(type(n) is not int for n in item['after'])
                    or item.get('original_preserved') is not True
                    or item.get('semantic_preserved') is not True):
                raise ValueError('Failed-repair offline processing did not preserve a reference')
    if rows['execution-denied'].get('real_execution_denial') is not True:
        raise ValueError('Native execution permission denial was not observed')


def validate_process_recovery(report, cases):
    expected = {item['case'] for item in cases if item['known_resolvable']}
    stages = {'during_download', 'before_select', 'after_select', 'concurrent_first_use'}
    if (not isinstance(report, dict) or report.get('passed') is not True
            or report.get('real_engine') is not True or set(report.get('scenarios', {})) != stages):
        raise ValueError('Native process recovery scenarios are incomplete')
    for name, row in report['scenarios'].items():
        references = row.get('cases', [])
        if (row.get('passed') is not True or row.get('old_handle_usable') is not True
                or row.get('offline_references') != len(expected)
                or len(references) != len(expected) or {r['case'] for r in references} != expected
                or any(r.get('after') != [0, 0, 0] or any(type(n) is not int for n in r['after'])
                       for r in references)):
            raise ValueError('Native process recovery did not preserve complete offline processing')
        if name == 'concurrent_first_use':
            if (row.get('workers') != 2 or row.get('acquisition_calls') != 1
                    or row.get('same_generation') is not True or row.get('workers_ready') != 2
                    or row.get('start_barrier') is not True):
                raise ValueError('Concurrent first use duplicated acquisition or selected generations')
        elif (row.get('exitcode') != 77 or row.get('lock_reacquired') is not True
                or row.get('orphan_untouched') is not True
                or row.get('selection') != ('new' if name == 'after_select' else 'previous')):
            raise ValueError('Crash did not preserve selector, orphan or release its lock')


def validate_cache_notice_result(report, fixture, expected):
    if (report.get('passed') is not True or report.get('qualified') is not False
            or report.get('engine_sha256')!=fixture['engine_sha256']
            or report.get('provenance_sha256')!=fixture['provenance_sha256']
            or report.get('before')!=expected or report.get('after')!=expected
            or report.get('offline_acquisition_calls')!=0 or report.get('initial_acquisition_calls')!=1
            or any(report.get(key) is not True for key in ('same_generation','corruption_rejected',
                'restored_snapshot_matches','modes_checked'))):
        raise ValueError('Installed cache notices differ from inventory or offline invariants')


def stage_engine_driver(work):
    driver = work / 'test-driver'
    files = ('tests/common.py', 'tests/runtime_support.py', 'tests/native_acceptance.py',
        'tests/integration/__init__.py', 'tests/integration/test_linux_runtime.py',
        'tests/integration/test_macos_runtime.py', 'tools/runtime/verify-artifact.py',
        '.github/scripts/probe-installed-recovery.py', '.github/scripts/probe-cache-notices.py')
    for name in files:
        target = driver / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    shutil.copytree(ROOT / 'tests/fixtures', driver / 'tests/fixtures',
        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    if (driver / 'src').exists():
        raise ValueError('Engine test driver must not expose the application checkout')
    return driver


def collect(wheel, sdist, wheelhouse, *, engine_artifact=None, engine_id=None, engine_check='runtime'):
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
        fixture = None
        if engine_artifact is not None:
            if sys.platform not in ('linux', 'darwin'):
                raise ValueError('Private engine integration requires matching native POSIX host')
            engine_package = work / 'private-engine'
            fixture = prepare_engine_fixture(engine_artifact, engine_package, engine_id)
            driver = stage_engine_driver(work)
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
            def run(argv, timeout=120):
                result = process.run_bounded([str(x) for x in argv], cwd=profile, env=env,
                    timeout=timeout, max_output=8 * 1024**2)
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
            runtime_report = None
            notice_report = None
            if fixture is not None:
                if engine_check=='notices':
                    report_path=work/('cache-notices-'+mode+'.json')
                    run([python,'-I',driver/'.github/scripts/probe-cache-notices.py','--driver',driver,
                        '--package',engine_package,'--provenance',engine_package/'provenance.json','--report',report_path])
                    if report_path.stat().st_size>1024**2:raise ValueError('Cache notice receipt exceeds bound')
                    notice_report=json.loads(report_path.read_bytes())
                    expected={r['path']:r['sha256'] for r in json.loads((engine_package/'inventory.json').read_bytes())['files']
                              if r['path'].startswith('third-party-notices/')}
                    application_notice=json.loads((ROOT/'src/twine_edge_overlap/runtime-manifest.json').read_bytes())['notices'][0]
                    expected['third-party-notices/private-integration-application.txt']=application_notice['sha256']
                    validate_cache_notice_result(notice_report,fixture,expected)
                else:
                    report_path = work / ('runtime-' + mode + '.json')
                    module = 'test_macos_runtime.py' if sys.platform == 'darwin' else 'test_linux_runtime.py'
                    command = [python, '-I', driver / 'tests/integration' / module,
                        '--package', engine_package, '--provenance', engine_package / 'provenance.json',
                        '--report', report_path]
                    if sys.platform == 'linux':
                        command.extend(['--environment-kind', 'wsl' if 'microsoft' in platform.release().lower() else 'native'])
                    run(command, timeout=300)
                    if report_path.stat().st_size > 1024**2:
                        raise ValueError('Private engine report exceeds bound')
                    runtime_report = json.loads(report_path.read_bytes())
                    cases = json.loads((ROOT / 'tests/fixtures/cases.json').read_bytes())
                    validate_engine_result(runtime_report, fixture, cases, sys.platform)
                    validate_recovery_result(runtime_report['observations']['explicit'].get('recovery'), cases)
                    validate_process_recovery(runtime_report['observations']['explicit'].get('process_recovery'), cases)
            records.append(dict(mode=mode, archive_sha256=digest(package.read_bytes()),
                package_files_verified=len(inventory['files']), licenses_verified=inventory['licenses'],
                installed_file_hashes=facts['files'], entrypoints_verified=3,
                import_from_venv=True, git_and_global_graphviz_absent=True,
                outside_checkout=True, engine_prepared=fixture is not None,
                private_engine=runtime_report, cache_notices=notice_report, commands=commands))
    return dict(kind='current-wheel-sdist-offline-installation-not-support-qualification',
        passed=True, qualified=False, captured_at=datetime.now(timezone.utc).isoformat(),
        application_revision=os.environ.get('GITHUB_SHA'), source_state='current-source-content-addressed',
        tool_sha256=digest(Path(__file__).read_bytes()),
        python=platform.python_version(), system=platform.system(),
        arch=platform.machine(), records=records, private_engine_fixture=fixture,
        build_tools=[dict(name=p.name, sha256=digest(p.read_bytes())) for p in wheels],
        limitations=['Current development packages, not final remotely distributed candidates',
            'Optional private engine uses controlled acquisition and a Python-only network guard',
            'No signature/notarization approval, syscall network claim or per-cell qualification'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('wheel', 'sdist', 'dist-dir'):
        parser.add_argument('--' + name, type=Path)
    for name in ('wheelhouse', 'report'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--engine-artifact', type=Path)
    parser.add_argument('--engine-id')
    parser.add_argument('--engine-check',choices=('runtime','notices'),default='runtime')
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
    if bool(args.engine_artifact) != bool(args.engine_id):
        parser.error('Supply both --engine-artifact and --engine-id')
    if args.engine_check=='notices' and not args.engine_artifact:
        parser.error('Notice cache check requires a private engine artifact')
    if args.report.exists():
        parser.error('Preserve existing reports; choose a new file')
    result = collect(args.wheel.resolve(), args.sdist.resolve(), args.wheelhouse.resolve(),
        engine_artifact=args.engine_artifact.resolve() if args.engine_artifact else None,
        engine_id=args.engine_id,engine_check=args.engine_check)
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print('Current wheel/sdist installed and verified outside checkout; no native support qualification.')
