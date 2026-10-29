import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('reviewed_graphviz_source', ROOT / 'tools/runtime/graphviz-source.py')
SOURCE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SOURCE)


class GraphvizSourceTests(unittest.TestCase):
    def test_production_replacements_keep_proved_hashes_and_current_notices(self):
        lock = json.loads((SOURCE.HERE / 'source-lock.json').read_bytes())
        files = SOURCE.replacements(lock)
        self.assertEqual(set(files), {SOURCE.PREFIX + 'lib/common/entities.html', SOURCE.PREFIX + 'lib/common/entities.py'})
        self.assertEqual(lock['entity_replacement']['source_tree_sha256'],
                         '54ae15738f636a57581272de3565f933c7c55b8d84005d2d8b3361aeb429f4d0')
        for raw in files.values():
            self.assertIn(b'BSD 3-Clause License', raw)
            self.assertIn(b'W3C Software and Document License 2002', raw)
            self.assertNotIn(b'conforming SGML systems', raw)

    def test_replacement_export_replays_and_rejects_tampering(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            replacement = root / 'replacement.html'
            replacement.write_bytes(b'reviewed names and values with complete notices')
            upstream = root / 'upstream.tar.gz'
            with tarfile.open(upstream, 'w:gz', pax_headers={'comment': 'revision'}) as archive:
                for name, raw in [('lib/common/entities.html', b'old entity input'), ('COPYING', b'unchanged license')]:
                    member = tarfile.TarInfo(SOURCE.PREFIX + name)
                    member.size = len(raw)
                    archive.addfile(member, io.BytesIO(raw))
            lock = dict(size=upstream.stat().st_size, sha256=hashlib.sha256(upstream.read_bytes()).hexdigest(),
                git_revision='revision', entity_replacement=dict(files={'lib/common/entities.html': dict(
                    file=replacement.name, size=replacement.stat().st_size,
                    sha256=hashlib.sha256(replacement.read_bytes()).hexdigest(),
                    upstream_sha256=hashlib.sha256(b'old entity input').hexdigest())}))
            with patch.object(SOURCE, 'HERE', root):
                lock['entity_replacement']['source_tree_sha256'] = SOURCE.tree_identity(upstream, lock)
                modified = root / 'modified.tar.gz'
                modified.write_bytes(SOURCE.export(upstream, lock))
                SOURCE.verify(modified, lock)
                with tarfile.open(modified) as archive:
                    self.assertEqual(archive.extractfile(SOURCE.PREFIX + 'lib/common/entities.html').read(), replacement.read_bytes())
                    self.assertEqual(archive.extractfile(SOURCE.PREFIX + 'COPYING').read(), b'unchanged license')
                    archive.extractall(root / 'replay', filter='data')
                SOURCE.apply(root / 'replay', lock)
                replacement.write_bytes(b'tampered replacement')
                with self.assertRaises(ValueError):
                    SOURCE.verify(upstream, lock)
                replacement.write_bytes(b'reviewed names and values with complete notices')
                lock['entity_replacement']['source_tree_sha256'] = '0' * 64
                with self.assertRaises(ValueError):
                    SOURCE.verify(modified, lock)


if __name__ == '__main__':
    unittest.main()
