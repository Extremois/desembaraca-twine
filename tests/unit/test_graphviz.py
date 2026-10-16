import json
import time
import unittest
from unittest.mock import patch
from common import fixture
from runtime_support import blocked_network,controlled_runtime,synthetic_runner
from twine_edge_overlap.formats.profile import parse
from twine_edge_overlap.engines.graphviz import build_dot,decode_layout,layout


class GraphvizTests(unittest.TestCase):
    def test_layout_requires_explicit_runtime_without_preparation(self):
        with blocked_network(),patch('twine_edge_overlap.engines.graphviz.ensure_runtime',side_effect=AssertionError('unexpected preparation')):
            with self.assertRaises(TypeError): layout(parse(fixture()),time.monotonic()+30)

    def test_layout_with_provided_runtime_does_not_acquire_components(self):
        document=parse(fixture())
        with blocked_network(),patch('twine_edge_overlap.engines.graphviz.ensure_runtime',side_effect=AssertionError('unexpected preparation')),patch('twine_edge_overlap.engines.graphviz.run_bounded',side_effect=synthetic_runner):
            positions=layout(document,time.monotonic()+30,runtime=controlled_runtime())
        self.assertEqual(set(positions),{node.id for node in document.nodes})

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
