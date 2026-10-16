import errno
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from common import fixture
from twine_edge_overlap.files import snapshot,publish
from twine_edge_overlap.errors import InputError,WriteError,IntegrityError


class FileFailureTests(unittest.TestCase):
    def test_read_permission_is_actionable(self):
        with patch.object(Path,'open',side_effect=PermissionError),self.assertRaises(InputError):
            snapshot(Path('story.twee'))

    def check_publication_failure(self,target,error,expected=WriteError):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'story.twee'; source.write_bytes(fixture())
            occupied=source.with_name('story.layout.twee'); occupied.write_bytes(b'KEEP')
            with patch(target,side_effect=error),self.assertRaises(expected):
                publish(source,fixture(),lambda data: None,original=fixture())
            self.assertEqual(source.read_bytes(),fixture())
            self.assertEqual(occupied.read_bytes(),b'KEEP')
            self.assertEqual(sorted(p.name for p in Path(folder).iterdir()),['story.layout.twee','story.twee'])

    def test_permission_disk_full_publication_and_interrupt(self):
        self.check_publication_failure('twine_edge_overlap.files.tempfile.mkstemp',PermissionError())
        self.check_publication_failure('twine_edge_overlap.files.os.fsync',OSError(errno.ENOSPC,'disk full'))
        if os.name=='nt':
            self.check_publication_failure('twine_edge_overlap.files.os.rename',PermissionError())
        self.check_publication_failure('twine_edge_overlap.files.os.fsync',KeyboardInterrupt(),KeyboardInterrupt)

    def test_short_write_never_publishes_or_leaves_partial(self):
        real_fdopen=os.fdopen
        class ShortWriter:
            def __init__(self,fd,mode): self.stream=real_fdopen(fd,mode)
            def __enter__(self): return self
            def __exit__(self,*args): self.stream.close()
            def write(self,data): return self.stream.write(data[:-1])
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'story.twee';source.write_bytes(fixture())
            with patch('twine_edge_overlap.files.os.fdopen',side_effect=ShortWriter),self.assertRaises(WriteError):
                publish(source,fixture(),lambda data: None)
            self.assertEqual(list(Path(folder).iterdir()),[source])
            self.assertEqual(source.read_bytes(),fixture())

    def test_fdopen_failure_closes_reserved_file_before_cleanup(self):
        descriptors=[]
        def fail(fd,mode):
            descriptors.append(fd)
            raise OSError('stream creation failed')
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'story.twee';source.write_bytes(fixture())
            try:
                with patch('twine_edge_overlap.files.os.fdopen',side_effect=fail),self.assertRaises(WriteError):
                    publish(source,fixture(),lambda data: None)
                self.assertEqual(list(Path(folder).iterdir()),[source])
            finally:
                for fd in descriptors:
                    try: os.close(fd)
                    except OSError: pass

    def test_corrupt_temporary_copy_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'story.twee';source.write_bytes(fixture())
            real_read=Path.read_bytes
            def read(path): return b'CORRUPTED' if path.suffix=='.tmp' else real_read(path)
            with patch.object(Path,'read_bytes',read),self.assertRaises(IntegrityError):
                publish(source,fixture(),lambda data: None)
            self.assertEqual(list(Path(folder).iterdir()),[source])

    def test_collision_during_commit_preserves_racing_file(self):
        if os.name!='nt': self.skipTest('Windows commit strategy')
        real_rename=os.rename
        first=True
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'story.twee';source.write_bytes(fixture())
            def collide(a,b):
                nonlocal first
                if first:
                    first=False; Path(b).write_bytes(b'RACE'); raise FileExistsError()
                return real_rename(a,b)
            with patch('twine_edge_overlap.files.os.rename',side_effect=collide):
                output=publish(source,fixture(),lambda data: None)
            self.assertEqual(output.name,'story.layout-2.twee')
            self.assertEqual(source.with_name('story.layout.twee').read_bytes(),b'RACE')
