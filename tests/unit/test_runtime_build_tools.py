import importlib.util
from pathlib import Path
import tempfile
import unittest
import hashlib
import json
import os
import shlex
from unittest.mock import patch
from common import ROOT


def tool(name):
    spec=importlib.util.spec_from_file_location(name.replace('-','_'),ROOT/'tools/runtime'/f'{name}.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BuildToolTests(unittest.TestCase):
    def test_native_network_trace_handles_children_and_split_exec(self):
        observer = tool('observe-linux-network')
        trace = ('execve("/usr/bin/python3", ["python3"], 0x0) = 0\n'
                 '[pid 42] execve("/tmp/engine/dot", ["dot", "-V"], 0x0 <unfinished ...>\n'
                 '[pid 42] <... execve resumed>) = 0\n'
                 '--- SIGCHLD {si_signo=SIGCHLD} ---\n')
        result = observer.parse_trace(trace)
        self.assertEqual(result['network_syscalls'], {})
        self.assertEqual(result['successful_executables'], ['/usr/bin/python3', '/tmp/engine/dot'])

    def test_native_network_trace_counts_failed_attempts_and_unix_sockets(self):
        observer = tool('observe-linux-network')
        trace = ('execve("/usr/bin/python3", [], 0x0) = 0\n'
                 '[pid 42] socket(AF_INET, SOCK_STREAM, IPPROTO_IP) = 3\n'
                 '[pid 42] connect(3, {sa_family=AF_INET}, 16) = -1 ECONNREFUSED\n'
                 '[pid 42] socket(AF_UNIX, SOCK_STREAM, 0) = 4\n')
        self.assertEqual(observer.parse_trace(trace)['network_syscalls'], {'socket': 2, 'connect': 1})

    def test_native_network_trace_refuses_missing_incomplete_or_unrecognized_output(self):
        observer = tool('observe-linux-network')
        for trace in ('', 'strace: ptrace denied\n',
                      'execve("/tmp/dot", [], 0x0 <unfinished ...>\n',
                      'execve("/tmp/dot", [], 0x0) = -1 ENOENT\n',
                      'execve("/tmp/dot", [], 0x0) = 0\ninvalid output\n'):
            with self.subTest(trace=trace), self.assertRaises(ValueError):
                observer.parse_trace(trace)

    def test_ci_source_download_rejects_tampering_and_preserves_existing_file(self):
        import io
        bootstrap = tool('prepare-linux-ci')
        lock = dict(url='https://example.invalid/pinned', size=4,
                    sha256=hashlib.sha256(b'good').hexdigest())
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'source'
            for content in (b'evil', b'good-extra', b'bad'):
                with patch.object(bootstrap.urllib.request, 'urlopen', return_value=io.BytesIO(content)):
                    with self.assertRaises(ValueError):
                        bootstrap.download(lock, target)
                self.assertFalse(target.exists())
            target.write_bytes(b'existing')
            with patch.object(bootstrap.urllib.request, 'urlopen', return_value=io.BytesIO(b'good')):
                with self.assertRaises(FileExistsError):
                    bootstrap.download(lock, target)
            self.assertEqual(target.read_bytes(), b'existing')

    def test_ci_source_download_accepts_only_exact_pinned_bytes(self):
        import io
        bootstrap = tool('prepare-linux-ci')
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'source'
            lock = dict(url='https://example.invalid/pinned', size=4,
                        sha256=hashlib.sha256(b'good').hexdigest())
            with patch.object(bootstrap.urllib.request, 'urlopen', return_value=io.BytesIO(b'good')):
                bootstrap.download(lock, target)
            self.assertEqual(target.read_bytes(), b'good')

    def test_cross_libc_build_requires_explicit_static_musl_experiment(self):
        builder=tool('build-common')
        from twine_edge_overlap.runtime_platform import HostEnvironment
        host=HostEnvironment(os='linux',arch='x86_64',libc_family='glibc')
        recipe=dict(os='linux',arch='x86_64',abi='musl',cmake=dict(CMAKE_EXE_LINKER_FLAGS='-static -static-libgcc'))
        with self.assertRaises(ValueError):builder.build_mode(host,recipe,False)
        self.assertEqual(builder.build_mode(host,recipe,True),'cpu-native-cross-libc-experiment')
        recipe['cmake']['CMAKE_EXE_LINKER_FLAGS']='-static-libgcc'
        with self.assertRaises(ValueError):builder.build_mode(host,recipe,True)

    def test_cross_libc_flag_does_not_allow_wrong_os_arch_or_translation(self):
        builder=tool('build-common')
        from twine_edge_overlap.runtime_platform import HostEnvironment
        recipe=dict(os='linux',arch='x86_64',abi='musl',cmake=dict(CMAKE_EXE_LINKER_FLAGS='-static'))
        for host in (HostEnvironment(os='windows',arch='x86_64'),
                     HostEnvironment(os='linux',arch='aarch64',libc_family='glibc'),
                     HostEnvironment(os='linux',arch='x86_64',libc_family='glibc',translated=True)):
            with self.subTest(host=host),self.assertRaises(ValueError):builder.build_mode(host,recipe,True)

    def test_static_experiment_refuses_loader_dynamic_dependencies_and_glibc(self):
        builder=tool('build-common')
        text='Elf file type is EXEC\nThere is no dynamic section in this file.\n'
        builder.confirm_static_linkage(text)
        for suffix in ('INTERP\n','(NEEDED) [libc.so.6]\n','GLIBC_2.2.5\n'):
            with self.subTest(suffix=suffix),self.assertRaises(ValueError):builder.confirm_static_linkage(text+suffix)
        with self.assertRaises(ValueError):builder.confirm_static_linkage('')

    def test_static_inspection_requires_explicit_policy_and_actual_no_dynamic_section(self):
        verifier=tool('verify-artifact')
        text='There is no dynamic section in this file.\n'
        with self.assertRaises(ValueError):verifier.linux_dependencies(text,[],'1.2.5')
        self.assertEqual(verifier.linux_dependencies(text,[],'1.2.5',require_static=True),[])
        for bad in ('',text+'INTERP',text+'(NEEDED) [libc.so.6]',text+'GLIBC_2.2.5'):
            with self.subTest(text=bad),self.assertRaises(ValueError):
                verifier.linux_dependencies(bad,[],'1.2.5',require_static=True)

    def test_extraction_report_binds_members_to_known_archive_hashes(self):
        relinker=tool('relink-zig')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            path=root/'why.tsv'
            archive=root/'runtime.a'
            unused=root/'unused.a'
            rows='reference\textracted\tsymbol\nsource.o\t'+str(archive)+'(a.o)\tfunction\n'
            path.write_text(rows)
            linkage=dict(inputs=[dict(path=str(archive),scope='sdk',sha256='a'*64),
                                 dict(path=str(unused),scope='sdk',sha256='b'*64)])
            result=relinker.capture_extractions(path,linkage,root)
            self.assertEqual(result['row_count'],1)
            self.assertEqual(result['rows'][0]['archive_sha256'],'a'*64)
            self.assertEqual(result['rows'][0]['member'],'a.o')
            counts={i['archive_sha256']:i['extracted_member_count'] for i in result['archives']}
            self.assertEqual(counts,{'a'*64:1,'b'*64:0})

    def test_extraction_report_refuses_unknown_archives_and_malformed_data(self):
        relinker=tool('relink-zig')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            path=root/'why.tsv'
            linkage=dict(inputs=[dict(path=str(root/'known.a'),scope='sdk',sha256='a'*64)])
            for text in ('incorrect header\n','reference\textracted\tsymbol\nsource.o\tunknown.a(x.o)\tsymbol\n',
                         'reference\textracted\tsymbol\nmalformed row\n',
                         'reference\textracted\tsymbol\nsource.o\t'+str(root/'known.a')+'()\tsymbol\n'):
                path.write_text(text)
                with self.subTest(text=text),self.assertRaises(ValueError):
                    relinker.capture_extractions(path,linkage,root)

    def test_relink_command_requires_one_expected_output_and_no_response_files(self):
        relinker=tool('relink-zig')
        self.assertEqual(relinker.replace_output(['cc','-o','dot'],'dot','new'),['cc','-o','new'])
        for command in (['cc'],['cc','-o'],['cc','-o','other'],['cc','-o','dot','-o','dot']):
            with self.subTest(command=command),self.assertRaises(ValueError):
                relinker.replace_output(command,'dot','new')
        for text in ('cc @unreviewed.rsp','cc '+ 'x'*65536,'cc\0 -o dot'):
            with self.subTest(text=text[:30]),self.assertRaises(ValueError):relinker.arguments(text)

    def test_relink_reads_verbose_argv_as_data_preserving_quoted_paths(self):
        relinker=tool('relink-zig')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'object with space.o').write_bytes(b'synthetic')
            text='compiler diagnostics\nld.lld -o "reference with space" "object with space.o" --as-needed\n'
            args=relinker.lld_arguments(text,'reference with space',root)
            self.assertEqual(args,['-o','dot',str((root/'object with space.o').resolve()),
                                   '--as-needed','--dependency-file=CMakeFiles/dot.dir/link.d'])
            for bad in ('compiler only\n',text+text,'ld.lld -o other @input.rsp\n'):
                with self.subTest(text=bad),self.assertRaises(ValueError):
                    relinker.lld_arguments(bad,'reference with space',root)

    def test_relink_outside_native_linux_refuses_before_output(self):
        relinker=tool('relink-zig')
        from twine_edge_overlap.runtime_platform import HostEnvironment
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'provenance.json').write_text('{}')
            with patch.object(relinker,'detect_host',return_value=HostEnvironment(os='windows',arch='x86_64')):
                with self.assertRaises(ValueError):relinker.relink(root,root/'new',root/'zig')
            self.assertFalse((root/'new').exists())

    def test_musl_relink_requires_measured_static_source_before_output(self):
        relinker=tool('relink-zig')
        from twine_edge_overlap.runtime_platform import HostEnvironment
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'provenance.json').write_text(json.dumps(dict(completed=True,artifact_id='linux-musl-x86_64')))
            with patch.object(relinker,'detect_host',return_value=HostEnvironment(os='linux',arch='x86_64',libc_family='glibc')):
                with self.assertRaisesRegex(ValueError,'static'):relinker.relink(root,root/'new',root/'zig')
            self.assertFalse((root/'new').exists())

    def test_relink_rejects_different_lld_bytes_without_replacing_source(self):
        relinker=tool('relink-zig')
        from twine_edge_overlap.runtime_platform import HostEnvironment
        from twine_edge_overlap.engines.process import ProcessResult
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            source=root/'source'
            (source/'candidate/bin').mkdir(parents=True)
            original=source/'candidate/bin/dot'
            original.write_bytes(b'synthetic original')
            compiler=root/'cc'
            compiler.write_bytes(b'synthetic compiler, never executed')
            zig=root/'zig'
            zig.write_bytes(b'synthetic zig, never executed')
            record=dict(completed=True,artifact_id='linux-glibc-x86_64',
                        executable_sha256=relinker.builder.digest(original),
                        sdk=dict(cxx_compiler=dict(path=str(compiler),sha256=relinker.builder.digest(compiler)),
                                 facts=dict(zig_sha256=relinker.builder.digest(zig))))
            (source/'provenance.json').write_text(json.dumps(record))
            metadata=source/'build/cmd/dot/CMakeFiles/dot.dir'
            metadata.mkdir(parents=True)
            (metadata/'link.txt').write_text(shlex.join([str(compiler),'-o','dot']))
            def runner(argv,**kwargs):
                cwd=Path(kwargs['cwd'])
                if argv[0]==str(compiler):
                    reference=Path(argv[argv.index('-o')+1])
                    reference.write_bytes(b'synthetic compiler reference')
                    return ProcessResult(0,b'',(shlex.join(['ld.lld','-o',str(reference)])+'\n').encode())
                (cwd/'dot').write_bytes(b'different synthetic LLD bytes')
                return ProcessResult(0,b'',b'')
            with patch.object(relinker,'detect_host',return_value=HostEnvironment(os='linux',arch='x86_64',libc_family='glibc')), \
                 patch.object(relinker,'run_bounded',side_effect=runner):
                with self.assertRaisesRegex(ValueError,'differs'):relinker.relink(source,root/'new',zig)
            self.assertEqual(original.read_bytes(),b'synthetic original')
            self.assertFalse((root/'new/candidate').exists())
            self.assertFalse((root/'new/provenance.json').exists())

    def test_link_dependencies_are_data_with_escaped_spaces_and_literal_dollars(self):
        builder=tool('build-common')
        text='dot: one\\ file.o \\\n lib$$name.a\n\none\\ file.o:\n'
        self.assertEqual(builder.parse_link_dependencies(text),['one file.o','lib$name.a'])
        for bad in ('other: x.o\n','dot: $(shell touch /never)\n','dot: broken\\','dot:\n'):
            with self.subTest(text=bad),self.assertRaises(ValueError):builder.parse_link_dependencies(bad)

    def test_linkage_capture_hashes_actual_inputs_and_preserves_references(self):
        builder=tool('build-common')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            build=root/'build'
            target=build/'cmd/dot/CMakeFiles/dot.dir'
            target.mkdir(parents=True)
            (target/'dot.c.o').write_bytes(b'synthetic object')
            binary=build/'cmd/dot/dot'
            binary.write_bytes(b'synthetic executable')
            (target/'link.txt').write_text('This is data, never a command to execute.')
            (target/'link.d').write_text('dot: CMakeFiles/dot.dir/dot.c.o CMakeFiles/dot.dir/dot.c.o\n')
            result=builder.capture_linkage(build,binary)
            self.assertTrue(result['recorded'])
            self.assertEqual(len(result['inputs']),1)
            self.assertEqual(result['inputs'][0]['references'],2)
            self.assertEqual(result['inputs'][0]['sha256'],hashlib.sha256(b'synthetic object').hexdigest())
            self.assertEqual(result['executable_sha256'],hashlib.sha256(binary.read_bytes()).hexdigest())
            (target/'link.d').write_text('dot: missing.a\n')
            with self.assertRaises(FileNotFoundError):builder.capture_linkage(build,binary)

    def test_missing_linker_metadata_is_explicitly_pending(self):
        builder=tool('build-common')
        with tempfile.TemporaryDirectory() as folder:
            result=builder.capture_linkage(Path(folder),Path(folder)/'absent')
            self.assertFalse(result['recorded'])
            self.assertIn('pending_reason',result)

    def test_separate_link_stage_retains_source_build_scope(self):
        builder=tool('build-common')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            build=root/'source build'
            build.mkdir()
            obj=build/'source.o'
            obj.write_bytes(b'synthetic source object')
            directory=root/'new link'
            metadata=directory/'CMakeFiles/dot.dir'
            metadata.mkdir(parents=True)
            binary=directory/'dot'
            binary.write_bytes(b'synthetic executable')
            (metadata/'link.txt').write_text('data only')
            # Relative path keeps the fixture portable to Windows drives.
            (metadata/'link.d').write_text('dot: ../source\\ build/source.o\n')
            result=builder.capture_linkage(build,binary,link_directory=directory)
            self.assertEqual(result['inputs'][0]['scope'],'build')
            self.assertEqual(result['inputs'][0]['path'],'source.o')

    def test_linux_audit_cannot_omit_compiler_archive_coverage(self):
        verifier=tool('verify-artifact')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            provenance=root/'provenance.json'
            provenance.write_text('{}')
            notice=root/'COPYING'
            notice.write_bytes(b'synthetic notice')
            source=dict(url='https://example.invalid/synthetic-source',sha256='a'*64)
            component=dict(name='synthetic-component',license_expression='synthetic-unit-only',
                source_url=source['url'],source_sha256=source['sha256'],notice_path='COPYING',notice_sha256=verifier.digest(notice))
            audit=dict(approved=True,reviewer='synthetic-unit-reviewer',provenance_sha256=verifier.digest(provenance),
                       source_references=[source['url']],components=[component])
            record=dict(source=source,executable_sha256='b'*64,linkage=dict(recorded=True,
                executable_sha256='b'*64,link_command_sha256='c'*64,dependency_file_sha256='d'*64,
                inputs=[dict(path='libgcc.a',scope='sdk',sha256='e'*64,size=10,references=1)]))
            with self.assertRaises(ValueError):verifier.validate_audit(audit,provenance,root,record,require_linkage=True)
            component['link_input_sha256']=['e'*64]
            verifier.validate_audit(audit,provenance,root,record,require_linkage=True)
            record['linkage']['recorded']=False
            with self.assertRaises(ValueError):verifier.validate_audit(audit,provenance,root,record,require_linkage=True)

    def test_inventory_creation_requires_matching_native_host_before_writing(self):
        verifier=tool('verify-artifact')
        from twine_edge_overlap.runtime_platform import HostEnvironment
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            provenance=root/'provenance.json'
            provenance.write_text(json.dumps(dict(completed=True,recipe=dict(os='linux',arch='x86_64',abi='glibc'))))
            with patch.object(verifier,'detect_host',return_value=HostEnvironment(os='windows',arch='x86_64')):
                with self.assertRaises(ValueError):verifier.create_inventory(root/'absent',provenance,minimum_libc='2.27')

    @unittest.skipIf(os.name=='nt','Inventory requires native POSIX modes; exercised on existing WSL')
    def test_local_inventory_needs_no_url_and_binds_exact_provenance_and_files(self):
        verifier=tool('verify-artifact')
        from twine_edge_overlap.runtime_platform import HostEnvironment
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            candidate=root/'candidate'
            (candidate/'bin').mkdir(parents=True)
            binary=candidate/'bin/dot'
            binary.write_bytes(b'\x7fELF\x02\x01'+b'\0'*12+b'\x3e\0')
            binary.chmod(0o755)
            (candidate/'COPYING').write_bytes(b'synthetic notice')
            (candidate/'COPYING').chmod(0o644)
            record=dict(completed=True,artifact_id='linux-glibc-x86_64',
                        recipe=dict(id='linux-glibc-x86_64',os='linux',arch='x86_64',abi='glibc'),
                        recipe_sha256='a'*64,sdk=dict(environment_digest='b'*64),
                        executable_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                        source=dict(url='https://example.invalid/synthetic-source',sha256='c'*64))
            record['linkage']=dict(recorded=True,executable_sha256=record['executable_sha256'],
                link_command_sha256='d'*64,dependency_file_sha256='e'*64,
                inputs=[dict(path='synthetic.o',scope='build',sha256='f'*64)])
            provenance=root/'provenance.json'
            provenance.write_text(json.dumps(record))
            with patch.object(verifier,'detect_host',return_value=HostEnvironment(os='linux',arch='x86_64')):
                inventory=verifier.create_inventory(candidate,provenance,minimum_libc='2.27')
            self.assertNotIn('url',inventory)
            self.assertEqual(inventory['qualification'],'inventory-only-not-qualified')
            path=root/'inventory.json'
            path.write_text(json.dumps(inventory))
            loaded=verifier.load_inventory(path,provenance)
            self.assertEqual(loaded['files'],inventory['files'])
            audit=root/'audit.json'
            notice=candidate/'COPYING'
            audit.write_text(json.dumps(dict(approved=True,reviewer='synthetic-unit-reviewer',
                provenance_sha256=verifier.digest(provenance),source_references=[record['source']['url']],
                system_libraries=['libc.so.6'],components=[dict(name='synthetic-unit-component',
                    license_expression='synthetic-unit-only',source_url=record['source']['url'],
                    source_sha256=record['source']['sha256'],notice_path='COPYING',
                    notice_sha256=verifier.digest(notice),link_input_sha256=['f'*64])])))
            from twine_edge_overlap.engines.process import ProcessResult
            calls=[]
            def runner(argv,**kwargs):
                calls.append(argv)
                return ProcessResult(0,b'dot graphviz 16.1.0' if '-V' in argv else
                                     b'(NEEDED) Shared library: [libc.so.6]\nName: GLIBC_2.27\n',b'')
            with patch.object(verifier,'detect_host',return_value=HostEnvironment(os='linux',arch='x86_64')), \
                 patch.object(verifier.shutil,'which',return_value='/usr/bin/readelf'), \
                 patch.object(verifier,'run_bounded',side_effect=runner):
                result=verifier.inspect(candidate,None,provenance,audit,inventory=path)
                self.assertTrue(result['inventory_verified'])
                self.assertTrue(result['artifact_identity'].startswith('local-inventory-'))
                self.assertIn('-V',calls[-1])
                inventory['minimum_libc']='2.26'
                path.write_text(json.dumps(inventory))
                with self.assertRaisesRegex(ValueError,'baseline'):
                    verifier.inspect(candidate,None,provenance,audit,inventory=path)
                self.assertNotIn('-V',calls[-1])
                inventory['minimum_libc']='2.27'
                path.write_text(json.dumps(inventory))
            provenance.write_text(json.dumps(dict(record,kernel='changed')))
            with self.assertRaises(ValueError):verifier.load_inventory(path,provenance)
            provenance.write_text(json.dumps(record))
            inventory['files'][0]['path']='../escape'
            path.write_text(json.dumps(inventory))
            with self.assertRaises(ValueError):verifier.load_inventory(path,provenance)

    @unittest.skipIf(os.name=='nt','Native POSIX modes and symlinks')
    def test_inventory_rejects_links_privileged_modes_and_changed_executable(self):
        verifier=tool('verify-artifact')
        from twine_edge_overlap.runtime_platform import HostEnvironment
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            candidate=root/'candidate'
            (candidate/'bin').mkdir(parents=True)
            binary=candidate/'bin/dot'
            binary.write_bytes(b'synthetic')
            binary.chmod(0o755)
            record=dict(completed=True,artifact_id='linux-glibc-x86_64',
                        recipe=dict(id='linux-glibc-x86_64',os='linux',arch='x86_64',abi='glibc'),
                        recipe_sha256='a'*64,sdk=dict(environment_digest='b'*64),
                        executable_sha256=hashlib.sha256(binary.read_bytes()).hexdigest())
            provenance=root/'provenance.json'
            provenance.write_text(json.dumps(record))
            with patch.object(verifier,'detect_host',return_value=HostEnvironment(os='linux',arch='x86_64')):
                candidate.chmod(0o777)
                with self.assertRaises(ValueError):verifier.create_inventory(candidate,provenance,minimum_libc='2.27')
                candidate.chmod(0o755)
                link=candidate/'escape'
                link.symlink_to(provenance)
                with self.assertRaises(ValueError):verifier.create_inventory(candidate,provenance,minimum_libc='2.27')
                link.unlink()
                binary.chmod(0o4755)
                with self.assertRaises(ValueError):verifier.create_inventory(candidate,provenance,minimum_libc='2.27')
                binary.chmod(0o755)
                binary.write_bytes(b'changed')
                with self.assertRaises(ValueError):verifier.create_inventory(candidate,provenance,minimum_libc='2.27')

    def test_audit_is_bound_to_provenance_sources_and_notices(self):
        verifier=tool('verify-artifact')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            provenance=root/'provenance.json'
            provenance.write_text('{}')
            notice=root/'COPYING'
            notice.write_bytes(b'reviewed notice')
            source=dict(url='https://example.invalid/pinned-source',sha256='a'*64)
            audit=dict(approved=True,reviewer='test-reviewer',provenance_sha256=verifier.digest(provenance),source_references=[source['url']],components=[dict(name='graphviz',license_expression='EPL-2.0',source_url=source['url'],source_sha256=source['sha256'],notice_path='COPYING',notice_sha256=verifier.digest(notice))])
            verifier.validate_audit(audit,provenance,root,dict(source=source))
            notice.write_bytes(b'changed')
            with self.assertRaises(ValueError): verifier.validate_audit(audit,provenance,root,dict(source=source))
            with self.assertRaises(ValueError): verifier.validate_audit(dict(audit,provenance_sha256='f'*64),provenance,root,dict(source=source))

    def test_elf_machine_must_match_manifest_even_if_execution_is_emulated(self):
        verifier=tool('verify-artifact')
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'object'
            path.write_bytes(b'\x7fELF\x02\x01'+b'\0'*12+b'\x3e\0')
            verifier.elf_architecture(path,'x86_64')
            with self.assertRaises(ValueError): verifier.elf_architecture(path,'aarch64')
            path.write_bytes(b'\xcf\xfa\xed\xfe\x0c\0\0\x01')
            verifier.macho_architecture(path,'aarch64')
            with self.assertRaises(ValueError): verifier.macho_architecture(path,'x86_64')

    def test_unpinned_source_is_rejected_before_extraction_or_build(self):
        builder=tool('build-common')
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'untrusted.tar.gz'
            source.write_bytes(b'not pinned source')
            output=Path(folder)/'output'
            with self.assertRaises(ValueError): builder.plan('linux-glibc-x86_64',source,output)
            self.assertFalse(output.exists())

    def test_baseline_and_dependency_closure_cannot_be_hidden(self):
        verifier=tool('verify-artifact')
        observed='(NEEDED) Shared library: [libc.so.6]\nName: GLIBC_2.38\n'
        with self.assertRaises(ValueError): verifier.linux_dependencies(observed,['libc.so.6'],'2.27')
        with self.assertRaises(ValueError): verifier.linux_dependencies(observed,['libm.so.6'],'2.43')
        self.assertEqual(verifier.linux_dependencies(observed,['libc.so.6'],'2.43'),['libc.so.6'])
        with self.assertRaises(ValueError): verifier.linux_dependencies(observed+'(RUNPATH) Library runpath: [/build/private]\n',['libc.so.6'],'2.43')
        with self.assertRaises(ValueError): verifier.linux_dependencies(observed+'(RUNPATH) Library runpath: [::::]\n',['libc.so.6'],'2.43')

    def test_darwin_system_dependencies_need_explicit_approval(self):
        verifier=tool('verify-artifact')
        text='dot:\n\t/usr/lib/libSystem.B.dylib (compatibility version 1.0.0)\n'
        self.assertEqual(verifier.darwin_dependencies(text,['/usr/lib/libSystem.B.dylib']),['/usr/lib/libSystem.B.dylib'])
        with self.assertRaises(ValueError): verifier.darwin_dependencies(text,[])
