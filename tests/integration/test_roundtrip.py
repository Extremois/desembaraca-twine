import unittest
from common import fixture
from twine_edge_overlap.formats.profile import parse,serialize,verify


class RoundtripTests(unittest.TestCase):
    def test_only_positions_change_including_unknown_metadata(self):
        raw=fixture('parallel_occurrences').replace(b'Synthetic passage.',b'\\:: escaped header\n<script>ignored()</script>')
        doc=parse(raw)
        self.assertEqual(len(doc.edges),2)
        positions={n.id:(n.x+25,n.y+10) for n in doc.nodes}
        candidate=parse(serialize(doc,positions))
        verify(doc,candidate)
        self.assertIn(b'"custom": {"retain": true}',candidate.raw)
        self.assertIn(b'\\:: escaped header',candidate.raw)
        self.assertEqual(doc.edges,candidate.edges)

    def test_bom_crlf_and_tags_survive(self):
        raw=b'\xef\xbb\xbf'+fixture().replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
        doc=parse(raw)
        self.assertEqual(serialize(doc,{n.id:(n.x,n.y) for n in doc.nodes}),raw)

    def test_empty_story_is_valid(self): self.assertEqual(parse(fixture('empty')).nodes,())

    def test_tagged_scripts_and_styles_are_preserved_without_execution(self):
        raw=fixture()+b'\n:: StoryScript [script]\nthrow new Error("never execute"); [[missing]]\n\n:: StoryStyles [stylesheet]\nbody { color: red; }\n'
        doc=parse(raw)
        self.assertEqual(len(doc.nodes),2)
        self.assertTrue(doc.opaque)
        candidate=parse(serialize(doc,{n.id:(n.x+10,n.y) for n in doc.nodes}))
        verify(doc,candidate)
        self.assertIn(b'throw new Error("never execute")',candidate.raw)
        self.assertIn(b'body { color: red; }',candidate.raw)

    def test_unicode_names_and_nested_position_key_are_not_rewritten(self):
        raw=fixture().replace(b'P0','Início'.encode()).replace(b'P1','Fim'.encode())
        raw=raw.replace(b'{"position"',b'{"nested":{"position":"KEEP"}, "position"')
        doc=parse(raw)
        candidate=parse(serialize(doc,{n.id:(n.x+12,n.y+7) for n in doc.nodes}))
        verify(doc,candidate)
        self.assertEqual(candidate.nodes[0].id,'Início')
        self.assertEqual(candidate.raw.count(b'"position":"KEEP"'),2)
