"""Do not silently evaluate a curved editor using a straight-edge hypothesis."""
import sys
from pathlib import Path
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'experiments'))
from compare_layouts import compare


class GeometryGateTests(unittest.TestCase):
    def test_comparison_without_explicit_hypothesis_is_refused_before_io(self):
        # Missing engines: the geometry gate must run before dependency validation.
        with self.assertRaisesRegex(ValueError, 'geometry'):
            compare(SimpleNamespace(geometry=None, dot=None, node=None, elk_root=Path('.tmp/missing-elk')))

    def test_unspecified_curve_model_is_not_treated_as_straight(self):
        with self.assertRaisesRegex(ValueError, 'geometry'):
            compare(SimpleNamespace(geometry='curved', dot=None, node=None, elk_root=Path('.tmp/missing-elk')))


if __name__ == '__main__':
    unittest.main()
