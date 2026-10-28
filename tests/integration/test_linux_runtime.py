"""Run only with a real Linux candidate; skipped drivers never approve the matrix."""
import os
import errno
import sys
import unittest
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import tempfile
from unittest.mock import patch
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common import ROOT,fixture
from runtime_support import ControlledTransport,blocked_network
from twine_edge_overlap.runtime import RuntimeManager,load_manifest
from twine_edge_overlap.errors import DependencyError
from twine_edge_overlap.application import run
from twine_edge_overlap.formats.profile import parse,verify
from native_acceptance import InstalledCandidateAcceptance


@unittest.skipUnless(sys.platform.startswith('linux') and os.environ.get('TWINE_NATIVE_ACCEPTANCE')=='1',
                     'Requires explicit real Linux candidate and existing native SDK; no approval from skip')
class LinuxCandidateAcceptanceTests(InstalledCandidateAcceptance,unittest.TestCase):
    pass


class LinuxPrivateBundleIntegrationTests(unittest.TestCase):
    """Real native bytes; controlled transfer is never distribution qualification."""
    configuration=None
    review_directory=None
    observations={}
    platform_name='linux'

    @classmethod
    def setUpClass(cls):
        if sys.platform!=cls.platform_name or cls.configuration is None:
            raise unittest.SkipTest('Requires explicit matching private bundle; no approval from skip')
        package,provenance=cls.configuration
        cls.record=json.loads(provenance.read_bytes())
        candidate=json.loads((package/'candidate.json').read_bytes())
        inventory_raw=(package/'inventory.json').read_bytes()
        cls.inventory=json.loads(inventory_raw)
        cls.payload=(package/'candidate.zip').read_bytes()
        digest=lambda raw:hashlib.sha256(raw).hexdigest()
        arch={'AMD64':'x86_64','arm64':'aarch64'}.get(platform.machine(),platform.machine())
        if (not cls.record.get('completed') or cls.record['native_os']!=cls.platform_name
                or cls.record['native_arch']!=arch or candidate['artifact_id']!=cls.record['artifact_id']
                or digest(cls.payload)!=candidate['archive_sha256']
                or digest(inventory_raw)!=candidate['inventory_sha256']
                or digest(provenance.read_bytes())!=candidate['provenance_sha256']
                or cls.inventory['provenance_sha256']!=candidate['provenance_sha256']):
            raise ValueError('Private bundle does not match completed native build and inventory')
        cls.observations={}

    def cache_configuration(self,work):
        xdg=work/'cache com espaços ação'
        return {'XDG_CACHE_HOME':str(xdg)},xdg

    def inspect_prepared_runtime(self,handle):
        return {}

    def process_recovery(self):
        path=ROOT/'.github/scripts/probe-installed-recovery.py'
        spec=importlib.util.spec_from_file_location('installed_process_recovery',path)
        driver=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(driver)
        return driver.exercise(SimpleNamespace(driver=ROOT),self,process_only=True)

    def failed_repairs(self, manager, previous, work):
        """Real cached engine; transport/disk failures are explicit injections."""
        selected = (manager.root/'active.json').read_bytes()
        runner = manager.runner
        references = [item for item in json.loads((ROOT/'tests/fixtures/cases.json').read_bytes())
                      if item['known_resolvable']]
        observations = {}
        for name in ('transfer', 'disk-space', 'corrupt-archive', 'execution-denied'):
            denial = []
            def denied_runner(argv, **kwargs):
                target = Path(argv[0])
                self.assertNotEqual(target, previous.executable)
                target.chmod(0o644)
                try:
                    return runner(argv, **kwargs)
                except PermissionError:
                    denial.append(True)
                    raise
            if name == 'transfer':
                transport = ControlledTransport(error=ConnectionError('injected transfer failure'))
            elif name == 'disk-space':
                transport = ControlledTransport(error=OSError(errno.ENOSPC, 'injected disk exhaustion'))
            elif name == 'corrupt-archive':
                transport = ControlledTransport(self.payload + b'corrupted')
            else:
                transport = ControlledTransport(self.payload)
                manager.runner = denied_runner
            manager.opener = transport
            try:
                with self.assertRaises(DependencyError):
                    manager.ensure(force_repair=True)
            finally:
                manager.runner = runner
            self.assertEqual(len(transport.calls), 1)
            self.assertEqual((manager.root/'active.json').read_bytes(), selected)
            if name == 'execution-denied':
                self.assertTrue(denial, 'Expected native exec permission failure')
            offline = ControlledTransport(error=AssertionError('Failed repair attempted offline acquisition'))
            manager.opener = offline
            self.assertEqual(manager.ensure().generation_id, previous.generation_id)
            rows = []
            for item in references:
                original = fixture(item['case'])
                story = work/('recovery-'+name+'-'+item['file'])
                story.write_bytes(original)
                # Exercise the returned previous handle directly, then the manager.
                result = run(story, runtime_provider=lambda: previous)
                verify(parse(original), parse(result.path.read_bytes()))
                self.assertEqual(story.read_bytes(), original)
                self.assertEqual(result.after.values, (0, 0, 0))
                rows.append(dict(case=item['case'], after=result.after.values,
                    input_sha256=hashlib.sha256(original).hexdigest(),
                    output_sha256=hashlib.sha256(result.path.read_bytes()).hexdigest(),
                    original_preserved=True, semantic_preserved=True))
            self.assertEqual(manager.ensure().generation_id, previous.generation_id)
            self.assertFalse(offline.calls)
            observations[name] = dict(selected_generation_preserved=True, previous_handle_usable=True,
                failed_repair_acquisition_calls=len(transport.calls), offline_acquisition_calls=0,
                failure_injection='native chmod/exec denial' if name == 'execution-denied' else 'controlled transport',
                real_execution_denial=bool(denial), references=rows)
        return observations

    def exercise(self,automatic):
        with tempfile.TemporaryDirectory(prefix=self.platform_name+'-runtime-integration-') as folder,blocked_network():
            work=Path(folder)
            cache_environment,cache_base=self.cache_configuration(work)
            data=dict(load_manifest().data)
            data.update(schema_version=2,platform=self.platform_name,artifact_arch=self.record['native_arch'],
                abi=self.record['recipe']['abi'],build_variant='private-integration-only',
                minimum_libc='0',minimum_kernel='0',minimum_os='15',files=self.inventory['files'],
                executable_relative_path='bin/dot',generated_files=[],
                url='https://runtime.invalid/artifact.zip',allowed_redirect_hosts=['runtime.invalid'],
                archive_sha256=hashlib.sha256(self.payload).hexdigest())
            # Keep an application-packaged notice without colliding with bundle notices.
            data['notices']=[dict(data['notices'][0],destination='third-party-notices/private-integration-application.txt')]
            data.pop('plugin_relative_path',None)
            manifest=work/'private-fixture.json'
            manifest.write_text(json.dumps(data),encoding='utf-8')
            artifact=load_manifest(manifest)
            transport=ControlledTransport(self.payload)
            probes=[]
            from twine_edge_overlap.engines.process import run_bounded
            def actual_runner(argv,**kwargs):
                if '-V' in argv:
                    probes.append(dict(final_destination='generations' in Path(argv[0]).parts,
                        ready_before_probe=(Path(argv[0]).parent.parent/'ready.json').exists()))
                return run_bounded(argv,**kwargs)
            with patch.dict(os.environ,cache_environment):
                manager=RuntimeManager(artifact=artifact,opener=transport,runner=actual_runner)
                self.assertTrue(manager.root.is_relative_to(cache_base/'DesembaracaTwine/runtimes/graphviz'))
                provider=lambda:manager.ensure()
                source=work/'entrada com espaços ação.twee'
                source.write_bytes(fixture('crossing'))
                if automatic:
                    self.assertFalse(manager.root.exists())
                    first=run(source,runtime_provider=provider)
                    self.assertEqual(first.after.values,(0,0,0))
                else:
                    manager.ensure()
                self.assertEqual(len(transport.calls),1)
                handle=manager.ensure()
                self.assertEqual(handle.executable.stat().st_mode&0o777,0o755)
                self.assertEqual(handle.root.stat().st_mode&0o777,0o700)
                self.assertEqual(hashlib.sha256(handle.executable.read_bytes()).hexdigest(),self.record['executable_sha256'])
                self.assertTrue(probes and all(row['final_destination'] for row in probes))
                self.assertFalse(probes[0]['ready_before_probe'])
                native_inspection=self.inspect_prepared_runtime(handle)
                recovery={} if automatic else self.failed_repairs(manager,handle,work)
                process_recovery={} if automatic else self.process_recovery()
                manager.opener=ControlledTransport(error=AssertionError('Offline cache attempted acquisition'))
                # Also run from another cwd; the cache and story use absolute paths.
                previous=Path.cwd()
                os.chdir(work)
                cases=[]
                try:
                    selected=json.loads((ROOT/'tests/fixtures/cases.json').read_text())
                    if automatic:selected=[row for row in selected if row['case']=='crossing']
                    for case in selected:
                        original=fixture(case['case'])
                        story=work/case['file'];story.write_bytes(original)
                        result=run(story,runtime_provider=provider)
                        output=result.path.read_bytes()
                        verify(parse(original),parse(output))
                        self.assertEqual(story.read_bytes(),original)
                        self.assertTrue(all(a<=b for a,b in zip(result.after.values,result.before.values)))
                        if case['known_resolvable']:self.assertEqual(result.after.values,(0,0,0))
                        if not automatic and case['known_resolvable'] and self.review_directory is not None:
                            with (self.review_directory/case['file']).open('xb') as exported:
                                exported.write(output)
                        cases.append(dict(case=case['case'],input_sha256=hashlib.sha256(original).hexdigest(),
                            output_sha256=hashlib.sha256(output).hexdigest(),before=result.before.values,after=result.after.values))
                finally:os.chdir(previous)
                self.assertEqual(manager.ensure().generation_id,handle.generation_id)
                self.assertEqual(manager.opener.calls,[])
                self.observations['automatic' if automatic else 'explicit']=dict(cases=cases,
                    acquisition_calls=1,offline_acquisition_calls=0,cache_xdg=self.platform_name=='linux',executable_mode=0o755,
                    generation_mode=0o700,final_destination_probe=True,probe_before_ready=True,
                    healthy_generation_reused=True,external_unicode_paths=True,real_engine=True,
                    fixture_transport=True,native_inspection=native_inspection,recovery=recovery,
                    process_recovery=process_recovery)

    def test_automatic_first_use_and_healthy_offline_cache(self):
        self.exercise(True)

    def test_explicit_preparation_and_thirteen_offline_cases(self):
        self.exercise(False)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    for name in ('package','provenance','report'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--review-directory',type=Path)
    parser.add_argument('--environment-kind',choices=('native','container','wsl'),required=True)
    args=parser.parse_args()
    if args.report.exists():parser.error('Report must be new')
    LinuxPrivateBundleIntegrationTests.configuration=(args.package.resolve(),args.provenance.resolve())
    LinuxPrivateBundleIntegrationTests.review_directory=args.review_directory
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(LinuxPrivateBundleIntegrationTests)
    result=unittest.TextTestRunner(stream=sys.stdout,verbosity=1).run(suite)
    observations=LinuxPrivateBundleIntegrationTests.observations
    report=dict(kind='linux-private-bundle-runtime-integration',passed=result.wasSuccessful(),qualified=False,
        environment_kind=args.environment_kind,python=platform.python_version(),arch=platform.machine(),
        engine_sha256=LinuxPrivateBundleIntegrationTests.record['executable_sha256'],
        provenance_sha256=hashlib.sha256(args.provenance.read_bytes()).hexdigest(),
        observations=observations,cases=observations.get('explicit',{}).get('cases',[]),
        scope='Real native engine and production manager; controlled acquisition fixture, not distributed-candidate acceptance')
    args.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    sys.exit(not result.wasSuccessful())
