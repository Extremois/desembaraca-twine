"""Offline maintainer build: pinned source, explicit SDK, no global install.

The default operation emits a build plan. --execute requires a native host and
a reviewed SDK record; outputs are candidates, never active runtime metadata.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE_SPEC = importlib.util.spec_from_file_location('graphviz_source_inputs', HERE / 'graphviz-source.py')
source_inputs = importlib.util.module_from_spec(SOURCE_SPEC)
SOURCE_SPEC.loader.exec_module(source_inputs)
sys.path.insert(0, str(ROOT / 'src'))
from twine_edge_overlap.runtime_platform import detect_host
from twine_edge_overlap.engines.process import ProcessLimitError, run_bounded


def digest(path, *, maximum=None):
    value = hashlib.sha256()
    total=0
    with Path(path).open('rb') as stream:
        while chunk := stream.read(65536):
            total+=len(chunk)
            if maximum is not None and total>maximum:raise ValueError('Link input exceeded its bound')
            value.update(chunk)
    return value.hexdigest()


def parse_link_dependencies(text):
    """Read the generated GNU ld first rule as data, never as make/shell code."""
    if len(text.encode('utf-8'))>8*1024**2:raise ValueError('Link dependency metadata too large')
    line=text.replace('\r\n','\n').replace('\\\n',' ').split('\n',1)[0]
    if not line.startswith('dot:'):raise ValueError('Expected the dot linker dependency rule')
    text=line[4:]
    names=[]
    token=[]
    index=0
    while index<len(text):
        char=text[index]
        if char=='\\':
            index+=1
            if index>=len(text) or text[index] not in ' \t#\\:':raise ValueError('Unsupported dependency escape')
            token.append(text[index])
        elif char=='$':
            index+=1
            if index>=len(text) or text[index]!='$':raise ValueError('Make expansion is not accepted')
            token.append('$')
        elif char.isspace():
            if token:names.append(''.join(token));token=[]
        elif char=='#' or ord(char)<32:
            raise ValueError('Unsupported dependency syntax')
        else:token.append(char)
        index+=1
    if token:names.append(''.join(token))
    if not names or len(names)>10000:raise ValueError('Link dependency count exceeds limit or is empty')
    return names


def capture_linkage(build, binary, *, link_directory=None):
    """Hash linker-read inputs, not a claim about individual incorporated members."""
    build=Path(build).resolve()
    directory=Path(link_directory).resolve() if link_directory is not None else build/'cmd/dot'
    command=directory/'CMakeFiles/dot.dir/link.txt'
    dependencies=directory/'CMakeFiles/dot.dir/link.d'
    if not command.is_file() or not dependencies.is_file():
        return dict(recorded=False,pending_reason='GNU ld dependency metadata unavailable; equivalent reviewed linkage evidence still required.')
    if command.stat().st_size>65536 or dependencies.stat().st_size>8*1024**2:
        raise ValueError('Link metadata exceeds maintainer limits')
    with dependencies.open('rb') as stream:payload=stream.read(8*1024**2+1)
    if len(payload)>8*1024**2:raise ValueError('Link metadata exceeds maintainer limits')
    names=parse_link_dependencies(payload.decode('utf-8'))
    inputs={}
    total=0
    for name in names:
        path=Path(name)
        path=(directory/path).resolve(strict=True) if not path.is_absolute() else path.resolve(strict=True)
        if path in inputs:
            inputs[path]['references']+=1
            continue
        if not path.is_file():raise ValueError('Link input is not a regular file')
        size=path.stat().st_size
        total+=size
        if total>1024**3:raise ValueError('Link inputs exceed maintainer budget')
        scope='build' if path.is_relative_to(build) else 'sdk'
        inputs[path]=dict(path=path.relative_to(build).as_posix() if scope=='build' else str(path),
                          scope=scope,size=size,sha256=digest(path,maximum=size),references=1)
    return dict(recorded=True,kind='linker-read-inputs-not-member-proof',
                executable_sha256=digest(binary),link_command_sha256=digest(command,maximum=65536),
                dependency_file_sha256=digest(dependencies,maximum=8*1024**2),
                inputs=sorted(inputs.values(),key=lambda item:(item['scope'],item['path'])))


def plan(artifact_id, archive, output):
    recipe = json.loads((HERE / (artifact_id + '.json')).read_text(encoding='utf-8'))
    source = json.loads((HERE / 'source-lock.json').read_text(encoding='utf-8'))
    source_inputs.verify(archive, source)
    with tarfile.open(archive) as incoming:
        if incoming.pax_headers.get('comment') != source['git_revision']:
            raise ValueError('Source revision differs from the pinned tag archive')
        copying = incoming.extractfile('graphviz-16.1.0/' + source['license_path']).read()
        if hashlib.sha256(copying).hexdigest() != source['license_sha256']:
            raise ValueError('Source license differs from the reviewed source')
    return dict(artifact_id=artifact_id, recipe=recipe, source=source,
                recipe_sha256=digest(HERE / (artifact_id + '.json')),
                output=str(Path(output).resolve()), qualification='candidate-not-qualified')


def build_mode(host, recipe, experimental):
    if host.os != recipe['os'] or host.arch != recipe['arch'] or host.translated:
        raise ValueError('Build requires the matching native OS/architecture')
    if experimental:
        if (host.os != 'linux' or host.libc_family != 'glibc' or recipe['abi'] != 'musl'
                or '-static' not in shlex.split(recipe['cmake'].get('CMAKE_EXE_LINKER_FLAGS',''))):
            raise ValueError('Cross-libc experiment requires Linux glibc host and explicit fully static musl recipe')
        return 'cpu-native-cross-libc-experiment'
    if host.os == 'linux' and host.libc_family != recipe['abi']:
        raise ValueError('Build requires the matching libc family')
    return 'native-host-toolchain'


def elf_verifier():
    spec=importlib.util.spec_from_file_location('static_elf_verifier',HERE/'verify-artifact.py')
    verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
    return verifier


def confirm_static_linkage(text):
    elf_verifier().linux_dependencies(text,[],'0',require_static=True)


def requires_static_inspection(recipe):
    return recipe.get('abi')=='musl' and '-static' in shlex.split(recipe['cmake'].get('CMAKE_EXE_LINKER_FLAGS',''))


def execute(record, archive, sdk_path, *, cross_libc_experiment=False):
    host = detect_host()
    recipe = record['recipe']
    mode = build_mode(host,recipe,cross_libc_experiment)
    inspect_static=requires_static_inspection(recipe)
    sdk = json.loads(Path(sdk_path).read_text(encoding='utf-8'))
    if not isinstance(sdk.get('environment_digest'), str) or not re.fullmatch(r'[0-9a-f]{64}',sdk['environment_digest']):
        raise ValueError('Reviewed SDK/container environment digest required')
    tools = {}
    keys = ('cmake', 'c_compiler', 'cxx_compiler') + (('elf_inspector',) if inspect_static else ())
    for key in keys:
        item = sdk[key]
        path = Path(item['path'])
        if not path.is_absolute() or not path.is_file() or digest(path) != item['sha256']:
            raise ValueError('SDK tool is missing or changed: ' + key)
        tools[key] = str(path)
    if inspect_static:
        facts=sdk.get('facts',{})
        if (facts.get('target_libc_family')!='musl' or facts.get('target_os')!='linux'
                or facts.get('target_arch')!=recipe['arch'] or facts.get('static_linking') is not True):
            raise ValueError('Experimental SDK must explicitly declare matching static musl target facts')
    output = Path(record['output'])
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    source_dir = output / 'source'
    source_dir.mkdir(mode=0o700)
    with tarfile.open(archive) as incoming:
        members = incoming.getmembers()
        if len(members) > 50_000 or sum(item.size for item in members) > 1024**3:
            raise ValueError('Source expansion exceeds maintainer budget')
        incoming.extractall(source_dir, filter='data')
    source_inputs.apply(source_dir, record['source'])
    source_dir /= 'graphviz-16.1.0'
    build = output / 'build'
    install = output / 'install'
    configure = [tools['cmake'], '-S', str(source_dir), '-B', str(build),
                 '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_C_COMPILER=' + tools['c_compiler'],
                 '-DCMAKE_CXX_COMPILER=' + tools['cxx_compiler'], '-DCMAKE_INSTALL_PREFIX=' + str(install)]
    configure.extend('-D' + name + '=' + str(value) for name, value in recipe['cmake'].items())
    record.update(sdk=sdk, native_os=host.os, native_arch=host.arch,
                  libc=host.libc_version, kernel=host.kernel_version, completed=False,
                  host_libc_family=host.libc_family, target_libc_family=recipe['abi'],build_execution_kind=mode)
    provenance = output / 'provenance.json'
    provenance.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    environment = {key:os.environ[key] for key in ('HOME','LANG','LC_ALL','TMPDIR','SDKROOT','DEVELOPER_DIR') if key in os.environ}
    # Never discover Windows interop executables or user wrappers from a WSL PATH.
    environment['PATH'] = '/usr/bin:/bin:/usr/sbin:/sbin'
    for command, timeout in ((configure,120), ([tools['cmake'], '--build', str(build), '--target', 'dot', '--parallel', '2'],600)):
        subprocess.run(command, check=True, shell=False, cwd=output, env=environment, timeout=timeout)
    candidates = [path for path in build.rglob('dot') if path.is_file() and not path.is_symlink() and os.access(path, os.X_OK)]
    if len(candidates) != 1:
        raise ValueError('Expected exactly one native dot build output')
    binary = output / 'candidate/bin/dot'
    binary.parent.mkdir(parents=True)
    shutil.copyfile(candidates[0], binary)
    binary.chmod(0o755)
    if inspect_static:
        elf_verifier().elf_architecture(binary,recipe['arch'])
        inspection=run_bounded([tools['elf_inspector'],'--program-headers','--dynamic','--version-info',str(binary)],
                               timeout=30,max_output=8*1024**2,env=environment,cwd=output)
        if inspection.returncode:raise ValueError('Experimental ELF inspection failed')
        confirm_static_linkage(inspection.stdout.decode('utf-8'))
        report=output/'static-elf-inspection.txt'
        report.write_bytes(inspection.stdout)
        record['static_elf_inspection']=dict(report_sha256=digest(report),no_interpreter=True,
            no_dynamic_section=True,no_needed_libraries=True,no_glibc_symbols=True,
            qualification='static build measurement only; no Alpine/kernel/CPU baseline qualification')
    notices = output / 'candidate/third-party-notices'
    notices.mkdir()
    shutil.copyfile(source_dir / 'COPYING', notices / 'Graphviz-COPYING.txt')
    record['linkage']=capture_linkage(build,binary) if host.os=='linux' else dict(recorded=False,pending_reason='Platform-specific reviewed linkage evidence required.')
    record.update(completed=True, executable_sha256=digest(binary),
                  qualification='build-only; dependency/license/corpus/signature qualification still required')
    provenance.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact-id', required=True, choices=('linux-glibc-x86_64', 'linux-glibc-aarch64', 'linux-musl-x86_64', 'linux-musl-aarch64', 'macos-x86_64', 'macos-arm64'))
    parser.add_argument('--source-archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--sdk-record', type=Path)
    parser.add_argument('--cross-libc-experiment',action='store_true',
                        help='Explicit glibc-host/static-musl build experiment; never native musl cell acceptance')
    args = parser.parse_args()
    try:
        if args.cross_libc_experiment and not args.execute:raise ValueError('--cross-libc-experiment requires --execute')
        record = plan(args.artifact_id, args.source_archive, args.output)
        if args.execute:
            if not args.sdk_record:
                raise ValueError('--execute requires --sdk-record; no SDK is installed automatically')
            record = execute(record, args.source_archive, args.sdk_record,cross_libc_experiment=args.cross_libc_experiment)
        print(json.dumps(record, indent=2))
    except (OSError, ValueError, KeyError, tarfile.TarError, subprocess.SubprocessError, ProcessLimitError) as exc:
        parser.exit(1, type(exc).__name__ + ': ' + str(exc) + '\n')


if __name__ == '__main__':
    main()
