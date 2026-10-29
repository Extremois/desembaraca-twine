import importlib.util
import unittest
from common import ROOT


def tool():
    spec=importlib.util.spec_from_file_location('graphviz_data_audit',ROOT/'tools/runtime/audit-graphviz-data.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


class DataAuditTests(unittest.TestCase):
    def test_entity_declaration_notices_are_preserved_and_bound_to_source_bytes(self):
        import hashlib
        module=tool()
        reference=module.reference_material('html401-entities.html')
        expected=hashlib.sha256(reference).hexdigest()
        name,data,origin=module.entity_declaration_notice(reference,expected)
        self.assertEqual(name,'W3C-HTML401-ENTITY-DECLARATION-NOTICES.txt')
        self.assertEqual(origin['declaration_notices'],3)
        self.assertEqual(data.count(b'International Organization for Standardization 1986'),3)
        self.assertIn(b'conforming SGML systems',data)
        self.assertFalse(origin['approved'])
        with self.assertRaises(ValueError):module.entity_declaration_notice(reference,'a'*64)
        altered=reference.replace(b'ISO 8879',b'ISO 0000')
        with self.assertRaises(ValueError):
            module.entity_declaration_notice(altered,hashlib.sha256(altered).hexdigest())

    def test_w3c_policy_versions_and_publication_copyright_are_preserved_separately(self):
        module=tool()
        materials,routing=module.w3c_reference_materials()
        payloads={name:b' '.join(data.split()) for name,data,origin in materials}
        self.assertEqual(len(payloads),6)
        self.assertIn(b'No right to create modifications',payloads['W3C-document-1999.txt'])
        self.assertIn(b'Permission to use, copy, modify',payloads['W3C-software-1998.txt'])
        self.assertIn(b'1997-1999',payloads['W3C-html401-index.txt'])
        self.assertIn('© 2011'.encode(),payloads['W3C-svg11-index.txt'])
        self.assertIn(b'W3C Recommendation',payloads['W3C-svg11-index.txt'])
        self.assertEqual(routing['html401']['policy_references'],['document-1999','software-1998'])
        self.assertEqual(routing['svg11']['policy_references'],['document-2002','document-2023'])
        for name,data,origin in materials:
            self.assertFalse(origin['approved'])
            self.assertIn('https://www.w3.org/',origin['source_url'])
            self.assertIn(b'Raw source SHA-256:',data)

    def test_policy_text_retains_link_destinations_and_ignores_active_html(self):
        module=tool()
        text=module.policy_text(b'<html><head><style>hidden CSS</style></head><body>'
            b'<p>License terms <a href="/policy">conditions</a>.</p>'
            b'<script>hidden JavaScript</script></body></html>',
            'utf-8','https://www.w3.org/origin')
        self.assertIn('License terms',text)
        self.assertIn('https://www.w3.org/policy',text)
        self.assertNotIn('hidden',text)

    def test_w3c_reference_tampering_is_refused_before_returning_materials(self):
        import json
        from pathlib import Path
        import tempfile
        from unittest.mock import patch
        module=tool()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            lock=json.loads((module.W3C_REFERENCES/'sources.json').read_text())
            (root/'sources.json').write_text(json.dumps(lock))
            for row in lock['references'].values():
                (root/row['file']).write_bytes((module.W3C_REFERENCES/row['file']).read_bytes())
            (root/lock['references']['document-1999']['file']).write_bytes(b'changed material')
            with patch.object(module,'W3C_REFERENCES',root),self.assertRaises(ValueError):
                module.w3c_reference_materials()

    def test_xorg_aliases_must_agree_and_channels_are_bounded(self):
        module=tool()
        self.assertEqual(module.xorg_colors(b'240 248 255 alice blue\n240 248 255 AliceBlue\n'),
                         {'aliceblue':(240,248,255)})
        for data in (b'240 248 255 AliceBlue\n0 0 0 alice blue\n',b'256 0 0 bad\n',b'not a color\n'):
            with self.subTest(data=data),self.assertRaises(ValueError):module.xorg_colors(data)

    def test_w3c_parsers_compare_values_without_executing_html(self):
        module=tool()
        self.assertEqual(module.svg_colors(b'<td>red</td><td>rgb(255, 0, 0)</td>'),{'red':(255,0,0)})
        self.assertEqual(module.entities(b'&lt;!ENTITY nbsp CDATA "&amp;#160;" -- x --&gt;'),{'nbsp':160})
        for data in (b'<p>red rgb(255,0,0) red rgb(0,0,0)</p>',b'no colors'):
            with self.subTest(data=data),self.assertRaises(ValueError):module.svg_colors(data)

    def test_graphviz_data_changes_cannot_be_hidden_as_xorg_aliases(self):
        module=tool()
        reference={'red':(255,0,0),'gray':(190,190,190),'grey':(190,190,190)}
        graphviz={'red':(255,0,0,255),'gray':(192,192,192,255),'grey':(192,192,192,255),
                  **{n:(255,255,254,0) for n in ('invis','none','transparent')}}
        self.assertEqual(module.compare_xorg(graphviz,reference)['matched'],1)
        graphviz['red']=(1,2,3,255)
        with self.assertRaises(ValueError):module.compare_xorg(graphviz,reference)

    def test_reference_material_is_pinned_and_preserves_the_xorg_notice(self):
        module=tool()
        self.assertIn(b'The Open Group',module.reference_material('xorg-rgb-1.1.0-COPYING'))
        self.assertEqual(len(module.svg_colors(module.reference_material('svg11-types.html'))),147)
        self.assertEqual(len(module.entities(module.reference_material('html401-entities.html'))),252)
