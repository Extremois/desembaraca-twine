import importlib.util
from pathlib import Path
import unittest


def tool():
    spec = importlib.util.spec_from_file_location('macos_link_audit',
        Path(__file__).resolve().parents[2] / 'tools/runtime/audit-macos-link.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MacosLinkTests(unittest.TestCase):
    def test_map_preserves_spaces_and_member_identity(self):
        report = tool().parse_map('# Path: /tmp/build dot\n# Arch: arm64\n# Object files:\n'
            '[ 0] linker synthesized\n[ 1] CMakeFiles/dot.dir/dot.c.o\n'
            '[ 2] /tmp/lib with spaces.a(utils.c.o)\n# Sections:\n')
        self.assertEqual(report['arch'], 'arm64')
        self.assertEqual(report['objects'][1]['path'], '/tmp/lib with spaces.a')
        self.assertEqual(report['objects'][1]['member'], 'utils.c.o')

    def test_map_rejects_duplicate_indices_and_incomplete_sections(self):
        prefix = '# Path: /tmp/dot\n# Arch: x86_64\n# Object files:\n'
        for text in ('', prefix+'[ 1] dot.o\n',
                     prefix+'[ 1] dot.o\n[ 1] other.o\n# Sections:\n',
                     prefix+'unrecognized row\n# Sections:\n'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                tool().parse_map(text)
