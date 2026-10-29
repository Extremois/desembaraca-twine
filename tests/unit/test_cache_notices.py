import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from common import ROOT


def tool():
    spec=importlib.util.spec_from_file_location('cache_notices',ROOT/'.github/scripts/probe-cache-notices.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


class CacheNoticeTests(unittest.TestCase):
    def test_independent_snapshot_checks_notice_bytes_and_complete_inventory(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);notice=root/'third-party-notices/license.txt'
            notice.parent.mkdir();notice.write_bytes(b'notice')
            expected={notice.relative_to(root).as_posix():dict(sha256=hashlib.sha256(b'notice').hexdigest(),size=6,mode=0o644)}
            self.assertEqual(tool().snapshot(root,expected),{next(iter(expected)):expected[next(iter(expected))]['sha256']})
            for change in ('bytes','missing','extra'):
                with self.subTest(change=change):
                    notice.write_bytes(b'changed' if change=='bytes' else b'notice')
                    extra=notice.parent/'extra.txt'
                    if change=='missing':notice.unlink()
                    if change=='extra':extra.write_bytes(b'extra')
                    try:
                        with self.assertRaises(ValueError):tool().snapshot(root,expected)
                    finally:extra.unlink(missing_ok=True)

    def test_cache_snapshot_refuses_links_to_other_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);parent=root/'third-party-notices';parent.mkdir()
            outside=root/'outside.txt';outside.write_bytes(b'notice')
            target=parent/'link.txt'
            try:target.symlink_to(outside)
            except OSError:self.skipTest('Symlink creation unavailable to this test account')
            with self.assertRaises(ValueError):
                tool().snapshot(root,{'third-party-notices/link.txt':dict(sha256=hashlib.sha256(b'notice').hexdigest(),size=6,mode=0o644)})
