import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from common import ROOT
from runtime_support import synthetic_artifact, synthetic_runner, ControlledTransport, blocked_network
from twine_edge_overlap import runtime
from twine_edge_overlap.errors import DependencyError


class PosixRuntimeTests(unittest.TestCase):
    @unittest.skipIf(os.name=='nt','POSIX umask and private control-file modes')
    def test_private_directories_and_records_do_not_depend_on_umask(self):
        artifact,archive=synthetic_artifact('linux')
        with tempfile.TemporaryDirectory() as folder,blocked_network():
            previous=os.umask(0)
            try:
                manager=runtime.RuntimeManager(artifact=artifact,cache_root=Path(folder)/'cache',opener=ControlledTransport(archive),runner=synthetic_runner)
                handle=manager.ensure()
                for path in (manager.root/'active.json',manager.root/'prepare.lock',handle.root/'ready.json'):
                    self.assertEqual(path.stat().st_mode & 0o777,0o600)
                for path in (manager.anchor,manager.root,manager.root/'generations',handle.root/'bin'):
                    self.assertEqual(path.stat().st_mode & 0o777,0o700)
            finally:
                os.umask(previous)

    def test_schema_two_rejects_privileged_modes_or_nonexecutable_entry(self):
        artifact, archive = synthetic_artifact('linux')
        for mode in (0o644, 0o777, 0o4755):
            data = copy.deepcopy(artifact.data)
            data['files'][0]['mode'] = mode
            with tempfile.TemporaryDirectory() as folder, blocked_network():
                manifest = Path(folder) / 'manifest.json'
                manifest.write_text(json.dumps(data), encoding='utf-8')
                with self.assertRaises(DependencyError): runtime.load_manifest(manifest)

    def test_posix_identity_includes_abi_build_and_manifest(self):
        artifact, archive = synthetic_artifact('linux')
        identities = {artifact.identity}
        for key,value in [('abi','musl'),('build_variant','other-build'),('_manifest_sha256','f'*64)]:
            identities.add(runtime.Artifact(dict(artifact.data,**{key:value})).identity)
        self.assertEqual(len(identities),4)

    @unittest.skipIf(os.name=='nt','POSIX permission and symlink behavior needs POSIX')
    def test_modes_tamper_and_internal_symlink_do_not_run_or_escape(self):
        artifact,archive=synthetic_artifact('linux')
        with tempfile.TemporaryDirectory() as folder,blocked_network():
            root=Path(folder)
            manager=runtime.RuntimeManager(artifact=artifact,cache_root=root/'cache',opener=ControlledTransport(archive),runner=synthetic_runner)
            handle=manager.ensure()
            self.assertEqual(handle.executable.stat().st_mode & 0o777,0o755)
            self.assertEqual(handle.cwd,handle.root)
            handle.executable.chmod(0o644)
            manager.opener=ControlledTransport(error=OSError('controlled offline'))
            with self.assertRaises(DependencyError): manager.ensure()
            outside=root/'sentinel'
            outside.write_bytes(b'PRESERVE')
            handle.executable.unlink()
            handle.executable.symlink_to(outside)
            manager.runner=lambda *a,**k:self.fail('unsafe bytes executed')
            with self.assertRaises(DependencyError): manager.ensure()
            self.assertEqual(outside.read_bytes(),b'PRESERVE')
