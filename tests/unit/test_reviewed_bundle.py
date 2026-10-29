import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from common import ROOT


class ReviewedBundleTests(unittest.TestCase):
    def test_another_archive_cannot_reuse_a_review_or_reach_native_execution(self):
        spec=importlib.util.spec_from_file_location('reviewed_bundle',ROOT/'tools/validation/check-reviewed-bundle.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        digest=lambda raw:hashlib.sha256(raw).hexdigest()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();artifact=root/'artifact';artifact.mkdir()
            provenance=json.dumps(dict(completed=True,artifact_id='linux-glibc-x86_64',executable_sha256='a'*64)).encode()
            inventory=json.dumps(dict(provenance_sha256=digest(provenance))).encode()
            archive=b'never executed'
            candidate=dict(artifact_id='linux-glibc-x86_64',qualified=False,
                inventory_sha256=digest(inventory),provenance_sha256=digest(provenance),
                archive_sha256=digest(archive),archive_bytes=len(archive))
            for name,raw in [('candidate.json',json.dumps(candidate).encode()),('provenance.json',provenance),
                             ('inventory.json',inventory),('candidate.zip',archive)]:
                (artifact/name).write_bytes(raw)
            (root/'decision.md').write_bytes(b'exact bytes only')
            audit=root/'audit.json';audit.write_text(json.dumps(dict(artifact_id=candidate['artifact_id'],
                decision_document='decision.md',decision_sha256=digest(b'exact bytes only'),
                source_pair=dict(candidate_sha256='0'*64))),encoding='utf-8')
            with patch.object(module,'ROOT',root),patch.object(module.native,'inspect') as execute:
                with self.assertRaisesRegex(ValueError,'exact candidate'):
                    module.inspect(artifact,candidate['artifact_id'],audit)
                execute.assert_not_called()
