"""Trace the public Linux candidate corpus and descendants; no catalog admission.

strace's %network class includes unsuccessful and local socket operations. The
gate requires zero such syscalls, not merely zero successful remote connects.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from twine_edge_overlap.engines.process import run_bounded


def parse_trace(text):
    if len(text.encode('utf-8')) > 8 * 1024**2:
        raise ValueError('Trace exceeds evidence bound')
    calls = Counter()
    executions = []
    pending = {}
    for raw in text.splitlines():
        prefix = re.match(r'^(?:\[pid\s+(\d+)\]|(\d+))\s+', raw)
        pid = (prefix.group(1) or prefix.group(2)) if prefix else 'root'
        line = raw[prefix.end():] if prefix else raw
        if re.fullmatch(r'--- SIGCHLD \{.*\} ---', line):
            continue
        resumed = re.match(r'^<\.\.\. (\w+) resumed>', line)
        call = re.match(r'^(\w+)\(', line)
        if not call and not resumed:
            raise ValueError('Unrecognized or incomplete trace output')
        name = (call or resumed).group(1)
        if name == 'execve':
            if call:
                match = re.match(r'^execve\("([^"\n]+)"', line)
                if not match:
                    raise ValueError('Cannot identify traced executable')
                path = match.group(1)
                if '<unfinished ...>' in line:
                    if pid in pending:
                        raise ValueError('Overlapping exec trace')
                    pending[pid] = path
                    continue
            else:
                if pid not in pending:
                    raise ValueError('Exec resume without matching start')
                path = pending.pop(pid)
            if re.search(r'= 0$', line):
                executions.append(path)
            elif not re.search(r'= -1 \w+', line):
                raise ValueError('Exec result missing from trace')
        elif call:
            # The command filters everything except execve and %network. Treat
            # every other syscall conservatively as a network operation.
            calls[name] += 1
    if pending or not executions:
        raise ValueError('Missing complete successful execution trace')
    return dict(network_syscalls=dict(calls), successful_executables=executions)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def observe(build, report_path, corpus_path, environment_kind, private_package=None):
    if platform.system() != 'Linux':
        raise ValueError('Native syscall observation requires Linux')
    tracer = Path(shutil.which('strace') or '/usr/bin/strace').resolve(strict=True)
    report_path, corpus_path = Path(report_path), Path(corpus_path)
    control_path = report_path.with_suffix('.control.trace')
    trace_path = report_path.with_suffix('.corpus.trace')
    for path in (report_path, corpus_path, control_path, trace_path):
        if path.exists():
            raise ValueError('Observation output must be new: ' + str(path))
    version = run_bounded([str(tracer), '--version'], timeout=10, max_output=65536)
    if version.returncode:
        raise ValueError('Cannot identify tracer')
    arguments = [str(tracer), '-f', '-qq', '--kill-on-exit', '-s', '256',
                 '-e', 'trace=%network,execve', '--']
    child = ('import socket; s=socket.socket(); '
             's.settimeout(1); s.connect_ex(("127.0.0.1",9)); s.close()')
    control = ('import subprocess,sys; subprocess.run([sys.executable,"-c",' +
               repr(child) + '],check=True)')
    result = run_bounded([*arguments, sys.executable, '-c', control], timeout=15, max_output=1024**2)
    with control_path.open('xb') as stream:
        stream.write(result.stderr)
    detected = parse_trace(result.stderr.decode('utf-8', errors='strict'))
    if (result.returncode or len(detected['successful_executables']) < 2
            or not detected['network_syscalls'].get('socket')
            or not detected['network_syscalls'].get('connect')):
        raise ValueError('Tracer failed to detect the child-process network control')
    if private_package is None:
        command=[sys.executable,str(ROOT/'tools/runtime/smoke-corpus.py'),'--build-output',str(build)]
    else:
        command=[sys.executable,str(ROOT/'tests/integration/test_linux_runtime.py'),
                 '--package',str(private_package),'--provenance',str(Path(build)/'provenance.json')]
    result = run_bounded([*arguments,*command,'--environment-kind',environment_kind,
                          '--report',str(corpus_path)],timeout=180,max_output=8*1024**2)
    with trace_path.open('xb') as stream:
        stream.write(result.stderr)
    traced = parse_trace(result.stderr.decode('utf-8', errors='strict'))
    dot_execs = sum(Path(path).name == 'dot' for path in traced['successful_executables'])
    corpus_bytes = corpus_path.read_bytes() if corpus_path.is_file() else b''
    corpus = json.loads(corpus_bytes) if corpus_bytes else {}
    passed = (result.returncode == 0 and not traced['network_syscalls'] and dot_execs > 0
              and corpus.get('passed') is True and len(corpus.get('cases', [])) == 13)
    report = dict(kind='linux-native-syscall-observation', passed=passed, qualified=False,
                  environment_kind=environment_kind, python=platform.python_version(),
                  kernel=platform.release(), arch=platform.machine(),
                  tracer=dict(path=str(tracer), sha256=sha(tracer.read_bytes()),
                              version=version.stdout.decode().splitlines()[0],
                              filter='trace=%network,execve', follow_children=True, kill_on_exit=True),
                  control=dict(detected=True, child_executions=len(detected['successful_executables']),
                               network_syscalls=detected['network_syscalls'], trace_sha256=sha(control_path.read_bytes())),
                  corpus=dict(engine_sha256=corpus.get('engine_sha256'), cases=len(corpus.get('cases', [])),
                              report_sha256=sha(corpus_bytes), dot_executions=dot_execs,
                              network_syscalls=traced['network_syscalls'], trace_sha256=sha(result.stderr)),
                  limits=dict(corpus_seconds=180, corpus_output_bytes=8*1024**2,
                              control_seconds=15, control_output_bytes=1024**2),
                  scope=('Real native engine and runtime manager with controlled acquisition fixture; not distributed-candidate or full-cell acceptance'
                         if private_package is not None else
                         'Public local-build corpus and relocation only; not installed-package acquisition, recovery, full cell or hostile-code sandbox'))
    with report_path.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    if not passed:
        raise ValueError('Corpus failed or native socket/network activity was observed')
    print('Corpus passed with zero observed native network syscalls; child control detected.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-output', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--corpus-report', type=Path, required=True)
    parser.add_argument('--environment-kind', choices=('github-actions','native', 'wsl', 'container', 'emulated'), required=True)
    parser.add_argument('--private-package',type=Path,help='Exercise production runtime manager using this private package and controlled transfer fixture')
    args = parser.parse_args()
    observe(args.build_output,args.report,args.corpus_report,args.environment_kind,args.private_package)
