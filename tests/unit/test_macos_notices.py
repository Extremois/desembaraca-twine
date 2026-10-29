import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[2] / 'tools/runtime'


def tool(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MacosNoticeTests(unittest.TestCase):
    def test_sdk_source_review_exports_observed_apsl_headers_and_rejects_changes(self):
        module = tool('prepare-macos-notices')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            include = root / 'usr/include'
            include.mkdir(parents=True)
            rows, expected = [], {}
            for name in ('float.h', 'math.h', 'i386/_limits.h', 'sys/types.h', 'private.h'):
                version = '2.0' if name.startswith('sys/') else '1.1'
                raw = (('/* Apple Public Source License Version ' + version + ' */\n').encode()
                       + b'#define REVIEW_HEADER 1\n') + name.encode()
                if name == 'private.h':
                    raw = b'/* unrelated header */\n'
                path = include / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
                digest = hashlib.sha256(raw).hexdigest()
                rows.append(dict(path=str(path), origin='external', size=len(raw), sha256=digest))
                if name in ('float.h', 'math.h'):
                    expected[name] = digest
            with patch.object(module, 'HEADER_REVIEW_SHA256', expected):
                materials = module.sdk_header_review_materials(rows, root)
                self.assertEqual({name for name, _, _ in materials},
                                 {'usr/include/float.h', 'usr/include/math.h', 'usr/include/i386/_limits.h',
                                  'usr/include/sys/types.h', 'APSL-1.1-COPYING.txt', 'APSL-2.0-COPYING.txt'})
                for name, raw, origin in materials:
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), origin['source_sha256'])
                with self.assertRaises(ValueError):
                    module.sdk_header_review_materials(rows[1:], root)
                with patch.object(module, 'HEADER_REVIEW_SHA256', {**expected, 'float.h': '0' * 64}):
                    with self.assertRaises(ValueError):
                        module.sdk_header_review_materials(rows, root)
                (include / 'float.h').write_bytes(b'changed')
                with self.assertRaises(ValueError):
                    module.sdk_header_review_materials(rows, root)

    def test_data_references_keep_iso_conditions_and_reject_changed_archive(self):
        import tarfile
        import io
        module = tool('prepare-macos-notices')
        data = module.load('audit-graphviz-data')
        entities = data.reference_material('html401-entities.html')
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / 'source.tar.gz'
            inputs = {'entities.html': entities, 'svgcolor_names': b'# SVG origin\n',
                      'color_names': b'# RGB origin\n'}
            with tarfile.open(archive, 'w:gz') as output:
                for name, raw in inputs.items():
                    item = tarfile.TarInfo('graphviz-16.1.0/lib/common/' + name)
                    item.size = len(raw)
                    output.addfile(item, io.BytesIO(raw))
            lock = dict(sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
            materials = module.data_reference_materials(archive, lock)
            by_name = {name: (raw, origin) for name, raw, origin in materials}
            raw, origin = by_name['W3C-HTML401-ENTITY-DECLARATION-NOTICES.txt']
            self.assertIn(b'conforming SGML systems', raw)
            self.assertEqual(origin['declaration_notices'], 3)
            for name, raw in inputs.items():
                stored, origin = by_name['Graphviz-data-' + name + '.txt']
                self.assertEqual(stored, raw)
                self.assertEqual(origin['source_sha256'], hashlib.sha256(raw).hexdigest())
            self.assertIn('W3C-software-1998.txt', by_name)
            self.assertIn('Xorg-rgb-1.1.0-COPYING.txt', by_name)
            archive.write_bytes(b'changed')
            with self.assertRaises(ValueError):
                module.data_reference_materials(archive, lock)

    def test_canonical_texts_follow_observed_notices_without_claiming_approval(self):
        module = tool('prepare-macos-notices')
        materials = [('apple.txt', b'Apple Public Source License\n * Version 2.0', {}),
                     ('apple-legacy.txt', b'Apple Public Source License Version 1.1', {}),
                     ('clang.txt', b'SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception', {}),
                     ('Bison-parser.txt', b'GNU General Public License\n * version 3', {})]
        references = module.canonical_references(materials)
        self.assertEqual(len(references), 4)
        self.assertEqual({item[2]['referenced_by'][0] for item in references},
                         {'apple.txt', 'apple-legacy.txt', 'clang.txt', 'Bison-parser.txt'})
        by_name = {name: origin['referenced_by'] for name, _, origin in references}
        self.assertEqual(by_name['APSL-1.1-COPYING.txt'], ['apple-legacy.txt'])
        self.assertEqual(by_name['APSL-2.0-COPYING.txt'], ['apple.txt'])
        for name, raw, origin in references:
            self.assertEqual(hashlib.sha256(raw).hexdigest(), origin['source_sha256'])
            self.assertIn('pending', origin['applicability'])
        self.assertEqual(module.canonical_references([]), [])

    def test_offline_origin_index_binds_every_payload_and_parent_evidence(self):
        import json
        module = tool('prepare-macos-notices')
        materials = [('notice.txt', b'Copyright Example', {'kind': 'test'})]
        raw = module.origin_index(materials, 'a' * 64, 'b' * 64)
        index = json.loads(raw)
        self.assertFalse(index['approved'])
        self.assertEqual(index['parent_provenance_sha256'], 'a' * 64)
        self.assertEqual(index['source_evidence_sha256'], 'b' * 64)
        self.assertEqual(index['notices'][0]['sha256'], hashlib.sha256(materials[0][1]).hexdigest())
        self.assertEqual(index['notices'][0]['origin'], materials[0][2])

    def test_apple_flex_requires_explicit_variant_and_exact_generator_version(self):
        common = tool('prepare-draft-notices')
        scanner = (b'/* A lexical scanner generated by flex */\n'
            b'#define YY_FLEX_MAJOR_VERSION 2\n#define YY_FLEX_MINOR_VERSION 6\n'
            b'#define YY_FLEX_SUBMINOR_VERSION 4\n')
        generator = dict(version='flex 2.6.4 Apple(flex-35)', sha256='a' * 64)
        with self.assertRaises(ValueError):
            common.flex_scanner_notice(scanner, generator)
        data, origin = common.flex_scanner_notice(scanner, generator, apple=True)
        self.assertEqual(hashlib.sha256(data).hexdigest(), '97fd685958d93be7f8dab939bb8161dbd6afb0718c63bfc337c24321aea44273')
        self.assertIn('8548f53e24244c0a411dea128a21686b61d29df4', origin['source_url'])
        with self.assertRaises(ValueError):
            common.flex_scanner_notice(scanner, dict(generator, version='flex 2.6.4 Apple(flex-36)'), apple=True)

    def test_header_notice_rejects_changed_bytes_and_outside_sdk_paths(self):
        module = tool('prepare-macos-notices')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sdk = root / 'sdk'
            sdk.mkdir()
            header = sdk / 'header.h'
            raw = b'/* Copyright Example; retain this notice. */\n#define HEADER 1\n'
            header.write_bytes(raw)
            row = dict(path=str(header), size=len(raw), sha256=hashlib.sha256(raw).hexdigest())
            prefix, origin = module.header_notice(row, sdk)
            self.assertIn(b'Copyright Example', prefix)
            self.assertEqual(origin['path'], 'header.h')
            header.write_bytes(raw.replace(b'Example', b'Changed'))
            with self.assertRaises(ValueError):
                module.header_notice(row, sdk)
            (root / 'outside.h').write_bytes(raw)
            with self.assertRaises(ValueError):
                module.header_notice(dict(row, path=str(root / 'outside.h')), sdk)
