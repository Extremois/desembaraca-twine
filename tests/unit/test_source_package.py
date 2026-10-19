import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('source_package', ROOT / 'tools/runtime/pack-sources.py')


class SourcePackageTests(unittest.TestCase):
    def setUp(self):
        self.module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(self.module)

    def fixture(self, root, bad=None):
        graphviz = root / 'graphviz.tar.gz'
        graphviz.write_bytes(b'pinned graphviz archive')
        sdk = root / 'sdk.tar.xz'
        with tarfile.open(sdk, 'w:xz') as archive:
            for name, content in [('zig-root/lib/libc/glibc/csu/init.c', b'LGPL source'),
                                  ('zig-root/LICENSE', b'MIT notice'),
                                  ('zig-root/zig', b'compiler excluded')]:
                entry = tarfile.TarInfo(name)
                entry.size = len(content)
                archive.addfile(entry, io.BytesIO(content))
            if bad:
                archive.addfile(bad)
        lock = lambda path: dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(), size=path.stat().st_size)
        source, toolchain = lock(graphviz), lock(sdk)
        recipe = self.module.HERE / 'linux-glibc-x86_64.json'
        provenance = root / 'provenance.json'
        provenance.write_text(json.dumps(dict(artifact_id='linux-glibc-x86_64', completed=True,
            executable_sha256='a' * 64, source=source, recipe_sha256=hashlib.sha256(recipe.read_bytes()).hexdigest(),
            sdk=dict(facts=dict(archive=toolchain)))), encoding='utf-8')
        return graphviz, sdk, provenance, source, toolchain

    def test_preserves_sources_excludes_compiler_and_binds_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            graphviz, sdk, provenance, source, toolchain = self.fixture(root)
            with patch.object(self.module, 'SOURCE_LOCK', source), patch.object(self.module, 'SDK_LOCK', toolchain):
                report = self.module.pack(graphviz, sdk, provenance, root / 'output')
                with tarfile.open(root / 'output/sources.tar.gz') as archive:
                    names = archive.getnames()
                    self.assertIn('sdk/lib/libc/glibc/csu/init.c', names)
                    self.assertNotIn('sdk/zig', names)
                    manifest = json.load(archive.extractfile('manifest.json'))
                    self.assertEqual(manifest['executable_sha256'], 'a' * 64)
                    self.assertFalse(manifest['approved'])
                    extracted = root / 'extracted'
                    archive.extractall(extracted, filter='data')
                command = subprocess.run([sys.executable, str(extracted / 'tools/runtime/build-common.py'), '--help'],
                    cwd=extracted, capture_output=True, text=True, timeout=10)
                self.assertEqual(command.returncode, 0, command.stderr)
                self.assertEqual(report['sdk_files'], 2)
                record = json.loads(provenance.read_bytes())
                record['sdk']['facts']['archive']['sha256'] = '0' * 64
                provenance.write_text(json.dumps(record), encoding='utf-8')
                with self.assertRaises(ValueError):
                    self.module.pack(graphviz, sdk, provenance, root / 'wrong-build')
                self.assertFalse((root / 'wrong-build').exists())
                with self.assertRaises(FileExistsError):
                    self.module.pack(graphviz, sdk, provenance, root / 'output')
                graphviz.write_bytes(b'tampered')
                with self.assertRaises(ValueError):
                    self.module.pack(graphviz, sdk, provenance, root / 'tampered')
                self.assertFalse((root / 'tampered').exists())

    def test_rejects_archive_links_and_traversal_before_output(self):
        for name in ('zig-root/lib/../../escape', 'zig-root/lib/link'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                bad = tarfile.TarInfo(name)
                if name.endswith('link'):
                    bad.type = tarfile.SYMTYPE
                    bad.linkname = '/etc/passwd'
                graphviz, sdk, provenance, source, toolchain = self.fixture(root, bad)
                with patch.object(self.module, 'SOURCE_LOCK', source), patch.object(self.module, 'SDK_LOCK', toolchain):
                    with self.assertRaises(ValueError):
                        self.module.pack(graphviz, sdk, provenance, root / 'output')
                self.assertFalse((root / 'output').exists())
