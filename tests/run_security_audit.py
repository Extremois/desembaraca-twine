"""Record the application security contracts, without qualifying native bundles.

Run from any directory with --report NEW_FILE.json. Test caches and child
processes belong to the existing isolated test fixtures. No network is needed.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULES = (
    'unit.test_security_limits', 'unit.test_runtime_archives',
    'unit.test_runtime_posix', 'unit.test_runtime_snapshot',
    'unit.test_runtime_platform', 'unit.test_runtime_repair',
    'integration.test_runtime_budget', 'integration.test_runtime_concurrency',
    'integration.test_runtime_recovery', 'integration.test_runtime_crash',
    'contract.test_cross_platform_results',
)


class RecordingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.observations = []
        self.started_tests = []

    def startTest(self, test):
        super().startTest(test)
        self.started_tests.append(test.id())

    def addSuccess(self, test):
        super().addSuccess(test)
        self.observations.append(dict(test=test.id(), outcome='passed'))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.observations.append(dict(test=test.id(), outcome='skipped', reason=reason,
            parent_test=getattr(test, 'test_case', test).id()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    destination = args.report.resolve()
    if destination.exists():
        raise FileExistsError('Preserve the existing audit report; choose a new path')
    sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'src')]
    paths = [*sorted((ROOT / 'src').rglob('*.py')), Path(__file__).resolve()]
    for name in MODULES:
        paths.append(ROOT / 'tests' / (name.replace('.', '/') + '.py'))
    def digests():
        return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    before = digests()
    environment, directory = dict(os.environ), Path.cwd()
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(MODULES)
    if loader.errors or suite.countTestCases() == 0:
        raise RuntimeError('Security contracts could not be loaded')
    started = time.monotonic()
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, resultclass=RecordingResult, verbosity=1).run(suite)
    unchanged = before == digests()
    restored = environment == dict(os.environ) and directory == Path.cwd()
    passed = result.wasSuccessful() and unchanged and restored
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    report = dict(kind='application-security-contracts-not-native-support-qualification',
        passed=passed, application_revision=revision, source_state='working-tree-content-addressed',
        python=platform.python_version(), implementation=platform.python_implementation(),
        host=dict(system=platform.system(), release=platform.release(), machine=platform.machine()),
        tests=result.testsRun, skipped=len(result.skipped), seconds=round(time.monotonic() - started, 3),
        failed=len(result.failures), errors=len(result.errors), source_sha256=before,
        source_unchanged=unchanged, parent_environment_and_cwd_restored=restored,
        observations=result.observations,
        limitations=['Controlled runtime transports do not qualify a native engine or distribution',
            'Skipped POSIX contracts require existing native CI evidence; no inheritance between platforms',
            'Environment restoration does not by itself prove absence of all global filesystem writes'])
    # unittest records a skip for each skipped subtest, without addSuccess for
    # its parent case. Compare parent identities rather than raw event counts.
    observed_tests = {item.get('parent_test', item['test']) for item in result.observations}
    if passed and observed_tests != set(result.started_tests):
        raise RuntimeError('Incomplete successful test observations')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(output.getvalue(), end='')
    return int(not passed)


if __name__ == '__main__':
    raise SystemExit(main())
