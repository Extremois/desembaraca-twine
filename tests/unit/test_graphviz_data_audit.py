import importlib.util
import unittest
from common import ROOT


def tool():
    spec=importlib.util.spec_from_file_location('graphviz_data_audit',ROOT/'tools/runtime/audit-graphviz-data.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


class DataAuditTests(unittest.TestCase):
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
