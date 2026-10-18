import importlib.util
from pathlib import Path
import tempfile
import unittest
from common import ROOT


def module():
    spec=importlib.util.spec_from_file_location('zig_runtime_audit',ROOT/'tools/runtime/audit-zig-runtime.py')
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def table(directories,files,version=4):
    return (f'DWARF Version: {version}\n The Directory Table (offset 0x1c):\n'+directories+
            '\n The File Name Table (offset 0x30):\n Entry Dir Time Size Name\n'+files+
            '\n Line Number Statements:\n instructions are not file table entries\n')


class ZigRuntimeAuditTests(unittest.TestCase):
    def test_license_indicators_include_later_lines_without_treating_them_as_approval(self):
        audit=module()
        data=(b'// Copyright synthetic header\nconst x = 1;\n'
              b'// Ported from https://golang.org/src/math/tan.go\n'
              b'// SPDX-License-Identifier: MIT\n')
        items=audit.license_indicators(data)
        self.assertEqual([i['line'] for i in items],[1,3,4])
        self.assertEqual([i['within_leading_comments'] for i in items],[True,False,False])
        self.assertEqual(audit.license_indicators(b'const x = 1;\n'),[])

    def test_line_table_preserves_spaces_and_resolves_zero_directory(self):
        audit=module()
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder)
            text=table(f' 1 {base}/sdk with spaces\n', ' 1 1 0 0 file with spaces.zig\n 2 0 0 0 builtin.zig\n')
            self.assertEqual(audit.line_table_files(text,base),[
                dict(file_id=1,path=base/'sdk with spaces/file with spaces.zig'),dict(file_id=2,path=base/'builtin.zig')])

    def test_ambiguous_malformed_and_unsupported_tables_are_refused(self):
        audit=module()
        directory=str(ROOT)
        valid=table(' 1 '+directory+'\n',' 1 1 0 0 file.zig\n')
        bad=(valid.replace('DWARF Version: 4','DWARF Version: 5'),valid+valid,
             valid.replace(' 1 1 0 0',' 1 2 0 0'),valid.replace('file.zig','../escape.zig'),
             valid.replace(' 1 1 0 0 file.zig',' 1 1 0 0 file.zig\n 1 1 0 0 duplicate.zig'),
             valid.replace(' 1 '+directory,' invalid directory'), 'not a line table')
        for text in bad:
            with self.subTest(text=text[:60]),self.assertRaises(ValueError):audit.line_table_files(text,ROOT)

    def test_generated_sources_are_confined_to_builtin_under_recorded_cache(self):
        audit=module()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);sdk=root/'sdk';cache=root/'cache'
            (sdk/'lib').mkdir(parents=True);(cache/'b/hash').mkdir(parents=True)
            source=sdk/'lib/source.zig';source.write_bytes(b'pinned source')
            generated=cache/'b/hash/builtin.zig';generated.write_bytes(b'generated target facts')
            self.assertEqual(audit.source_identity(source,sdk,cache),('sdk','lib/source.zig'))
            self.assertEqual(audit.source_identity(generated,sdk,cache),('generated','b/hash/builtin.zig'))
            for path in (root/'outside.zig',cache/'b/hash/not-builtin.zig',cache/'o/builtin.zig'):
                path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'outside approved origin')
                with self.subTest(path=path),self.assertRaises(ValueError):audit.source_identity(path,sdk,cache)


if __name__=='__main__':unittest.main()
