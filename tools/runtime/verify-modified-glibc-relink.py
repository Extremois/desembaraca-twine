"""Verify controlled modified-glibc relink from exported Linux candidate sources.

Proves that a downstream recipient can modify the four observed glibc startup
and libc_nonshared source files in the exported SDK tree (including
lib/libc/glibc/csu/init.c, which lacks the startup linking exception phrase)
and relink the dot executable against the existing pre-built Graphviz objects
without recompiling Graphviz or requiring excluded third-party sources.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('glibc_object_audit', HERE / 'audit-glibc-objects.py')
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)

COMMON_EDITS = (
    (
        'lib/libc/glibc/csu/init.c',
        'const int _IO_stdin_used = 0x20001;\n',
        'const int _IO_stdin_used = 0x20002;\n',
    ),
    (
        'lib/libc/glibc/csu/elf-init-2.33.c',
        '__libc_csu_init (int argc, char **argv, char **envp)\n{\n',
        '__libc_csu_init (int argc, char **argv, char **envp)\n{\n'
        '  extern const int _IO_stdin_used;\n'
        '  __asm__ volatile ("nop" : : "r" (_IO_stdin_used));\n',
    ),
    (
        'lib/libc/glibc/io/fstat-2.32.c',
        '__fstat (int fd, struct stat *buf)\n{\n  return __fxstat (_STAT_VER, fd, buf);\n}\n',
        '__fstat (int fd, struct stat *buf)\n{\n  __asm__ volatile ("nop");\n  return __fxstat (_STAT_VER, fd, buf);\n}\n',
    ),
)

START_EDITS = {
    'x86_64': (
        'lib/libc/glibc/sysdeps/x86_64/start-2.33.S',
        '\txorl %ebp, %ebp\n',
        '\txorl %ebp, %ebp\n\tnop\n',
    ),
    'aarch64': (
        'lib/libc/glibc/sysdeps/aarch64/start-2.33.S',
        '\tmov\tx30, #0\n',
        '\tmov\tx30, #0\n\tnop\n',
    ),
}

EXPECTED_OBJECTS = (
    ('crt1.o', None),
    ('libc_nonshared.a', 'elf-init-2.33.o'),
    ('libc_nonshared.a', 'fstat-2.32.o'),
)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def detect_sdk_arch(sdk_root):
    sdk_root = Path(sdk_root)
    found = [
        arch for arch, (rel_path, _, _) in START_EDITS.items()
        if (sdk_root / rel_path).is_file()
    ]
    if len(found) != 1:
        raise ValueError('Expected exactly one native glibc startup architecture in SDK tree')
    return found[0]


def edits_for_arch(arch):
    if arch not in START_EDITS:
        raise ValueError('Unsupported glibc relink architecture')
    return (START_EDITS[arch], *COMMON_EDITS)


def modify_sdk(sdk_root, edit_receipt_path, cache_dir=None):
    sdk_root = Path(sdk_root).resolve(strict=True)
    edit_receipt_path = Path(edit_receipt_path)
    if edit_receipt_path.exists() or edit_receipt_path.is_symlink():
        raise ValueError('Edit receipt path must be new')
    arch = detect_sdk_arch(sdk_root)
    edits = []
    for rel_path, before_snippet, after_snippet in edits_for_arch(arch):
        target = sdk_root / rel_path
        before_raw = AUDIT.audit.bounded(target, 1024**2)
        text = before_raw.decode('utf-8', errors='strict')
        if text.count(before_snippet) != 1:
            raise ValueError('Expected exact unmodified glibc snippet in ' + rel_path)
        updated_text = text.replace(before_snippet, after_snippet, 1)
        after_raw = updated_text.encode('utf-8')
        before_notice = AUDIT.notices.source_notice_prefix(before_raw)
        after_notice = AUDIT.notices.source_notice_prefix(after_raw)
        if not before_notice or before_notice != after_notice:
            raise ValueError('Modification must preserve leading source license notice in ' + rel_path)
        target.write_bytes(after_raw)
        edits.append(dict(
            path=rel_path,
            before_size=len(before_raw),
            after_size=len(after_raw),
            before_sha256=sha256_bytes(before_raw),
            after_sha256=sha256_bytes(after_raw),
            leading_comment_bytes=len(after_notice),
            leading_comment_sha256=sha256_bytes(after_notice),
        ))
    cache_cleared = False
    if cache_dir is not None:
        cache_path = Path(cache_dir)
        if cache_path.is_symlink():
            raise ValueError('Refusing to clear symlinked compiler cache')
        if cache_path.exists():
            resolved_cache = cache_path.resolve(strict=True)
            if resolved_cache.name != 'cache' or sdk_root.is_relative_to(resolved_cache):
                raise ValueError('Compiler cache path must be a dedicated cache directory outside sdk_root')
            shutil.rmtree(resolved_cache)
            cache_cleared = True
    receipt = dict(
        kind='modified-glibc-sdk-edit-receipt',
        approved=False,
        qualified=False,
        arch=arch,
        artifact_id='linux-glibc-' + arch,
        sdk_root=str(sdk_root),
        cache_cleared=cache_cleared,
        edits=edits,
    )
    with edit_receipt_path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(receipt, stream, indent=2)
        stream.write('\n')
    return receipt


def collect_modified_observations(modified_linked, modified_sdk_root, sdk_archive, edit_receipt):
    modified_linked = Path(modified_linked).resolve(strict=True)
    modified_sdk_root = Path(modified_sdk_root).resolve(strict=True)
    sdk_archive = Path(sdk_archive).resolve(strict=True)
    try:
        AUDIT.collect(modified_linked, modified_sdk_root, sdk_archive)
    except ValueError as exc:
        if 'glibc source differs from pinned SDK' not in str(exc):
            raise
    else:
        raise ValueError('Modified build was not rejected by pinned SDK audit')

    edits_by_path = {row['path']: row for row in edit_receipt.get('edits', ())}
    original_archive_files = AUDIT.notices.archive_files

    def verify_modified_against_pinned(archive, root_name, names):
        pinned = original_archive_files(archive, root_name, names)
        result = {}
        for name in names:
            actual = AUDIT.audit.bounded(modified_sdk_root / name, 1024**2)
            actual_sha = sha256_bytes(actual)
            pinned_sha = sha256_bytes(pinned[name])
            if name in edits_by_path:
                expected = edits_by_path[name]
                if pinned_sha != expected['before_sha256'] or actual_sha != expected['after_sha256']:
                    raise ValueError('Modified SDK source does not match recorded edit receipt: ' + name)
            elif actual_sha != pinned_sha:
                raise ValueError('Unexpected modification to non-target glibc source: ' + name)
            result[name] = actual
        return result

    with patch.object(AUDIT.notices, 'archive_files', side_effect=verify_modified_against_pinned):
        observations = AUDIT.collect(modified_linked, modified_sdk_root, sdk_archive)
    observations['modified_sdk_edit_receipt_verified'] = True
    return observations


def _build_inputs(provenance):
    linkage = provenance.get('linkage', {})
    if linkage.get('recorded') is not True:
        raise ValueError('Provenance is missing recorded linkage inputs')
    rows = [
        (item['path'], item['sha256'], item['size'], item['references'])
        for item in linkage.get('inputs', ())
        if item.get('scope') == 'build'
    ]
    if not rows:
        raise ValueError('Expected at least one Graphviz build-scope linker input')
    return rows


def _build_allocated_sections(allocations):
    rows = [
        (
            item['input_path'],
            item['input_sha256'],
            item['member'],
            item['input_section'],
            item['output_section'],
            item['bytes'],
            item['executable'],
        )
        for item in allocations.get('sections', ())
        if item.get('scope') == 'build'
    ]
    if not rows:
        raise ValueError('Expected at least one Graphviz build-scope allocated section')
    return rows


def compare_relink_records(
    baseline_prov,
    baseline_obs,
    baseline_alloc,
    modified_prov,
    modified_obs,
    modified_alloc,
    edit_receipt,
    syscall_report,
    corpus_report,
    *,
    pinned_sdk_rejected=True,
):
    if pinned_sdk_rejected is not True:
        raise ValueError('Modified build was not rejected by pinned SDK audit')
    if edit_receipt.get('kind') != 'modified-glibc-sdk-edit-receipt':
        raise ValueError('Invalid modified glibc edit receipt')
    arch = edit_receipt.get('arch')
    expected_paths = {row[0] for row in edits_for_arch(arch)}
    edits_by_path = {row['path']: row for row in edit_receipt.get('edits', ())}
    if set(edits_by_path) != expected_paths or len(edits_by_path) != len(edit_receipt.get('edits', ())):
        raise ValueError('Edit receipt does not cover the exact four observed glibc source files')
    for edit in edits_by_path.values():
        if edit['before_sha256'] == edit['after_sha256']:
            raise ValueError('Edit receipt did not change source hash for ' + edit['path'])

    artifact_id = 'linux-glibc-' + arch
    if (baseline_prov.get('artifact_id') != artifact_id
            or modified_prov.get('artifact_id') != artifact_id
            or baseline_prov.get('completed') is not True
            or modified_prov.get('completed') is not True):
        raise ValueError('Expected completed matching glibc provenance records')

    base_relink = baseline_prov.get('relink', {})
    mod_relink = modified_prov.get('relink', {})
    if (base_relink.get('byte_identical_to_compiler') is not True
            or mod_relink.get('byte_identical_to_compiler') is not True
            or base_relink.get('byte_identical_to_source') is not True
            or mod_relink.get('byte_identical_to_source') is not False):
        raise ValueError('Baseline relink must match source executable and modified relink must differ')
    if (base_relink.get('parent_output') != mod_relink.get('parent_output')
            or base_relink.get('parent_provenance_sha256') != mod_relink.get('parent_provenance_sha256')
            or not base_relink.get('parent_provenance_sha256')):
        raise ValueError('Baseline and modified relinks must share the same parent source build')
    if baseline_prov.get('executable_sha256') == modified_prov.get('executable_sha256'):
        raise ValueError('Modified executable hash must differ from baseline executable hash')

    base_build_inputs = _build_inputs(baseline_prov)
    mod_build_inputs = _build_inputs(modified_prov)
    if base_build_inputs != mod_build_inputs:
        raise ValueError('Graphviz build-scope linker inputs changed during modified glibc relink')

    base_build_sections = _build_allocated_sections(baseline_alloc)
    mod_build_sections = _build_allocated_sections(modified_alloc)
    if base_build_sections != mod_build_sections:
        raise ValueError('Graphviz build-scope allocated sections changed during modified glibc relink')

    base_joined = AUDIT.allocated_source_observations(baseline_obs, baseline_alloc)
    mod_joined = AUDIT.allocated_source_observations(modified_obs, modified_alloc)
    if (base_joined['other_allocated_sdk_inputs'] != ['libcompiler_rt.a']
            or mod_joined['other_allocated_sdk_inputs'] != ['libcompiler_rt.a']):
        raise ValueError('Unexpected non-glibc allocated SDK inputs')

    base_sources = {item['path']: item for item in baseline_obs.get('sources', ())}
    mod_sources = {item['path']: item for item in modified_obs.get('sources', ())}
    additional = 'lib/libc/glibc/csu/abi-note.S'
    if set(base_sources) != expected_paths | {additional} or set(mod_sources) != expected_paths | {additional}:
        raise ValueError('Observed glibc source inventory differs from expected startup/nonshared set')
    if base_sources[additional]['sha256'] != mod_sources[additional]['sha256']:
        raise ValueError('Unmodified abi-note.S source hash changed unexpectedly')

    source_comparisons = []
    for path in sorted(expected_paths):
        edit = edits_by_path[path]
        base_src = base_sources[path]
        mod_src = mod_sources[path]
        if (base_src['sha256'] != edit['before_sha256']
                or mod_src['sha256'] != edit['after_sha256']
                or base_src['leading_comment_sha256'] != edit['leading_comment_sha256']
                or mod_src['leading_comment_sha256'] != edit['leading_comment_sha256']):
            raise ValueError('Observed source hashes or notices do not match edit receipt for ' + path)
        source_comparisons.append(dict(
            path=path,
            baseline_sha256=base_src['sha256'],
            modified_sha256=mod_src['sha256'],
            leading_comment_sha256=mod_src['leading_comment_sha256'],
        ))

    base_objs = {(item['input'], item['member']): item for item in base_joined['objects']}
    mod_objs = {(item['input'], item['member']): item for item in mod_joined['objects']}
    if set(base_objs) != set(EXPECTED_OBJECTS) or set(mod_objs) != set(EXPECTED_OBJECTS):
        raise ValueError('Retained glibc object set differs from expected crt1.o and libc_nonshared.a members')

    object_comparisons = []
    for key in EXPECTED_OBJECTS:
        base_obj = base_objs[key]
        mod_obj = mod_objs[key]
        if (base_obj['input_sha256'] == mod_obj['input_sha256']
                or base_obj['object_sha256'] == mod_obj['object_sha256']):
            raise ValueError('Retained glibc object hash did not change: ' + str(key))
        if (mod_obj['allocated_bytes'] <= base_obj['allocated_bytes']
                or mod_obj['executable_bytes'] <= base_obj['executable_bytes']):
            raise ValueError('Retained glibc object allocated/executable bytes did not increase: ' + str(key))
        base_units = {u['path']: u for u in base_obj['compilation_units']}
        mod_units = {u['path']: u for u in mod_obj['compilation_units']}
        if list(base_units) != list(mod_units):
            raise ValueError('Compilation unit list changed for retained glibc object: ' + str(key))
        for path, base_unit in base_units.items():
            mod_unit = mod_units[path]
            edit = edits_by_path[path]
            if (base_unit['sha256'] != edit['before_sha256']
                    or mod_unit['sha256'] != edit['after_sha256']
                    or base_unit['linking_exception_phrase_present'] != mod_unit['linking_exception_phrase_present']):
                raise ValueError('Compilation unit binding mismatch in retained glibc object: ' + path)
        if key == ('crt1.o', None):
            base_non_exec = base_obj['allocated_bytes'] - base_obj['executable_bytes']
            mod_non_exec = mod_obj['allocated_bytes'] - mod_obj['executable_bytes']
            if (mod_non_exec <= base_non_exec
                    or not any(sec == '.rodata' or sec.startswith('.rodata.') for sec in mod_obj['input_sections'])):
                raise ValueError('Modified crt1.o did not retain allocated .rodata from init.c')
        object_comparisons.append(dict(
            input=base_obj['input'],
            member=base_obj['member'],
            baseline_input_sha256=base_obj['input_sha256'],
            modified_input_sha256=mod_obj['input_sha256'],
            baseline_object_sha256=base_obj['object_sha256'],
            modified_object_sha256=mod_obj['object_sha256'],
            baseline_allocated_bytes=base_obj['allocated_bytes'],
            modified_allocated_bytes=mod_obj['allocated_bytes'],
            baseline_executable_bytes=base_obj['executable_bytes'],
            modified_executable_bytes=mod_obj['executable_bytes'],
            baseline_input_sections=base_obj['input_sections'],
            modified_input_sections=mod_obj['input_sections'],
            compilation_units=[u['path'] for u in mod_obj['compilation_units']],
        ))

    mod_exec_sha = modified_prov['executable_sha256']
    if (syscall_report.get('kind') != 'linux-native-syscall-observation'
            or syscall_report.get('passed') is not True
            or syscall_report.get('qualified') is not False
            or syscall_report.get('environment_kind') != 'native'
            or syscall_report.get('arch') != arch
            or syscall_report.get('control', {}).get('detected') is not True
            or syscall_report.get('corpus', {}).get('engine_sha256') != mod_exec_sha
            or syscall_report.get('corpus', {}).get('cases') != 13
            or syscall_report.get('corpus', {}).get('dot_executions', 0) <= 0
            or syscall_report.get('corpus', {}).get('network_syscalls') != {}):
        raise ValueError('Modified glibc relink failed native syscall observation gate')

    cases = corpus_report.get('cases', ())
    if (corpus_report.get('passed') is not True
            or corpus_report.get('engine_sha256') != mod_exec_sha
            or len(cases) != 13
            or sum(1 for item in cases if item.get('reference_expected')) != 6
            or not all(item.get('passed') is True for item in cases)
            or corpus_report.get('relocation', {}).get('passed') is not True
            or corpus_report.get('relocation', {}).get('unicode_directory') is not True):
        raise ValueError('Modified glibc relink failed public corpus or Unicode relocation gate')

    return dict(
        kind='modified-glibc-relink-verification',
        passed=True,
        approved=False,
        qualified=False,
        artifact_id=artifact_id,
        arch=arch,
        lgpl_section_6_mechanism='LGPL-2.1-section-6a-and-6d-source-and-object-relink',
        parent_source_build_provenance_sha256=base_relink['parent_provenance_sha256'],
        baseline_executable_sha256=baseline_prov['executable_sha256'],
        modified_executable_sha256=mod_exec_sha,
        pinned_sdk_audit_rejected_modified_build=True,
        graphviz_build_inputs_count=len(base_build_inputs),
        graphviz_build_inputs_unchanged=True,
        graphviz_allocated_sections_count=len(base_build_sections),
        graphviz_allocated_sections_unchanged=True,
        other_allocated_sdk_inputs=mod_joined['other_allocated_sdk_inputs'],
        modified_sources=source_comparisons,
        retained_glibc_objects=object_comparisons,
        functional_and_offline_verification=dict(
            corpus_passed=True,
            corpus_cases=len(cases),
            reference_cases=6,
            unicode_relocation_passed=True,
            dot_executions=syscall_report['corpus']['dot_executions'],
            network_syscalls=syscall_report['corpus']['network_syscalls'],
            child_network_control_detected=True,
            syscall_trace_sha256=syscall_report['corpus']['trace_sha256'],
            corpus_report_sha256=syscall_report['corpus']['report_sha256'],
        ),
        limitations=[
            'Technical proof of modified glibc startup/nonshared rebuild and object relink only; not legal advice or catalog admission',
            'Final distribution still requires binding the corresponding-source package/offer to the distributed artifact',
            'Remaining third-party component license compatibility reviews remain separate gates',
        ],
    )


def verify_relink(
    baseline_linked,
    modified_linked,
    modified_sdk_root,
    sdk_archive,
    edit_receipt_path,
    syscall_report_path,
    corpus_report_path,
    report_path,
    modified_observations_out=None,
):
    baseline_linked = Path(baseline_linked).resolve(strict=True)
    modified_linked = Path(modified_linked).resolve(strict=True)
    report_path = Path(report_path)
    if report_path.exists() or report_path.is_symlink():
        raise ValueError('Verification report path must be new')
    if modified_observations_out is not None:
        modified_observations_out = Path(modified_observations_out)
        if modified_observations_out.exists() or modified_observations_out.is_symlink():
            raise ValueError('Modified observations output path must be new')

    load_json = lambda path: json.loads(AUDIT.audit.bounded(Path(path), 8 * 1024**2))
    baseline_prov = load_json(baseline_linked / 'provenance.json')
    baseline_obs = load_json(baseline_linked / 'glibc-object-sources.json')
    baseline_alloc = load_json(baseline_linked / 'allocated-sections.json')
    modified_prov = load_json(modified_linked / 'provenance.json')
    modified_alloc = load_json(modified_linked / 'allocated-sections.json')
    edit_receipt = load_json(edit_receipt_path)
    syscall_report = load_json(syscall_report_path)
    corpus_report = load_json(corpus_report_path)

    if AUDIT.builder.digest(baseline_linked / 'candidate/bin/dot') != baseline_prov.get('executable_sha256'):
        raise ValueError('Baseline relink executable differs from provenance')
    if AUDIT.builder.digest(modified_linked / 'candidate/bin/dot') != modified_prov.get('executable_sha256'):
        raise ValueError('Modified relink executable differs from provenance')

    modified_obs = collect_modified_observations(
        modified_linked, modified_sdk_root, sdk_archive, edit_receipt
    )
    if modified_observations_out is not None:
        with modified_observations_out.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(modified_obs, stream, indent=2)
            stream.write('\n')

    report = compare_relink_records(
        baseline_prov,
        baseline_obs,
        baseline_alloc,
        modified_prov,
        modified_obs,
        modified_alloc,
        edit_receipt,
        syscall_report,
        corpus_report,
        pinned_sdk_rejected=True,
    )
    with report_path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--modify-sdk', action='store_true')
    mode.add_argument('--verify', action='store_true')
    parser.add_argument('--sdk-root', type=Path)
    parser.add_argument('--cache-dir', type=Path)
    parser.add_argument('--edit-receipt', type=Path, required=True)
    parser.add_argument('--baseline-linked', type=Path)
    parser.add_argument('--modified-linked', type=Path)
    parser.add_argument('--modified-sdk-root', type=Path)
    parser.add_argument('--sdk-archive', type=Path)
    parser.add_argument('--syscall-report', type=Path)
    parser.add_argument('--corpus-report', type=Path)
    parser.add_argument('--modified-observations-out', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    try:
        if args.modify_sdk:
            if args.sdk_root is None:
                raise ValueError('--modify-sdk requires --sdk-root')
            result = modify_sdk(args.sdk_root, args.edit_receipt, args.cache_dir)
            print(json.dumps(dict(arch=result['arch'], edits=len(result['edits']), cache_cleared=result['cache_cleared'])))
        else:
            required = (
                args.baseline_linked,
                args.modified_linked,
                args.modified_sdk_root,
                args.sdk_archive,
                args.syscall_report,
                args.corpus_report,
                args.report,
            )
            if any(item is None for item in required):
                raise ValueError('--verify requires baseline/modified builds, SDK paths, syscall/corpus reports and --report')
            result = verify_relink(
                args.baseline_linked,
                args.modified_linked,
                args.modified_sdk_root,
                args.sdk_archive,
                args.edit_receipt,
                args.syscall_report,
                args.corpus_report,
                args.report,
                args.modified_observations_out,
            )
            print(json.dumps(dict(
                artifact_id=result['artifact_id'],
                passed=result['passed'],
                graphviz_build_inputs_count=result['graphviz_build_inputs_count'],
                modified_executable_sha256=result['modified_executable_sha256'],
                qualified=result['qualified'],
            )))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, type(exc).__name__ + ': ' + str(exc) + '\n')


if __name__ == '__main__':
    main()
