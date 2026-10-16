import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'experiments'))
from comparison_corpus import graph
from twine_geometry import counts, connection


class TwineGeometryTests(unittest.TestCase):
    def test_horizontal_arc_midpoint_matches_svg(self):
        g=graph([(0,0),(300,0)],[(0,1)])
        a=connection(*g['nodes'])
        self.assertAlmostEqual(a.point(.5)[0],200)
        self.assertAlmostEqual(a.point(.5)[1],50-150*(1-3**.5/2))

    def test_arc_avoids_node_on_chord_but_hits_node_on_arc(self):
        # Endpoint chord is y=50; its arc reaches y~=9.81 at the middle.
        g=graph([(0,0),(500,0),(295,48)],[(0,1)])
        g['nodes'][2].update(w=10,h=4)
        self.assertEqual(counts(g),[0,0,0])
        g['nodes'][2]['y']=8
        self.assertEqual(counts(g),[0,0,1])

    def test_reciprocal_connections_coincide(self):
        self.assertEqual(counts(graph([(0,0),(300,0)],[(0,1),(1,0)])),[1,0,0])

    def test_self_loop_and_duplicate_occurrences(self):
        self.assertEqual(counts(graph([(0,0)],[(0,0),(0,0)])),[0,0,0])

    def test_crossing_counts_once(self):
        self.assertEqual(counts(graph([(0,0),(400,0),(0,400),(400,400)],[(0,3),(1,2)])),[1,0,0])

    def test_touching_nodes_are_not_overlapping(self):
        self.assertEqual(counts(graph([(0,0),(100,0)],[])),[0,0,0])

    def test_shared_node_is_not_an_edge_conflict(self):
        self.assertEqual(counts(graph([(0,0),(-300,300),(300,300)],[(0,1),(0,2)])),[0,0,0])

    def test_hidden_edges_inside_coincident_nodes(self):
        self.assertEqual(counts(graph([(0,0),(0,0)],[(0,1)])),[0,1,0])


if __name__=='__main__': unittest.main()
