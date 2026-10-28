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

    def test_macos_sources_bind_both_architectures_without_collecting_apple_sdk_archive(self):
        for artifact,arch in (('macos-x86_64','x86_64'),('macos-arm64','aarch64')):
            with self.subTest(artifact=artifact),tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                graphviz,sdk,provenance,source,_=self.fixture(root)
                record=json.loads(provenance.read_bytes())
                record.update(artifact_id=artifact,native_os='darwin',native_arch=arch,
                    recipe_sha256=self.module.digest(self.module.HERE/(artifact+'.json')),
                    sdk=dict(facts=dict(provider='Apple Xcode',target_os='darwin',target_arch=arch,deployment_target='15.0')))
                provenance.write_text(json.dumps(record),encoding='utf-8')
                with patch.object(self.module,'SOURCE_LOCK',source):
                    report=self.module.pack(graphviz,None,provenance,root/'output')
                    self.assertFalse(report['approved'])
                    self.assertEqual(report['sdk_files'],0)
                    with tarfile.open(root/'output/sources.tar.gz') as archive:
                        manifest=json.load(archive.extractfile('manifest.json'))
                        self.assertFalse(any(name.startswith('sdk/') for name in archive.getnames()))
                        self.assertIsNone(manifest['sdk_archive_sha256'])
                        self.assertEqual(archive.extractfile('candidate-provenance.json').read(),provenance.read_bytes())
                        self.assertEqual(archive.extractfile('graphviz.tar.gz').read(),graphviz.read_bytes())
                    with self.assertRaises(ValueError):self.module.pack(graphviz,sdk,provenance,root/'sdk-forbidden')
                    record['sdk']['facts']['target_arch']='wrong'
                    provenance.write_text(json.dumps(record),encoding='utf-8')
                    with self.assertRaises(ValueError):self.module.pack(graphviz,None,provenance,root/'wrong-arch')
                    self.assertFalse((root/'wrong-arch').exists())
                    record['sdk']['facts']['target_arch'] = arch
                    header_dir = root / 'header-review'
                    header_dir.mkdir()
                    license_bytes = (self.module.HERE / 'licenses/apsl-1.1-COPYING.txt').read_bytes()
                    contents = {'float.h': b'/* APSL header source */\n#define FLT_REVIEW 1\n',
                                'math.h': b'/* APSL header source */\n#define MATH_REVIEW 1\n',
                                'APSL-1.1-COPYING.txt': license_bytes}
                    rows = []
                    for name, raw in contents.items():
                        (header_dir / name).write_bytes(raw)
                        sha = hashlib.sha256(raw).hexdigest()
                        rows.append(dict(path='header-review/' + name, size=len(raw), sha256=sha,
                            origin=dict(kind='recorded-xcode-header-source' if name.endswith('.h')
                                        else 'pinned-canonical-license-text', source_sha256=sha)))
                    review = root / 'review.json'
                    review.write_bytes(json.dumps(dict(artifact_id=artifact, executable_sha256=record['executable_sha256'],
                        sdk_header_source_review=rows)).encode())
                    record['notice_preparation'] = dict(selected_sdk_header_files=2,
                        review_sha256=self.module.digest(review))
                    provenance.write_bytes(json.dumps(record).encode())
                    with self.assertRaises(ValueError):
                        self.module.pack(graphviz,None,provenance,root/'missing-review')
                    self.assertFalse((root/'missing-review').exists())
                    selected = self.module.pack(graphviz,None,provenance,root/'with-headers',header_review=review)
                    self.assertEqual(selected['selected_sdk_header_files'],2)
                    self.assertEqual(selected['sdk_files'],0)
                    with tarfile.open(root/'with-headers/sources.tar.gz') as archive:
                        for name, raw in contents.items():
                            self.assertEqual(archive.extractfile('header-review/'+name).read(),raw)
                        self.assertEqual(archive.extractfile('notice-review.json').read(),review.read_bytes())
                    # The current producer includes every observed APSL header,
                    # preserving subdirectories and both license versions.
                    extended = dict(contents)
                    extended['i386/_limits.h'] = b'/* APSL 1.1 */\n#define LIMIT_REVIEW 1\n'
                    extended['sys/types.h'] = b'/* APSL 2.0 */\n#define TYPES_REVIEW 1\n'
                    extended['APSL-2.0-COPYING.txt'] = (self.module.HERE/'licenses/apsl-2.0-COPYING.txt').read_bytes()
                    current_rows, headers = [], []
                    for name, raw in extended.items():
                        path = header_dir/name
                        path.parent.mkdir(parents=True,exist_ok=True)
                        path.write_bytes(raw)
                        sha = hashlib.sha256(raw).hexdigest()
                        origin = dict(kind='pinned-canonical-license-text',source_sha256=sha)
                        if name.endswith('.h'):
                            version = 'APSL-2.0' if name == 'sys/types.h' else 'APSL-1.1'
                            origin.update(kind='recorded-xcode-header-source',path=name,source_license=version)
                            headers.append(dict(path=name,source_sha256=sha,source_license=version))
                        current_rows.append(dict(path='header-review/'+name,size=len(raw),sha256=sha,origin=origin))
                    current = dict(artifact_id=artifact,executable_sha256=record['executable_sha256'],headers=headers,
                                   sdk_header_source_scope='observed-apsl-headers-v1',sdk_header_source_review=current_rows)
                    review.write_bytes(json.dumps(current).encode())
                    record['notice_preparation'].update(selected_sdk_header_files=4,review_sha256=self.module.digest(review))
                    provenance.write_bytes(json.dumps(record).encode())
                    selected = self.module.pack(graphviz,None,provenance,root/'all-observed',header_review=review)
                    self.assertEqual(selected['selected_sdk_header_files'],4)
                    with tarfile.open(root/'all-observed/sources.tar.gz') as archive:
                        for name,raw in extended.items():
                            self.assertEqual(archive.extractfile('header-review/'+name).read(),raw)
                    current['sdk_header_source_review'] = current_rows[:-1]
                    review.write_bytes(json.dumps(current).encode())
                    record['notice_preparation']['review_sha256'] = self.module.digest(review)
                    provenance.write_bytes(json.dumps(record).encode())
                    with self.assertRaises(ValueError):
                        self.module.pack(graphviz,None,provenance,root/'omitted-license',header_review=review)
                    self.assertFalse((root/'omitted-license').exists())
                    current['sdk_header_source_review'] = current_rows
                    review.write_bytes(json.dumps(current).encode())
                    record['notice_preparation']['review_sha256'] = self.module.digest(review)
                    provenance.write_bytes(json.dumps(record).encode())
                    (header_dir/'math.h').write_bytes(b'changed')
                    with self.assertRaises(ValueError):
                        self.module.pack(graphviz,None,provenance,root/'changed-header',header_review=review)
                    self.assertFalse((root/'changed-header').exists())
                    (header_dir/'math.h').write_bytes(contents['math.h'])
                    review.write_bytes(review.read_bytes()+b'\n')
                    with self.assertRaises(ValueError):
                        self.module.pack(graphviz,None,provenance,root/'changed-review',header_review=review)
                    self.assertFalse((root/'changed-review').exists())

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
