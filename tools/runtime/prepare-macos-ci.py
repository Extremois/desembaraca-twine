"""Prepare an explicit native Xcode SDK record; never sign or qualify a build."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('macos_source_download', HERE / 'prepare-linux-ci.py')
DOWNLOADER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DOWNLOADER)
DEVELOPER = Path('/Applications/Xcode_16.4.app/Contents/Developer')
MAX_SDK_BYTES = 4 * 1024**3


def sdk_identity(root):
    """Hash source/header/stub bytes and link destinations without copying SDK."""
    root = Path(root).resolve(strict=True)
    rows, total = [], 0
    for path in sorted(root.rglob('*')):
        if len(rows) >= 100000:
            raise ValueError('SDK inventory count exceeds budget')
        name = path.relative_to(root).as_posix()
        if path.is_symlink():
            target = os.readlink(path)
            if not path.resolve().is_relative_to(root):
                raise ValueError('SDK link escapes recorded tree')
            rows.append(dict(path=name, type='symlink', target=target))
        elif path.is_file():
            size = path.stat().st_size
            total += size
            if size > 64 * 1024**2 or total > MAX_SDK_BYTES:
                raise ValueError('SDK file bytes exceed budget')
            rows.append(dict(path=name, type='file', size=size, sha256=DOWNLOADER.digest(path)))
        elif not path.is_dir():
            raise ValueError('SDK contains a special file')
    if not rows:
        raise ValueError('SDK inventory is empty')
    canonical = json.dumps(rows, sort_keys=True, separators=(',', ':')).encode()
    return dict(sha256=hashlib.sha256(canonical).hexdigest(), bytes=total, entries=len(rows), files=rows)


def command(args):
    return subprocess.check_output(args, text=True, timeout=15,
        env=dict(os.environ, DEVELOPER_DIR=str(DEVELOPER))).strip()


def executable(path):
    # Preserve the clang++ name: its driver mode depends on argv[0].
    path = Path(path).absolute()
    if not path.is_file():
        raise ValueError('Required native tool is unavailable: ' + str(path))
    return dict(path=str(path), sha256=DOWNLOADER.digest(path))


def cmake_wrapper(cmake, sdk, bison, flex, python, make='/usr/bin/make', link_map=None):
    arguments = ['-G', 'Unix Makefiles', '-DCMAKE_MAKE_PROGRAM=' + str(make),
        '-DCMAKE_OSX_SYSROOT=' + str(sdk), '-DBISON_EXECUTABLE=' + str(bison),
        '-DFLEX_EXECUTABLE=' + str(flex), '-DPython3_EXECUTABLE=' + str(python), '-DMATH_LIB=m']
    if link_map is not None:
        arguments.append('-DCMAKE_EXE_LINKER_FLAGS=-Wl,-map,' + str(link_map))
    return ('#!' + str(python) + '\nimport os,sys\nargs=sys.argv[1:]\n'
        + f'if "-S" in args: args.extend({arguments!r})\n'
        + f'os.execv({str(cmake)!r},[{str(cmake)!r},*args])\n')


def prepare(work, arch):
    actual = {'arm64': 'aarch64', 'x86_64': 'x86_64'}.get(platform.machine())
    if platform.system() != 'Darwin' or arch != actual:
        raise ValueError('Matching native macOS architecture required')
    translated = subprocess.run(['/usr/sbin/sysctl', '-in', 'sysctl.proc_translated'],
                                capture_output=True, text=True, timeout=10)
    if translated.stdout.strip() == '1':
        raise ValueError('Translated build is not native evidence')
    version = command(['/usr/bin/xcodebuild', '-version'])
    if version != 'Xcode 16.4\nBuild version 16F6':
        raise ValueError('Expected Xcode 16.4 build 16F6')
    sdk = Path(command(['/usr/bin/xcrun', '--sdk', 'macosx', '--show-sdk-path']))
    sdk_version = command(['/usr/bin/xcrun', '--sdk', 'macosx', '--show-sdk-version'])
    if sdk_version != '15.5':
        raise ValueError('Expected macOS 15.5 SDK')
    # The workflow supplies Bison on the ephemeral runner. No brew install/update
    # or xcode-select mutation occurs in this preparer.
    prefix = Path(command(['brew', '--prefix', 'bison']))
    bison = executable(prefix / 'bin/bison')
    flex = executable(command(['/usr/bin/xcrun', '--find', 'flex']))
    make = executable(command(['/usr/bin/xcrun', '--find', 'make']))
    otool = executable(command(['/usr/bin/xcrun', '--find', 'otool']))
    cmake = executable(shutil.which('cmake') or '')
    compilers = DEVELOPER / 'Toolchains/XcodeDefault.xctoolchain/usr/bin'
    work = Path(work).resolve()
    work.mkdir(mode=0o700, parents=True, exist_ok=False)
    source = json.loads((HERE / 'source-lock.json').read_bytes())
    DOWNLOADER.download(source, work / 'graphviz.tar.gz')
    sdk_inventory = sdk_identity(sdk)
    (work / 'sdk-inventory.json').write_text(json.dumps(sdk_inventory, indent=2) + '\n', encoding='utf-8')
    wrapper = work / 'cmake-native'
    wrapper.write_text(cmake_wrapper(cmake['path'], sdk, bison['path'], flex['path'], sys.executable,
                                    make['path'], work / 'link-map.txt'), encoding='utf-8')
    wrapper.chmod(0o755)
    tools = dict(cmake=executable(wrapper), c_compiler=executable(compilers / 'clang'),
                 cxx_compiler=executable(compilers / 'clang++'))
    host_tools = dict(cmake=cmake, bison=bison, flex=flex, make=make,
                      python=executable(sys.executable), otool=otool)
    for name in ('cmake', 'bison', 'flex', 'make'):
        host_tools[name]['version'] = command([host_tools[name]['path'], '--version']).splitlines()[0]
    facts = dict(provider='Apple Xcode', xcode=version, developer_dir=str(DEVELOPER),
        link_map=str(work / 'link-map.txt'),
        sdk_path=str(sdk), sdk_version=sdk_version, sdk_settings_sha256=DOWNLOADER.digest(sdk / 'SDKSettings.json'),
        sdk_tree_sha256=sdk_inventory['sha256'], sdk_tree_entries=sdk_inventory['entries'], sdk_tree_bytes=sdk_inventory['bytes'],
        compiler_version=command([tools['c_compiler']['path'], '--version']), host_tools=host_tools,
        target_os='darwin', target_arch=arch, deployment_target='15.0', environment_kind='native',
        kernel=platform.release(), macos=platform.mac_ver()[0],
        image_os=os.environ.get('ImageOS'), image_version=os.environ.get('ImageVersion'),
        runner_arch=os.environ.get('RUNNER_ARCH'),
        limitations='SDK tree/tool hashes identify this run; dependency/license audit and qualified environment snapshot still pending')
    record = dict(**tools, facts=facts,
        environment_digest=hashlib.sha256(json.dumps(facts, sort_keys=True, separators=(',', ':')).encode()).hexdigest())
    (work / 'sdk-record.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--arch', choices=('x86_64', 'aarch64'), required=True)
    args = parser.parse_args()
    try:
        prepare(args.work, args.arch)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        parser.exit(1, type(exc).__name__ + ': ' + str(exc) + '\n')


if __name__ == '__main__':
    main()
