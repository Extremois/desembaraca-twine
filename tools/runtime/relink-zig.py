"""Capture real LLD dependencies in a new private candidate; never approve it.

Zig 0.15.2's cc driver rejects --dependency-file. Replay its verbose LLD
invocation directly, require byte equality with the compiler's reference, and
retain the dependency file from that final link. No shell or global install.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'src'))
from twine_edge_overlap.engines.process import ProcessLimitError, run_bounded
from twine_edge_overlap.runtime_platform import detect_host

spec = importlib.util.spec_from_file_location('runtime_builder', HERE / 'build-common.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
map_spec=importlib.util.spec_from_file_location('runtime_link_map',HERE/'link-map.py')
link_map=importlib.util.module_from_spec(map_spec);map_spec.loader.exec_module(link_map)


def arguments(text):
    if len(text.encode('utf-8')) > 65536 or '\0' in text:
        raise ValueError('Link command exceeds limit or contains NUL')
    argv = shlex.split(text, posix=True)
    if not argv or len(argv) > 10000 or any(x.startswith('@') for x in argv):
        raise ValueError('Missing command, excessive arguments or response file')
    return argv


def replace_output(argv, expected, replacement):
    if argv.count('-o') != 1:
        raise ValueError('Expected exactly one output option')
    index = argv.index('-o') + 1
    if index >= len(argv) or argv[index] != str(expected):
        raise ValueError('Unexpected linker output')
    result = list(argv)
    result[index] = str(replacement)
    return result


def lld_arguments(text, reference, original_cwd):
    if len(text.encode('utf-8')) > 8 * 1024**2:
        raise ValueError('Verbose linker output exceeds limit')
    lines = [line for line in text.splitlines() if line.startswith('ld.lld ')]
    if len(lines) != 1:
        raise ValueError('Expected exactly one LLD invocation')
    argv = replace_output(arguments(lines[0]), reference, 'dot')
    # The final link runs in a new directory. Resolve inputs against the
    # compiler invocation directory, preserving options and their values.
    for index, arg in enumerate(argv):
        if index == argv.index('-o') + 1 or arg.startswith('-'):
            continue
        path = Path(arg)
        if not path.is_absolute() and (original_cwd / path).is_file():
            argv[index] = str((original_cwd / path).resolve(strict=True))
    return argv[1:] + ['--dependency-file=CMakeFiles/dot.dir/link.d']


def capture_extractions(path, linkage, build_root):
    """Bind LLD's extraction observations to hashed inputs, without approval.

    Extraction does not prove retention after section GC. Zero observations
    do not prove absence of code, particularly with other linker modes.
    """
    with path.open('rb') as stream:
        payload = stream.read(8 * 1024**2 + 1)
    if len(payload) > 8 * 1024**2:
        raise ValueError('Extraction report exceeds limit')
    lines = payload.decode('utf-8').splitlines()
    if not lines or lines[0] != 'reference\textracted\tsymbol' or len(lines) > 100001:
        raise ValueError('Malformed or excessive extraction rows')
    archives = {}
    members = {}
    for item in linkage['inputs']:
        source = Path(item['path'])
        if source.suffix != '.a':
            continue
        absolute = build_root / source if item['scope'] == 'build' else source
        archives[str(absolute)] = item
        members[str(absolute)] = set()
    rows = []
    for line in lines[1:]:
        fields = line.split('\t')
        if len(fields) != 3 or any(not value or '\0' in value or len(value) > 16384 for value in fields):
            raise ValueError('Malformed extraction row')
        reference, extracted, symbol = fields
        archive, separator, member = extracted.rpartition('(')
        if not separator or not member.endswith(')') or not member[:-1] or archive not in archives:
            raise ValueError('Extraction does not match a hashed archive input')
        member = member[:-1]
        members[archive].add(member)
        rows.append(dict(reference=reference, archive_sha256=archives[archive]['sha256'],
                         member=member, symbol=symbol))
    return dict(recorded=True, kind='archive-extraction-observations-not-section-retention-or-license-approval',
        report_sha256=builder.digest(path, maximum=8*1024**2), row_count=len(rows), rows=rows,
        archives=[dict(path=item['path'], scope=item['scope'], archive_sha256=item['sha256'],
                       extracted_member_count=len(members[absolute])) for absolute, item in sorted(archives.items())])


def relink_variant(host, record):
    variants = {'linux-glibc-x86_64': ('x86_64', 'glibc'),
                'linux-glibc-aarch64': ('aarch64', 'glibc'),
                'linux-musl-x86_64': ('x86_64', 'musl'),
                'linux-musl-aarch64': ('aarch64', 'musl')}
    variant = variants.get(record.get('artifact_id'))
    if variant is None or record.get('completed') is not True:
        raise ValueError('Expected a completed supported Linux source build')
    arch, abi = variant
    legacy_cross_libc = (arch, abi, host.libc_family) == ('x86_64', 'musl', 'glibc')
    if ((host.os, host.arch, host.translated) != ('linux', arch, False)
            or (host.libc_family != abi and not legacy_cross_libc)):
        raise ValueError('Relink requires matching Linux CPU/ABI or the existing x64 static cross-libc experiment')
    recipe = record.get('recipe', {})
    if not isinstance(recipe, dict):
        raise ValueError('Source recipe must be an object')
    if ((record.get('native_os'), record.get('native_arch')) != ('linux', arch)
            or (recipe.get('os'), recipe.get('arch'), recipe.get('abi')) != ('linux', arch, abi)):
        raise ValueError('Source provenance architecture or ABI differs from its artifact')
    return abi == 'musl'


def relink(source_output, output, zig):
    source_output = source_output.resolve(strict=True)
    provenance_path = source_output / 'provenance.json'
    record = json.loads(provenance_path.read_text(encoding='utf-8'))
    host = detect_host()
    musl = relink_variant(host, record)
    if musl and any(record.get('static_elf_inspection',{}).get(key) is not True for key in
                    ('no_interpreter','no_dynamic_section','no_needed_libraries','no_glibc_symbols')):
        raise ValueError('musl relink requires measured static source candidate')
    zig = zig.resolve(strict=True)
    if builder.digest(zig) != record['sdk']['facts']['zig_sha256']:
        raise ValueError('Zig does not match the source SDK record')
    compiler = record['sdk']['cxx_compiler']
    if builder.digest(compiler['path']) != compiler['sha256']:
        raise ValueError('Source compiler wrapper changed')
    if musl:
        inspector=record['sdk']['elf_inspector']
        if not Path(inspector['path']).is_absolute() or builder.digest(inspector['path'])!=inspector['sha256']:
            raise ValueError('Static ELF inspector changed')
    source_binary = source_output / 'candidate/bin/dot'
    if builder.digest(source_binary) != record['executable_sha256']:
        raise ValueError('Source executable changed')
    original_cwd = source_output / 'build/cmd/dot'
    command_path = original_cwd / 'CMakeFiles/dot.dir/link.txt'
    if command_path.stat().st_size > 65536:
        raise ValueError('Source link command exceeds limit')
    argv = arguments(command_path.read_text(encoding='utf-8'))
    if argv[0] != compiler['path']:
        raise ValueError('Source command does not use the pinned compiler')
    output = output.resolve()
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    cwd = output / 'build/cmd/dot'
    (cwd / 'CMakeFiles/dot.dir').mkdir(parents=True)
    reference = cwd / 'compiler-reference'
    argv = replace_output(argv, 'dot', reference) + ['-v']
    environment = {key: os.environ[key] for key in ('HOME', 'LANG', 'LC_ALL', 'TMPDIR') if key in os.environ}
    environment['PATH'] = '/usr/bin:/bin'
    result = run_bounded(argv, cwd=original_cwd, env=environment, timeout=120, max_output=8*1024**2)
    (output / 'compiler-verbose.txt').write_bytes(result.stdout + result.stderr)
    if result.returncode:
        raise ValueError('Reference compiler link failed; see compiler-verbose.txt')
    link = [str(zig), 'ld.lld', *lld_arguments(result.stderr.decode('utf-8'), reference, original_cwd)]
    link.append('--why-extract=CMakeFiles/dot.dir/why-extract.tsv')
    link.append('--Map=CMakeFiles/dot.dir/link-map.txt')
    # JSON is a record only. capture_linkage hashes it; nothing reads it as code.
    (cwd / 'CMakeFiles/dot.dir/link.txt').write_text(json.dumps(link) + '\n', encoding='utf-8')
    result = run_bounded(link, cwd=cwd, env=environment, timeout=120, max_output=8*1024**2)
    (output / 'lld-output.txt').write_bytes(result.stdout + result.stderr)
    if result.returncode:
        raise ValueError('Direct LLD link failed; see lld-output.txt')
    if builder.digest(cwd / 'dot') != builder.digest(reference):
        raise ValueError('Direct LLD output differs from compiler reference')
    candidate = output / 'candidate'
    (candidate / 'bin').mkdir(parents=True)
    binary = candidate / 'bin/dot'
    shutil.copyfile(cwd / 'dot', binary)
    binary.chmod(0o755)
    if musl:
        builder.elf_verifier().elf_architecture(binary,record['native_arch'])
        measured=run_bounded([inspector['path'],'--program-headers','--dynamic','--version-info',str(binary)],
                             cwd=output,env=environment,timeout=30,max_output=8*1024**2)
        if measured.returncode:raise ValueError('Relink static ELF inspection failed')
        builder.confirm_static_linkage(measured.stdout.decode('utf-8'))
        (output/'static-elf-inspection.txt').write_bytes(measured.stdout)
        record['static_elf_inspection']['report_sha256']=builder.digest(output/'static-elf-inspection.txt')
    shutil.copytree(source_output / 'candidate/third-party-notices', candidate / 'third-party-notices')
    linkage = builder.capture_linkage(source_output / 'build', binary, link_directory=cwd)
    if not linkage['recorded']:
        raise ValueError('Direct LLD dependency capture is missing')
    linkage['archive_extractions'] = capture_extractions(cwd / 'CMakeFiles/dot.dir/why-extract.tsv',
                                                        linkage, source_output / 'build')
    retained=link_map.capture(cwd/'CMakeFiles/dot.dir/link-map.txt',binary,linkage,source_output/'build')
    retained_bytes=(json.dumps(retained,indent=2)+'\n').encode()
    if len(retained_bytes)>8*1024**2:raise ValueError('Allocated-section report exceeds limit')
    retained_path=output/'allocated-sections.json'
    retained_path.write_bytes(retained_bytes)
    linkage['allocated_input_sections']=dict(kind=retained['kind'],approved=False,qualified=False,
        executable_sha256=retained['executable_sha256'],map_sha256=retained['map_sha256'],
        report_sha256=builder.digest(retained_path),sections=len(retained['sections']),
        allocated_output_sections=retained['allocated_output_sections'])
    record.update(output=str(output), executable_sha256=builder.digest(binary), linkage=linkage,
        qualification='experimental-relink-only; no dependency/license/native-cell approval',
        relink=dict(parent_provenance_sha256=builder.digest(provenance_path),
                    parent_output=str(source_output), compiler_reference_sha256=builder.digest(reference),
                    byte_identical_to_compiler=True, zig_sha256=builder.digest(zig),
                    byte_identical_to_source=builder.digest(binary) == record['executable_sha256'],
                    compiler_verbose_sha256=builder.digest(output / 'compiler-verbose.txt'),
                    tool_sha256=builder.digest(Path(__file__))))
    (output / 'provenance.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-output', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--zig', type=Path, required=True)
    args = parser.parse_args()
    try:
        record = relink(args.source_output, args.output, args.zig)
        print(json.dumps(dict(executable_sha256=record['executable_sha256'],
                             inputs=len(record['linkage']['inputs']), qualified=False)))
    except (OSError, ValueError, KeyError, ProcessLimitError) as exc:
        parser.exit(1, type(exc).__name__ + ': ' + str(exc) + '\n')


if __name__ == '__main__':
    main()
