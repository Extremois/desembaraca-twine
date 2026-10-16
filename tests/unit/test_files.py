from pathlib import Path
import tempfile
import unittest
from common import fixture
from twine_edge_overlap.files import snapshot,publish


class FilesTests(unittest.TestCase):
    def test_collision_and_repeated_execution_never_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'test.twee'
            source.write_bytes(fixture())
            occupied=source.with_name('test.layout.twee')
            occupied.write_bytes(b'KEEP')
            first=publish(source,snapshot(source),lambda b: self.assertEqual(b,fixture()))
            second=publish(source,snapshot(source),lambda b: self.assertEqual(b,fixture()))
            self.assertNotEqual(first,second)
            self.assertEqual(first.parent,source.parent)
            self.assertEqual(occupied.read_bytes(),b'KEEP')
            self.assertEqual(source.read_bytes(),fixture())
