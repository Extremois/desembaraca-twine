import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from common import ROOT
from twine_edge_overlap.runtime_catalog import CatalogError, load_catalog, select_artifact, support_status, validate_manifest_identity, GATES
from twine_edge_overlap.runtime_platform import HostEnvironment


class CatalogTests(unittest.TestCase):
    def test_all_seven_published_artifacts_have_bound_manifests_and_exact_selection(self):
        from twine_edge_overlap.runtime_catalog import verified_manifest
        from twine_edge_overlap.runtime import load_manifest
        catalog=load_catalog()
        self.assertEqual(len(catalog['artifacts']),7)
        for item in catalog['artifacts']:
            artifact=load_manifest(verified_manifest(item))
            validate_manifest_identity(item,artifact.data)
            host=HostEnvironment(os=item['os'],arch=item['arch'],os_version=item.get('minimum_os',''),
                libc_family=item.get('abi',''),libc_version=item.get('minimum_libc',''),
                kernel_version=item.get('minimum_kernel',''))
            self.assertEqual(select_artifact(catalog,host)['id'],item['id'])

    def test_packaged_catalog_preserves_windows_manifest_bytes(self):
        catalog = load_catalog()
        host = HostEnvironment(os='windows', os_version='11', arch='x86_64')
        descriptor = select_artifact(catalog, host)
        self.assertEqual(descriptor['manifest_path'], 'runtime-manifest.json')
        raw = (ROOT / 'src/twine_edge_overlap/runtime-manifest.json').read_bytes()
        self.assertEqual(descriptor['manifest_sha256'], hashlib.sha256(raw).hexdigest())

    def test_wrong_abi_unknown_minimum_and_ties_never_guess(self):
        catalog = load_catalog()
        with self.assertRaises(CatalogError):
            select_artifact(catalog, HostEnvironment(os='linux', arch='x86_64', libc_family='musl'))
        duplicate = copy.deepcopy(catalog)
        duplicate['artifacts'].append(copy.deepcopy(duplicate['artifacts'][0]))
        duplicate['artifacts'][-1]['id'] += '-other'
        with self.assertRaises(CatalogError):
            select_artifact(duplicate, HostEnvironment(os='windows', os_version='11', arch='x86_64'))
        with self.assertRaises(CatalogError):
            select_artifact(catalog, HostEnvironment(os='windows', os_version='11', arch='x86_64', translated=True))

    def test_duplicate_json_keys_and_unsafe_manifest_paths_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'catalog.json'
            path.write_text('{"schema_version":2,"schema_version":2}', encoding='utf-8')
            with self.assertRaises(CatalogError): load_catalog(path)
            data = load_catalog()
            data['artifacts'][0]['manifest_path'] = '../outside.json'
            path.write_text(json.dumps(data), encoding='utf-8')
            with self.assertRaises(CatalogError): load_catalog(path)

    def test_pending_registry_does_not_promote_from_one_python(self):
        data = json.loads((ROOT / 'tools/runtime/support-targets.json').read_text(encoding='utf-8'))
        for target in data['targets']:
            self.assertEqual(support_status(target, {}), 'pendente')
        target = copy.deepcopy(data['targets'][0])
        target['python_qualifications'][0]['status'] = 'validada'
        self.assertNotEqual(support_status(target, {}), 'validada')
        target['python_qualifications'][1]['python_minor'] = '3.12'
        with self.assertRaises(CatalogError): support_status(target, {})

    def test_unknown_libc_minimum_and_manifest_abi_mismatch_are_rejected(self):
        item=copy.deepcopy(load_catalog()['artifacts'][0])
        item.update(id='controlled-linux',os='linux',abi='glibc',minimum_libc='2.27',minimum_kernel='4.15',build_variant='controlled')
        for libc in ('','2.26'):
            with self.assertRaises(CatalogError):
                select_artifact({'artifacts':[item]},HostEnvironment(os='linux',arch='x86_64',libc_family='glibc',libc_version=libc,kernel_version='4.15-test'))
        from twine_edge_overlap.runtime import load_manifest
        with self.assertRaises(CatalogError): validate_manifest_identity(item,load_manifest().data)

    def test_two_native_slots_same_revision_artifact_and_gates_required(self):
        target=json.loads((ROOT/'tools/runtime/support-targets.json').read_text(encoding='utf-8'))['targets'][0]
        target.update(application_revision='a'*40,artifact_id='reviewed-test-fixture')
        evidence={}
        for slot in target['python_qualifications']:
            reference='test-'+slot['python_minor']
            slot.update(status='validada',application_revision=target['application_revision'],artifact_id=target['artifact_id'],evidence_ids=[reference])
            evidence[reference]=dict(target_id=target['id'],python_minor=slot['python_minor'],application_revision=target['application_revision'],artifact_id=target['artifact_id'],snapshot_id=None,environment_kind='native',passed=True,checks=dict.fromkeys(GATES,True))
        self.assertEqual(support_status(target,evidence),'validada')
        for key,value in [('environment_kind','simulated'),('application_revision','b'*40),('artifact_id','other'),('snapshot_id','f'*64)]:
            altered=copy.deepcopy(evidence)
            altered['test-3.14'][key]=value
            self.assertNotEqual(support_status(target,altered),'validada')

