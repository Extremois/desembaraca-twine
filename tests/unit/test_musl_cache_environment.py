import importlib.util
import json
from pathlib import Path
import unittest
from common import ROOT


class MuslCacheEnvironmentTests(unittest.TestCase):
    def test_pinned_userland_requires_matching_cpu_python_and_distribution(self):
        spec=importlib.util.spec_from_file_location('musl_cache',ROOT/'.github/scripts/run-musl-cache-notices.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        lock=json.loads((ROOT/'tools/runtime/alpine-ci-images.json').read_bytes())
        image=lock['images']['3.12']['platforms']['aarch64']['reference']
        facts=dict(arch='aarch64',python_minor='3.12',distribution='alpine',version='3.22.2',uid=1001)
        module.validate_environment(lock,image,'aarch64','3.12',facts)
        for key,value in [('arch','x86_64'),('python_minor','3.14'),('distribution','ubuntu'),('uid',0)]:
            changed=dict(facts);changed[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                module.validate_environment(lock,image,'aarch64','3.12',changed)
