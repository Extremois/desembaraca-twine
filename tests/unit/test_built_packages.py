import copy
import importlib.util
import io
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
