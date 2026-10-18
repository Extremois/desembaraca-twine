"""Controlled failure injection for both POSIX schemas, not native qualification."""
import errno
from pathlib import Path
import unittest
from common import ROOT
from posix_support import private_test_directory
from runtime_support import synthetic_artifact,synthetic_runner,ControlledTransport,blocked_network
from twine_edge_overlap.runtime import RuntimeManager
from twine_edge_overlap.errors import DependencyError


class PosixRecoveryTests(unittest.TestCase):
    def test_failed_repair_then_offline_reuse_and_successful_retry(self):
        for system in ('linux','darwin'):
            for error in (ConnectionError(),OSError(errno.ENOSPC,'private'),PermissionError(errno.EACCES,'private')):
                with self.subTest(system=system,error=type(error).__name__),private_test_directory() as folder,blocked_network():
                    artifact,payload=synthetic_artifact(system)
                    manager=RuntimeManager(artifact=artifact,cache_root=Path(folder),opener=ControlledTransport(payload),runner=synthetic_runner)
                    old=manager.ensure()
                    selected=(manager.root/'active.json').read_bytes()
                    manager.opener=ControlledTransport(error=error)
                    with self.assertRaises(DependencyError):manager.ensure(force_repair=True)
                    self.assertEqual((manager.root/'active.json').read_bytes(),selected)
                    manager.opener=ControlledTransport(error=AssertionError('network'))
                    self.assertEqual(manager.ensure().generation_id,old.generation_id)
                    manager.opener=ControlledTransport(payload)
                    self.assertNotEqual(manager.ensure(force_repair=True).generation_id,old.generation_id)
                    self.assertTrue(old.executable.is_file())

    def test_execution_denied_preserves_previous_generation_and_reports_recovery(self):
        for system in ('linux','darwin'):
            with self.subTest(system=system),private_test_directory() as folder,blocked_network():
                artifact,payload=synthetic_artifact(system)
                manager=RuntimeManager(artifact=artifact,cache_root=Path(folder),opener=ControlledTransport(payload),runner=synthetic_runner)
                previous=manager.ensure()
                selected=(manager.root/'active.json').read_bytes()
                def denied(*args,**kwargs):raise PermissionError(errno.EACCES,'private path')
                manager.runner=denied
                with self.assertRaisesRegex(DependencyError,'sistema negou a execução'):
                    manager.ensure(force_repair=True)
                self.assertEqual((manager.root/'active.json').read_bytes(),selected)
                manager.runner=synthetic_runner
                manager.opener=ControlledTransport(error=AssertionError('network'))
                self.assertEqual(manager.ensure().generation_id,previous.generation_id)
