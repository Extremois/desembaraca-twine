import json
import unittest
from common import ROOT,fixture
from twine_edge_overlap.formats.profile import parse
from twine_edge_overlap.formats.profile import serialize
from twine_edge_overlap.domain.geometry import measure


class GeometryTests(unittest.TestCase):
    def test_independent_expected_counts(self):
        for case in json.loads((ROOT/'tests/fixtures/cases.json').read_text()):
            with self.subTest(case=case['case']):
                self.assertEqual(list(measure(parse(fixture(case['case']))).values),case['before'])

    def test_known_clear_arrangements_independent_of_motor(self):
        for case in json.loads((ROOT/'tests/fixtures/cases.json').read_text()):
            if 'known_clear_positions' in case:
                with self.subTest(case=case['case']):
                    doc=parse(fixture(case['case']))
                    known=parse(serialize(doc,case['known_clear_positions']))
                    self.assertEqual(measure(known).values,(0,0,0))
