import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from common import ROOT
from twine_edge_overlap import runtime
from twine_edge_overlap.errors import DependencyError
from runtime_support import synthetic_artifact, synthetic_runner, ControlledTransport, isolated_cache, blocked_network


class ManifestTests(unittest.TestCase):
    def test_file_ancestor_collisions_and_notice_root_are_rejected_before_acquisition(self):
        original=runtime.load_manifest().data
        cases=[]
        # Check both ordering and case-insensitive hierarchy comparisons.
        for prepend in (False,True):
            data=copy.deepcopy(original)
            entry=copy.deepcopy(data['files'][0])
            entry['path']=data['executable_relative_path'].split('/')[0].upper()
            data['files'].insert(0 if prepend else len(data['files']),entry)
            cases.append(data)
        data=copy.deepcopy(original)
        data['notices'][0]['destination']='third-party-notices'
        cases.append(data)
        data=copy.deepcopy(original)
        data['notices'][1]['destination']=data['notices'][0]['destination']+'/child'
        cases.append(data)
        for index,data in enumerate(cases):
            with self.subTest(index=index),patch.object(runtime,'_read_json',return_value=data),blocked_network(),patch.object(runtime,'run_bounded',side_effect=AssertionError('executed')):
                with self.assertRaises(DependencyError): runtime.load_manifest()

    def test_source_references_must_be_a_nonempty_list_of_source_urls(self):
        original=runtime.load_manifest().data
        for references in ('placeholder',[],[None],['placeholder'],['file:///private'],['https://'],['https://user:secret@example.com/source']):
            data=copy.deepcopy(original)
            data['source_references']=references
            with self.subTest(references=references),patch.object(runtime,'_read_json',return_value=data),blocked_network(),patch.object(runtime,'run_bounded',side_effect=AssertionError('executed')):
                with self.assertRaises(DependencyError): runtime.load_manifest()

    def test_real_manifest_and_notices_are_valid(self):
        artifact = runtime.load_manifest()
        self.assertEqual(artifact.data['version'], '16.1.0')
        self.assertEqual(len(artifact.data['files']), 302)
        self.assertGreater(len(artifact.data['notices']), 20)

    def test_invalid_schema_hash_paths_and_inventory_fail_before_network(self):
        original = runtime.load_manifest().data
        cases = []
        for key, value in [('schema_version',99),('archive_sha256',''),('executable_relative_path','../dot.exe'),('url','http://gitlab.com/no')]:
            data = copy.deepcopy(original)
            data[key] = value
            cases.append(data)
        data = copy.deepcopy(original)
        data['files'].append(copy.deepcopy(data['files'][0]))
        cases.append(data)
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/'manifest.json'
            for data in cases:
                target.write_text(json.dumps(data),encoding='utf-8')
                with self.subTest(data=list(data)), patch('urllib.request.OpenerDirector.open',side_effect=AssertionError('network')):
                    with self.assertRaises(DependencyError): runtime.load_manifest(target)

    def test_missing_manifest_and_unsupported_platform(self):
        with self.assertRaises(DependencyError): runtime.load_manifest(ROOT/'missing-manifest.json')
        with patch.object(runtime.sys,'platform','linux'), self.assertRaises(DependencyError):
            runtime.check_platform()


class PreparationTests(unittest.TestCase):
    def test_first_preparation_then_reuse_without_network_and_preserved_environment(self):
        import os
        artifact,archive=synthetic_artifact()
        transport=ControlledTransport(archive)
        before=dict(os.environ)
        with isolated_cache() as root:
            manager=runtime.RuntimeManager(artifact=artifact,cache_root=root,opener=transport,runner=synthetic_runner)
            first=manager.ensure()
            self.assertTrue(first.executable.is_file())
            self.assertEqual(len(transport.calls),1)
            with blocked_network():
                second=runtime.RuntimeManager(artifact=artifact,cache_root=root,opener=ControlledTransport(error=AssertionError('network')),runner=synthetic_runner).ensure()
            self.assertEqual(first.generation_id,second.generation_id)
            for notice in artifact.data['notices']:
                self.assertTrue((first.root/notice['destination']).is_file())
        self.assertEqual(dict(os.environ),before)

    def test_bad_hash_never_executes_and_has_no_active_selection(self):
        artifact,_=synthetic_artifact()
        with isolated_cache() as root:
            with self.assertRaises(DependencyError) as result:
                runtime.RuntimeManager(artifact=artifact,cache_root=root,opener=ControlledTransport(b'bad'),runner=lambda *a,**k:self.fail('executed')).ensure()
            self.assertIn('SHA-256',str(result.exception))
            self.assertFalse(any(root.rglob('active.json')))

    def test_absent_or_changed_notice_invalidates_cache(self):
        artifact,archive=synthetic_artifact()
        with isolated_cache() as root:
            manager=runtime.RuntimeManager(artifact=artifact,cache_root=root,opener=ControlledTransport(archive),runner=synthetic_runner)
            initial=manager.ensure()
            notice=initial.root/artifact.data['notices'][0]['destination']
            for changed in (False,True):
                if changed: notice.write_bytes(b'changed')
                else: notice.unlink()
                manager.opener=ControlledTransport(error=OSError('offline'))
                with self.assertRaises(DependencyError): manager.ensure()
                manager.opener=ControlledTransport(archive)
                initial=manager.ensure()
                notice=initial.root/artifact.data['notices'][0]['destination']
