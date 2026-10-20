"""Native macOS manager integration; signed distribution acceptance is separate.

Only acquisition uses a controlled fixture. Engine execution, cache/probes,
permissions, Mach-O inspection and platform security observations are real.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'src')]
from integration import test_linux_runtime as linux
from native_acceptance import InstalledCandidateAcceptance
from twine_edge_overlap.engines.process import run_bounded


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
        spec=importlib.util.spec_from_file_location('macos_runtime_inspector',ROOT/'tools/runtime/verify-artifact.py')
        cls.inspector=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.inspector)

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
        self.assertNotIn('LC_RPATH',commands.stdout.decode('utf-8'))
        self.assertEqual(security_snapshot(),self.security_before)
        return dict(thin_native_macho=True,system_libraries=dependencies,rpath=[],
            relocation='No private dylibs or search paths; system dylibs only',
            library_commands_sha256=hashlib.sha256(libraries.stdout).hexdigest(),
            load_commands_sha256=hashlib.sha256(commands.stdout).hexdigest(),
            cache_library_caches=True,quarantine_present='com.apple.quarantine' in os.listxattr(handle.executable),
            security_settings_unchanged=True,signature_notarization_approved=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('package','provenance','report'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    if sys.platform!='darwin':parser.error('Requires native macOS; another host cannot produce a passed receipt')
    if args.report.exists() or args.report.is_symlink():parser.error('Report must be new')
    driver=MacOSPrivateBundleIntegrationTests
    driver.configuration=(args.package.resolve(),args.provenance.resolve())
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
