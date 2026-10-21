import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
import zipfile
from common import ROOT


def tool():
    spec = importlib.util.spec_from_file_location('built_packages', ROOT / 'tools/validation/check-built-packages.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BuiltPackagesTests(unittest.TestCase):
    def test_cache_notice_result_requires_exact_before_after_bytes_and_offline_reuse(self):
        validate=tool().validate_cache_notice_result
        fixture=dict(engine_sha256='a'*64,provenance_sha256='b'*64)
        expected={'third-party-notices/license.txt':'c'*64}
        report=dict(passed=True,qualified=False,**fixture,before=expected,after=expected,
            offline_acquisition_calls=0,initial_acquisition_calls=1,same_generation=True,
            corruption_rejected=True,restored_snapshot_matches=True,modes_checked=True)
        validate(report,fixture,expected)
        for key,value in [('after',{}),('before',{}),('offline_acquisition_calls',1),
                ('same_generation',False),('corruption_rejected',False),('modes_checked',False)]:
            changed=copy.deepcopy(report);changed[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate(changed,fixture,expected)

    def test_process_recovery_requires_native_exits_lock_release_and_shared_generation(self):
        validate = tool().validate_process_recovery
        cases = [dict(case='known', known_resolvable=True)]
        flags = dict(passed=True, exitcode=77, lock_reacquired=True, orphan_untouched=True,
            old_handle_usable=True, offline_references=1,
            cases=[dict(case='known', after=[0, 0, 0])])
        rows = {stage: dict(copy.deepcopy(flags), selection='new' if stage=='after_select' else 'previous')
                for stage in ('during_download', 'before_select', 'after_select')}
        rows['concurrent_first_use'] = dict(copy.deepcopy(flags), acquisition_calls=1,
            same_generation=True, workers=2, workers_ready=2, start_barrier=True)
        report = dict(passed=True, real_engine=True, scenarios=rows)
        validate(report, cases)
        for mutation in ('missing', 'exit', 'lock', 'selector', 'orphan', 'network', 'generation', 'barrier', 'reference'):
            changed = copy.deepcopy(report)
            changed_rows = changed['scenarios']
            if mutation == 'missing': del changed_rows['during_download']
            elif mutation == 'exit': changed_rows['during_download']['exitcode'] = 0
            elif mutation == 'lock': changed_rows['before_select']['lock_reacquired'] = False
            elif mutation == 'selector': changed_rows['after_select']['selection'] = 'previous'
            elif mutation == 'orphan': changed_rows['during_download']['orphan_untouched'] = False
            elif mutation == 'network': changed_rows['concurrent_first_use']['acquisition_calls'] = 2
            elif mutation == 'generation': changed_rows['concurrent_first_use']['same_generation'] = False
            elif mutation == 'barrier': changed_rows['concurrent_first_use']['workers_ready'] = 1
            else: changed_rows['after_select']['cases'] = []
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                validate(changed, cases)

    def test_failed_repair_receipts_require_every_fault_and_offline_reference(self):
        validate = tool().validate_recovery_result
        cases = [dict(case='known', known_resolvable=True)]
        flags = dict(selected_generation_preserved=True, previous_handle_usable=True,
            offline_acquisition_calls=0, failed_repair_acquisition_calls=1,
            references=[dict(case='known', after=[0, 0, 0], original_preserved=True,
                semantic_preserved=True)])
        rows = {name: copy.deepcopy(flags) for name in
            ('transfer', 'disk-space', 'corrupt-archive', 'execution-denied')}
        rows['execution-denied']['real_execution_denial'] = True
        validate(rows, cases)
        for mutation in ('missing', 'selected', 'network', 'reference', 'geometry', 'denial'):
            changed = copy.deepcopy(rows)
            if mutation == 'missing': del changed['transfer']
            elif mutation == 'selected': changed['transfer']['selected_generation_preserved'] = False
            elif mutation == 'network': changed['transfer']['offline_acquisition_calls'] = 1
            elif mutation == 'reference': changed['transfer']['references'] = []
            elif mutation == 'geometry': changed['transfer']['references'][0]['after'] = [1, 0, 0]
            else: changed['execution-denied']['real_execution_denial'] = False
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                validate(changed, cases)

    def test_private_engine_stage_binds_id_archive_inventory_and_provenance_before_copy(self):
        module = tool()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            artifact = root / 'download'
            artifact.mkdir()
            sha = lambda raw: hashlib.sha256(raw).hexdigest()
            provenance = json.dumps(dict(completed=True, artifact_id='linux-glibc-x86_64',
                executable_sha256='f' * 64)).encode()
            inventory = json.dumps(dict(provenance_sha256=sha(provenance), files=[])).encode()
            archive = b'controlled private archive'
            candidate = json.dumps(dict(artifact_id='linux-glibc-x86_64', qualified=False,
                archive_sha256=sha(archive), archive_bytes=len(archive),
                inventory_sha256=sha(inventory), provenance_sha256=sha(provenance))).encode()
            for name, raw in [('candidate.json', candidate), ('candidate.zip', archive),
                              ('inventory.json', inventory), ('provenance.json', provenance)]:
                (artifact / name).write_bytes(raw)
            result = module.prepare_engine_fixture(artifact, root / 'staged', 'linux-glibc-x86_64')
            self.assertEqual(result['engine_sha256'], 'f' * 64)
            self.assertEqual((root / 'staged/candidate.zip').read_bytes(), archive)
            with self.assertRaises(ValueError):
                module.prepare_engine_fixture(artifact, root / 'wrong-id', 'linux-glibc-aarch64')
            self.assertFalse((root / 'wrong-id').exists())
            (artifact / 'candidate.zip').write_bytes(b'changed bytes')
            with self.assertRaises(ValueError):
                module.prepare_engine_fixture(artifact, root / 'changed', 'linux-glibc-x86_64')
            self.assertFalse((root / 'changed').exists())

    def engine_result(self):
        fixture = dict(engine_sha256='a' * 64, provenance_sha256='b' * 64)
        flags = dict(acquisition_calls=1, offline_acquisition_calls=0, real_engine=True,
            fixture_transport=True, healthy_generation_reused=True, final_destination_probe=True,
            probe_before_ready=True, external_unicode_paths=True, executable_mode=0o755, generation_mode=0o700,
            native_inspection=dict(security_settings_unchanged=True))
        cases = [dict(case='known', known_resolvable=True), dict(case='other', known_resolvable=False)]
        report = dict(passed=True, qualified=False, **fixture,
            observations=dict(automatic=copy.deepcopy(flags), explicit=copy.deepcopy(flags)),
            cases=[dict(case='known', before=[1, 2, 3], after=[0, 0, 0]),
                   dict(case='other', before=[1, 2, 3], after=[1, 2, 3])],
            security_before=dict(gatekeeper='enabled'), security_after=dict(gatekeeper='enabled'))
        return fixture, cases, report

    def test_engine_result_requires_real_first_use_and_complete_offline_corpus(self):
        fixture, cases, report = self.engine_result()
        validate = tool().validate_engine_result
        validate(report, fixture, cases, 'linux')
        for mutation in ('hash', 'skip', 'acquisition', 'mode', 'duplicate', 'regression', 'known', 'nan'):
            changed = copy.deepcopy(report)
            if mutation == 'hash': changed['engine_sha256'] = 'c' * 64
            elif mutation == 'skip': del changed['observations']['automatic']
            elif mutation == 'acquisition': changed['observations']['explicit']['offline_acquisition_calls'] = 1
            elif mutation == 'mode': changed['observations']['explicit']['executable_mode'] = 0o644
            elif mutation == 'duplicate': changed['cases'].append(changed['cases'][0])
            elif mutation == 'regression': changed['cases'][1]['after'][0] = 2
            elif mutation == 'known': changed['cases'][0]['after'][0] = 1
            else: changed['cases'][1]['after'][0] = float('nan')
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                validate(changed, fixture, cases, 'linux')

    def test_mac_engine_result_does_not_treat_missing_or_changed_protections_as_acceptance(self):
        fixture, cases, report = self.engine_result()
        validate = tool().validate_engine_result
        validate(report, fixture, cases, 'darwin')
        for value in (None, dict(gatekeeper='disabled')):
            changed = copy.deepcopy(report)
            changed['security_after'] = value
            with self.assertRaises(ValueError):
                validate(changed, fixture, cases, 'darwin')

    def fixture(self, root, omit=None, change=None, unsafe=False):
        files = {'src/twine_edge_overlap/__init__.py': b'',
                 'src/twine_edge_overlap/runtime-catalog.json': b'{"artifacts":[]}',
                 'src/twine_edge_overlap/third_party/graphviz-16.1.0/NOTICE.txt': b'upstream notice',
                 'LICENSE': b'project license', 'NOTICE': b'project notice'}
        for name, raw in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        wheel = root / 'app.whl'
        with zipfile.ZipFile(wheel, 'w') as archive:
            for name, raw in files.items():
                if name == omit:
                    continue
                path = name.removeprefix('src/') if name.startswith('src/') else 'app.dist-info/licenses/' + name
                archive.writestr(path, b'changed' if name == change else raw)
        sdist = root / 'app.tar.gz'
        with tarfile.open(sdist, 'w:gz') as archive:
            for name, raw in files.items():
                info = tarfile.TarInfo('app/' + name)
                info.size = len(raw)
                archive.addfile(info, io.BytesIO(raw))
            if unsafe:
                info = tarfile.TarInfo('app/link')
                info.type = tarfile.SYMTYPE
                info.linkname = '/outside'
                archive.addfile(info)
        return wheel, sdist

    def test_current_archives_bind_sources_data_and_both_project_notices(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            wheel, sdist = self.fixture(root)
            inventory = tool().package_inventory(wheel, sdist, root)
            self.assertEqual(len(inventory['files']), 3)
            self.assertEqual(set(inventory['licenses']), {'LICENSE', 'NOTICE'})

    def test_missing_metadata_notice_or_changed_source_cannot_pass_inventory(self):
        for options in ({'omit': 'src/twine_edge_overlap/runtime-catalog.json'},
                        {'omit': 'src/twine_edge_overlap/third_party/graphviz-16.1.0/NOTICE.txt'},
                        {'omit': 'LICENSE'}, {'change': 'src/twine_edge_overlap/__init__.py'},
                        {'unsafe': True}):
            with self.subTest(options=options), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                wheel, sdist = self.fixture(root, **options)
                with self.assertRaises(ValueError):
                    tool().package_inventory(wheel, sdist, root)

    def test_installed_facts_reject_drift_wrong_archive_checkout_import_and_global_tools(self):
        with tempfile.TemporaryDirectory() as folder:
            environment = Path(folder) / 'venv'
            inventory = dict(files={'twine_edge_overlap/__init__.py': 'a'}, licenses={'LICENSE': 'b'})
            facts = dict(**inventory, package_path=str(environment / 'lib/twine_edge_overlap/__init__.py'),
                git_available=False, graphviz_available=False,
                direct_url=dict(archive_info=dict(hashes=dict(sha256='c'))))
            checker = tool().validate_installation
            checker(facts, inventory, environment, 'c')
            for field, value in [('files', {}), ('licenses', {}), ('git_available', True),
                                 ('graphviz_available', True), ('direct_url', {}),
                                 ('package_path', str(environment / '../checkout/__init__.py')),
                                 ('package_path', str(ROOT / 'src/twine_edge_overlap/__init__.py'))]:
                changed = copy.deepcopy(facts)
                changed[field] = value
                with self.subTest(field=field), self.assertRaises(ValueError):
                    checker(changed, inventory, environment, 'c')
