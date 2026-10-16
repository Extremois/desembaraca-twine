"""Known geometric answers; these tests do not validate Twine's renderer."""
import sys
from pathlib import Path
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'experiments'))
from comparison_corpus import cases, graph
from straight_geometry import counts


class StraightGeometryTests(unittest.TestCase):
    def test_known_crossing(self):
        self.assertEqual(counts(cases()['crossing']), [1, 0, 0])

    def test_coincident_pair_counted_once(self):
        self.assertEqual(counts(cases()['coincident']), [1, 0, 2])

    def test_node_overlap_and_border_exclusion(self):
        self.assertEqual(counts(cases()['isolated_overlap']), [0, 1, 0])
        self.assertEqual(counts(graph([(0, 0), (100, 0)], [])), [0, 0, 0])

    def test_edge_node_interior_and_border_exclusion(self):
        self.assertEqual(counts(cases()['through_isolated']), [0, 0, 1])
        self.assertEqual(counts(cases()['border_only']), [0, 0, 0])

    def test_shared_endpoint_is_not_a_conflict(self):
        self.assertEqual(counts(graph([(0, 0), (-200, 300), (200, 300)], [(0, 1), (0, 2)])), [0, 0, 0])

    def test_repeated_semantic_links_form_one_visual_connection(self):
        self.assertEqual(counts(cases()['parallel_occurrences']), [0, 0, 0])

    def test_uncharacterized_geometry_is_explicit(self):
        for case in ('self_loop', 'reciprocal'):
            with self.subTest(case=case), self.assertRaisesRegex(ValueError, 'not characterized'):
                counts(cases()[case])

    def test_deadline_interrupts_geometry(self):
        with self.assertRaises(TimeoutError):
            counts(cases()['crossing'], time.monotonic() - 1)


if __name__ == '__main__':
    unittest.main()
