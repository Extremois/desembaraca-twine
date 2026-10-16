"""Import-compatible Twee variants must keep story text and existing attributes."""
import tempfile
from pathlib import Path
import unittest
from common import fixture
from twine_edge_overlap.application import run
from twine_edge_overlap.formats.profile import parse,serialize,verify
from twine_edge_overlap.errors import FormatError


class TweeCompatibilityTests(unittest.TestCase):
    def test_missing_destinations_are_identified_without_creating_passages(self):
        with self.assertRaisesRegex(FormatError,'MissingA, MissingB'):
            parse(b':: A\n[[label->MissingB]] [[MissingA]] [[MissingB]]\n')

    def test_standard_labeled_links_and_setters_preserve_occurrences(self):
        raw=fixture().replace(b'[[P1]]',b'[[label->P1]] [[P1<-label]] [[label|P1]] [[label->P1][$x=1]]')
        doc=parse(raw)
        self.assertEqual(doc.edges,(('P0','P1'),)*4)
        candidate=parse(serialize(doc,{n.id:(n.x+10,n.y) for n in doc.nodes}))
        verify(doc,candidate)
        self.assertIn(b'[[label->P1][$x=1]]',candidate.raw)

    def test_plain_twee_initializes_grid_and_keeps_source_body(self):
        raw=':: Início\nTexto com [[Avançar->Fim]].\n\n:: Fim\nFim da história.\n'.encode('utf-8')
        doc=parse(raw)
        self.assertEqual([(n.x,n.y,n.w,n.h) for n in doc.nodes],[(25,25,100,100),(150,25,100,100)])
        self.assertEqual(doc.edges,(('Início','Fim'),))
        self.assertTrue(doc.layout_initialized)
        self.assertIn('Texto com [[Avançar->Fim]].'.encode('utf-8'),doc.raw)
        self.assertNotIn(b'StoryData',doc.raw)

    def test_partial_metadata_uses_defaults_without_losing_unknown_fields(self):
        raw=b':: A [tag] {"custom":{"position":"KEEP"},"position":"400,500"}\n[[B]]\n:: B\nEnd\n'
        doc=parse(raw)
        self.assertEqual([(n.x,n.y,n.w,n.h) for n in doc.nodes],[(400,500,100,100),(0,0,100,100)])
        self.assertIn(b'"custom":{"position":"KEEP"}',doc.raw)
        self.assertIn(b'[tag]',doc.raw)

    def test_all_zero_positions_follow_twine_grid_fallback(self):
        raw=b':: A {"position":"0,0","size":"100,100"}\n[[B]]\n:: B {"position":"0,0","size":"100,100"}\nEnd\n'
        self.assertEqual([(n.x,n.y) for n in parse(raw).nodes],[(25,25),(150,25)])

    def test_plain_crlf_without_final_newline_keeps_all_body_bytes(self):
        raw=b'\xef\xbb\xbf:: A [tag]\r\n[[label|B]]\r\n\r\n:: B\r\nTail'
        doc=parse(raw)
        self.assertIn(b'\r\n[[label|B]]\r\n\r\n:: B',doc.raw)
        self.assertTrue(doc.raw.endswith(b'\r\nTail'))
        self.assertTrue(doc.raw.startswith(b'\xef\xbb\xbf'))

    def test_grid_wrap_and_non_narrative_passages(self):
        raw=b':: Style [stylesheet]\nbody{}\n'+b''.join(f':: P{i}\nText\n'.encode() for i in range(11))
        doc=parse(raw)
        self.assertEqual(len(doc.nodes),11)
        self.assertEqual((doc.nodes[10].x,doc.nodes[10].y),(25,150))
        self.assertIn(b':: Style [stylesheet]\nbody{}\n',doc.raw)

    def test_link_precedence_and_external_targets(self):
        raw=b':: A\n[[label->ignored->B]] [[B<-ignored<-label]] [[label|ignored|B]] [[site->https://example.com]]\n:: B\nEnd\n'
        self.assertEqual(parse(raw).edges,(('A','B'),)*3)

    def test_plain_input_original_is_unchanged_and_output_can_be_parsed(self):
        raw=b':: A\n[[Go->B]]\n:: B\nEnd\n'
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'plain.twee';source.write_bytes(raw)
            result=run(source)
            self.assertEqual(source.read_bytes(),raw)
            candidate=parse(result.path.read_bytes())
            self.assertEqual(candidate.edges,(('A','B'),))
            self.assertIn(b'[[Go->B]]',candidate.raw)
            self.assertIn('inicial',result.reason.lower())
