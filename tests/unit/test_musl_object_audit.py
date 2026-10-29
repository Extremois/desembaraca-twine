import importlib.util
from pathlib import Path
import tempfile
import unittest
from common import ROOT


def module():
    spec=importlib.util.spec_from_file_location('musl_object_audit',ROOT/'tools/runtime/audit-musl-objects.py')
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


class MuslObjectAuditTests(unittest.TestCase):
    def test_compilation_units_use_only_top_level_names_and_keep_spaces(self):
        audit=module()
        text=(' <0><b>: Abbrev Number: 1 (DW_TAG_compile_unit)\n'
              '    <12> DW_AT_name : (indirect string, offset: 0x1): /sdk with spaces/lib/a.c\n'
              '    <16> DW_AT_comp_dir : /build\n'
              ' <1><20>: Abbrev Number: 2 (DW_TAG_subprogram)\n'
              '    <22> DW_AT_name : not_a_source\n'
              ' <0><90>: Abbrev Number: 1 (DW_TAG_compile_unit)\n'
              '    <a0> DW_AT_name : relative.c\n'
              '    <a4> DW_AT_comp_dir : /sdk/lib\n')
        self.assertEqual(audit.compilation_units(text),[
            dict(name='/sdk with spaces/lib/a.c',comp_dir='/build'),dict(name='relative.c',comp_dir='/sdk/lib')])
        self.assertEqual(audit.compilation_units('no debug info'),[])
        with self.assertRaises(ValueError):audit.compilation_units(text.replace('DW_AT_comp_dir : /build','DW_AT_name : repeated.c'))

    def test_source_resolution_refuses_outside_sdk_and_unknown_relative_root(self):
        audit=module()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);sdk=root/'sdk';sdk.mkdir();(sdk/'a.c').write_text('source')
            self.assertEqual(audit.sdk_source(dict(name='a.c',comp_dir=str(sdk)),sdk),'a.c')
            for name in ('../outside.c',str(root/'outside.c')):
                with self.subTest(name=name),self.assertRaises(ValueError):
                    audit.sdk_source(dict(name=name,comp_dir=str(sdk)),sdk)
            with self.assertRaises(ValueError):audit.sdk_source(dict(name='a.c'),sdk)

    def test_notice_prefix_preserves_all_leading_comments_without_code(self):
        audit=module()
        prefix=b'/* Copyright synthetic\n * permission text */\n\n// next notice\n'
        self.assertEqual(audit.notice_prefix(prefix+b'#include "header.h"\n'),prefix)
        self.assertEqual(audit.notice_prefix(b'#include "x.h"'),b'')
        with self.assertRaises(ValueError):audit.notice_prefix(b'/* unterminated')


if __name__=='__main__':unittest.main()
