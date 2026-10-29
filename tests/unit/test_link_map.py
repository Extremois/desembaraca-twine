import hashlib
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest
from common import ROOT


def tool():
    spec=importlib.util.spec_from_file_location('link_map',ROOT/'tools/runtime/link-map.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


class LinkMapTests(unittest.TestCase):
    def fixture(self,root):
        names=b'\0.shstrtab\0.text\0.debug_info\0'
        raw=bytearray(512)
        raw[:16]=b'\x7fELF\x02\x01\x01'+bytes(9)
        struct.pack_into('<HHIQQQIHHHHHH',raw,16,2,62,1,0x1000,0,64,0,64,0,0,64,4,1)
        struct.pack_into('<IIQQQQIIQQ',raw,128,1,3,0,0,320,len(names),0,0,1,0)
        struct.pack_into('<IIQQQQIIQQ',raw,192,11,1,6,0x1000,384,32,0,0,16,0)
        struct.pack_into('<IIQQQQIIQQ',raw,256,17,1,0,0,416,8,0,0,1,0)
        raw[320:320+len(names)]=names
        binary=root/'dot';binary.write_bytes(raw)
        archive=str(root/'runtime with spaces.a');obj=str(root/'main.o')
        linkage=dict(executable_sha256=hashlib.sha256(raw).hexdigest(),inputs=[
            dict(path=archive,scope='sdk',sha256='a'*64),dict(path=obj,scope='sdk',sha256='b'*64)],
            archive_extractions=dict(rows=[dict(archive_sha256='a'*64,member='runtime.o')]))
        text=('             VMA              LMA     Size Align Out     In      Symbol\n'
              '1000 1000 20 16 .text\n'
              '1000 1000 10 16         '+archive+'(runtime.o):(.text.__extendsftf2)\n'
              '1000 1000 10 1                 __extendsftf2\n'
              '1010 1010 10 16         '+obj+':(.text)\n'
              '0 0 8 1 .debug_info\n'
              '0 0 8 1         '+archive+'(runtime.o):(.debug_info)\n')
        path=root/'map.txt';path.write_text(text)
        return binary,path,linkage,text

    def test_only_allocated_contributions_are_bound_to_binary_and_hashed_inputs(self):
        module=tool()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);binary,path,linkage,text=self.fixture(root)
            report=module.capture(path,binary,linkage,root)
            self.assertFalse(report['approved']);self.assertFalse(report['qualified'])
            self.assertEqual(len(report['sections']),2)
            runtime=report['sections'][0]
            self.assertEqual(runtime['input_sha256'],'a'*64)
            self.assertEqual(runtime['member'],'runtime.o')
            self.assertEqual(runtime['input_section'],'.text.__extendsftf2')
            self.assertTrue(runtime['executable'])
            self.assertEqual(runtime['bytes'],16)
            self.assertNotIn('.debug_info',[row['input_section'] for row in report['sections']])
            self.assertEqual(report['executable_sha256'],linkage['executable_sha256'])
            # Reading Linux metadata on Windows must preserve POSIX input paths.
            text=text.replace(str(root/'main.o'),'/build with spaces/main.o')
            path.write_text(text)
            linkage['inputs'][1].update(path='main.o',scope='build')
            portable=module.capture(path,binary,linkage,'/build with spaces')
            self.assertEqual(portable['sections'][1]['input_path'],'main.o')

    def test_map_cannot_claim_unknown_inputs_members_or_different_binary_ranges(self):
        module=tool()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);binary,path,linkage,text=self.fixture(root)
            for changed in (text.replace('runtime with spaces.a','unknown.a'),text.replace('(runtime.o)','(unknown.o)'),
                    text.replace('1000 1000 20 16 .text','1000 1000 21 16 .text'),
                    text.replace('1010 1010 10 16','1020 1020 10 16'),text.replace('VMA','HEADER'),
                    text.replace('1000 1000 20 16 .text\n','')):
                path.write_text(changed)
                with self.subTest(changed=changed[:90]),self.assertRaises(ValueError):
                    module.capture(path,binary,linkage,root)
            path.write_text(text);binary.write_bytes(binary.read_bytes()+b'changed')
            with self.assertRaises(ValueError):module.capture(path,binary,linkage,root)

    def test_malformed_or_excessive_elf_metadata_is_refused(self):
        module=tool()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);binary,path,linkage,text=self.fixture(root)
            valid=binary.read_bytes()
            for offset,fmt,value in ((40,'Q',2**64-1),(58,'H',1),(60,'H',65535),(62,'H',65535)):
                raw=bytearray(valid);struct.pack_into('<'+fmt,raw,offset,value)
                with self.subTest(offset=offset),self.assertRaises(ValueError):module.allocated_sections(bytes(raw))
            with self.assertRaises(ValueError):module.allocated_sections(valid[:60])
