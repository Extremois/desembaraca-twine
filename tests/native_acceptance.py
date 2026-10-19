"""Explicit opt-in drivers; missing environments are never qualification evidence."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
from common import ROOT


class InstalledCandidateAcceptance:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        required=('TWINE_CANDIDATE_PACKAGE','TWINE_PACKAGE_SHA256','TWINE_TARGET_ID','TWINE_ARTIFACT_ID',
                  'TWINE_APPLICATION_REVISION','TWINE_PYTHON312','TWINE_PYTHON314','TWINE_IMAGE_ID','TWINE_IMAGE_DIGEST')
        missing=[name for name in required if not os.environ.get(name)]
        if missing:raise RuntimeError('Native acceptance explicitly requested without configuration: '+', '.join(missing))
        spec=importlib.util.spec_from_file_location('native_qualifier',ROOT/'tools/runtime/qualify-target.py')
        qualifier=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(qualifier)
        env=os.environ
        args=argparse.Namespace(registry=ROOT/'tools/runtime/support-targets.json',target=env['TWINE_TARGET_ID'],
              package=Path(env['TWINE_CANDIDATE_PACKAGE']),package_sha256=env['TWINE_PACKAGE_SHA256'],
              artifact_id=env['TWINE_ARTIFACT_ID'],application_revision=env['TWINE_APPLICATION_REVISION'],
              python_312=Path(env['TWINE_PYTHON312']),python_314=Path(env['TWINE_PYTHON314']),
              python_minor=env.get('TWINE_PYTHON_MINOR',f'{sys.version_info.major}.{sys.version_info.minor}'),
              python_origin=env.get('TWINE_PYTHON_ORIGIN','explicit maintainer SDK; exact patch recorded'),
              source_state=env.get('TWINE_SOURCE_STATE','unverified'),image_id=env['TWINE_IMAGE_ID'],
              image_digest=env['TWINE_IMAGE_DIGEST'],environment_kind='native',wheelhouse=None)
        cls.record=qualifier.collect(args)

    def test_native_candidate_first_use_cache_modes_and_external_unicode_paths(self):
        self.assertEqual(self.record['environment_kind'],'native','WSL/container/emulation does not approve a native cell')
        self.assertTrue(self.record['checks']['first_run'])
        observed=self.record['observations']
        self.assertTrue(observed['cache_matches_platform'])
        self.assertTrue(observed['invalid_input_refused_without_acquisition'])
        self.assertEqual(observed['runtime_schema'],2)
        self.assertEqual(observed['executable_mode'],0o755)
        self.assertTrue(observed['healthy_generation_reused'])
        self.assertTrue(observed['paths_with_spaces_and_accents'])
        if self.record['os']=='darwin':self.assertTrue(observed['macos_security_assessed'])

    def test_real_corpus_preservation_and_honest_network_gate(self):
        self.assertTrue(self.record['checks']['preservation'])
        cases=json.loads((ROOT/'tests/fixtures/cases.json').read_text())
        self.assertEqual(len(self.record['corpus']),len(cases))
        expected={case['case'] for case in cases if case['known_resolvable']}
        for row in self.record['corpus']:
            self.assertTrue(row['original_preserved'] and row['semantics_preserved'])
            self.assertTrue(all(a<=b for a,b in zip(row['after'],row['before'])))
            if row['case'] in expected:self.assertEqual(row['after'],[0,0,0])
        self.assertEqual(self.record['network']['observation'],'python-only')
        self.assertNotIn('offline',self.record['checks'])
        self.assertIn('offline',self.record['pending_checks'])
