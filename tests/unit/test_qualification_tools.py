import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from common import ROOT
from unit.test_runtime_build_tools import tool


class QualificationToolTests(unittest.TestCase):
    def test_review_export_preserves_exact_six_public_outputs_without_overwrite(self):
        collector=tool('qualify-target')
        cases=json.loads((ROOT/'tests/fixtures/cases.json').read_text())
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            work=root/'work'
            (work/'review').mkdir(parents=True)
            corpus=[]
            for case in cases:
                data=(ROOT/'tests/fixtures'/case['file']).read_bytes()
                corpus.append(dict(case=case['case'],output_sha256=hashlib.sha256(data).hexdigest()))
                if case['known_resolvable']:
                    (work/'review'/(case['case']+'.twee')).write_bytes(data)
            record=dict(target_id='synthetic-unit',python_minor='3.12',application_revision='a'*40,
                        artifact_sha256='b'*64,source_state='dirty',corpus=corpus)
            destination=root/'review-export'
            bundle=collector.export_review(work,record,destination)
            manifest=json.loads((destination/'manifest.json').read_text())
            self.assertEqual(len(manifest['outputs']),6)
            self.assertEqual(manifest['review_status'],'pending')
            self.assertEqual(bundle['manifest_sha256'],hashlib.sha256((destination/'manifest.json').read_bytes()).hexdigest())
            for item in manifest['outputs']:
                self.assertEqual(hashlib.sha256((destination/item['file']).read_bytes()).hexdigest(),item['sha256'])
            with self.assertRaises(FileExistsError):collector.export_review(work,record,destination)
            # Tampering is rejected before creating a destination.
            first=next((work/'review').glob('*.twee'))
            first.write_bytes(b'changed')
            with self.assertRaises(ValueError):collector.export_review(work,record,root/'bad')
            self.assertFalse((root/'bad').exists())

    def test_review_export_rejects_missing_duplicate_or_unsafe_cases(self):
        collector=tool('qualify-target')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for corpus in ([],[dict(case='../escape',output_sha256='a'*64)],
                           [dict(case='crossing',output_sha256='a'*64)]*2):
                with self.subTest(corpus=corpus),self.assertRaises(ValueError):
                    collector.export_review(root,dict(corpus=corpus),root/'bad')
                self.assertFalse((root/'bad').exists())

    def test_common_license_audit_does_not_fabricate_a_second_execution_environment(self):
        promotion=tool('promote-support')
        registry=json.loads((ROOT/'tools/runtime/support-targets.json').read_text(encoding='utf-8'))
        target=registry['targets'][0]
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            records=self.records(target,root)
            audit=copy.deepcopy(records[0])
            audit.update(id='common-artifact-audit',python_minor=None,evidence_scope='artifact-license-audit',checks={'licenses':True})
            for key in ('os','architecture','distribution_id','os_version','channel','cpu_variant','image_id','image_digest','kernel','cpu','python_patch','python_origin','package_sha256'):
                audit.pop(key,None)
            for item in records:item['checks'].pop('licenses')
            # Different application formats may have different package hashes.
            records[1]['package_sha256']='f'*64
            proposal=promotion.propose(registry,target['id'],records+[audit],root)
            self.assertEqual(proposal['targets'][0]['status'],'validada')
            self.assertEqual(proposal['targets'][0]['evidence_ids'],[audit['id']])
            audit['checks']['offline']=True
            with self.assertRaises(ValueError):promotion.propose(registry,target['id'],records+[audit],root)

    def records(self,target,root):
        from twine_edge_overlap.runtime_catalog import GATES
        log=root/'synthetic-unit.log'
        log.write_text('Synthetic test data, never native qualification.')
        ref=dict(path=log.name,sha256=hashlib.sha256(log.read_bytes()).hexdigest())
        cases=json.loads((ROOT/'tests/fixtures/cases.json').read_text())
        corpus=[dict(case=case['case'],input_sha256=hashlib.sha256((ROOT/'tests/fixtures'/case['file']).read_bytes()).hexdigest(),output_sha256='a'*64,before=case['before'],after=[0,0,0] if case['known_resolvable'] else case['before'],original_preserved=True,semantics_preserved=True) for case in cases]
        records=[]
        for minor in ('3.12','3.14'):
            records.append(dict(id='synthetic-'+minor,target_id=target['id'],os=target['os'],architecture=target['arch'],distribution_id=target['distribution_id'],os_version=target['version'],channel=target['channel'],cpu_variant=target['cpu_variant'],snapshot_id=None,environment_kind='native',passed=True,reviewer='synthetic-unit-reviewer',artifact_id='synthetic-artifact',application_revision='b'*40,artifact_sha256='c'*64,package_sha256='d'*64,recipe_revision='synthetic-recipe',image_id='synthetic-image',image_digest='e'*64,kernel='synthetic-kernel',cpu='synthetic-cpu',captured_at='2026-10-17T00:00:00Z',python_minor=minor,python_patch=minor+'.1',python_origin='synthetic-unit-fixture',checks=dict.fromkeys(GATES,True),commands=['synthetic-test-only'],logs=[ref],corpus=corpus,network=dict(observation='native-trace',attempts=0,reviewer='synthetic-unit-reviewer',log=ref),installation=dict.fromkeys(('wheel','sdist','remote','outside_checkout','console','module'),True),license_audit=dict(approved=True,reviewer='synthetic-unit-reviewer',artifact_sha256='c'*64,log=ref,components=[dict(name='synthetic-component',license_expression='synthetic-test-only',source_url='https://example.invalid/synthetic-unit',source_sha256='f'*64)]),twine=dict(version='synthetic-test-only',reviewer='synthetic-unit-reviewer',log=ref,outputs=[dict(case=case['case'],sha256='a'*64,reopened=True) for case in cases if case['known_resolvable']])))
        for item in records:item['source_state']='committed'
        return records

    def test_complete_synthetic_cell_proposal_preserves_other_pending_targets(self):
        promotion=tool('promote-support')
        registry=json.loads((ROOT/'tools/runtime/support-targets.json').read_text(encoding='utf-8'))
        original=copy.deepcopy(registry)
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            records=self.records(registry['targets'][0],root)
            proposal=promotion.propose(registry,registry['targets'][0]['id'],records,root)
            self.assertEqual(proposal['targets'][0]['status'],'validada')
            self.assertNotIn('corpus',proposal['evidence'][records[0]['id']])
            self.assertEqual(len(proposal['evidence'][records[0]['id']]['qualified_record_sha256']),64)
            self.assertEqual(proposal['targets'][1:],registry['targets'][1:])
            self.assertEqual(registry,original)
            for key,value in (('environment_kind','wsl'),('application_revision','f'*40),('artifact_sha256','f'*64),('image_digest','f'*64),('os_version','999'),('python_minor','3.12'),('source_state','dirty')):
                altered=copy.deepcopy(records)
                altered[1][key]=value
                with self.subTest(key=key),self.assertRaises(ValueError):promotion.propose(registry,registry['targets'][0]['id'],altered,root)
            altered=copy.deepcopy(records)
            altered[0]['network']['observation']='python-only'
            with self.assertRaises(ValueError):promotion.propose(registry,registry['targets'][0]['id'],altered,root)
            altered=copy.deepcopy(records)
            altered[0]['twine']['outputs'][0]['sha256']='0'*64
            with self.assertRaises(ValueError):promotion.propose(registry,registry['targets'][0]['id'],altered,root)
            (root/'synthetic-unit.log').write_text('tampered')
            with self.assertRaises(ValueError):promotion.propose(registry,registry['targets'][0]['id'],records,root)

    def test_first_rolling_capture_is_canonical_and_cannot_replace_an_existing_snapshot(self):
        promotion=tool('promote-support')
        from twine_edge_overlap.runtime_snapshot import collect_snapshot
        from twine_edge_overlap.runtime_catalog import EnvironmentSnapshot
        from twine_edge_overlap.engines.process import ProcessResult
        registry=json.loads((ROOT/'tools/runtime/support-targets.json').read_text(encoding='utf-8'))
        target=next(item for item in registry['targets'] if item['distribution_id']=='arch')
        meta=dict(distribution_id='arch',version_id=None,build_id=None,channel='rolling',native_arch=target['arch'],kernel_release='synthetic-kernel')
        capture=collect_snapshot('pacman',lambda:meta.copy(),runner=lambda *a,**k:ProcessResult(0,b'a 1\n',b''))
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            records=self.records(target,root)
            for item in records:
                item.update(snapshot_id=capture.snapshot_id,environment_snapshot=EnvironmentSnapshot.from_probe(capture).data)
            proposal=promotion.propose(registry,target['id'],records,root)
            self.assertEqual(next(item for item in proposal['targets'] if item['id']==target['id'])['snapshot_id'],capture.snapshot_id)
            target['snapshot_id']='f'*64
            with self.assertRaises(ValueError):promotion.propose(registry,target['id'],records,root)

    def test_signing_cannot_run_or_create_outputs_on_another_os(self):
        signer=tool('sign-macos')
        from twine_edge_overlap.runtime_platform import HostEnvironment
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            with patch.object(signer,'detect_host',return_value=HostEnvironment(os='windows',arch='x86_64')):
                with self.assertRaises(ValueError):signer.sign(root/'absent',root/'output',root/'audit','Developer ID Application: unit-test','test-profile')
            self.assertFalse((root/'output').exists())

    def test_promotion_refuses_status_without_records_or_duplicate_python(self):
        promotion=tool('promote-support')
        registry=json.loads((ROOT/'tools/runtime/support-targets.json').read_text(encoding='utf-8'))
        target=registry['targets'][0]
        target['status']='validada'
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                promotion.propose(registry,target['id'],[],Path(folder))
            target['python_qualifications'][1]['python_minor']='3.12'
            with self.assertRaises(ValueError):
                promotion.propose(registry,target['id'],[],Path(folder))

    def test_qualification_requires_explicit_context_and_unsupported_host_is_pending(self):
        qualifier=tool('qualify-target')
        from twine_edge_overlap.runtime_platform import HostEnvironment
        registry=json.loads((ROOT/'tools/runtime/support-targets.json').read_text(encoding='utf-8'))
        target=next(item for item in registry['targets'] if item['distribution_id']=='ubuntu')
        self.assertFalse(qualifier.host_matches(target,HostEnvironment(os='linux',arch='aarch64',distribution_id='ubuntu',distribution_version=target['version'])))
        self.assertFalse(qualifier.host_matches(target,HostEnvironment(os='linux',arch=target['arch'],distribution_id='derivative',distribution_version=target['version'])))
