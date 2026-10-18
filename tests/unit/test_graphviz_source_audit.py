import hashlib
import importlib.util
from pathlib import Path
import unittest
import tempfile
from common import ROOT


def module():
    spec=importlib.util.spec_from_file_location('graphviz_source_audit',ROOT/'tools/runtime/audit-graphviz-sources.py')
    value=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def entry(name,data):
    header=name.encode().ljust(16)+b'0'.ljust(12)+b'0'.ljust(6)+b'0'.ljust(6)+b'644'.ljust(8)+str(len(data)).encode().ljust(10)+b'`\n'
    return header+data+(b'\n' if len(data)%2 else b'')


class GraphvizSourceAuditTests(unittest.TestCase):
    def test_member_matching_requires_unique_bytes_not_just_filename(self):
        audit=module()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            first=root/'same.o'
            second=root/'copy.o'
            first.write_bytes(b'object')
            second.write_bytes(b'different')
            member=dict(sha256=hashlib.sha256(b'object').hexdigest())
            self.assertEqual(audit.match_member_object(member,[first,second]),first)
            with self.assertRaises(ValueError):audit.match_member_object(member,[second])
            second.write_bytes(b'object')
            with self.assertRaises(ValueError):audit.match_member_object(member,[first,second])

    def test_archive_reader_hashes_real_payload_for_simple_gnu_and_bsd_names(self):
        audit=module()
        for raw,name in ((entry('one.o/',b'object'),'one.o'),
                         (entry('//',b'long object.o/\n')+entry('/0',b'object'),'long object.o'),
                         (entry('#1/9',b'bsdname.oobject'),'bsdname.o')):
            with self.subTest(name=name):
                members=audit.ar_members(b'!<arch>\n'+raw)
                self.assertEqual(members[name],dict(sha256=hashlib.sha256(b'object').hexdigest(),size=6))

    def test_archive_reader_rejects_thin_truncated_and_ambiguous_archives(self):
        audit=module()
        good=b'!<arch>\n'+entry('one.o/',b'object')
        for data in (b'!<thin>\n',good[:-2],good+entry('one.o/',b'different'),
                     b'!<arch>\n'+entry('/99',b'object'),b'!<arch>\n'+b'x'*60):
            with self.subTest(data=data[:20]),self.assertRaises(ValueError):audit.ar_members(data)

    def test_object_dependencies_require_exact_target_and_do_not_expand_make(self):
        audit=module()
        self.assertEqual(audit.object_dependencies('part.c.o: source\\ file.c \\\n include.h\n','part.c.o'),['source file.c','include.h'])
        for text in ('wrong.o: source.c\n','part.c.o: $(shell command)\n','part.c.o:\n'):
            with self.subTest(text=text),self.assertRaises(ValueError):audit.object_dependencies(text,'part.c.o')


if __name__=='__main__':unittest.main()
