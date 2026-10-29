import tempfile
from pathlib import Path
import unittest
from common import ROOT,fixture
from runtime_support import blocked_network,active_artifact
from twine_edge_overlap.runtime import ensure_runtime
from twine_edge_overlap.application import run


class ManagedRuntimeIntegrationTests(unittest.TestCase):
    def test_native_recovery_with_controlled_transfer_preserves_story_and_old_handle(self):
        import copy,hashlib,os
        from unittest.mock import patch
        from runtime_support import archive_bytes,ControlledTransport
        from twine_edge_overlap.runtime import Artifact,RuntimeManager,load_manifest
        from twine_edge_overlap.errors import DependencyError
        healthy=ensure_runtime()
        data=copy.deepcopy(active_artifact().data)
        # Repack verified native files only for a deterministic, offline transport seam.
        # This is not evidence for downloading or qualifying the original upstream ZIP.
        payload=archive_bytes({entry['path']:(healthy.root/entry['path']).read_bytes() for entry in data['files']})
        data.update(url='https://runtime.invalid/artifact.zip',allowed_redirect_hosts=['runtime.invalid'],archive_sha256=hashlib.sha256(payload).hexdigest())
        base=tempfile.gettempdir()
        if os.name=='nt' and not base.startswith('\\\\?\\'): base='\\\\?\\'+base
        with tempfile.TemporaryDirectory(dir=base) as folder,blocked_network():
            root=Path(folder)
            manager=RuntimeManager(artifact=Artifact(data),cache_root=root/'cache',opener=ControlledTransport(error=ConnectionError('offline')))
            source=root/'story.twee'
            original=fixture('crossing')
            source.write_bytes(original)
            provider=lambda:manager.ensure()
            with self.assertRaises(DependencyError): run(source,runtime_provider=provider)
            self.assertEqual(list(root.glob('*.layout*.twee')),[])
            manager.opener=ControlledTransport(payload)
            first=run(source,runtime_provider=provider)
            self.assertEqual(first.after.values,(0,0,0))
            previous=manager.ensure()
            preserved=first.path.read_bytes()
            manager.opener=ControlledTransport(error=ConnectionError('offline'))
            with self.assertRaises(DependencyError): manager.ensure(force_repair=True)
            self.assertEqual(manager.ensure().generation_id,previous.generation_id)
            self.assertTrue(previous.executable.is_file())
            tampered=next((entry['path'] for entry in data['files'] if entry['path']!=data['executable_relative_path']),data['executable_relative_path'])
            (previous.root/tampered).write_bytes(b'altered')
            with self.assertRaises(DependencyError): run(source,runtime_provider=provider)
            manager.opener=ControlledTransport(payload)
            recovered=run(source,runtime_provider=provider)
            self.assertEqual(recovered.after.values,(0,0,0))
            self.assertNotEqual(manager.ensure().generation_id,previous.generation_id)
            self.assertEqual(first.path.read_bytes(),preserved)
            self.assertEqual(source.read_bytes(),original)

    def test_real_generation_in_unicode_cache_ignores_system_settings(self):
        import json,shutil,os
        from unittest.mock import patch
        from twine_edge_overlap.runtime import RuntimeManager
        handle=ensure_runtime()
        # Keep the cleanup path in the same long-path namespace as the cache contents.
        temporary_base=tempfile.gettempdir()
        if os.name=='nt' and not temporary_base.startswith('\\\\?\\'):
            temporary_base='\\\\?\\'+temporary_base
        with tempfile.TemporaryDirectory(dir=temporary_base) as folder:
            manager=RuntimeManager(artifact=active_artifact(),cache_root=Path(folder)/('cache com acentos ação '+('longo '*12)).rstrip())
            target=manager.root/'generations'/handle.generation_id
            target.parent.mkdir(parents=True)
            shutil.copytree(handle.root,target)
            (manager.root/'active.json').write_text(json.dumps({'artifact_identity':handle.identity,'generation_id':handle.generation_id}))
            with blocked_network(),patch.dict(os.environ,{'TWINE_GRAPHVIZ_DOT':'C:/inexistente/dot.exe','GVBINDIR':'C:/incompatível'}),patch('shutil.which',side_effect=AssertionError('system lookup')):
                selected=manager.ensure()
            self.assertEqual(selected.generation_id,handle.generation_id)
            self.assertGreater(len(str(selected.executable.parent)),260)
            self.assertEqual(selected.cwd,manager.root.parent if os.name=='nt' else selected.root)

    def test_managed_motor_produces_same_identities(self):
        import time
        from twine_edge_overlap.formats.profile import parse
        from twine_edge_overlap.engines.graphviz import layout
        handle=ensure_runtime()
        document=parse(fixture('crossing'))
        with blocked_network():
            result=layout(document,time.monotonic()+30,runtime=handle)
        self.assertEqual(set(result),{node.id for node in document.nodes})

    def test_reference_layouts_without_network_or_system_discovery(self):
        import json
        runtime=ensure_runtime()
        cases=json.loads((ROOT/'tests/fixtures/cases.json').read_text())
        with blocked_network(),tempfile.TemporaryDirectory() as folder:
            for case in cases:
                source=Path(folder)/case['file']
                original=fixture(case['case'])
                source.write_bytes(original)
                result=run(source,runtime_provider=lambda:runtime)
                self.assertEqual(source.read_bytes(),original)
                self.assertTrue(all(a<=b for a,b in zip(result.after.values,result.before.values)))
                if case['known_resolvable']: self.assertEqual(result.after.values,(0,0,0))
