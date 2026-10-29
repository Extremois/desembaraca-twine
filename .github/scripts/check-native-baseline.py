"""Prepare and run pinned Linux engine baselines on GitHub's x64 KVM runner."""
import argparse
import hashlib
import io
import importlib.util
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
CANDIDATE_REVISION='b13cd6f90db31163e62119bb83e2eb8db5ac8458'
IMAGE_PROFILES={
    'fedora-43':dict(url='https://dl.fedoraproject.org/pub/fedora/linux/releases/43/Cloud/x86_64/images/Fedora-Cloud-Base-Generic-43-1.6.x86_64.qcow2',
                 distribution='fedora',version='43',maximum_bytes=1024**3,
                 kernel=r'[0-9]+\.[0-9]+\.[0-9]+-[0-9]+\.fc43\.x86_64',glibc='glibc 2.42',disk_bytes=8*1024**3),
    'fedora-44':dict(url='https://dl.fedoraproject.org/pub/fedora/linux/releases/44/Cloud/x86_64/images/Fedora-Cloud-Base-Generic-44-1.7.x86_64.qcow2',
                 distribution='fedora',version='44',maximum_bytes=1024**3,
                 kernel=r'[0-9]+\.[0-9]+\.[0-9]+-[0-9]+\.fc44\.x86_64',glibc='glibc 2.43',disk_bytes=8*1024**3),
    'debian-12':dict(url='https://laotzu.ftp.acc.umu.se/images/cloud/bookworm/20261026-2643/debian-12-generic-amd64-20261026-2643.qcow2',
                 distribution='debian',version='12',image_hash='sha512',maximum_bytes=1024**3,
                 kernel=r'6\.1\.0-[0-9]+-amd64',glibc='glibc 2.36',disk_bytes=8*1024**3),
    'debian-13':dict(url='https://chuangtzu.ftp.acc.umu.se/images/cloud/trixie/20261026-2643/debian-13-generic-amd64-20261026-2643.qcow2',
                 distribution='debian',version='13',image_hash='sha512',maximum_bytes=1024**3,
                 kernel=r'6\.12\.[0-9]+\+deb13-amd64',glibc='glibc 2.41',disk_bytes=8*1024**3),
    '18.04':dict(url=IMAGE_URL,maximum_bytes=512*1024**2,kernel=r'4\.15\.0-[0-9]+-generic',glibc='glibc 2.27'),
    '20.04':dict(url='https://cloud-images.ubuntu.com/releases/focal/release-20250516/ubuntu-20.04-server-cloudimg-amd64.img',
                 maximum_bytes=1024**3,kernel=r'5\.4\.0-[0-9]+-generic',glibc='glibc 2.31',disk_bytes=8*1024**3),
    '22.04':dict(url='https://cloud-images.ubuntu.com/releases/jammy/release-20261020/ubuntu-22.04-server-cloudimg-amd64.img',
                 maximum_bytes=1024**3,kernel=r'5\.15\.0-[0-9]+-generic',glibc='glibc 2.35',disk_bytes=8*1024**3),
    '24.04':dict(url='https://cloud-images.ubuntu.com/releases/noble/release-20261017/ubuntu-24.04-server-cloudimg-amd64.img',
                 maximum_bytes=1024**3,kernel=r'6\.8\.0-[0-9]+-generic',glibc='glibc 2.39',disk_bytes=8*1024**3),
    '26.04':dict(url='https://cloud-images.ubuntu.com/releases/resolute/release-20261016/ubuntu-26.04-server-cloudimg-amd64.img',
                 maximum_bytes=1024**3,kernel=r'7\.0\.0-[0-9]+-generic',glibc='glibc 2.43',disk_bytes=8*1024**3),
    '26.10':dict(url='https://cloud-images.ubuntu.com/releases/stonking/release-20261025/ubuntu-26.10-server-cloudimg-amd64.img',
                 maximum_bytes=1024**3,kernel=r'7\.3\.0-[0-9]+-generic',glibc='glibc 2.44',disk_bytes=8*1024**3),
}
ENGINE_SHA='43ce8d686720467c21be91cab4b8f3b246baae49c2cfe293714ebdf8a82f5716'
ENGINES={
    'glibc':dict(artifact_id='linux-glibc-x86_64',sha256=ENGINE_SHA,run_id=39434565632),
    'musl':dict(artifact_id='linux-musl-x86_64',sha256='f4dfee4e052704b1a7efdb7b6a4c43583ccaa062aec800b76224dae24eb2b69b',run_id=39434565540),
}
digest=lambda data:hashlib.sha256(data).hexdigest()


def baseline_profile(release):
    if release not in IMAGE_PROFILES:raise ValueError('Unsupported native baseline release')
    return IMAGE_PROFILES[release]


def validate_candidate_source(revision,run_id):
    if (not isinstance(revision,str) or not re.fullmatch(r'[0-9a-f]{40}',revision)
            or type(run_id) is not int or run_id<=0):
        raise ValueError('Candidate requires a full revision and positive Actions run ID')


def validate_pin(pin,release='18.04'):
    profile=baseline_profile(release)
    algorithm=profile.get('image_hash','sha256')
    if (pin.get('url')!=profile['url'] or type(pin.get('size')) is not int or not 0<pin['size']<=profile['maximum_bytes']
            or pin.get('release',release)!=profile.get('version',release) or pin.get('arch','x86_64')!='x86_64'
            or pin.get('distribution','ubuntu')!=profile.get('distribution','ubuntu')
            or not re.fullmatch(r'[0-9a-f]{'+str(hashlib.new(algorithm).digest_size*2)+'}',pin.get(algorithm,''))):
        raise ValueError('Invalid immutable baseline image pin')


def validate_baseline(guest,kvm,release='18.04'):
    profile=baseline_profile(release)
    if (kvm.get('enabled') is not True or kvm.get('present') is not True
            or guest.get('identity',{}).get('ID')!=profile.get('distribution','ubuntu')
            or guest['identity'].get('VERSION_ID')!=profile.get('version',release)
            or guest.get('arch')!='x86_64' or not re.fullmatch(profile['kernel'],guest.get('kernel',''))
            or guest.get('glibc')!=profile['glibc']
            or (profile.get('distribution')=='debian' and not re.fullmatch(profile['version']+r'\.[0-9]+',guest.get('distribution_patch','')))):
        raise ValueError('Baseline requires accelerated '+profile.get('distribution','ubuntu')+' '+release+' x64 with its pinned kernel/libc family')
    if profile.get('distribution')=='fedora':
        rows=guest.get('distribution_packages',[])
        packages={row['name']:row for row in rows}
        if len(rows)!=3 or set(packages)!={'kernel-core','glibc','fedora-release-common'}:
            raise ValueError('Incomplete Fedora RPM identity')
        kernel=packages['kernel-core'];libc=packages['glibc'];system=packages['fedora-release-common']
        if (kernel['version']+'-'+kernel['release']+'.'+kernel['arch']!=guest['kernel']
                or libc['arch']!='x86_64' or 'glibc '+libc['version']!=profile['glibc']
                or system['version']!=profile['version'] or system['arch']!='noarch'
                or guest.get('security',{}).get('selinux')!='enforcing'):
            raise ValueError('Fedora requires matching installed kernel/libc/release and enforcing SELinux')


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


def validate_application_report(report,patch,wheel_sha,engine_sha,cases):
    rows=report.get('cases',[])
    if (report.get('passed') is not True or report.get('qualified') is not False
            or report.get('python')!=patch or report.get('arch')!='x86_64'
            or report.get('wheel_sha256')!=wheel_sha or report.get('engine_sha256')!=engine_sha
            or report.get('installed_package_verified') is not True or report.get('entrypoints_verified') is not True
            or len(rows)!=13 or {r.get('case') for r in rows}!={r['case'] for r in cases}):
        raise ValueError('Incomplete installed application or corpus evidence')
    for mode in ('automatic','explicit'):
        observed=report.get('observations',{}).get(mode,{})
        if (observed.get('acquisition_calls')!=1 or observed.get('offline_acquisition_calls')!=0
                or observed.get('executable_mode')!=0o755 or observed.get('generation_mode')!=0o700
                or any(observed.get(key) is not True for key in ('healthy_generation_reused','final_destination_probe',
                    'probe_before_ready','external_unicode_paths','real_engine','fixture_transport'))):
            raise ValueError('Preparation/cache/runtime observation failed')
    for item in cases:
        row=next(r for r in rows if r['case']==item['case'])
        before,after=row.get('before',[]),row.get('after',[])
        if (len(before)!=3 or len(after)!=3 or any(a>b for a,b in zip(after,before))
                or (item['known_resolvable'] and after!=[0,0,0])):
            raise ValueError('Corpus regressed or known reference did not finish clean')


def validate_private_tracer(report,receipt):
    observed=report.get('native_network',{})
    tracer=next(row for row in receipt['files'] if row['name']=='strace')
    if (observed.get('private_tracer')!=receipt or observed.get('tracer_sha256')!=tracer['sha256']
            or observed.get('version')!='strace -- version '+receipt['version']):
        raise ValueError('Private tracer provenance or observed version differs')


def validate_network_observation(control,corpus):
    if (len(control.get('successful_executables',[]))<2
            or not control.get('network_syscalls',{}).get('socket')
            or not control.get('network_syscalls',{}).get('connect')
            or corpus.get('network_syscalls')!={}
            or not any(Path(path).name=='dot' for path in corpus.get('successful_executables',[]))):
        raise ValueError('Native tracing missed the child control or observed corpus network calls')


def validate_recovery_report(report):
    names={'download','disk_full','execution_denied','corrupt_archive','during_download','before_select','after_select','concurrent_first_use'}
    rows=report.get('scenarios',{})
    if report.get('passed') is not True or report.get('real_engine') is not True or set(rows)!=names:
        raise ValueError('Incomplete private installed-engine recovery evidence')
    for name,row in rows.items():
        if row.get('passed') is not True or row.get('offline_references')!=6 or row.get('old_handle_usable') is not True:
            raise ValueError('Recovery did not preserve offline processing or old handle')
        if name in ('during_download','before_select','after_select') and (row.get('exitcode')!=77 or row.get('lock_reacquired') is not True):
            raise ValueError('Crash/lock recovery failed')
    concurrent=rows['concurrent_first_use']
    if concurrent.get('acquisition_calls')!=1 or concurrent.get('same_generation') is not True:
        raise ValueError('Concurrent first use did not share one generation/acquisition')


def prepare_application(artifact,work):
    folder=work/'input/application';folder.mkdir()
    subprocess.run([sys.executable,'-m','pip','wheel','--no-deps','--wheel-dir',str(folder),str(ROOT)],check=True,timeout=180)
    wheels=list(folder.glob('*.whl'))
    if len(wheels)!=1:raise ValueError('Expected exactly one development wheel')
    wheel=wheels[0];payload=bounded(wheel,128*1024**2);files=[]
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        for item in archive.infolist():
            if item.filename.startswith('twine_edge_overlap/') and not item.is_dir():
                files.append(dict(path=item.filename,sha256=digest(archive.read(item))))
    pin=dict(name=wheel.name,sha256=digest(payload),size=len(payload),source_revision=os.environ.get('GITHUB_SHA'),files=files)
    raw=(json.dumps(pin,indent=2)+'\n').encode()
    (folder/'wheel.json').write_bytes(raw);(work/'evidence/application-wheel.json').write_bytes(raw)
    package=next(artifact.rglob('candidate.json')).parent;private=folder/'private-package';private.mkdir()
    for name in ('candidate.json','candidate.zip','inventory.json'):shutil.copyfile(package/name,private/name)
    shutil.copyfile(work/'evidence/provenance.json',private/'provenance.json')
    driver=folder/'test-driver/tests';(driver/'integration').mkdir(parents=True)
    for name in ('common.py','runtime_support.py','native_acceptance.py','integration/test_linux_runtime.py'):
        shutil.copyfile(ROOT/'tests'/name,driver/name)
    shutil.copytree(ROOT/'tests/fixtures',driver/'fixtures',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    observer=folder/'test-driver/tools/runtime';observer.mkdir(parents=True)
    shutil.copyfile(ROOT/'tools/runtime/observe-linux-network.py',observer/'observe-linux-network.py')
    shutil.copyfile(ROOT/'.github/scripts/probe-installed-application.py',folder/'probe.py')
    shutil.copyfile(ROOT/'.github/scripts/probe-installed-recovery.py',folder/'recovery.py')
    processes=folder/'test-driver/.github/scripts'
    processes.mkdir(parents=True)
    shutil.copyfile(ROOT/'.github/scripts/probe-installed-recovery.py',processes/'probe-installed-recovery.py')


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


def prepare(artifact,work,abi='glibc',release='18.04',candidate_revision=CANDIDATE_REVISION,candidate_run_id=None):
    baseline_profile(release)
    sys.path.insert(0,str(ROOT/'src'))
    from twine_edge_overlap.formats.profile import parse
    from twine_edge_overlap.engines.graphviz import build_dot
    expected=ENGINES[abi]
    if candidate_run_id is None:candidate_run_id=expected['run_id']
    validate_candidate_source(candidate_revision,candidate_run_id)
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
    (source/'inputs.json').write_text(json.dumps(dict(abi=abi,engine_sha256=expected['sha256'],cases=cases,
        guest_release=release,candidate_revision=candidate_revision,candidate_run_id=candidate_run_id),indent=2)+'\n',encoding='utf-8')
    for name,data in [('candidate.json',candidate_raw),('provenance.json',provenance_raw),('inventory.json',inventory_raw)]:
        (evidence/name).write_bytes(data)


def execute(work,release='18.04'):
    if os.environ.get('GITHUB_ACTIONS')!='true' or sys.platform!='linux' or platform.machine()!='x86_64' or os.geteuid()!=0:
        raise ValueError('Boot is restricted to elevated ephemeral GitHub x64 Linux runner')
    work=work.resolve(strict=True);evidence=work/'evidence'
    inputs=json.loads(bounded(work/'input/inputs.json'))
    abi=inputs['abi'];expected=ENGINES[abi]
    profile=baseline_profile(release)
    if inputs.get('guest_release','18.04')!=release:raise ValueError('Prepared guest release differs from execution request')
    candidate_revision=inputs.get('candidate_revision',CANDIDATE_REVISION)
    candidate_run_id=inputs.get('candidate_run_id',expected['run_id'])
    validate_candidate_source(candidate_revision,candidate_run_id)
    if inputs['engine_sha256']!=expected['sha256']:raise ValueError('Prepared ABI/engine pin changed')
    pin_name=(release if profile.get('distribution','ubuntu')!='ubuntu' else 'ubuntu-'+release)+'-amd64.json'
    pin=json.loads((ROOT/'.github/native-images'/pin_name).read_bytes());validate_pin(pin,release)
    algorithm=profile.get('image_hash','sha256')
    image=work/'base.img';hasher=hashlib.new(algorithm);received=0
    with urllib.request.urlopen(pin['url'],timeout=30) as incoming,image.open('xb') as output:
        if incoming.geturl()!=pin['url']:raise ValueError('Image origin redirected')
        while True:
            chunk=incoming.read(1024**2)
            if not chunk:break
            received+=len(chunk)
            if received>pin['size']:raise ValueError('Excessive baseline image')
            hasher.update(chunk);output.write(chunk)
    if received!=pin['size'] or hasher.hexdigest()!=pin[algorithm]:raise ValueError('Baseline image changed')
    def run(argv,**kwargs):return subprocess.run(argv,check=True,timeout=60,**kwargs)
    info=json.loads(run(['qemu-img','info','--output=json',str(image)],capture_output=True).stdout)
    if info['format']!='qcow2' or info.get('backing-filename') or info['virtual-size']>16*1024**3:raise ValueError('Unexpected image storage')
    overlay=work/'overlay.qcow2';run(['qemu-img','create','-f','qcow2','-F','qcow2','-b',str(image),str(overlay)])
    if 'disk_bytes' in profile:
        if info['virtual-size']>profile['disk_bytes']:raise ValueError('Image exceeds the guest disk budget')
        run(['qemu-img','resize',str(overlay),str(profile['disk_bytes'])])
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
            python_report_sha=None;application_reports=[]
            if (work/'input/private-python.json').exists():
                subprocess.run([*ssh,'python3 /home/twine/baseline/probe-private-python.py --input /home/twine/baseline --output /home/twine/python-results'],check=True,timeout=360)
                run(['scp',*options,'-P','2222','twine@127.0.0.1:/home/twine/python-results/private-python-report.json',str(evidence/'private-python-report.json')])
                raw=bounded(evidence/'private-python-report.json');pins=json.loads(bounded(work/'input/private-python.json'))
                validate_python_report(json.loads(raw),pins['interpreters']);python_report_sha=digest(raw)
                if (work/'input/application/wheel.json').exists():
                    application=evidence/'application';application.mkdir()
                    wheel_pin=json.loads(bounded(work/'input/application/wheel.json'))
                    cases=json.loads((ROOT/'tests/fixtures/cases.json').read_bytes())
                    for pin_python in pins['interpreters']:
                        name='application-'+pin_python['minor']+'.json'
                        run(['scp',*options,'-P','2222','twine@127.0.0.1:/home/twine/python-results/'+name,str(application/name)])
                        report=json.loads(bounded(application/name))
                        validate_application_report(report,pin_python['patch'],wheel_pin['sha256'],expected['sha256'],cases)
                        validate_recovery_report(report.get('recovery',{}))
                        if (work/'input/tracer.json').exists():
                            validate_private_tracer(report,json.loads(bounded(work/'input/tracer.json')))
                        spec=importlib.util.spec_from_file_location('network_observer',ROOT/'tools/runtime/observe-linux-network.py')
                        observer=importlib.util.module_from_spec(spec);spec.loader.exec_module(observer)
                        traces={}
                        for kind in ('control','corpus'):
                            trace_name='application-'+pin_python['minor']+'.'+kind+'.trace'
                            run(['scp',*options,'-P','2222','twine@127.0.0.1:/home/twine/python-results/'+trace_name,str(application/trace_name)])
                            trace=bounded(application/trace_name,8*1024**2)
                            if digest(trace)!=report['native_network'][kind]['trace_sha256']:raise ValueError('Native trace changed')
                            traces[kind]=observer.parse_trace(trace.decode('utf-8'))
                        validate_network_observation(traces['control'],traces['corpus'])
                        if (report.get('wheel_source_revision')!=os.environ.get('GITHUB_SHA')
                                or report.get('application_outside_checkout') is not True
                                or report.get('global_graphviz_and_git_absent') is not True):
                            raise ValueError('Installed application revision/isolation differs from prepared wheel')
                        application_reports.append(dict(python=pin_python['patch'],report=name,
                            sha256=digest(bounded(application/name)),wheel_sha256=wheel_pin['sha256']))
            run(['scp',*options,'-P','2222','-r','twine@127.0.0.1:/home/twine/results',str(evidence/'guest')])
            guest=json.loads((evidence/'guest/guest.json').read_bytes());validate_baseline(guest,kvm,release)
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
            result=dict(kind='native-'+profile.get('distribution','ubuntu')+profile.get('version',release).replace('.','')+'-'+abi+'-engine-baseline',passed=True,approved=False,qualified=False,abi=abi,
                revision=os.environ.get('GITHUB_SHA'),candidate_revision=candidate_revision,
                candidate_run_id=candidate_run_id,artifact_id=expected['artifact_id'],engine_sha256=expected['sha256'],image_pin=pin,kvm=kvm,
                guest_kernel=guest['kernel'],guest_glibc=guest['glibc'],guest_arch=guest['arch'],
                guest_report_sha256=digest((evidence/'guest/guest.json').read_bytes()),cases=13,geometry_decoded=True,
                private_python_report_sha256=python_report_sha,
                installed_application_reports=application_reports,
                environment_kind='native',execution='same-architecture hardware-accelerated guest; no TCG fallback',
                scope=('Private engine/kernel/Python/application observations only; controlled acquisition; distributed candidate, maintenance eligibility, full cell and Twine pending'
                       if abi=='glibc' else
                       'Static musl engine on '+profile.get('distribution','ubuntu')+' '+release+' kernel only; guest is not native Alpine; Alpine cell qualification remains pending'))
            (evidence/'summary.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        finally:
            process.terminate()
            try:process.wait(timeout=10)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=10)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',type=Path,required=True);parser.add_argument('--artifact',type=Path)
    parser.add_argument('--abi',choices=('glibc','musl'),default='glibc')
    parser.add_argument('--release',choices=tuple(IMAGE_PROFILES),default='18.04')
    parser.add_argument('--candidate-revision',default=CANDIDATE_REVISION)
    parser.add_argument('--candidate-run-id',type=int)
    parser.add_argument('--python-prerequisites',action='store_true')
    parser.add_argument('--python-application',action='store_true')
    parser.add_argument('--execute',action='store_true');args=parser.parse_args()
    if args.execute:execute(args.work,args.release)
    elif args.artifact:
        prepare(args.artifact,args.work,args.abi,args.release,args.candidate_revision,args.candidate_run_id)
        if args.python_prerequisites:prepare_pythons(args.work)
        if args.python_application:
            if not args.python_prerequisites:parser.error('--python-application requires --python-prerequisites')
            prepare_application(args.artifact,args.work)
            if baseline_profile(args.release).get('distribution') in ('debian','fedora'):
                spec=importlib.util.spec_from_file_location('private_tracer',ROOT/'.github/scripts/private-tracer.py')
                tracer=importlib.util.module_from_spec(spec);spec.loader.exec_module(tracer);tracer.prepare(args.work)
    else:parser.error('--artifact or --execute is required')
