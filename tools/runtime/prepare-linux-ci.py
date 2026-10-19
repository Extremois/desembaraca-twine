"""Prepare a private, pinned native Linux SDK for experimental maintainer builds.

Downloads are explicit in this CI-only entrypoint. Nothing is installed globally
and an SDK record never authorizes runtime catalog admission.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tarfile
import urllib.request

HERE = Path(__file__).resolve().parent
ZIG = dict(version='0.15.2',
           url='https://ziglang.org/download/0.15.2/zig-x86_64-linux-0.15.2.tar.xz',
           sha256='02aa270f183da276e5b5920b1dac44a63f1a49e55050ebde3aecc9eb82f93239',
           size=53733924,
           executable_sha256='2858dc89dbbfdd08cceda1b841e7fd0a793a1a67b49f150bc3d0d1de44ed7f51')
ZIG_ARM64 = dict(version='0.15.2',
    url='https://ziglang.org/download/0.15.2/zig-aarch64-linux-0.15.2.tar.xz',
    sha256='958ed7d1e00d0ea76590d27666efbf7a932281b3d7ba0c6b01b0ff26498f667f',
    size=49471996,
    executable_sha256='931b8e9a9327dac87bc439067f07604219510fa541133ff6e542c6243968cc86')


def native_sdk(arch, libc='glibc'):
    if (platform.system() != 'Linux' or arch not in ('x86_64', 'aarch64')
            or platform.machine() != arch or libc not in ('glibc','musl')):
        raise ValueError('This SDK requires the matching native Linux architecture')
    suffix='-linux.4.15-gnu.2.27' if libc=='glibc' else '-linux.4.15-musl'
    return (ZIG if arch == 'x86_64' else ZIG_ARM64), arch + suffix


def compiler_wrapper(zig, cache, arch, mode, target):
    flags = ('-march=x86-64', '-mtune=generic')
    guard = ('args=[x for x in args if x not in ' + repr(flags) + ']\n' if arch == 'x86_64' else
             'if any(x in ' + repr(flags) + ' for x in args): raise SystemExit("x86 flags forbidden in ARM64 build")\n')
    return ('#!/usr/bin/python3\nimport os,sys\n'
            f'os.environ["ZIG_GLOBAL_CACHE_DIR"]={str(cache)!r}\nargs=sys.argv[1:]\n' + guard +
            f'os.execv({str(zig)!r},["zig",{mode!r},"-target",{target!r},"-mcpu=baseline",*args])\n')


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def download(lock, destination):
    """Bound transfer size and authenticate every byte before any extraction."""
    destination = Path(destination)
    try:
        request = urllib.request.Request(lock['url'], headers={'User-Agent': 'desembaraca-maintainer-ci'})
        with urllib.request.urlopen(request, timeout=30) as response, destination.open('xb') as output:
            total = 0
            while chunk := response.read(65536):
                total += len(chunk)
                if total > lock['size']:
                    raise ValueError('Pinned download exceeded expected size')
                output.write(chunk)
        if total != lock['size'] or digest(destination) != lock['sha256']:
            raise ValueError('Pinned download size/hash mismatch')
    except BaseException:
        # Only remove the file created by this call; preserve preexisting files.
        if 'output' in locals():
            destination.unlink(missing_ok=True)
        raise


def executable(path):
    path = Path(path).resolve(strict=True)
    return dict(path=str(path), sha256=digest(path))


def prepare(work, arch=None, libc='glibc', environment_kind='native'):
    arch = platform.machine() if arch is None else arch
    compiler_lock, target = native_sdk(arch,libc)
    if environment_kind not in ('native','container'):raise ValueError('Unsupported build environment kind')
    work = Path(work).resolve()
    work.mkdir(mode=0o700, parents=True, exist_ok=False)
    source = json.loads((HERE / 'source-lock.json').read_text(encoding='utf-8'))
    download(source, work / 'graphviz.tar.gz')
    archive = work / 'zig.tar.xz'
    download(compiler_lock, archive)
    with tarfile.open(archive) as incoming:
        members = incoming.getmembers()
        if len(members) > 100000 or sum(m.size for m in members) > 2 * 1024**3:
            raise ValueError('SDK expansion exceeded budget')
        incoming.extractall(work / 'sdk', filter='data')
    zig = work / ('sdk/zig-' + arch + '-linux-0.15.2/zig')
    if digest(zig) != compiler_lock['executable_sha256']:
        raise ValueError('Pinned compiler executable hash mismatch')
    cmake = Path(shutil.which('cmake') or '').resolve(strict=True)
    tools = {}
    for key, mode in (('c_compiler', 'cc'), ('cxx_compiler', 'c++')):
        path = work / key
        path.write_text(compiler_wrapper(zig, work / 'cache', arch, mode, target), encoding='utf-8')
        path.chmod(0o755)
        tools[key] = executable(path)
    wrapper = work / 'cmake-math'
    wrapper.write_text('#!/usr/bin/python3\nimport os,sys\nargs=sys.argv[1:]\n'
                       'if "-S" in args: args.append("-DMATH_LIB=m")\n'
                       f'os.execv({str(cmake)!r},[{str(cmake)!r},*args])\n', encoding='utf-8')
    wrapper.chmod(0o755)
    tools['cmake'] = executable(wrapper)
    tools['elf_inspector'] = executable(shutil.which('readelf') or '/usr/bin/readelf')
    host_tools = {}
    for name in ('cmake', 'make', 'bison', 'flex'):
        path = shutil.which(name)
        if not path:
            raise ValueError('Missing runner build dependency: ' + name)
        host_tools[name] = dict(**executable(path), version=subprocess.check_output(
            [path, '--version'], text=True, timeout=10).splitlines()[0])
    facts = dict(provider='Zig', archive=compiler_lock, zig_sha256=digest(zig), target=target, environment_kind=environment_kind,
                 kernel=platform.release(), host=platform.platform(), tools=tools,
                 host_tools=host_tools, image_os=os.environ.get('ImageOS'),
                 image_version=os.environ.get('ImageVersion'), runner_arch=os.environ.get('RUNNER_ARCH'),
                 compiler=executable(zig),
                 target_arch=arch,
                 target_os='linux',target_libc_family=libc,static_linking=libc=='musl',
                 container_image=os.environ.get('TWINE_BUILD_CONTAINER_IMAGE') if environment_kind=='container' else None,
                 flag_translation=('Only -march=x86-64 and -mtune=generic become -mcpu=baseline'
                                   if arch == 'x86_64' else 'No x86 flag translation; ARM64 baseline CPU'),
                 math_library='MATH_LIB=m; no absolute host libm',
                 qualification='experimental SDK; compiler target is not oldest kernel/CPU qualification')
    record = dict(**tools, facts=facts, environment_digest=hashlib.sha256(
        json.dumps(facts, sort_keys=True, separators=(',', ':')).encode()).hexdigest())
    (work / 'sdk-record.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--arch', choices=('x86_64', 'aarch64'))
    parser.add_argument('--libc',choices=('glibc','musl'),default='glibc')
    parser.add_argument('--environment-kind',choices=('native','container'),default='native')
    args = parser.parse_args()
    prepare(args.work, args.arch,args.libc,args.environment_kind)
