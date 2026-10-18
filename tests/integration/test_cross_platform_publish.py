from concurrent.futures import ThreadPoolExecutor
import errno
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from common import fixture
from twine_edge_overlap.files import publish
from twine_edge_overlap.errors import WriteError


class CrossPlatformPublishTests(unittest.TestCase):
    def test_concurrent_unicode_publications_never_replace_existing_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            source=root/('a'+chr(0xe7)+'ao.twee')
            original=fixture()
            source.write_bytes(original)
            occupied=source.with_name(source.stem+'.layout.twee')
            occupied.write_bytes(b'KEEP')
            def commit(_):
                return publish(source,original,lambda value:self.assertEqual(value,original),original=original)
            with ThreadPoolExecutor(max_workers=2) as pool:
                outputs=list(pool.map(commit,range(2)))
            self.assertEqual(len(set(outputs)),2)
            for output in outputs:self.assertEqual(output.read_bytes(),original)
            self.assertEqual(occupied.read_bytes(),b'KEEP')
            self.assertEqual(source.read_bytes(),original)
            self.assertEqual(list(root.glob('.twine-layout-*')),[])

    @unittest.skipIf(os.name=='nt','POSIX hardlink commit contract')
    def test_no_hardlink_filesystem_fails_without_copy_or_rename_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'story.twee'
            original=fixture()
            source.write_bytes(original)
            with patch('twine_edge_overlap.files.os.link',side_effect=OSError(errno.EOPNOTSUPP,'unsupported')),patch('twine_edge_overlap.files.os.rename',side_effect=AssertionError('unsafe fallback')):
                with self.assertRaisesRegex(WriteError,'publicação atômica'):
                    publish(source,original,lambda value:None,original=original)
            self.assertEqual(list(Path(folder).iterdir()),[source])
            self.assertEqual(source.read_bytes(),original)

    def test_case_distinct_existing_name_is_preserved_on_this_filesystem(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'story.twee'
            source.write_bytes(fixture())
            other=source.with_name('STORY.LAYOUT.TWEE')
            other.write_bytes(b'CASE-SENTINEL')
            output=publish(source,fixture(),lambda value:None)
            self.assertEqual(other.read_bytes(),b'CASE-SENTINEL')
            self.assertEqual(output.read_bytes(),fixture())
