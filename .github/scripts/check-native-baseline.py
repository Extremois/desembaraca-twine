"""Prepare and run a pinned Ubuntu 18.04 engine baseline on GitHub's x64 KVM runner."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import urllib.parse
import zipfile

ROOT=Path(__file__).resolve().parents[2]
IMAGE_URL='https://cloud-images.ubuntu.com/releases/bionic/release-20230607/ubuntu-18.04-server-cloudimg-amd64.img'
ENGINE_SHA='43ce8d686720467c21be91cab4b8f3b246baae49c2cfe293714ebdf8a82f5716'
ENGINES={
    'glibc':dict(artifact_id='linux-glibc-x86_64',sha256=ENGINE_SHA,run_id=39434565632),
    'musl':dict(artifact_id='linux-musl-x86_64',sha256='f4dfee4e052704b1a7efdb7b6a4c43583ccaa062aec800b76224dae24eb2b69b',run_id=39434565540),
}
digest=lambda data:hashlib.sha256(data).hexdigest()


def validate_pin(pin):
    if (pin.get('url')!=IMAGE_URL or type(pin.get('size')) is not int or not 0<pin['size']<=512*1024**2
            or not re.fullmatch(r'[0-9a-f]{64}',pin.get('sha256',''))):
        raise ValueError('Invalid immutable baseline image pin')


def validate_baseline(guest,kvm):
    if (kvm.get('enabled') is not True or kvm.get('present') is not True
            or guest.get('identity',{}).get('ID')!='ubuntu' or guest['identity'].get('VERSION_ID')!='18.04'
            or guest.get('arch')!='x86_64' or not re.fullmatch(r'4\.15\.0-[0-9]+-generic',guest.get('kernel',''))
            or guest.get('glibc')!='glibc 2.27'):
        raise ValueError('Baseline requires accelerated Ubuntu 18.04 x64 with its 4.15 kernel and glibc 2.27')


def guest_output_path(folder,case,reported):
    if not re.fullmatch(r'[a-z_]+',case) or reported!=case+'.json':
        raise ValueError('Unexpected guest output path')
    path=folder/(case+'.json')
    if path.is_symlink():raise ValueError('Guest output cannot be a symlink')
    return path


def validate_engine_kind(guest,abi):
    expected=ENGINES.get(abi)
    if expected is None or guest.get('abi')!=abi or guest.get('engine_sha256')!=expected['sha256']:
        raise ValueError('Guest did not run the pinned engine for the requested ABI')
    elf=guest.get('elf',{})
    if abi=='musl':
        if elf.get('no_interpreter') is not True or elf.get('no_dynamic_section') is not True or guest.get('loader') is not None:
            raise ValueError('musl baseline requires the fully static private engine')
    elif (elf.get('no_interpreter') is not False or elf.get('no_dynamic_section') is not False
          or not guest.get('loader')):
        raise ValueError('glibc baseline requires its measured dynamic loader')


def bounded(path,limit=16*1024**2):
    with path.open('rb') as stream:raw=stream.read(limit+1)
    if len(raw)>limit:raise ValueError('Baseline input exceeds bound')
    return raw


def validate_python_report(report,pins):
    rows=report.get('interpreters',[])
    if (report.get('passed') is not True or len(rows)!=2
            or {r.get('minor') for r in rows}!={'3.12','3.14'}
            or not re.fullmatch(r'[0-9a-f]{64}',report.get('system_python_before',''))
            or report['system_python_before']!=report.get('system_python_after')):
        raise ValueError('Incomplete private Python prerequisite report or changed system Python')
    for pin in pins:
        row=next(r for r in rows if r['minor']==pin['minor']);facts=row.get('facts',{})
        if (row.get('archive_sha256')!=pin['sha256'] or facts.get('python')!=pin['patch']
                or facts.get('implementation')!='CPython' or facts.get('arch')!='x86_64' or facts.get('bits')!=64
                or facts.get('venv_active') is not True or facts.get('gil_disabled') is not False
                or facts.get('ssl_context') is not True or not facts.get('pip') or not facts.get('ensurepip')):
            raise ValueError('Private CPython/venv/pip/SSL requirements failed')


def prepare_pythons(work):
    pin_path=ROOT/'.github/native-images/private-python-x64.json'
    pins=json.loads(pin_path.read_bytes())
    for pin in pins['interpreters']:
        hasher=hashlib.sha256();received=0
        with urllib.request.urlopen(pin['url'],timeout=30) as incoming,(work/'input'/('python-'+pin['minor']+'.tar.gz')).open('xb') as output:
            origin=urllib.parse.urlsplit(incoming.geturl())
            if origin.scheme!='https' or origin.hostname not in ('github.com','release-assets.githubusercontent.com','objects.githubusercontent.com'):
                raise ValueError('Unexpected interpreter download origin')
            while True:
                chunk=incoming.read(1024**2)
                if not chunk:break
                received+=len(chunk)
                if received>pin['size']:raise ValueError('Interpreter download exceeds pin')
                hasher.update(chunk);output.write(chunk)
        if received!=pin['size'] or hasher.hexdigest()!=pin['sha256']:raise ValueError('Private interpreter archive changed')
    shutil.copyfile(pin_path,work/'input/private-python.json')
    shutil.copyfile(pin_path,work/'evidence/private-python-pins.json')
    shutil.copyfile(ROOT/'.github/scripts/probe-private-python.py',work/'input/probe-private-python.py')


def prepare(artifact,work,abi='glibc'):
    sys.path.insert(0,str(ROOT/'src'))
    from twine_edge_overlap.formats.profile import parse
    from twine_edge_overlap.engines.graphviz import build_dot
    expected=ENGINES[abi]
    work.mkdir(parents=True,exist_ok=False);source=work/'input';source.mkdir();evidence=work/'evidence';evidence.mkdir()
    candidates=list(artifact.rglob('candidate.json'))
    if len(candidates)!=1:raise ValueError('Expected exactly one candidate')
    package=candidates[0].parent;candidate_raw=bounded(candidates[0]);candidate=json.loads(candidate_raw)
    if candidate['artifact_id']!=expected['artifact_id'] or candidate['qualified'] is not False:raise ValueError('Wrong candidate')
    inventory_raw=bounded(package/'inventory.json');inventory=json.loads(inventory_raw)
    if digest(inventory_raw)!=candidate['inventory_sha256']:raise ValueError('Inventory changed')
    payload=bounded(package/'candidate.zip',128*1024**2)
    if len(payload)!=candidate['archive_bytes'] or digest(payload)!=candidate['archive_sha256']:raise ValueError('Archive changed')
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        if set(archive.namelist())!={r['path'] for r in inventory['files']}:raise ValueError('Inventory differs')
        for row in inventory['files']:
            if row['size']>16*1024**2:raise ValueError('Excessive candidate file')
            data=archive.read(row['path'])
            if len(data)!=row['size'] or digest(data)!=row['sha256']:raise ValueError('Candidate bytes changed')
        binary=archive.read('bin/dot')
    if digest(binary)!=expected['sha256']:raise ValueError('Engine changed from reviewed candidate')
    provenance=[bounded(p) for p in artifact.rglob('provenance.json')]
    provenance_raw=next(p for p in provenance if digest(p)==candidate['provenance_sha256'])
    record=json.loads(provenance_raw)
    if (record['executable_sha256']!=expected['sha256'] or record['recipe']['abi']!=abi
            or record['native_arch']!='x86_64' or record['native_os']!='linux'):
        raise ValueError('Provenance changed or describes another ABI/CPU')
    (source/'dot').write_bytes(binary);(source/'dot').chmod(0o755)
    shutil.copyfile(ROOT/'.github/scripts/probe-guest-baseline.py',source/'probe.py')
    cases=[]
    for case in json.loads((ROOT/'tests/fixtures/cases.json').read_bytes()):
        if not re.fullmatch(r'[a-z_]+',case['case']):raise ValueError('Unsafe case name')
        raw=build_dot(parse((ROOT/'tests/fixtures'/case['file']).read_bytes())).encode('ascii')
        name=case['case']+'.dot';(source/name).write_bytes(raw)
        cases.append(dict(case=case['case'],dot_file=name,dot_sha256=digest(raw),fixture=case['file']))
    (source/'inputs.json').write_text(json.dumps(dict(abi=abi,engine_sha256=expected['sha256'],cases=cases),indent=2)+'\n',encoding='utf-8')
    for name,data in [('candidate.json',candidate_raw),('provenance.json',provenance_raw),('inventory.json',inventory_raw)]:
        (evidence/name).write_bytes(data)


def execute(work):
    if os.environ.get('GITHUB_ACTIONS')!='true' or sys.platform!='linux' or platform.machine()!='x86_64' or os.geteuid()!=0:
        raise ValueError('Boot is restricted to elevated ephemeral GitHub x64 Linux runner')
    work=work.resolve(strict=True);evidence=work/'evidence'
    inputs=json.loads(bounded(work/'input/inputs.json'))
    abi=inputs['abi'];expected=ENGINES[abi]
    if inputs['engine_sha256']!=expected['sha256']:raise ValueError('Prepared ABI/engine pin changed')
    pin=json.loads((ROOT/'.github/native-images/ubuntu-18.04-amd64.json').read_bytes());validate_pin(pin)
    image=work/'base.img';hasher=hashlib.sha256();received=0
    with urllib.request.urlopen(pin['url'],timeout=30) as incoming,image.open('xb') as output:
        if incoming.geturl()!=pin['url']:raise ValueError('Image origin redirected')
        while True:
            chunk=incoming.read(1024**2)
            if not chunk:break
            received+=len(chunk)
            if received>pin['size']:raise ValueError('Excessive baseline image')
            hasher.update(chunk);output.write(chunk)
    if received!=pin['size'] or hasher.hexdigest()!=pin['sha256']:raise ValueError('Baseline image changed')
    def run(argv,**kwargs):return subprocess.run(argv,check=True,timeout=60,**kwargs)
    info=json.loads(run(['qemu-img','info','--output=json',str(image)],capture_output=True).stdout)
    if info['format']!='qcow2' or info.get('backing-filename') or info['virtual-size']>16*1024**3:raise ValueError('Unexpected image storage')
    overlay=work/'overlay.qcow2';run(['qemu-img','create','-f','qcow2','-F','qcow2','-b',str(image),str(overlay)])
    key=work/'ssh-key';run(['ssh-keygen','-q','-t','ed25519','-N','','-f',str(key)])
    public=key.with_suffix('.pub').read_text().strip()
    user_data=work/'user-data';user_data.write_text('#cloud-config\nusers:\n  - name: twine\n    shell: /bin/bash\n    lock_passwd: true\n    ssh_authorized_keys:\n      - '+public+'\nssh_pwauth: false\ndisable_root: true\npackage_update: false\npackage_upgrade: false\n',encoding='utf-8')
    metadata=work/'meta-data';metadata.write_text('instance-id: twine-engine-baseline\nlocal-hostname: twine-baseline\n')
    seed=work/'seed.img';run(['cloud-localds',str(seed),str(user_data),str(metadata)])
    qmp=work/'qmp.sock';serial=evidence/'serial.log'
    command=['qemu-system-x86_64','-accel','kvm','-cpu','host','-m','2048','-smp','2','-display','none',
        '-serial','file:'+str(serial),'-monitor','none','-qmp','unix:'+str(qmp)+',server=on,wait=off',
        '-drive','file='+str(overlay)+',format=qcow2,if=virtio',
        '-drive','file='+str(seed)+',format=raw,if=virtio,readonly=on',
        '-netdev','user,id=net0,restrict=on,hostfwd=tcp:127.0.0.1:2222-:22','-device','virtio-net-pci,netdev=net0']
    with (evidence/'qemu.log').open('wb') as log:
        process=subprocess.Popen(command,stdout=log,stderr=log)
        try:
            options=['-i',str(key),'-o','BatchMode=yes','-o','ConnectTimeout=3','-o','StrictHostKeyChecking=accept-new',
                     '-o','UserKnownHostsFile='+str(work/'known-hosts')]
            ssh=['ssh',*options,'-p','2222','twine@127.0.0.1']
            deadline=time.monotonic()+180
            while True:
                if process.poll() is not None:raise ValueError('QEMU failed; inspect qemu.log')
                ready=subprocess.run([*ssh,'test -f /var/lib/cloud/instance/boot-finished'],capture_output=True,timeout=10)
                if ready.returncode==0:break
                if time.monotonic()>=deadline:raise ValueError('Guest readiness deadline exceeded')
                time.sleep(2)
            with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as client:
                client.settimeout(10);client.connect(str(qmp))
                with client.makefile('rwb') as stream:
                    json.loads(stream.readline())
                    def query(name):
                        stream.write((json.dumps(dict(execute=name))+'\n').encode());stream.flush()
                        while True:
                            row=json.loads(stream.readline())
                            if 'return' in row:return row['return']
                            if 'error' in row:raise ValueError('QMP query failed')
                    query('qmp_capabilities');kvm=query('query-kvm')
            (evidence/'qmp-kvm.json').write_text(json.dumps(kvm,indent=2)+'\n')
            if kvm.get('enabled') is not True or kvm.get('present') is not True:raise ValueError('Hardware acceleration unavailable')
            run(['scp',*options,'-P','2222','-r',str(work/'input'),'twine@127.0.0.1:/home/twine/baseline'])
            subprocess.run([*ssh,'python3 /home/twine/baseline/probe.py --input /home/twine/baseline --output /home/twine/results'],check=True,timeout=180)
            python_report_sha=None
            if (work/'input/private-python.json').exists():
                subprocess.run([*ssh,'python3 /home/twine/baseline/probe-private-python.py --input /home/twine/baseline --output /home/twine/python-results'],check=True,timeout=360)
                run(['scp',*options,'-P','2222','twine@127.0.0.1:/home/twine/python-results/private-python-report.json',str(evidence/'private-python-report.json')])
                raw=bounded(evidence/'private-python-report.json');pins=json.loads(bounded(work/'input/private-python.json'))
                validate_python_report(json.loads(raw),pins['interpreters']);python_report_sha=digest(raw)
            run(['scp',*options,'-P','2222','-r','twine@127.0.0.1:/home/twine/results',str(evidence/'guest')])
            guest=json.loads((evidence/'guest/guest.json').read_bytes());validate_baseline(guest,kvm)
            validate_engine_kind(guest,abi)
            sys.path.insert(0,str(ROOT/'src'))
            from twine_edge_overlap.engines.graphviz import decode_layout
            from twine_edge_overlap.formats.profile import parse
            if not guest['passed'] or len(guest['cases'])!=13:raise ValueError('Incomplete guest corpus')
            for item in inputs['cases']:
                result=next(r for r in guest['cases'] if r['case']==item['case'])
                raw=bounded(guest_output_path(evidence/'guest',item['case'],result['output']),8*1024**2)
                if digest(raw)!=result['output_sha256'] or result['dot_sha256']!=item['dot_sha256']:raise ValueError('Guest result changed')
                decode_layout(raw,parse((ROOT/'tests/fixtures'/item['fixture']).read_bytes()))
            result=dict(kind='native-ubuntu1804-'+abi+'-engine-baseline',passed=True,approved=False,qualified=False,abi=abi,
                revision=os.environ.get('GITHUB_SHA'),candidate_revision='b13cd6f90db31163e62119bb83e2eb8db5ac8458',
                candidate_run_id=expected['run_id'],artifact_id=expected['artifact_id'],engine_sha256=expected['sha256'],image_pin=pin,kvm=kvm,
                guest_kernel=guest['kernel'],guest_glibc=guest['glibc'],guest_arch=guest['arch'],
                guest_report_sha256=digest((evidence/'guest/guest.json').read_bytes()),cases=13,geometry_decoded=True,
                private_python_report_sha256=python_report_sha,
                environment_kind='native',execution='same-architecture hardware-accelerated guest; no TCG fallback',
                scope=('Engine/kernel baseline only; CPython 3.12/3.14 application, Pro eligibility, full cell and Twine pending'
                       if abi=='glibc' else
                       'Static musl engine on Linux 4.15 only; guest is Ubuntu, not native Alpine; Alpine cell qualification remains pending'))
            (evidence/'summary.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        finally:
            process.terminate()
            try:process.wait(timeout=10)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=10)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',type=Path,required=True);parser.add_argument('--artifact',type=Path)
    parser.add_argument('--abi',choices=('glibc','musl'),default='glibc')
    parser.add_argument('--python-prerequisites',action='store_true')
    parser.add_argument('--execute',action='store_true');args=parser.parse_args()
    if args.execute:execute(args.work)
    elif args.artifact:
        prepare(args.artifact,args.work,args.abi)
        if args.python_prerequisites:prepare_pythons(args.work)
    else:parser.error('--artifact or --execute is required')
