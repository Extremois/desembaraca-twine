import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import tarfile
import tempfile
import unittest
from common import ROOT


def load(name, path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def elf():
    raw=bytearray(64);raw[:6]=b'\x7fELF\x02\x01';struct.pack_into('<H',raw,18,62)
    return bytes(raw)


def deb(entries):
    output=io.BytesIO()
    with tarfile.open(fileobj=output,mode='w:xz') as archive:
        for name,raw,kind in entries:
            member=tarfile.TarInfo(name);member.size=len(raw);member.type=kind
            archive.addfile(member,io.BytesIO(raw))
    raw=b'!<arch>\n'
    for name,payload in [('debian-binary',b'2.0\n'),('data.tar.xz',output.getvalue())]:
        raw+=(name+'/').ljust(16).encode()+b'0           0     0     100644  '+str(len(payload)).ljust(10).encode()+b'`\n'+payload
        if len(payload)%2:raw+=b'\n'
    return raw


class PrivateTracerTests(unittest.TestCase):
    def setUp(self):
        self.tool=load('private_tracer','.github/scripts/private-tracer.py')

    def test_deb_selection_copies_only_reviewed_regular_elf_without_scripts_or_links(self):
        raw=deb([('./usr/bin/strace',elf(),tarfile.REGTYPE),('./unused',b'ignored',tarfile.REGTYPE)])
        self.assertEqual({'strace':elf()},self.tool.unpack_deb(raw,{'./usr/bin/strace':'strace'}))
        for name,content,kind in [('../escape',elf(),tarfile.REGTYPE),
                                   ('./usr/bin/strace',elf(),tarfile.SYMTYPE),
                                   ('./usr/bin/strace',b'script',tarfile.REGTYPE)]:
            with self.subTest(name=name,kind=kind),self.assertRaises(ValueError):
                self.tool.unpack_deb(deb([(name,content,kind)]),{'./usr/bin/strace':'strace'})
        with self.assertRaises(ValueError):self.tool.unpack_deb(raw,{'./missing':'strace'})
        with self.assertRaises(ValueError):self.tool.unpack_deb(raw,{'./usr/bin/strace':'../strace'})
        with self.assertRaises(ValueError):self.tool.unpack_deb(b'invalid',{'./usr/bin/strace':'strace'})

    def test_deb_rejects_duplicate_payload_truncation_and_wrong_cpu(self):
        wrong=bytearray(elf());struct.pack_into('<H',wrong,18,183)
        for payload in (deb([('./usr/bin/strace',bytes(wrong),tarfile.REGTYPE)]),
                        deb([('./usr/bin/strace',elf(),tarfile.REGTYPE)] )[:-5],
                        deb([('./usr/bin/strace',elf(),tarfile.REGTYPE),('./usr/bin/strace',elf(),tarfile.REGTYPE)])):
            with self.assertRaises(ValueError):self.tool.unpack_deb(payload,{'./usr/bin/strace':'strace'})

    def test_guest_uses_private_loader_path_only_after_verifying_every_file(self):
        probe=load('application_probe','.github/scripts/probe-installed-application.py')
        with tempfile.TemporaryDirectory() as temporary:
            source=Path(temporary);folder=source/'private-tracer';folder.mkdir()
            rows=[]
            for name in ('strace','libunwind-ptrace.so.0','libunwind-x86_64.so.8','libunwind.so.8'):
                (folder/name).write_bytes(elf());rows.append(dict(name=name,sha256=hashlib.sha256(elf()).hexdigest()))
            pin=dict(files=rows,packages=[],version='6.1')
            (source/'tracer.json').write_text(json.dumps(pin))
            command,receipt=probe.tracer_command(source)
            self.assertEqual(['--library-path',str(folder),str(folder/'strace')],command[1:])
            self.assertEqual(receipt,pin)
            (folder/'strace').write_bytes(b'changed')
            with self.assertRaises(ValueError):probe.tracer_command(source)
            (folder/'strace').write_bytes(elf())
            pin['files'][0]['name']='../strace';(source/'tracer.json').write_text(json.dumps(pin))
            with self.assertRaises(ValueError):probe.tracer_command(source)
