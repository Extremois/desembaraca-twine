import errno
import json
import os
import stat
import unittest
from unittest.mock import patch
from common import ROOT
from twine_edge_overlap import runtime
from twine_edge_overlap.errors import DependencyError
from runtime_support import synthetic_artifact,synthetic_runner,ControlledTransport,ControlledResponse,isolated_cache,blocked_network


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(blocked_network())

    def manager(self,root):
        artifact,data=synthetic_artifact()
        return runtime.RuntimeManager(artifact=artifact,cache_root=root,opener=ControlledTransport(data),runner=synthetic_runner)

    def junction(self,target,link):
        if os.name!='nt': self.skipTest('Real Windows junction test')
        import _winapi
        try:
            _winapi.CreateJunction(str(target),str(link))
        except PermissionError as exc:
            self.skipTest(f'Windows denied junction creation: {exc.winerror}')
        self.assertTrue(link.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)

    def test_existing_junctions_in_cache_selector_and_tree_are_rejected(self):
        for location in ('cache','selector','tree'):
            with self.subTest(location=location),isolated_cache() as root,isolated_cache() as external:
                sentinel=external/'outside.txt'
                sentinel.write_bytes(b'EXTERNAL MUST SURVIVE')
                cache=root/'cache'
                manager=self.manager(cache)
                previous=None
                preserved={}
                if location=='cache':
                    self.junction(external,cache)
                else:
                    previous=manager.ensure()
                    preserved={path:path.read_bytes() for path in previous.root.rglob('*') if path.is_file()}
                    if location=='selector':
                        selector=manager.root/'active.json'
                        selector.rename(manager.root/'saved-selector.json')
                        self.junction(external,selector)
                    else:
                        self.junction(external,previous.root/'outside')
                manager.opener=ControlledTransport(error=OSError('offline test'))
                manager.runner=lambda *a,**k:self.fail('unsafe cache payload executed')
                with self.assertRaises(DependencyError): manager.ensure()
                self.assertEqual(sentinel.read_bytes(),b'EXTERNAL MUST SURVIVE')
                self.assertEqual(sorted(p.name for p in external.iterdir()),['outside.txt'])
                for path,data in preserved.items(): self.assertEqual(path.read_bytes(),data)
                if previous: self.assertTrue(previous.executable.exists())

    def test_staging_and_pending_cleanup_do_not_follow_external_junctions(self):
        for location in ('staging','pending'):
            with self.subTest(location=location),isolated_cache() as root,isolated_cache() as external:
                sentinel=external/'outside.txt'
                sentinel.write_bytes(b'EXTERNAL MUST SURVIVE')
                manager=self.manager(root/'cache')
                previous=manager.ensure()
                selected=(manager.root/'active.json').read_bytes()
                old_files={path:path.read_bytes() for path in previous.root.rglob('*') if path.is_file()}
                def interrupt(stage):
                    if location=='staging' and stage=='generation':
                        staging=list(manager.root.glob('staging-*'))
                        self.assertEqual(len(staging),1)
                        self.junction(external,staging[0]/'outside')
                        raise OSError(errno.EACCES,'controlled failure before cleanup')
                    if location=='pending' and stage=='before_select':
                        pending=list(manager.root.glob('.active-*.tmp'))
                        self.assertEqual(len(pending),1)
                        # Replace this attempt's disposable selector with a directory link.
                        pending[0].unlink()
                        self.junction(external,pending[0])
                        raise OSError(errno.EACCES,'controlled failure before cleanup')
                manager.checkpoint=interrupt
                with self.assertRaises(DependencyError): manager.ensure(force_repair=True)
                self.assertEqual(sentinel.read_bytes(),b'EXTERNAL MUST SURVIVE')
                self.assertEqual(sorted(p.name for p in external.iterdir()),['outside.txt'])
                self.assertEqual((manager.root/'active.json').read_bytes(),selected)
                self.assertFalse(list(manager.root.glob('staging-*')))
                for path,data in old_files.items(): self.assertEqual(path.read_bytes(),data)
                manager.checkpoint=lambda stage:None
                manager.opener=ControlledTransport(error=AssertionError('unexpected network'))
                self.assertEqual(manager.ensure().generation_id,previous.generation_id)

    def test_successful_repair_preserves_previous_handle_and_changes_generation(self):
        with isolated_cache() as root:
            manager=self.manager(root)
            original=manager.ensure()
            replacement=manager.ensure(force_repair=True)
            self.assertNotEqual(original.generation_id,replacement.generation_id)
            self.assertTrue(original.executable.is_file())
            manager.opener=ControlledTransport(error=AssertionError('network'))
            with blocked_network(): self.assertEqual(manager.ensure().generation_id,replacement.generation_id)

    def test_interruption_at_each_transition_preserves_expected_selection(self):
        for stage in ('generation','validated','before_select','after_select'):
            with self.subTest(stage=stage),isolated_cache() as root:
                manager=self.manager(root)
                original=manager.ensure()
                def stop(current):
                    if current==stage: raise KeyboardInterrupt()
                manager.checkpoint=stop
                with self.assertRaises(KeyboardInterrupt): manager.ensure(force_repair=True)
                manager.checkpoint=lambda stage:None
                manager.opener=ControlledTransport(error=AssertionError('network'))
                with blocked_network(): current=manager.ensure()
                self.assertTrue(original.executable.exists())
                self.assertEqual(current.generation_id==original.generation_id,stage!='after_select')

    def test_failed_download_or_pointer_swap_preserves_healthy_runtime(self):
        for failure in ('download','swap'):
            with self.subTest(failure=failure),isolated_cache() as root:
                manager=self.manager(root)
                original=manager.ensure()
                if failure=='download': manager.opener=ControlledTransport(error=OSError('offline'))
                with patch.object(runtime.os,'replace',side_effect=PermissionError('busy')) if failure=='swap' else patch.object(manager,'progress'):
                    with self.assertRaises(DependencyError): manager.ensure(force_repair=True)
                manager.opener=ControlledTransport(error=AssertionError('network'))
                with blocked_network(): self.assertEqual(manager.ensure().generation_id,original.generation_id)

    def test_missing_extra_dll_and_false_ready_are_not_accepted(self):
        for defect in ('extra','missing','ready','selector'):
            with self.subTest(defect=defect),isolated_cache() as root:
                manager=self.manager(root)
                current=manager.ensure()
                if defect=='extra': (current.root/'extra.dll').write_bytes(b'bad')
                elif defect=='missing': current.executable.unlink()
                elif defect=='ready': (current.root/'ready.json').write_text('{}')
                else: (manager.root/'active.json').write_text(json.dumps({'artifact_identity':manager.artifact.identity,'generation_id':'../escape'}))
                manager.opener=ControlledTransport(error=OSError('offline'))
                with self.assertRaises(DependencyError): manager.ensure()

    def test_permission_space_timeout_and_probe_failures_are_actionable(self):
        for error in (PermissionError('blocked'),OSError(errno.ENOSPC,'full'),TimeoutError('late')):
            with self.subTest(error=type(error)),isolated_cache() as root:
                manager=self.manager(root)
                manager.opener=ControlledTransport(error=error)
                with self.assertRaises(DependencyError) as result: manager.ensure()
                self.assertIn('nenhuma cópia',str(result.exception))
                self.assertNotIn('Traceback',str(result.exception))
        with isolated_cache() as root:
            manager=self.manager(root)
            manager.runner=lambda *a,**k:runtime.run_bounded(['does-not-exist'])
            with self.assertRaises(DependencyError): manager.ensure()

    def test_cooperative_deadline_during_transfer_preserves_selection(self):
        clock=[100.0]
        with isolated_cache() as root,patch.object(runtime.time,'monotonic',side_effect=lambda:clock[0]):
            manager=self.manager(root)
            previous=manager.ensure()
            selection=(manager.root/'active.json').read_bytes()
            artifact,data=synthetic_artifact()
            class SlowResponse(ControlledResponse):
                def read(self,size=-1):
                    clock[0]+=301
                    return super().read(size)
            class Transport:
                def open(self,request,timeout):
                    self.timeout=timeout
                    return SlowResponse(data)
            transport=Transport()
            manager.opener=transport
            with self.assertRaisesRegex(DependencyError,'Prazo de preparação esgotado'):
                manager.ensure(force_repair=True)
            self.assertEqual(transport.timeout,30)
            self.assertEqual((manager.root/'active.json').read_bytes(),selection)
            self.assertEqual(manager.ensure().generation_id,previous.generation_id)

    def test_socket_and_probe_allowances_use_the_remaining_preparation_budget(self):
        for remaining in (300,5):
            clock=[100.0]
            with self.subTest(remaining=remaining),isolated_cache() as root,patch.object(runtime.time,'monotonic',side_effect=lambda:clock[0]):
                manager=self.manager(root)
                calls=[]
                original_download=manager.download
                def download(target):
                    clock[0]+=300-remaining
                    return original_download(target)
                def probe(command,**kwargs):
                    calls.append(kwargs)
                    return synthetic_runner(command,**kwargs)
                with patch.object(manager,'download',side_effect=download):
                    manager.runner=probe
                    manager.ensure()
                self.assertEqual(manager.opener.calls[0][1],min(30,remaining))
                self.assertEqual(len(calls),2)
                for call in calls:
                    self.assertEqual(call['timeout'],min(10,remaining))
                    self.assertEqual(call['max_output'],1024**2)

    def test_probe_rejections_leave_previous_runtime_usable(self):
        failures=('version','json','identities','position','returncode','timeout','output')
        for defect in failures:
            with self.subTest(defect=defect),isolated_cache() as root:
                manager=self.manager(root)
                previous=manager.ensure()
                selection=(manager.root/'active.json').read_bytes()
                def invalid_probe(command,**kwargs):
                    if defect in ('timeout','output'):
                        raise runtime.ProcessLimitError(defect)
                    result=synthetic_runner(command,**kwargs)
                    if defect=='version' and '-V' in command:
                        return type(result)(0,b'',b'graphviz 0.0.0')
                    if '-V' in command:
                        return result
                    if defect=='returncode': return type(result)(1,b'',b'failed')
                    if defect=='json': return type(result)(0,b'not json',b'')
                    data=json.loads(result.stdout)
                    if defect=='identities': data['objects'][1]['name']='unknown'
                    if defect=='position': data['objects'][0]['pos']='NaN,0'
                    return type(result)(0,json.dumps(data).encode(),b'')
                manager.runner=invalid_probe
                with self.assertRaises(DependencyError) as result:
                    manager.ensure(force_repair=True)
                self.assertIn('nenhuma cópia gerada',str(result.exception))
                self.assertIn('--repair-runtime',str(result.exception))
                self.assertEqual((manager.root/'active.json').read_bytes(),selection)
                manager.runner=synthetic_runner
                self.assertEqual(manager.ensure().generation_id,previous.generation_id)
