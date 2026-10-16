"""Reject malformed layouts before experimental metrics are trusted."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'experiments'))
import layout_engines
from comparison_corpus import cases


class LayoutValidationTests(unittest.TestCase):
    def test_valid_positions_and_identical_graph(self):
        original = cases()['crossing']
        positions = {n['id']: (n['x'], n['y']) for n in original['nodes']}
        result = layout_engines.validate_positions(original, positions)
        self.assertEqual(result, original)

    def test_wrong_ids_nonfinite_and_huge_positions(self):
        original = cases()['clean']
        for positions in ({'0': (0, 0)}, {'0': (0, 0), '1': (float('nan'), 0)},
                          {'0': (0, 0), '1': (float('inf'), 0)},
                          {'0': (0, 0), '1': (1e30, 0)},
                          {'0': (0, 0), '1': (0, 0), 'extra': (1, 2)}):
            with self.subTest(positions=positions), self.assertRaises(ValueError):
                layout_engines.validate_positions(original, positions)


if __name__ == '__main__':
    unittest.main()
