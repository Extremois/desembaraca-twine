"""Recheck the eight native guest artifacts offline; no engine or VM execution."""
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[4]
OUTPUT = Path(__file__).resolve().parent
REVISION = '96f765bb19e30536d505fe875fa57b52622cb336'
CANDIDATE = 'a825f0d80bd7892de0e307656d28070885a9d1ed'
SOURCE_SNAPSHOT = {}


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


baseline = load('native_ubuntu_review', '.github/scripts/check-native-baseline.py')
observer = load('native_ubuntu_network_review', 'tools/runtime/observe-linux-network.py')
sys.path[:0] = [str(ROOT / 'src')]
from twine_edge_overlap.engines.graphviz import build_dot, decode_layout
from twine_edge_overlap.formats.profile import parse


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(value)


def checked_guest(archive_row):
    require(re.fullmatch(r'actions-artifact-[0-9]+\.zip', archive_row['file']) is not None, 'Unsafe download path')
    raw = baseline.bounded(ROOT / '.tmp' / archive_row['file'], 8 * 1024**2)
    require(sha(raw) == archive_row['sha256'] and len(raw) == archive_row['bytes'], 'Downloaded guest artifact changed')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        require(len(entries) <= 200 and sum(row.file_size for row in entries) <= 64 * 1024**2, 'Guest evidence exceeds bound')
        payloads = {}
        for entry in entries:
            name = entry.filename
            require(not name.startswith('/') and '\\' not in name and ':' not in name
                    and all(part not in ('', '.', '..') for part in name.split('/')), 'Unsafe guest evidence path')
            require(name not in payloads and not entry.is_dir() and entry.file_size <= 8 * 1024**2, 'Ambiguous or excessive guest file')
            require(Path(name).suffix in ('.json', '.log', '.trace', '.txt'), 'Unexpected guest disk/key/payload')
            payloads[name] = archive.read(entry)

    def read(suffix):
        names = [name for name in payloads if name == suffix or name.endswith('/' + suffix)]
        require(len(names) == 1, 'Missing or ambiguous guest evidence: ' + suffix)
        return payloads[names[0]]

    native_raw = read('summary.json')
    native = json.loads(native_raw)
    release = native['image_pin']['release']
    abi = native['abi']
    require(release in ('18.04', '20.04', '22.04', '26.04') and abi in ('glibc', 'musl'), 'Unexpected guest release or ABI')
    require(native['revision'] == REVISION and native['candidate_revision'] == CANDIDATE, 'Guest application/candidate revision differs')
    require(native['candidate_run_id'] == (40565098269 if abi == 'glibc' else 40565098367), 'Candidate run reference differs')
    require(native['passed'] is True and native['qualified'] is False and native['approved'] is False, 'Guest must remain unqualified')
    require(native['image_pin'] == json.loads((ROOT / '.github/native-images' / ('ubuntu-' + release + '-amd64.json')).read_bytes()), 'Image pin differs')
    baseline.validate_pin(native['image_pin'], release)
    guest_raw = read('guest/guest.json')
    guest = json.loads(guest_raw)
    require(sha(guest_raw) == native['guest_report_sha256'], 'Guest report differs from host summary')
    baseline.validate_baseline(guest, native['kvm'], release)
    baseline.validate_engine_kind(guest, abi)
    cases = json.loads((ROOT / 'tests/fixtures/cases.json').read_bytes())
    require(len(guest['cases']) == 13 and len({row['case'] for row in guest['cases']}) == 13, 'Guest corpus is incomplete')
    for case in cases:
        row = next(row for row in guest['cases'] if row['case'] == case['case'])
        original = parse((ROOT / 'tests/fixtures' / case['file']).read_bytes())
        require(row['dot_sha256'] == sha(build_dot(original).encode('ascii')), 'Guest input differs from public fixture')
        require(row['output'] == case['case'] + '.json', 'Guest selected unexpected output name')
        layout = read('guest/' + row['output'])
        require(sha(layout) == row['output_sha256'], 'Guest layout bytes changed')
        decode_layout(layout, original)

    slots = []
    if abi == 'glibc':
        python_raw = read('private-python-report.json')
        require(sha(python_raw) == native['private_python_report_sha256'], 'Private Python report changed')
        pins = json.loads(read('private-python-pins.json'))
        require(pins == json.loads((ROOT / '.github/native-images/private-python-x64.json').read_bytes()), 'Private Python pins differ')
        python_report = json.loads(python_raw)
        baseline.validate_python_report(python_report, pins['interpreters'])
        wheel = json.loads(read('application-wheel.json'))
        require(wheel['source_revision'] == REVISION, 'Installed wheel source revision differs')
        for row in wheel['files']:
            name = row['path']
            require(name.startswith('twine_edge_overlap/') and '..' not in name.split('/') and '\\' not in name, 'Unexpected installed source path')
            if name not in SOURCE_SNAPSHOT:
                SOURCE_SNAPSHOT[name] = subprocess.check_output(
                    ['git', 'show', REVISION + ':src/' + name], cwd=ROOT, timeout=10)
            require(sha(SOURCE_SNAPSHOT[name]) == row['sha256'], 'Installed package source differs from committed source')
        for pin in pins['interpreters']:
            name = 'application-' + pin['minor'] + '.json'
            report_raw = read('application/' + name)
            report = json.loads(report_raw)
            reference = next(row for row in native['installed_application_reports'] if row['report'] == name)
            require(sha(report_raw) == reference['sha256'], 'Application report changed')
            baseline.validate_application_report(report, pin['patch'], wheel['sha256'], native['engine_sha256'], cases)
            baseline.validate_recovery_report(report['recovery'])
            require(report['wheel_source_revision'] == REVISION, 'Application wheel revision differs')
            require(report['application_outside_checkout'] is True and report['global_graphviz_and_git_absent'] is True
                    and report['installed_files_verified'] == len(wheel['files']), 'Installed application isolation/count differs')
            parsed = {}
            for kind in ('control', 'corpus'):
                trace = read('application/application-' + pin['minor'] + '.' + kind + '.trace')
                require(sha(trace) == report['native_network'][kind]['trace_sha256'], 'Native network trace changed')
                parsed[kind] = observer.parse_trace(trace.decode('utf-8'))
            baseline.validate_network_observation(parsed['control'], parsed['corpus'])
            slots.append(dict(python=pin['patch'], minor=pin['minor'], cases=13, known_zero_references=6,
                              recovery_scenarios=len(report['recovery']['scenarios']),
                              offline_reference_runs=sum(row['offline_references'] for row in report['recovery']['scenarios'].values()),
                              dot_executions=sum(Path(path).name == 'dot' for path in parsed['corpus']['successful_executables']),
                              native_network_syscalls=parsed['corpus']['network_syscalls'],
                              installed_files_verified=len(wheel['files']), report_sha256=sha(report_raw),
                              wheel_sha256=wheel['sha256']))
    destination = OUTPUT / ('ubuntu' + release.replace('.', '') + '-' + abi)
    require(not destination.exists(), 'Do not overwrite guest review files')
    for name, payload in payloads.items():
        write(destination / 'raw' / (name + '.gz'), gzip.compress(payload, mtime=0))
    return dict(release=release, abi=abi, run_id=archive_row['run_id'], actions_artifact_id=archive_row['id'],
                actions_archive_sha256=archive_row['sha256'], native_summary_sha256=sha(native_raw),
                kernel=guest['kernel'], glibc=guest['glibc'], arch=guest['arch'], kvm=native['kvm'],
                engine_sha256=guest['engine_sha256'], candidate_revision=CANDIDATE,
                image_pin=native['image_pin'], cases=13, geometry_decoded=True,
                system_python_unchanged=(python_report['system_python_before'] == python_report['system_python_after'] if slots else None),
                python_slots=slots,
                preserved_files=[dict(file=(destination.relative_to(OUTPUT) / 'raw' / (name + '.gz')).as_posix(),
                                      uncompressed_sha256=sha(payload)) for name, payload in payloads.items()])


def main():
    require(len(sys.argv) == 2, 'Usage: python capture.py DOWNLOAD_RECEIPT')
    index = json.loads(Path(sys.argv[1]).read_bytes())
    require(index['revision'] == REVISION and all(row['conclusion'] == 'success' for row in index['runs']), 'Wrong revision or unfinished workflow')
    require(not (OUTPUT / 'summary.json').exists(), 'Do not overwrite native review')
    require(len(index['downloads']) == 8 and len(index['foundation']) == 6, 'Missing guest artifacts or foundation logs')
    rows = [checked_guest(row) for row in index['downloads']]
    require({(row['release'], row['abi']) for row in rows} == {(release, abi) for release in ('18.04', '20.04', '22.04', '26.04') for abi in ('glibc', 'musl')}, 'Missing or duplicate guest cell')
    for row in index['foundation']:
        require(re.fullmatch(r'resolute-foundation-job-[0-9]+\.log', row['file']) is not None, 'Unsafe foundation log path')
        raw = baseline.bounded(ROOT / '.tmp' / row['file'], 8 * 1024**2)
        require(sha(raw) == row['sha256'], 'Foundation log changed')
        write(OUTPUT / 'foundation' / (row['file'] + '.gz'), gzip.compress(raw, mtime=0))
    summary = dict(kind='verified-native-ubuntu1804-2004-2204-2604-private-runtime-review', revision=REVISION,
                   qualified=False, approved=False, task_complete=False, tasks=['T033', 'T037', 'T076', 'T078'],
                   runs=index['runs'], foundation=index['foundation'], guests=rows,
                   capture_sha256=sha(Path(__file__).read_bytes()),
                   limitations=['Private development wheel and controlled runtime acquisition; no final remote candidate or sdist acceptance',
                                'Ubuntu historical images; no Pro/ESM eligibility assertion',
                                'Musl engine kernel observation on Ubuntu; no native Alpine qualification',
                                'No local VM, Twine review, ARM64 qualification, catalog or support promotion'])
    write(OUTPUT / 'summary.json', (json.dumps(summary, indent=2) + '\n').encode())
    print(json.dumps(dict(guests=len(rows), python_slots=sum(len(row['python_slots']) for row in rows), passed=True)))


if __name__ == '__main__':
    main()
