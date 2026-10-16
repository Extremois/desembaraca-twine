import json
import time
import unittest
from common import fixture
from twine_edge_overlap.formats.profile import parse
from twine_edge_overlap.engines.graphviz import build_dot,decode_layout,layout


class GraphvizTests(unittest.TestCase):
    def test_dot_contains_geometry_and_keeps_repeated_edges(self):
        text=build_dot(parse(fixture('parallel_occurrences')))
        self.assertNotIn('strict',text)
        self.assertNotIn('Synthetic',text)
        self.assertNotIn('P0',text)
        self.assertEqual(text.count('n0 -> n1'),2)
        self.assertIn('fixedsize=true',text)
        self.assertIn('label=""',text)

    def test_center_and_y_conversion(self):
        doc=parse(fixture())
        data=json.dumps({'bb':'0,0,400,500','objects':[{'name':'n0','pos':'50,450'},{'name':'n1','pos':'350,50'}]}).encode()
        self.assertEqual(decode_layout(data,doc),{'P0':(0,0),'P1':(300,400)})

    def test_installed_motor_produces_same_identities(self):
        doc=parse(fixture('crossing'))
        result=layout(doc,time.monotonic()+30)
        self.assertEqual(set(result),{n.id for n in doc.nodes})
