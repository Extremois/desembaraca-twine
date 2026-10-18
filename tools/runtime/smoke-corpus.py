"""Exercise a local build and relocation; this never qualifies a support cell."""
import argparse
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import platform
import re
import shutil
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from twine_edge_overlap.application import run
from twine_edge_overlap.runtime import RuntimeHandle
from twine_edge_overlap.runtime_platform import runtime_environment
from twine_edge_overlap.formats.profile import parse, verify
from twine_edge_overlap.engines.process import run_bounded


def smoke(build, environment_kind):
    build = Path(build).resolve()
    provenance = json.loads((build / 'provenance.json').read_text())
    binary = build / 'candidate/bin/dot'
    actual_sha = hashlib.sha256(binary.read_bytes()).hexdigest()
    if not provenance.get('completed') or actual_sha != provenance['executable_sha256']:
        raise ValueError('Candidate differs from completed build provenance')
    report = dict(environment_kind=environment_kind, python=platform.python_version(),
                  kernel=platform.release(), arch=platform.machine(), engine_sha256=actual_sha,
                  source_sha256=provenance['source']['sha256'], recipe_sha256=provenance['recipe_sha256'], cases=[])
    with tempfile.TemporaryDirectory(prefix='desembaraca-smoke-') as folder, ExitStack() as stack:
        work = Path(folder)
        relocated = work / ('engine with spaces and ' + chr(0xe7))
        relocated.mkdir()
        executable = relocated / 'dot'
        shutil.copyfile(binary, executable)
        executable.chmod(0o755)
        env = runtime_environment(executable, host_os=provenance['native_os'])
        handle = RuntimeHandle('experimental-local-build', 'local-smoke', relocated, executable, relocated, env)
        for name in ('socket.getaddrinfo', 'socket.socket.connect', 'socket.create_connection'):
            stack.enter_context(patch(name, side_effect=AssertionError('Unexpected Python network attempt')))
        probe = run_bounded([str(executable), '-V'], cwd=relocated, env=env, timeout=10, max_output=1024**2)
        if probe.returncode or b'16.1.0' not in probe.stdout + probe.stderr:
            raise ValueError('Relocated version probe failed')
        for case in json.loads((ROOT / 'tests/fixtures/cases.json').read_text()):
            original = (ROOT / 'tests/fixtures' / case['file']).read_bytes()
            source = work / case['file']
            source.write_bytes(original)
            result = run(source, runtime_provider=lambda: handle)
            output = result.path.read_bytes()
            verify(parse(original), parse(output))
            if source.read_bytes() != original or any(a > b for a, b in zip(result.after.values, result.before.values)):
                raise ValueError('Corpus preservation or non-regression failed: ' + case['case'])
            if case['known_resolvable'] and result.after.values != (0, 0, 0):
                raise ValueError('Known reference did not finish clean: ' + case['case'])
            report['cases'].append(dict(case=case['case'], input_sha256=hashlib.sha256(original).hexdigest(),
                                        output_sha256=hashlib.sha256(output).hexdigest(), before=result.before.values,
                                        after=result.after.values, status=result.status))
        if provenance['native_os'] == 'linux':
            inspector = shutil.which('readelf')
            if not inspector:
                raise ValueError('SDK readelf is required for the ABI smoke report')
            result = run_bounded([inspector, '--dynamic', '--version-info', str(executable)], timeout=30, max_output=8*1024**2)
            if result.returncode:
                raise ValueError('ABI inspection failed')
            text = result.stdout.decode('utf-8')
            report['needed'] = re.findall(r'\(NEEDED\).*?\[([^]]+)\]', text)
            versions = re.findall(r'\bGLIBC_(\d+(?:\.\d+)+)', text)
            report['highest_glibc_symbol'] = max(versions, key=lambda value: tuple(map(int, value.split('.')))) if versions else None
            report['abi_report_sha256'] = hashlib.sha256(result.stdout).hexdigest()
    report.update(passed=True, python_network_attempts=0,
                  qualification='library smoke only; no installation, full cell, native network tracing, Twine, license audit or oldest ABI qualification')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-output', type=Path, required=True)
    parser.add_argument('--environment-kind', choices=('native', 'wsl', 'container', 'emulated'), required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    report = smoke(args.build_output, args.environment_kind)
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print('Corpus and relocation passed; support qualification remains pending.')


if __name__ == '__main__':
    main()
