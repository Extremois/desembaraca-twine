from pathlib import Path
import os
import json
import subprocess
import sys
import tempfile
import unittest
import time
from common import ROOT
from runtime_support import synthetic_artifact,synthetic_runner,ControlledTransport,blocked_network
from twine_edge_overlap.runtime import RuntimeManager,load_manifest
from twine_edge_overlap.errors import DependencyError


CHILD = r'''
import sys, json, os, time
from pathlib import Path
sys.path.insert(0,sys.argv[1])
sys.path.insert(0,sys.argv[2])
from runtime_support import ControlledTransport,synthetic_runner
from twine_edge_overlap.runtime import RuntimeManager,load_manifest
cache,manifest,archive,stage,result=sys.argv[3:]
def checkpoint(current):
    if current==stage: os._exit(77)
class SlowTransport(ControlledTransport):
    def open(self,*args,**kwargs):
        if stage=='during_download': os._exit(77)
        time.sleep(.3)
        return super().open(*args,**kwargs)
manager=RuntimeManager(artifact=load_manifest(manifest),cache_root=cache,opener=SlowTransport(Path(archive).read_bytes()),runner=synthetic_runner,checkpoint=checkpoint)
handle=manager.ensure(force_repair=stage!='normal')
Path(result).write_text(handle.generation_id)
'''


class ConcurrentRuntimeTests(unittest.TestCase):
    @unittest.skipUnless(os.name=='nt','Windows byte-range locking')
    def test_empty_windows_lock_contender_waits_without_writing_locked_byte(self):
        import msvcrt
        from twine_edge_overlap.runtime_platform import preparation_lock
        contender = r'''
import sys,time
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from twine_edge_overlap.runtime_platform import preparation_lock,LockBusyError
try:
    with preparation_lock(Path(sys.argv[2]),deadline=time.monotonic()+.2,check=lambda:None):
        raise AssertionError('contender acquired owner lock')
except LockBusyError:
    pass
'''
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'prepare.lock'
            with path.open('w+b',buffering=0) as owner:
                msvcrt.locking(owner.fileno(),msvcrt.LK_NBLCK,1)
                try:
                    result=subprocess.run([sys.executable,'-c',contender,str(ROOT/'src'),str(path)],capture_output=True,timeout=5)
                    self.assertEqual(result.returncode,0,result.stderr.decode(errors='replace'))
                    self.assertEqual(path.stat().st_size,0)
                finally:
                    owner.seek(0)
                    msvcrt.locking(owner.fileno(),msvcrt.LK_UNLCK,1)
            with preparation_lock(path,deadline=time.monotonic()+1,check=lambda:None):
                self.assertEqual(path.stat().st_size,0)

    def test_lock_wait_is_bounded_and_does_not_stop_owner(self):
        holder = r'''
import sys,time
from pathlib import Path
sys.path[:0]=sys.argv[1:3]
from twine_edge_overlap.runtime import RuntimeManager,load_manifest
manager=RuntimeManager(artifact=load_manifest(sys.argv[3]),cache_root=sys.argv[4])
manager.deadline=time.monotonic()+300
with manager.locked():
    Path(sys.argv[5]).write_text('locked')
    sys.stdin.readline()
'''
        with tempfile.TemporaryDirectory() as folder:
            root,artifact,archive,manifest,zip_path=self.setup_paths(folder)
            signal=root/'locked.txt'
            child=subprocess.Popen([sys.executable,'-c',holder,str(ROOT/'src'),str(ROOT/'tests'),str(manifest),str(root/'cache'),str(signal)],stdin=subprocess.PIPE,stderr=subprocess.PIPE)
            try:
                until=time.monotonic()+10
                while not signal.exists() and time.monotonic()<until:
                    self.assertIsNone(child.poll())
                    time.sleep(.02)
                self.assertTrue(signal.exists())
                manager=RuntimeManager(artifact=artifact,cache_root=root/'cache',opener=ControlledTransport(archive),runner=synthetic_runner)
                started=time.monotonic()
                with self.assertRaisesRegex(DependencyError,'Outra preparação'):
                    manager.ensure()
                self.assertGreaterEqual(time.monotonic()-started,9.9)
                self.assertLess(time.monotonic()-started,12)
                self.assertIsNone(child.poll())
                child.communicate(b'continue\n',timeout=5)
                self.assertEqual(child.returncode,0)
                manager.ensure()
            finally:
                if child.poll() is None:
                    child.kill()
                    child.communicate()

    def setup_paths(self,folder):
        root=Path(folder)
        # Controlled payload for the host's runtime schema, not native engine evidence.
        artifact,archive=synthetic_artifact(sys.platform if sys.platform in ('linux','darwin') else None)
        manifest=root/'manifest.json'
        manifest.write_text(json.dumps({key:value for key,value in artifact.data.items() if not key.startswith('_')}),encoding='utf-8')
        artifact=load_manifest(manifest)
        zip_path=root/'archive.zip'
        zip_path.write_bytes(archive)
        return root,artifact,archive,manifest,zip_path

    def command(self,root,manifest,archive,stage,result):
        return [sys.executable,'-c',CHILD,str(ROOT/'src'),str(ROOT/'tests'),str(root/'cache'),str(manifest),str(archive),stage,str(result)]

    def test_two_first_runs_select_same_generation(self):
        with tempfile.TemporaryDirectory() as folder:
            root,artifact,archive,manifest,zip_path=self.setup_paths(folder)
            outputs=[root/'first.txt',root/'second.txt']
            children=[subprocess.Popen(self.command(root,manifest,zip_path,'normal',output),stdout=subprocess.PIPE,stderr=subprocess.PIPE) for output in outputs]
            try:
                for child in children:
                    stdout,stderr=child.communicate(timeout=15)
                    self.assertEqual(child.returncode,0,stderr.decode(errors='replace'))
                self.assertEqual(outputs[0].read_text(),outputs[1].read_text())
            finally:
                for child in children:
                    if child.poll() is None: child.kill(); child.wait()

    def test_abrupt_exit_before_and_after_selection_is_offline_recoverable(self):
        for stage in ('before_select','after_select'):
            with self.subTest(stage=stage),tempfile.TemporaryDirectory() as folder:
                root,artifact,archive,manifest,zip_path=self.setup_paths(folder)
                manager=RuntimeManager(artifact=artifact,cache_root=root/'cache',opener=ControlledTransport(archive),runner=synthetic_runner)
                original=manager.ensure()
                result=subprocess.run(self.command(root,manifest,zip_path,stage,root/'unused.txt'),capture_output=True,timeout=15)
                self.assertEqual(result.returncode,77,result.stderr.decode(errors='replace'))
                manager.opener=ControlledTransport(error=AssertionError('network'))
                with blocked_network(): selected=manager.ensure()
                self.assertEqual(selected.generation_id==original.generation_id,stage=='before_select')
                self.assertTrue(original.executable.is_file())
                # A force preparation proves that the OS released the dead process's lock.
                manager.opener=ControlledTransport(archive)
                manager.ensure(force_repair=True)
