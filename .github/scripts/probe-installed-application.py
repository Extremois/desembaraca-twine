"""Exercise an installed development wheel with a private engine and controlled acquisition."""
import argparse
import hashlib
import importlib.metadata
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
    result=run([sys.executable,'-I',driver/'tests/integration/test_linux_runtime.py',
        '--package',source/'application/private-package',
        '--provenance',source/'application/private-package/provenance.json',
        '--report',report_path,'--environment-kind','native'],180)
    report=json.loads(report_path.read_bytes())
    report.update(wheel_sha256=pin['sha256'],wheel_source_revision=pin['source_revision'],
        installed_package_verified=True,installed_files_verified=len(pin['files']),entrypoints_verified=True,
        application_outside_checkout=True,global_graphviz_and_git_absent=True,
        driver_output_sha256=hashlib.sha256(result.stdout+result.stderr).hexdigest(),
        scope='Installed development wheel and production runtime manager with controlled acquisition; Python socket guard only; no distributed-candidate, native network trace or full-cell acceptance')
    report_path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();probe(args.input.resolve(strict=True),args.output.resolve())
