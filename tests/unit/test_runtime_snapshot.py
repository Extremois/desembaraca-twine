import unittest
from common import ROOT
from unittest.mock import patch
from runtime_support import blocked_network
from twine_edge_overlap.engines.process import ProcessResult, ProcessLimitError
from twine_edge_overlap.runtime_snapshot import canonical_inventory, inventory_digest, fingerprint, collect_snapshot, manjaro_branch


META = dict(distribution_id='arch', version_id=None, build_id=None, channel='rolling', native_arch='x86_64', kernel_release='6.1-test')


class SnapshotTests(unittest.TestCase):
    def test_reference_snapshot_rechecks_identity_and_keeps_labels_out_of_hash(self):
        from dataclasses import replace
        from twine_edge_overlap.runtime_catalog import EnvironmentSnapshot, CatalogError
        result = collect_snapshot('pacman', lambda: META.copy(),
                                  runner=lambda *a, **k: ProcessResult(0, b'a 1\n', b''))
        reference = EnvironmentSnapshot.from_probe(result, label='public-test-image')
        self.assertEqual(reference.data['manager'], 'pacman')
        self.assertEqual(reference.data['snapshot_id'], result.snapshot_id)
        self.assertEqual(EnvironmentSnapshot.from_probe(result, label='renamed').data['snapshot_id'], result.snapshot_id)
        with self.assertRaises(CatalogError):
            EnvironmentSnapshot.from_probe(replace(result, snapshot_id='f'*64))

    def test_order_independence_and_exact_versions(self):
        first = canonical_inventory('pacman', b'z 2:1.0-2\na 1.0-1\n')
        second = canonical_inventory('pacman', b'a 1.0-1\nz 2:1.0-2\n')
        self.assertEqual(inventory_digest('pacman', first), inventory_digest('pacman', second))
        original = fingerprint(META, 'pacman', first)
        for key, value in [('kernel_release', 'other'), ('channel', 'testing'), ('distribution_id', 'manjaro')]:
            self.assertNotEqual(original, fingerprint(dict(META, **{key: value}), 'pacman', first))
        self.assertNotEqual(original, fingerprint(META, 'pacman', canonical_inventory('pacman', b'a 1.0-2\nz 2:1.0-2\n')))

    def test_rpm_epoch_normalizes_but_keeps_parallel_versions(self):
        records = canonical_inventory('rpm', b'kernel\t00\t6.1\t1\tx86_64\nkernel\t0\t6.2\t1\tx86_64\n')
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0][1], '0')

    def test_malformed_duplicate_and_excess_inventory_rejected(self):
        for payload in (b'a 1\na 1\n', b'a\n', b'a 1 extra\n', b'a \xff\n', b'a 1\x00\n'):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                canonical_inventory('pacman', payload)
        with self.assertRaises(ValueError): canonical_inventory('pacman', b'a 1\nb 2\n', max_records=1)

    def test_branch_is_data_and_never_assumes_default(self):
        self.assertEqual(manjaro_branch('[General]\nBranch = stable\n'), 'stable')
        for value in ('#Branch=stable', 'Branch=stable\nBranch=testing', 'Branch=$(anything)'):
            with self.assertRaises(ValueError): manjaro_branch(value)

    def test_two_equal_reads_or_unknown_without_network(self):
        calls = []
        def runner(command, **kwargs):
            calls.append((command, kwargs))
            return ProcessResult(0, b'a 1\n', b'')
        with blocked_network():
            result = collect_snapshot('pacman', lambda: META.copy(), runner=runner)
        self.assertTrue(result.known)
        self.assertEqual(len(calls), 2)
        self.assertTrue(calls[0][0][0].startswith('/usr/bin/'))
        self.assertLessEqual(sum(len(b'a 1\n') for _ in calls), 8 * 1024**2)
        for error in (FileNotFoundError(), ProcessLimitError('timeout')):
            def failed(*args, **kwargs): raise error
            self.assertFalse(collect_snapshot('pacman', lambda: META.copy(), runner=failed).known)
        values = iter([b'a 1\n', b'a 2\n'])
        self.assertFalse(collect_snapshot('pacman', lambda: META.copy(), runner=lambda *a, **k: ProcessResult(0, next(values), b'')).known)

    def test_time_output_and_record_limits_fail_closed_to_unknown(self):
        clock=[0.0]
        def slow(*a,**k):
            clock[0]=6
            return ProcessResult(0,b'a 1\n',b'')
        self.assertFalse(collect_snapshot('pacman',lambda:META.copy(),runner=slow,clock=lambda:clock[0]).known)
        with patch('twine_edge_overlap.runtime_snapshot.MAX_OUTPUT',3):
            self.assertFalse(collect_snapshot('pacman',lambda:META.copy(),runner=lambda *a,**k:ProcessResult(0,b'a 1\n',b'')).known)
        payload=''.join(f'p{i} 1\n' for i in range(100001)).encode()
        with self.assertRaises(ValueError): canonical_inventory('pacman',payload)

