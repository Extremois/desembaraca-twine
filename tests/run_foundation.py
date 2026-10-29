"""Run portable contracts separately from qualified native-engine acceptance."""
from pathlib import Path
import os
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


def main():
    os.chdir(ROOT)
    sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'src')]
    loader = unittest.TestLoader()
    suite = loader.discover(str(ROOT / 'tests'))
    if loader.errors:
        for error in loader.errors:
            print(error, file=sys.stderr)
        return 1
    def leaves(node):
        for item in node:
            if isinstance(item, unittest.TestSuite):
                yield from leaves(item)
            else:
                yield item
    prefixes = ('unit.', 'contract.test_runtime_catalog.', 'contract.test_support_policy.', 'contract.test_abi_qualification.',
                'contract.test_cli_runtime.', 'integration.test_runtime_budget.',
                'integration.test_runtime_concurrency.', 'contract.test_cli_linux.',
                'contract.test_cli_macos.', 'contract.test_runtime_diagnostics.',
                'contract.test_cross_platform_results.', 'integration.test_cross_platform_publish.',
                'integration.test_runtime_recovery.', 'integration.test_runtime_crash.',
                'integration.test_macos_runtime.')
    selected = unittest.TestSuite(test for test in leaves(suite) if test.id().startswith(prefixes))
    if not selected.countTestCases():
        raise RuntimeError('No foundation tests discovered')
    result = unittest.TextTestRunner(verbosity=1).run(selected)
    return int(not result.wasSuccessful())


if __name__ == '__main__':
    raise SystemExit(main())
