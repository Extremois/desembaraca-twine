"""Native macOS manager integration; signed distribution acceptance is separate.

Only acquisition uses a controlled fixture. Engine execution, cache/probes,
permissions, Mach-O inspection and platform security observations are real.
Simulated tests explicitly record environment_kind='simulated' and simulation=True,
ensuring mocks never falsely qualify a target.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import struct
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'src')]
from common import ROOT, fixture
from integration import test_linux_runtime as linux
from native_acceptance import InstalledCandidateAcceptance
from posix_support import simulated_runtime
from runtime_support import blocked_network, synthetic_runner
from twine_edge_overlap import runtime
from twine_edge_overlap.application import run
from twine_edge_overlap.engines.process import ProcessResult, run_bounded
from twine_edge_overlap.errors import DependencyError
from twine_edge_overlap.formats.profile import parse, verify
from twine_edge_overlap.runtime_catalog import GATES, support_status
from twine_edge_overlap.runtime_platform import cache_directory, HostEnvironment


def load_inspector():
    spec=importlib.util.spec_from_file_location('macos_runtime_inspector',ROOT/'tools/runtime/verify-artifact.py')
    inspector=importlib.util.module_from_spec(spec);spec.loader.exec_module(inspector)
    return inspector


def security_snapshot():
    observations={}
    for name,command in (('gatekeeper',['/usr/sbin/spctl','--status']),
                         ('sip',['/usr/bin/csrutil','status'])):
        result=run_bounded(command,timeout=10,max_output=65536)
        observations[name]=dict(returncode=result.returncode,
            output=(result.stdout+result.stderr).decode('utf-8',errors='strict').strip())
    return observations


@unittest.skipUnless(sys.platform=='darwin' and os.environ.get('TWINE_NATIVE_ACCEPTANCE')=='1',
    'Requires explicit installed macOS candidate; no approval from skip')
class MacCandidateAcceptanceTests(InstalledCandidateAcceptance,unittest.TestCase):
    """Requires normal codesign/spctl checks in the installed-candidate worker."""


class MacOSPrivateBundleIntegrationTests(linux.LinuxPrivateBundleIntegrationTests):
    platform_name='darwin'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.security_before=security_snapshot()
        cls.inspector=load_inspector()

    def cache_configuration(self,work):
        home=work/'usuário com espaços ação';home.mkdir()
        # HOME is isolated; cache_directory and all native execution stay real.
        return {'HOME':str(home)},(home/'Library/Caches').resolve()

    def inspect_prepared_runtime(self,handle):
        self.inspector.macho_architecture(handle.executable,self.record['native_arch'])
        libraries=run_bounded(['/usr/bin/otool','-L',str(handle.executable)],timeout=10,max_output=1024**2)
        commands=run_bounded(['/usr/bin/otool','-l',str(handle.executable)],timeout=10,max_output=1024**2)
        self.assertEqual(libraries.returncode,0);self.assertEqual(commands.returncode,0)
        dependencies=self.inspector.darwin_dependencies(libraries.stdout.decode('utf-8'),
            ['/usr/lib/libSystem.B.dylib','/usr/lib/libc++.1.dylib'])
        attributes=run_bounded(['/usr/bin/xattr',str(handle.executable)],timeout=10,max_output=65536)
        self.assertEqual(attributes.returncode,0)
        self.assertNotIn('LC_RPATH',commands.stdout.decode('utf-8'))
        self.assertEqual(security_snapshot(),self.security_before)
        return dict(thin_native_macho=True,system_libraries=dependencies,rpath=[],
            relocation='No private dylibs or search paths; system dylibs only',
            library_commands_sha256=hashlib.sha256(libraries.stdout).hexdigest(),
            load_commands_sha256=hashlib.sha256(commands.stdout).hexdigest(),
            cache_library_caches=True,quarantine_present='com.apple.quarantine' in attributes.stdout.decode('utf-8').splitlines(),
            security_settings_unchanged=True,signature_notarization_approved=False)


class MacOSSimulatedRuntimeIntegrationTests(unittest.TestCase):
    """Deterministic simulation of macOS runtime contracts and verification invariants.

    All simulated observations explicitly record `environment_kind='simulated'` and
    `simulation=True` to enforce that mock runs never falsely qualify a target.
    """

    @classmethod
    def setUpClass(cls):
        cls.inspector = load_inspector()

    def test_probe_timing_and_final_destination(self):
        with simulated_runtime('darwin') as (root, transport, host):
            probes = []
            def recording_runner(command, **kwargs):
                if '-V' in command:
                    exe = Path(command[0])
                    probes.append(dict(
                        final_destination='generations' in exe.parts,
                        ready_before_probe=(exe.parent.parent / 'ready.json').exists(),
                    ))
                return synthetic_runner(command, **kwargs)

            manager = runtime.RuntimeManager()
            manager.runner = recording_runner
            handle = manager.ensure()

            self.assertTrue(probes and all(p['final_destination'] for p in probes))
            self.assertFalse(probes[0]['ready_before_probe'])
            self.assertTrue((handle.root / 'ready.json').is_file())
            active_before = (manager.root / 'active.json').read_text(encoding='utf-8')

            def failing_runner(command, **kwargs):
                if '-V' in command:
                    return ProcessResult(1, b'', b'probe failure')
                return synthetic_runner(command, **kwargs)

            failing_manager = runtime.RuntimeManager()
            failing_manager.runner = failing_runner
            with self.assertRaises(DependencyError):
                failing_manager.ensure(force_repair=True)

            # Invariant: failed repair preserves prior active selector and remains reusable
            self.assertEqual((manager.root / 'active.json').read_text(encoding='utf-8'), active_before)
            reused_handle = manager.ensure()
            self.assertEqual(reused_handle.generation_id, handle.generation_id)

    def test_library_caches_and_environment_isolation(self):
        with simulated_runtime('darwin') as (root, transport, host):
            expected_cache = root.resolve() / 'Library/Caches/DesembaracaTwine/runtimes/graphviz'
            self.assertEqual(cache_directory(host, environ={}, home=root), expected_cache)
            # macOS convention strictly ignores XDG_CACHE_HOME override
            self.assertEqual(cache_directory(host, environ={'XDG_CACHE_HOME': '/unwanted/xdg'}, home=root), expected_cache)

            manager = runtime.RuntimeManager()
            handle = manager.ensure()
            for forbidden_var in ('DYLD_LIBRARY_PATH', 'DYLD_FALLBACK_LIBRARY_PATH', 'LD_LIBRARY_PATH'):
                self.assertNotIn(forbidden_var, handle.env)
            self.assertIn('GVBINDIR', handle.env)

            if os.name != 'nt':
                self.assertEqual(handle.root.stat().st_mode & 0o777, 0o700)
                self.assertEqual(handle.executable.stat().st_mode & 0o777, 0o755)

    def test_relocation_and_macho_verification_contracts(self):
        with tempfile.TemporaryDirectory() as folder:
            temp_dir = Path(folder)
            for arch_name, cpu_magic in (('x86_64', 0x01000007), ('aarch64', 0x0100000c)):
                macho_file = temp_dir / f'test_{arch_name}'
                macho_file.write_bytes(b'\xcf\xfa\xed\xfe' + struct.pack('<I', cpu_magic))
                self.inspector.macho_architecture(macho_file, arch_name)
                wrong_arch = 'aarch64' if arch_name == 'x86_64' else 'x86_64'
                with self.assertRaises(ValueError):
                    self.inspector.macho_architecture(macho_file, wrong_arch)
                # Unsupported architecture name
                with self.assertRaises(ValueError):
                    self.inspector.macho_architecture(macho_file, 'armv7')

            invalid_bin = temp_dir / 'invalid_bin'
            invalid_bin.write_bytes(b'\x7fELF\x02\x01\x01\x00')
            with self.assertRaises(ValueError):
                self.inspector.macho_architecture(invalid_bin, 'x86_64')

            # Boundary edge cases: truncated files (< 8 bytes)
            for length in (0, 4, 7):
                trunc_file = temp_dir / f'trunc_{length}'
                trunc_file.write_bytes(b'\xcf\xfa\xed\xfe'[:length])
                with self.assertRaises(ValueError):
                    self.inspector.macho_architecture(trunc_file, 'x86_64')

            # Big-endian thin Mach-O 64-bit
            be_macho = temp_dir / 'macho_be'
            be_macho.write_bytes(b'\xfe\xed\xfa\xcf' + struct.pack('>I', 0x01000007))
            with self.assertRaises(ValueError):
                self.inspector.macho_architecture(be_macho, 'x86_64')

            # Universal / FAT Mach-O binaries
            for magic in (b'\xca\xfe\xba\xbe', b'\xbe\xba\xfe\xca'):
                fat_macho = temp_dir / 'macho_fat'
                fat_macho.write_bytes(magic + b'\x00' * 4)
                with self.assertRaises(ValueError):
                    self.inspector.macho_architecture(fat_macho, 'x86_64')

            # 32-bit Mach-O
            macho_32 = temp_dir / 'macho_32'
            macho_32.write_bytes(b'\xce\xfa\xed\xfe' + struct.pack('<I', 7))
            with self.assertRaises(ValueError):
                self.inspector.macho_architecture(macho_32, 'x86_64')

        allowed_dylibs = ['/usr/lib/libSystem.B.dylib', '/usr/lib/libc++.1.dylib']
        valid_otool_output = (
            '/opt/twine/bin/dot:\n'
            '\t/usr/lib/libSystem.B.dylib (compatibility version 1.0.0, current version 1319.0.0)\n'
            '\t/usr/lib/libc++.1.dylib (compatibility version 1.0.0, current version 1300.23.0)\n'
        )
        observed = self.inspector.darwin_dependencies(valid_otool_output, allowed_dylibs)
        self.assertEqual(observed, allowed_dylibs)

        # Relocation via @loader_path: rejected when not in allowed list
        loader_path_otool_output = (
            '/opt/twine/bin/dot:\n'
            '\t/usr/lib/libSystem.B.dylib (compatibility version 1.0.0, current version 1319.0.0)\n'
            '\t@loader_path/../lib/libplugin.dylib (compatibility version 1.0.0, current version 1.0.0)\n'
        )
        with self.assertRaises(ValueError):
            self.inspector.darwin_dependencies(loader_path_otool_output, allowed_dylibs)

        # Relocation via @loader_path: accepted when explicitly in approved list
        extended_allowed = allowed_dylibs + ['@loader_path/../lib/libplugin.dylib']
        observed_relocated = self.inspector.darwin_dependencies(loader_path_otool_output, extended_allowed)
        self.assertEqual(observed_relocated, ['/usr/lib/libSystem.B.dylib', '@loader_path/../lib/libplugin.dylib'])

        # Unapproved absolute library path rejection
        unapproved_otool_output = (
            '/opt/twine/bin/dot:\n'
            '\t/usr/lib/libSystem.B.dylib (compatibility version 1.0.0, current version 1319.0.0)\n'
            '\t/usr/local/lib/libunapproved.dylib (compatibility version 1.0.0, current version 1.0.0)\n'
        )
        with self.assertRaises(ValueError):
            self.inspector.darwin_dependencies(unapproved_otool_output, allowed_dylibs)

        # Missing or empty dependency text rejection
        for empty_text in ('/opt/twine/bin/dot:\n', '', '   \n  \n'):
            with self.assertRaises(ValueError):
                self.inspector.darwin_dependencies(empty_text, allowed_dylibs)

    def test_offline_reference_execution_and_preservation(self):
        with simulated_runtime('darwin') as (root, transport, host):
            manager = runtime.RuntimeManager()
            handle = manager.ensure()
            initial_calls = len(transport.calls)
            self.assertEqual(initial_calls, 1)

            cases_json = json.loads((ROOT / 'tests/fixtures/cases.json').read_text(encoding='utf-8'))
            resolvable_cases = [c for c in cases_json if c['known_resolvable']]
            self.assertEqual(len(resolvable_cases), 6)

            for case_item in resolvable_cases:
                original_bytes = fixture(case_item['case'])
                story_file = root / ('test_' + case_item['file'])
                story_file.write_bytes(original_bytes)

                result = run(story_file, runtime_provider=lambda: handle)
                output_bytes = result.path.read_bytes()

                verify(parse(original_bytes), parse(output_bytes))
                self.assertEqual(story_file.read_bytes(), original_bytes)
                self.assertTrue(all(a <= b for a, b in zip(result.after.values, result.before.values)))

            self.assertEqual(len(transport.calls), initial_calls)

    def test_simulated_evidence_is_explicitly_marked_and_non_qualifying(self):
        target_matrix = json.loads((ROOT / 'tools/runtime/support-targets.json').read_text(encoding='utf-8'))
        darwin_targets = [t for t in target_matrix['targets'] if t['os'] == 'darwin']
        self.assertTrue(darwin_targets)
        target = copy.deepcopy(darwin_targets[0])
        rev = 'a' * 40
        artifact = 'macos-x86_64'
        target['application_revision'] = rev
        target['artifact_id'] = artifact
        for slot in target['python_qualifications']:
            slot['status'] = 'validada'
            slot['application_revision'] = rev
            slot['artifact_id'] = artifact
            slot['evidence_ids'] = ['ev-' + slot['python_minor']]

        simulated_evidence = {
            'ev-' + slot['python_minor']: dict(
                target_id=target['id'],
                python_minor=slot['python_minor'],
                application_revision=rev,
                artifact_id=artifact,
                environment_kind='simulated',
                simulation=True,
                passed=True,
                checks=dict.fromkeys(GATES, True),
            )
            for slot in target['python_qualifications']
        }

        # Simulated evidence must block qualification (status returns 'em_qualificacao', never 'validada')
        status = support_status(target, simulated_evidence)
        self.assertNotEqual(status, 'validada')
        self.assertEqual(status, 'em_qualificacao')

        # Control check: when environment_kind is 'native', the target is fully validated
        native_evidence = copy.deepcopy(simulated_evidence)
        for entry in native_evidence.values():
            entry['environment_kind'] = 'native'
            entry['simulation'] = False
        self.assertEqual(support_status(target, native_evidence), 'validada')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('package','provenance','report'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--review-directory',type=Path)
    args=parser.parse_args()
    if sys.platform!='darwin':parser.error('Requires native macOS; another host cannot produce a passed receipt')
    if args.report.exists() or args.report.is_symlink():parser.error('Report must be new')
    driver=MacOSPrivateBundleIntegrationTests
    driver.configuration=(args.package.resolve(),args.provenance.resolve())
    driver.review_directory=args.review_directory
    result=unittest.TextTestRunner(stream=sys.stdout,verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(driver))
    observations=driver.observations
    passed=result.wasSuccessful() and result.testsRun==2 and not result.skipped and len(observations)==2
    report=dict(kind='macos-private-bundle-runtime-integration',passed=passed,qualified=False,
        environment_kind='native',python=platform.python_version(),arch=platform.machine(),
        os_version=platform.mac_ver()[0],kernel=platform.release(),
        engine_sha256=getattr(driver,'record',{}).get('executable_sha256'),provenance_sha256=hashlib.sha256(args.provenance.read_bytes()).hexdigest(),
        security_before=getattr(driver,'security_before',None),security_after=security_snapshot(),
        tests=result.testsRun,skipped=len(result.skipped),observations=observations,
        cases=observations.get('explicit',{}).get('cases',[]),
        scope='Real engine and production runtime manager; fixture acquisition, Python-only network guard; no signed/quarantined distributed-candidate acceptance')
    if report['security_before']!=report['security_after']:report['passed']=False
    with args.report.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    return int(not report['passed'])


if __name__=='__main__':raise SystemExit(main())
