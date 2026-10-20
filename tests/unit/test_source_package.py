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

    def fixture(self, root, bad=None, arch='x86_64', abi='glibc'):
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
        artifact='linux-'+abi+'-'+arch
        recipe = self.module.HERE / (artifact+'.json')
        provenance = root / 'provenance.json'
        provenance.write_text(json.dumps(dict(artifact_id=artifact, completed=True,native_os='linux',native_arch=arch,
            executable_sha256='a' * 64, source=source, recipe_sha256=hashlib.sha256(recipe.read_bytes()).hexdigest(),
            sdk=dict(facts=dict(archive=toolchain)))), encoding='utf-8')
        return graphviz, sdk, provenance, source, toolchain

    def test_musl_source_export_selects_native_sdk_and_requires_static_target_facts(self):
        for arch in ('x86_64','aarch64'):
            with self.subTest(arch=arch),tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                graphviz,sdk,provenance,source,toolchain=self.fixture(root,arch=arch,abi='musl')
                record=json.loads(provenance.read_bytes())
                record['sdk']['facts'].update(target_os='linux',target_arch=arch,target_libc_family='musl',
                    static_linking=True,target=arch+'-linux.4.15-musl')
                record['static_elf_inspection']=dict(no_interpreter=True,no_dynamic_section=True,
                    no_needed_libraries=True,no_glibc_symbols=True)
                provenance.write_text(json.dumps(record))
                lock_name='SDK_LOCK' if arch=='x86_64' else 'SDK_LOCK_ARM64'
                with patch.object(self.module,'SOURCE_LOCK',source),patch.object(self.module,lock_name,toolchain):
                    result=self.module.pack(graphviz,sdk,provenance,root/'output')
                    self.assertEqual(result['artifact_id'],'linux-musl-'+arch)
                    record['sdk']['facts']['target_arch']='wrong'
                    provenance.write_text(json.dumps(record))
                    with self.assertRaises(ValueError):self.module.pack(graphviz,sdk,provenance,root/'wrong-target')
                    self.assertFalse((root/'wrong-target').exists())
                    record['sdk']['facts']['target_arch']=arch
                    record['static_elf_inspection']['no_dynamic_section']=False
                    provenance.write_text(json.dumps(record))
                    with self.assertRaises(ValueError):self.module.pack(graphviz,sdk,provenance,root/'dynamic')
                    self.assertFalse((root/'dynamic').exists())

    def test_arm_source_export_selects_arm_sdk_and_rejects_mismatched_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            graphviz,sdk,provenance,source,toolchain=self.fixture(root,arch='aarch64')
            with patch.object(self.module,'SOURCE_LOCK',source), patch.object(self.module,'SDK_LOCK_ARM64',toolchain):
                report=self.module.pack(graphviz,sdk,provenance,root/'output')
                self.assertEqual(report['artifact_id'],'linux-glibc-aarch64')
                with tarfile.open(root/'output/sources.tar.gz') as archive:
                    manifest=json.load(archive.extractfile('manifest.json'))
                    self.assertEqual(manifest['sdk_archive_sha256'],toolchain['sha256'])
                    self.assertNotIn('sdk/zig',archive.getnames())
                record=json.loads(provenance.read_bytes())
                record['native_arch']='x86_64';provenance.write_text(json.dumps(record))
                with self.assertRaises(ValueError):self.module.pack(graphviz,sdk,provenance,root/'wrong-arch')
                self.assertFalse((root/'wrong-arch').exists())
                record['native_arch']='aarch64';record['sdk']['facts']['archive']['sha256']='0'*64
                provenance.write_text(json.dumps(record))
                with self.assertRaises(ValueError):self.module.pack(graphviz,sdk,provenance,root/'wrong-sdk')
                self.assertFalse((root/'wrong-sdk').exists())

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
                inspection = subprocess.run([sys.executable, str(extracted / 'tools/runtime/verify-artifact.py'), '--help'],
                    cwd=extracted, capture_output=True, text=True, timeout=10)
                self.assertEqual(inspection.returncode, 0, inspection.stderr)
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
