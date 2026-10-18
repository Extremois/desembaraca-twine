"""Controlled crash/reader tests; do not qualify native artifact execution."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import threading
import unittest
from common import ROOT
from posix_support import private_test_directory
from integration import test_runtime_concurrency as concurrency
from runtime_support import synthetic_artifact,synthetic_runner,ControlledTransport,blocked_network
from twine_edge_overlap.runtime import RuntimeManager


class RuntimeCrashTests(unittest.TestCase):
    def test_death_during_staging_releases_lock_and_keeps_orphan_untouched(self):
        helper=concurrency.ConcurrentRuntimeTests()
        with private_test_directory() as root,blocked_network():
            root,artifact,payload,manifest,archive=helper.setup_paths(root)
            manager=RuntimeManager(artifact=artifact,cache_root=root/'cache',opener=ControlledTransport(payload),runner=synthetic_runner)
            previous=manager.ensure()
            selected=(manager.root/'active.json').read_bytes()
            child=subprocess.run(helper.command(root,manifest,archive,'during_download',root/'unused'),capture_output=True,timeout=15)
            self.assertEqual(child.returncode,77,child.stderr.decode(errors='replace'))
            orphans=set(manager.root.glob('staging-*'))
            self.assertEqual(len(orphans),1)
            manager.opener=ControlledTransport(error=AssertionError('network'))
            self.assertEqual(manager.ensure().generation_id,previous.generation_id)
            self.assertEqual((manager.root/'active.json').read_bytes(),selected)
            manager.opener=ControlledTransport(payload)
            manager.ensure(force_repair=True)
            self.assertTrue(previous.executable.is_file())
            self.assertTrue(all(path.is_dir() for path in orphans))

    def test_healthy_reader_and_old_handle_continue_while_repair_holds_lock(self):
        artifact,payload=synthetic_artifact('linux')
        with private_test_directory() as root,blocked_network(),ThreadPoolExecutor(max_workers=1) as pool:
            writer=RuntimeManager(artifact=artifact,cache_root=root,opener=ControlledTransport(payload),runner=synthetic_runner)
            previous=writer.ensure()
            started,release=threading.Event(),threading.Event()
            class Paused(ControlledTransport):
                def open(self,*args,**kwargs):
                    started.set()
                    if not release.wait(5):raise TimeoutError('test did not release writer')
                    return super().open(*args,**kwargs)
            writer.opener=Paused(payload)
            pending=pool.submit(writer.ensure,force_repair=True)
            try:
                self.assertTrue(started.wait(3))
                reader=RuntimeManager(artifact=artifact,cache_root=root,opener=ControlledTransport(error=AssertionError('network')),runner=synthetic_runner)
                self.assertEqual(reader.ensure().generation_id,previous.generation_id)
                self.assertTrue(previous.executable.is_file())
            finally:release.set()
            self.assertNotEqual(pending.result(timeout=10).generation_id,previous.generation_id)
            self.assertTrue(previous.executable.is_file())
