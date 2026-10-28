import hashlib
import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path
from common import ROOT


class RemoteSourceInventoryTests(unittest.TestCase):
    def test_remote_archive_inventory_is_exact_and_rejects_duplicate_paths(self):
        spec=importlib.util.spec_from_file_location('installation_docs',ROOT/'tools/validation/check-installation-docs.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        revision='a'*40;prefix='desembaraca-twine-'+revision+'/'
        files={'src/twine_edge_overlap/__init__.py':b'example\n',
               'src/twine_edge_overlap/runtime-catalog.json':b'{}',
               'src/twine_edge_overlap/third_party/license.txt':b'vendor notice',
               'LICENSE':b'application license','NOTICE':b'application notice','README.md':b'not installed'}
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'project.zip'
            with zipfile.ZipFile(path,'w') as archive:
                for name,raw in files.items():archive.writestr(prefix+name,raw)
            expected,licenses=module.source_facts(path,revision)
            self.assertEqual(expected,{name.removeprefix('src/'):hashlib.sha256(raw).hexdigest()
                                       for name,raw in files.items() if name.startswith('src/')})
            self.assertEqual(licenses,{name:hashlib.sha256(files[name]).hexdigest() for name in ('LICENSE','NOTICE')})
            with self.assertRaises(ValueError):module.source_facts(path,'b'*40)
            import warnings
            with warnings.catch_warnings(),zipfile.ZipFile(path,'a') as archive:
                warnings.simplefilter('ignore',UserWarning)
                archive.writestr(prefix+'LICENSE',b'changed')
            with self.assertRaises(ValueError):module.source_facts(path,revision)
