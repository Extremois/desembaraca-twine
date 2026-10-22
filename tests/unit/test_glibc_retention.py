import copy
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from common import ROOT


def tool():
    spec = importlib.util.spec_from_file_location('glibc_retention', ROOT / 'tools/runtime/audit-glibc-objects.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def relink_verifier():
    spec = importlib.util.spec_from_file_location(
        'modified_glibc_relink', ROOT / 'tools/runtime/verify-modified-glibc-relink.py'
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GlibcRetentionTests(unittest.TestCase):
    def fixture(self):
        sources = []
        for name, text in [('start.S', '/* permission to link the compiled\n version of this file */'),
                           ('init.c', '/* LGPL without the extra permission */')]:
            raw = text.encode()
            sources.append(dict(path=name, sha256='f' * 64, leading_comments=text,
                leading_comment_bytes=len(raw), leading_comment_sha256=hashlib.sha256(raw).hexdigest()))
        observations = dict(kind='glibc-object-source-observations-not-license-approval',
            artifact_id='linux-glibc-x86_64', executable_sha256='a' * 64, sources=sources,
            objects=[dict(input='crt1.o', input_sha256='b' * 64, member=None,
                object_sha256='b' * 64, sources=['start.S', 'init.c']),
                dict(input='libc_nonshared.a', input_sha256='c' * 64, member='init.o',
                    object_sha256='d' * 64, sources=['init.c'])])
        allocations = dict(kind='lld-allocated-input-sections-not-source-closure',
            executable_sha256='a' * 64, sections=[
                dict(scope='sdk', input_path='/linux/cache/crt1.o', input_sha256='b' * 64,
                    member=None, bytes=44, executable=True, input_section='.text'),
                dict(scope='sdk', input_path='/linux/cache/libc_nonshared.a', input_sha256='c' * 64,
                    member='/linux/cache/member/init.o', bytes=20, executable=True, input_section='.text'),
                dict(scope='sdk', input_path='/linux/cache/libcompiler_rt.a', input_sha256='e' * 64,
                    member='math.o', bytes=64, executable=True, input_section='.text.math')])
        return observations, allocations

    def modified_relink_fixture(self, arch='x86_64'):
        verifier = relink_verifier()
        artifact_id = 'linux-glibc-' + arch
        start_path = f'lib/libc/glibc/sysdeps/{arch}/start-2.33.S'
        edits = []
        base_sources = []
        mod_sources = []
        for idx, (path, _, _) in enumerate(verifier.edits_for_arch(arch), start=1):
            has_exception = path != 'lib/libc/glibc/csu/init.c'
            comment = (
                '/* permission to link the compiled version of this file */'
                if has_exception
                else '/* LGPL 2.1 without linking exception */'
            )
            comment_raw = comment.encode('utf-8')
            comment_sha = hashlib.sha256(comment_raw).hexdigest()
            before_sha = f'{idx:01x}' * 64
            after_sha = f'{idx + 8:01x}' * 64
            edits.append(dict(
                path=path,
                before_size=100 + idx,
                after_size=120 + idx,
                before_sha256=before_sha,
                after_sha256=after_sha,
                leading_comment_bytes=len(comment_raw),
                leading_comment_sha256=comment_sha,
            ))
            base_sources.append(dict(
                path=path,
                sha256=before_sha,
                leading_comments=comment,
                leading_comment_bytes=len(comment_raw),
                leading_comment_sha256=comment_sha,
            ))
            mod_sources.append(dict(
                path=path,
                sha256=after_sha,
                leading_comments=comment,
                leading_comment_bytes=len(comment_raw),
                leading_comment_sha256=comment_sha,
            ))
        abi_comment = '/* ABI note */'
        abi_raw = abi_comment.encode('utf-8')
        for target in (base_sources, mod_sources):
            target.append(dict(
                path='lib/libc/glibc/csu/abi-note.S',
                sha256='0' * 64,
                leading_comments=abi_comment,
                leading_comment_bytes=len(abi_raw),
                leading_comment_sha256=hashlib.sha256(abi_raw).hexdigest(),
            ))
        edit_receipt = dict(
            kind='modified-glibc-sdk-edit-receipt',
            approved=False,
            qualified=False,
            arch=arch,
            artifact_id=artifact_id,
            sdk_root='/tmp/sdk',
            cache_cleared=True,
            edits=edits,
        )
        base_exec = 'a' * 64
        mod_exec = 'b' * 64
        parent_prov = 'c' * 64
        build_input = dict(path='cmd/dot/CMakeFiles/dot.dir/dot.c.o', scope='build', size=1024, sha256='d' * 64, references=1)
        baseline_prov = dict(
            artifact_id=artifact_id,
            completed=True,
            executable_sha256=base_exec,
            linkage=dict(recorded=True, inputs=[build_input]),
            relink=dict(
                parent_output='/tmp/replay-build',
                parent_provenance_sha256=parent_prov,
                byte_identical_to_compiler=True,
                byte_identical_to_source=True,
            ),
        )
        modified_prov = dict(
            artifact_id=artifact_id,
            completed=True,
            executable_sha256=mod_exec,
            linkage=dict(recorded=True, inputs=[copy.deepcopy(build_input)]),
            relink=dict(
                parent_output='/tmp/replay-build',
                parent_provenance_sha256=parent_prov,
                byte_identical_to_compiler=True,
                byte_identical_to_source=False,
            ),
        )
        baseline_obs = dict(
            kind='glibc-object-source-observations-not-license-approval',
            artifact_id=artifact_id,
            executable_sha256=base_exec,
            sources=base_sources,
            objects=[
                dict(input='crt1.o', input_sha256='1' * 64, member=None, object_sha256='1' * 64,
                     sources=[start_path, 'lib/libc/glibc/csu/init.c']),
                dict(input='libc_nonshared.a', input_sha256='2' * 64, member='elf-init-2.33.o', object_sha256='3' * 64,
                     sources=['lib/libc/glibc/csu/elf-init-2.33.c']),
                dict(input='libc_nonshared.a', input_sha256='2' * 64, member='fstat-2.32.o', object_sha256='4' * 64,
                     sources=['lib/libc/glibc/io/fstat-2.32.c']),
            ],
        )
        modified_obs = dict(
            kind='glibc-object-source-observations-not-license-approval',
            artifact_id=artifact_id,
            executable_sha256=mod_exec,
            sources=mod_sources,
            objects=[
                dict(input='crt1.o', input_sha256='5' * 64, member=None, object_sha256='5' * 64,
                     sources=[start_path, 'lib/libc/glibc/csu/init.c']),
                dict(input='libc_nonshared.a', input_sha256='6' * 64, member='elf-init-2.33.o', object_sha256='7' * 64,
                     sources=['lib/libc/glibc/csu/elf-init-2.33.c']),
                dict(input='libc_nonshared.a', input_sha256='6' * 64, member='fstat-2.32.o', object_sha256='8' * 64,
                     sources=['lib/libc/glibc/io/fstat-2.32.c']),
            ],
        )
        build_sec = dict(
            scope='build', input_path='cmd/dot/CMakeFiles/dot.dir/dot.c.o', input_sha256='d' * 64,
            member=None, input_section='.text', output_section='.text', bytes=256, executable=True,
        )
        rt_sec = dict(
            scope='sdk', input_path='/linux/cache/libcompiler_rt.a', input_sha256='e' * 64,
            member='math.o', input_section='.text.math', output_section='.text', bytes=64, executable=True,
        )
        baseline_alloc = dict(
            kind='lld-allocated-input-sections-not-source-closure',
            executable_sha256=base_exec,
            sections=[
                copy.deepcopy(build_sec),
                copy.deepcopy(rt_sec),
                dict(scope='sdk', input_path='/linux/cache/crt1.o', input_sha256='1' * 64,
                     member=None, input_section='.text', output_section='.text', bytes=38, executable=True),
                dict(scope='sdk', input_path='/linux/cache/crt1.o', input_sha256='1' * 64,
                     member=None, input_section='.note.ABI-tag', output_section='.note.ABI-tag', bytes=32, executable=False),
                dict(scope='sdk', input_path='/linux/cache/libc_nonshared.a', input_sha256='2' * 64,
                     member='/linux/cache/o/elf-init-2.33.o', input_section='.text', output_section='.text', bytes=95, executable=True),
                dict(scope='sdk', input_path='/linux/cache/libc_nonshared.a', input_sha256='2' * 64,
                     member='/linux/cache/o/fstat-2.32.o', input_section='.text', output_section='.text', bytes=16, executable=True),
            ],
        )
        modified_alloc = dict(
            kind='lld-allocated-input-sections-not-source-closure',
            executable_sha256=mod_exec,
            sections=[
                copy.deepcopy(build_sec),
                copy.deepcopy(rt_sec),
                dict(scope='sdk', input_path='/linux/cache/crt1.o', input_sha256='5' * 64,
                     member=None, input_section='.text', output_section='.text', bytes=42, executable=True),
                dict(scope='sdk', input_path='/linux/cache/crt1.o', input_sha256='5' * 64,
                     member=None, input_section='.note.ABI-tag', output_section='.note.ABI-tag', bytes=32, executable=False),
                dict(scope='sdk', input_path='/linux/cache/crt1.o', input_sha256='5' * 64,
                     member=None, input_section='.rodata', output_section='.rodata', bytes=4, executable=False),
                dict(scope='sdk', input_path='/linux/cache/libc_nonshared.a', input_sha256='6' * 64,
                     member='/linux/cache/o/elf-init-2.33.o', input_section='.text', output_section='.text', bytes=103, executable=True),
                dict(scope='sdk', input_path='/linux/cache/libc_nonshared.a', input_sha256='6' * 64,
                     member='/linux/cache/o/fstat-2.32.o', input_section='.text', output_section='.text', bytes=20, executable=True),
            ],
        )
        syscall_report = dict(
            kind='linux-native-syscall-observation',
            passed=True,
            qualified=False,
            environment_kind='native',
            arch=arch,
            control=dict(detected=True),
            corpus=dict(
                engine_sha256=mod_exec,
                cases=13,
                dot_executions=14,
                network_syscalls={},
                trace_sha256='f' * 64,
                report_sha256='9' * 64,
            ),
        )
        corpus_report = dict(
            passed=True,
            engine_sha256=mod_exec,
            cases=[dict(passed=True, reference_expected=(i < 6)) for i in range(13)],
            relocation=dict(passed=True, unicode_directory=True),
        )
        return (
            baseline_prov,
            baseline_obs,
            baseline_alloc,
            modified_prov,
            modified_obs,
            modified_alloc,
            edit_receipt,
            syscall_report,
            corpus_report,
        )

    def test_combined_object_does_not_transfer_exception_or_prove_source_retention(self):
        observations, allocations = self.fixture()
        result = tool().allocated_source_observations(observations, allocations)
        self.assertEqual(result['objects'][0]['allocated_bytes'], 44)
        units = result['objects'][0]['compilation_units']
        self.assertEqual([unit['linking_exception_phrase_present'] for unit in units], [True, False])
        self.assertEqual(result['other_allocated_sdk_inputs'], ['libcompiler_rt.a'])
        for field in ('approved', 'qualified', 'source_to_binary_complete'):
            self.assertFalse(result[field])
        self.assertFalse(result['objects'][0]['per_source_retention_established'])

    def test_same_names_cannot_join_different_executable_or_input_hashes(self):
        observations, original = self.fixture()
        for change in ('executable', 'archive', 'direct', 'member'):
            allocations = copy.deepcopy(original)
            if change == 'executable':
                allocations['executable_sha256'] = '9' * 64
            elif change == 'member':
                allocations['sections'][1]['member'] = '/linux/cache/other.o'
            else:
                allocations['sections'][1 if change == 'archive' else 0]['input_sha256'] = '9' * 64
            with self.subTest(change=change), self.assertRaises(ValueError):
                tool().allocated_source_observations(observations, allocations)

    def test_ambiguous_objects_or_changed_notice_are_rejected(self):
        original, allocations = self.fixture()
        for change in ('object', 'source', 'notice', 'direct_hash'):
            observations = copy.deepcopy(original)
            if change == 'object':
                observations['objects'].append(observations['objects'][1])
            elif change == 'source':
                observations['sources'].append(observations['sources'][0])
            elif change == 'notice':
                observations['sources'][0]['leading_comments'] += 'changed'
            else:
                observations['objects'][0]['object_sha256'] = '9' * 64
            with self.subTest(change=change), self.assertRaises(ValueError):
                tool().allocated_source_observations(observations, allocations)

    def test_debug_only_unit_is_not_omitted_from_combined_object_review(self):
        observations, allocations = self.fixture()
        # No allocated .rodata is present, but that alone cannot discard init.c.
        result = tool().allocated_source_observations(observations, allocations)
        self.assertEqual([unit['path'] for unit in result['objects'][0]['compilation_units']],
                         ['start.S', 'init.c'])

    def test_empty_or_invalid_allocations_cannot_generate_positive_observation(self):
        observations, original = self.fixture()
        for size in (0, -1, True):
            allocations = copy.deepcopy(original)
            allocations['sections'][0]['bytes'] = size
            with self.subTest(size=size), self.assertRaises(ValueError):
                tool().allocated_source_observations(observations, allocations)
        with self.assertRaises(ValueError):
            tool().allocated_source_observations(observations, dict(original, sections=[]))

    def test_modify_sdk_updates_exact_four_glibc_sources_and_preserves_notices(self):
        verifier = relink_verifier()
        for arch in ('x86_64', 'aarch64'):
            with self.subTest(arch=arch), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                sdk_root = root / f'zig-{arch}-linux-0.15.2'
                cache_dir = root / 'cache'
                (cache_dir / 'o').mkdir(parents=True)
                (cache_dir / 'o/dummy').write_bytes(b'cached')
                for rel_path, before_snippet, _ in verifier.edits_for_arch(arch):
                    target = sdk_root / rel_path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(('/* License notice */\n' + before_snippet).encode('utf-8'))
                receipt_path = root / 'edits.json'
                receipt = verifier.modify_sdk(sdk_root, receipt_path, cache_dir)
                self.assertEqual(receipt['arch'], arch)
                self.assertTrue(receipt['cache_cleared'])
                self.assertFalse(cache_dir.exists())
                self.assertEqual(len(receipt['edits']), 4)
                for row in receipt['edits']:
                    self.assertNotEqual(row['before_sha256'], row['after_sha256'])
                with self.assertRaises(ValueError):
                    verifier.modify_sdk(sdk_root, root / 'second.json')
                with self.assertRaises(ValueError):
                    verifier.modify_sdk(sdk_root, receipt_path)

    def test_compare_relink_records_accepts_valid_relink_and_rejects_violations(self):
        verifier = relink_verifier()
        for arch in ('x86_64', 'aarch64'):
            with self.subTest(arch=arch):
                args = self.modified_relink_fixture(arch)
                report = verifier.compare_relink_records(*args)
                self.assertTrue(report['passed'])
                self.assertFalse(report['approved'])
                self.assertFalse(report['qualified'])
                self.assertTrue(report['graphviz_build_inputs_unchanged'])
                self.assertTrue(report['graphviz_allocated_sections_unchanged'])
                self.assertTrue(report['pinned_sdk_audit_rejected_modified_build'])
                self.assertEqual(len(report['modified_sources']), 4)
                self.assertEqual(len(report['retained_glibc_objects']), 3)

                with self.assertRaisesRegex(ValueError, 'pinned SDK audit'):
                    verifier.compare_relink_records(*args, pinned_sdk_rejected=False)

                bad_build_input = copy.deepcopy(args)
                bad_build_input[3]['linkage']['inputs'][0]['sha256'] = '9' * 64
                with self.assertRaisesRegex(ValueError, 'Graphviz build-scope linker inputs'):
                    verifier.compare_relink_records(*bad_build_input)

                bad_build_sec = copy.deepcopy(args)
                bad_build_sec[5]['sections'][0]['bytes'] += 4
                with self.assertRaisesRegex(ValueError, 'Graphviz build-scope allocated sections'):
                    verifier.compare_relink_records(*bad_build_sec)

                no_rodata = copy.deepcopy(args)
                no_rodata[5]['sections'] = [
                    s for s in no_rodata[5]['sections'] if s['input_section'] != '.rodata'
                ]
                with self.assertRaisesRegex(ValueError, 'retain allocated .rodata'):
                    verifier.compare_relink_records(*no_rodata)

                bad_syscall = copy.deepcopy(args)
                bad_syscall[7]['corpus']['network_syscalls'] = {'socket': 1}
                with self.assertRaisesRegex(ValueError, 'native syscall observation'):
                    verifier.compare_relink_records(*bad_syscall)

                bad_corpus = copy.deepcopy(args)
                bad_corpus[8]['relocation']['passed'] = False
                with self.assertRaisesRegex(ValueError, 'public corpus or Unicode relocation'):
                    verifier.compare_relink_records(*bad_corpus)

    def test_collect_modified_observations_enforces_pinned_rejection_and_edit_receipt(self):
        verifier = relink_verifier()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            sdk_root = root / 'zig-x86_64-linux-0.15.2'
            linked = root / 'modified-linked'
            linked.mkdir()
            sdk_archive = root / 'zig.tar.xz'
            sdk_archive.write_bytes(b'archive')
            pinned_files = {}
            for rel_path, before_snippet, _ in verifier.edits_for_arch('x86_64'):
                target = sdk_root / rel_path
                target.parent.mkdir(parents=True, exist_ok=True)
                raw = ('/* Notice */\n' + before_snippet).encode('utf-8')
                target.write_bytes(raw)
                pinned_files[rel_path] = raw
            abi_path = 'lib/libc/glibc/csu/abi-note.S'
            abi_raw = b'/* ABI */\n'
            (sdk_root / abi_path).parent.mkdir(parents=True, exist_ok=True)
            (sdk_root / abi_path).write_bytes(abi_raw)
            pinned_files[abi_path] = abi_raw
            receipt = verifier.modify_sdk(sdk_root, root / 'edits.json')

            with patch.object(verifier.AUDIT, 'collect', return_value=dict(sources=[])):
                with self.assertRaisesRegex(ValueError, 'not rejected by pinned SDK audit'):
                    verifier.collect_modified_observations(linked, sdk_root, sdk_archive, receipt)

            calls = []

            def fake_collect(build_dir, sdk_dir, archive_path):
                calls.append(len(calls))
                if len(calls) == 1:
                    raise ValueError('glibc source differs from pinned SDK')
                verified = verifier.AUDIT.notices.archive_files(archive_path, sdk_dir.name, set(pinned_files))
                return dict(kind='glibc-object-source-observations-not-license-approval', sources=list(verified))

            with patch.object(verifier.AUDIT, 'collect', side_effect=fake_collect), \
                 patch.object(verifier.AUDIT.notices, 'archive_files', return_value=dict(pinned_files)):
                observed = verifier.collect_modified_observations(linked, sdk_root, sdk_archive, receipt)
                self.assertTrue(observed['modified_sdk_edit_receipt_verified'])

            # Tampering with an edited file after receipt creation must fail verification.
            tampered_target = sdk_root / 'lib/libc/glibc/csu/init.c'
            tampered_target.write_bytes(tampered_target.read_bytes() + b'\n')
            calls.clear()
            with patch.object(verifier.AUDIT, 'collect', side_effect=fake_collect), \
                 patch.object(verifier.AUDIT.notices, 'archive_files', return_value=dict(pinned_files)):
                with self.assertRaisesRegex(ValueError, 'does not match recorded edit receipt'):
                    verifier.collect_modified_observations(linked, sdk_root, sdk_archive, receipt)

