"""Exercise an installed development wheel with a private engine and controlled acquisition."""
import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def probe(source,output):
    output.mkdir(exist_ok=False)
    pin=json.loads((source/'application/wheel.json').read_bytes())
    wheel=source/'application'/pin['name']
    if wheel.stat().st_size!=pin['size'] or hashlib.sha256(wheel.read_bytes()).hexdigest()!=pin['sha256']:
        raise ValueError('Development wheel changed')
    env=dict(PATH=str(Path(sys.executable).parent),HOME=str(output),LANG='C.UTF-8',
             PIP_NO_INDEX='1',PIP_CONFIG_FILE=os.devnull,PIP_DISABLE_PIP_VERSION_CHECK='1',PYTHONNOUSERSITE='1')
    def run(argv,timeout=30):
        return subprocess.run([str(v) for v in argv],cwd=output,env=env,check=True,
                              stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
    run([sys.executable,'-I','-m','pip','install','--no-index','--no-deps',wheel],60)
    import twine_edge_overlap
    installed=Path(twine_edge_overlap.__file__).resolve()
    if not installed.is_relative_to(Path(sys.prefix).resolve()) or installed.is_relative_to(source):
        raise ValueError('Application was not imported from the private venv')
    distribution=importlib.metadata.distribution('twine-edge-overlap')
    direct=json.loads(distribution.read_text('direct_url.json'))
    if direct.get('archive_info',{}).get('hashes',{}).get('sha256')!=pin['sha256']:
        raise ValueError('pip installed a different wheel')
    for item in pin['files']:
        path=Path(distribution.locate_file(item['path'])).resolve(strict=True)
        if not path.is_relative_to(Path(sys.prefix).resolve()) or hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:
            raise ValueError('Installed application/package data differs from wheel')
    console=Path(sys.executable).parent/'desembaraca-twine'
    for command in ([console,'--help'],[sys.executable,'-I','-m','twine_edge_overlap','--help'],
                    [sys.executable,'-I','-m','twine_edge_overlap.cli','--help']):
        help_text=run(command).stdout
        if b'--prepare-runtime' not in help_text or b'--repair-runtime' not in help_text:
            raise ValueError('Installed entrypoint options missing')
    if shutil.which('dot',path=env['PATH']) or shutil.which('git',path=env['PATH']):
        raise ValueError('Restricted application PATH contains global Graphviz or Git')
    # This directory contains test helpers and public fixtures only, with no src/.
    driver=source/'application/test-driver'
    if (driver/'src').exists():raise ValueError('Application checkout must not be available to the test driver')
    report_path=output/'runtime.json'
    from twine_edge_overlap.engines.process import run_bounded
    spec=importlib.util.spec_from_file_location('network_observer',driver/'tools/runtime/observe-linux-network.py')
    observer=importlib.util.module_from_spec(spec);spec.loader.exec_module(observer)
    tracer=Path('/usr/bin/strace').resolve(strict=True)
    version=run([tracer,'--version']).stdout.decode('utf-8').splitlines()[0]
    if version!='strace -- version 4.21':raise ValueError('Unexpected tracer in pinned Ubuntu image')
    # 4.21 predates --kill-on-exit. The owned ephemeral guest is terminated by
    # the host's finally block, including after any failed observation.
    arguments=[str(tracer),'-f','-qq','-s','256','-e','trace=%network,execve','--']
    child='import socket; s=socket.socket(); s.settimeout(1); s.connect_ex(("127.0.0.1",9)); s.close()'
    control='import subprocess,sys; subprocess.run([sys.executable,"-I","-c",'+repr(child)+'],check=True)'
    control_result=run_bounded([*arguments,sys.executable,'-I','-c',control],cwd=output,env=env,timeout=15,max_output=1024**2)
    (output/'network-control.trace').write_bytes(control_result.stderr)
    detected=observer.parse_trace(control_result.stderr.decode('utf-8'))
    if (control_result.returncode or len(detected['successful_executables'])<2
            or not detected['network_syscalls'].get('socket') or not detected['network_syscalls'].get('connect')):
        raise ValueError('Native tracer did not detect the child socket/connect control')
    result=run_bounded([*arguments,sys.executable,'-I',str(driver/'tests/integration/test_linux_runtime.py'),
        '--package',source/'application/private-package',
        '--provenance',source/'application/private-package/provenance.json',
        '--report',report_path,'--environment-kind','native'],cwd=output,env=env,timeout=180,max_output=8*1024**2)
    (output/'network-corpus.trace').write_bytes(result.stderr)
    traced=observer.parse_trace(result.stderr.decode('utf-8'))
    dot_execs=sum(Path(path).name=='dot' for path in traced['successful_executables'])
    if result.returncode or traced['network_syscalls'] or not dot_execs:
        raise ValueError('Installed application failed or made native network calls')
    report=json.loads(report_path.read_bytes())
    report.update(wheel_sha256=pin['sha256'],wheel_source_revision=pin['source_revision'],
        installed_package_verified=True,installed_files_verified=len(pin['files']),entrypoints_verified=True,
        application_outside_checkout=True,global_graphviz_and_git_absent=True,
        native_network=dict(passed=True,tracer_sha256=hashlib.sha256(tracer.read_bytes()).hexdigest(),version=version,
            filter='trace=%network,execve',follow_children=True,kill_on_exit=False,
            cleanup='Owned ephemeral guest terminated by host finally; no local VM or system tracer installation',
            control=dict(network_syscalls=detected['network_syscalls'],child_executions=len(detected['successful_executables']),
                trace_sha256=hashlib.sha256(control_result.stderr).hexdigest()),
            corpus=dict(network_syscalls=traced['network_syscalls'],dot_executions=dot_execs,
                trace_sha256=hashlib.sha256(result.stderr).hexdigest()),
            limits=dict(control_seconds=15,control_output_bytes=1024**2,corpus_seconds=180,corpus_output_bytes=8*1024**2)),
        driver_output_sha256=hashlib.sha256(result.stdout+result.stderr).hexdigest(),
        scope='Installed development wheel and production runtime manager with controlled acquisition; zero observed native network syscalls with child control; no distributed-candidate or full-cell acceptance')
    report_path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();probe(args.input.resolve(strict=True),args.output.resolve())
