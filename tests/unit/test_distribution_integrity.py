import hashlib
import importlib.util
import io
import json
from pathlib import Path
import stat
import tempfile
import unittest
import zipfile
from common import ROOT


def tool():
    spec=importlib.util.spec_from_file_location('distribution_integrity',ROOT/'tools/validation/check-distribution-integrity.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


class DistributionIntegrityTests(unittest.TestCase):
    def test_artifact_uses_candidate_inventory_and_hash_bound_provenance(self):
        candidate,inventory,provenance,archive_raw=self.fixture()
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'artifact.zip'
            with zipfile.ZipFile(path,'w') as archive:
                for name,raw in [('package/candidate.json',candidate),('package/inventory.json',inventory),
                        ('package/candidate.zip',archive_raw),('build/provenance.json',provenance),
                        ('old/provenance.json',b'{}'),('old/inventory.json',b'{}')]:
                    archive.writestr(name,raw)
            self.assertEqual(tool().inspect_artifact(path)['notice_payloads_verified'],1)

    def fixture(self, *, change=None):
        digest=lambda raw:hashlib.sha256(raw).hexdigest()
        license=b'upstream license'
        index=dict(approved=False,notices=[dict(path='COPYING.txt',size=len(license),
            sha256=digest(license),origin=dict(kind='pinned-source',source_sha256='c'*64))])
        if change=='origin':index['notices'][0]['sha256']='d'*64
        files={'bin/dot':b'controlled native bytes','third-party-notices/COPYING.txt':license,
            'third-party-notices/NOTICE-ORIGINS.json':json.dumps(index).encode()}
        if change=='unindexed':files['third-party-notices/extra.txt']=b'missing origin'
        inventory=dict(artifact_id='linux-test',files=[dict(path=name,size=len(raw),sha256=digest(raw),
            mode=0o755 if name=='bin/dot' else 0o644) for name,raw in files.items()])
        provenance=json.dumps(dict(completed=True,artifact_id='linux-test',
            executable_sha256=digest(files['bin/dot']),source=dict(url='https://example.invalid/source',
            sha256='c'*64,license='test-only',license_sha256=digest(license)))).encode()
        inventory['provenance_sha256']=digest(provenance)
        inventory_raw=json.dumps(inventory).encode()
        output=io.BytesIO()
        with zipfile.ZipFile(output,'w') as archive:
            for item in inventory['files']:
                info=zipfile.ZipInfo(item['path']);info.create_system=3
                info.external_attr=(stat.S_IFREG|item['mode'])<<16
                if change=='mode' and item['path']=='bin/dot':info.external_attr=(stat.S_IFREG|0o644)<<16
                archive.writestr(info,b'changed' if change=='bytes' and item['path']=='bin/dot' else files[item['path']])
            if change=='extra':archive.writestr('extra.txt',b'uninventoried')
        archive_raw=output.getvalue()
        candidate=json.dumps(dict(qualified=False,artifact_id='linux-test',archive_bytes=len(archive_raw),
            archive_sha256=digest(archive_raw),inventory_sha256=digest(inventory_raw),
            provenance_sha256=digest(provenance))).encode()
        return candidate,inventory_raw,provenance,archive_raw

    def test_exact_inventory_and_offline_origins_do_not_grant_license_approval(self):
        result=tool().inspect_candidate(*self.fixture())
        self.assertEqual(result['files_verified'],3)
        self.assertEqual(result['notice_payloads_verified'],1)
        self.assertFalse(result['license_compatibility_approved'])
        self.assertFalse(result['qualified'])

    def test_changed_or_uninventoried_bytes_and_unindexed_notices_fail(self):
        for change in ('bytes','extra','unindexed','origin','mode'):
            with self.subTest(change=change),self.assertRaises(ValueError):
                tool().inspect_candidate(*self.fixture(change=change))

    def test_unbound_metadata_cannot_pass_an_otherwise_valid_bundle(self):
        candidate,inventory,provenance,archive=self.fixture()
        with self.assertRaises(ValueError):
            tool().inspect_candidate(candidate,inventory,provenance+b' ',archive)
        with self.assertRaises(ValueError):
            tool().inspect_candidate(candidate,inventory+b' ',provenance,archive)
