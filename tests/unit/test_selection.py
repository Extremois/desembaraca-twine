import unittest
from common import fixture
from twine_edge_overlap.domain.model import Metrics
from twine_edge_overlap.domain.selection import choose


class SelectionTests(unittest.TestCase):
    def test_no_compensation_between_metrics(self):
        self.assertEqual(choose('old','new',Metrics(3,0,1),Metrics(0,0,2)),'old')
        self.assertEqual(choose('old','new',Metrics(3,0,1),Metrics(2,0,1)),'new')
        self.assertEqual(choose('old','new',Metrics(0,0,0),Metrics(0,0,0)),'old')
