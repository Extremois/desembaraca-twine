import importlib.util
from pathlib import Path
import tempfile
import struct
import unittest
from common import ROOT


class NativeBaselineTests(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('native_baseline',ROOT/'.github/scripts/check-native-baseline.py')
        self.tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.tool)

    def test_host_kernel_wrong_distribution_or_unaccelerated_guest_cannot_approve_baseline(self):
        guest=dict(identity=dict(ID='ubuntu',VERSION_ID='18.04'),arch='x86_64',kernel='4.15.0-213-generic',glibc='glibc 2.27')
        self.tool.validate_baseline(guest,dict(enabled=True,present=True))
        for key,value in [('arch','aarch64'),('kernel','6.17.0-1022-azure'),('glibc','glibc 2.39'),
                          ('identity',dict(ID='ubuntu',VERSION_ID='24.04'))]:
            with self.assertRaises(ValueError):
                self.tool.validate_baseline(dict(guest,**{key:value}),dict(enabled=True,present=True))
        for kvm in ({'present':True,'enabled':False},{'present':False,'enabled':False}):
            with self.assertRaises(ValueError):self.tool.validate_baseline(guest,kvm)

    def test_image_pin_refuses_mutable_or_foreign_origins_and_excessive_downloads(self):
        pin=dict(url='https://cloud-images.ubuntu.com/releases/bionic/release-20230607/ubuntu-18.04-server-cloudimg-amd64.img',
                 size=405667840,sha256='8dd2e6b5e5aad20c3f836123b300cba9861249408cbb07c359145a65d6bab6b6')
        self.tool.validate_pin(pin)
        for key,value in [('url',pin['url'].replace('release-20230607','release')),
                          ('url',pin['url'].replace('cloud-images.ubuntu.com','example.com')),
                          ('size',1024**3),('sha256','not-a-hash')]:
            with self.assertRaises(ValueError):self.tool.validate_pin(dict(pin,**{key:value}))

    def test_guest_report_cannot_choose_a_path_on_the_runner(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.assertEqual(root/'clean.json',self.tool.guest_output_path(root,'clean','clean.json'))
            for reported in ('../secret.json','/etc/shadow','clean/../../secret.json','other.json'):
                with self.assertRaises(ValueError):self.tool.guest_output_path(root,'clean',reported)

    def test_musl_baseline_requires_its_own_bytes_and_static_elf_observation(self):
        guest=dict(abi='musl',engine_sha256='f4dfee4e052704b1a7efdb7b6a4c43583ccaa062aec800b76224dae24eb2b69b',
                   elf=dict(no_interpreter=True,no_dynamic_section=True),loader=None)
        self.tool.validate_engine_kind(guest,'musl')
        for replacement in (dict(abi='glibc'),dict(engine_sha256=self.tool.ENGINE_SHA),
                            dict(elf=dict(no_interpreter=False,no_dynamic_section=True)),dict(loader='/lib/ld-musl-x86_64.so.1')):
            with self.assertRaises(ValueError):self.tool.validate_engine_kind(dict(guest,**replacement),'musl')
        with self.assertRaises(ValueError):self.tool.validate_engine_kind(guest,'other')

    def test_guest_checks_real_elf_headers_before_executing_the_requested_abi(self):
        spec=importlib.util.spec_from_file_location('guest_probe',ROOT/'.github/scripts/probe-guest-baseline.py')
        tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)
        data=bytearray(120);data[:6]=b'\x7fELF\x02\x01'
        struct.pack_into('<HH',data,16,2,62);struct.pack_into('<Q',data,32,64)
        struct.pack_into('<HH',data,54,56,1);struct.pack_into('<I',data,64,1)
        self.assertTrue(tool.inspect_binary(data,'musl')['no_interpreter'])
        with self.assertRaises(ValueError):tool.inspect_binary(data,'glibc')
        for kind in (2,3):
            modified=bytearray(data);struct.pack_into('<I',modified,64,kind)
            with self.assertRaises(ValueError):tool.inspect_binary(modified,'musl')
        modified=bytearray(data);struct.pack_into('<H',modified,18,183)
        with self.assertRaises(ValueError):tool.inspect_binary(modified,'musl')
        with self.assertRaises(ValueError):tool.inspect_binary(data[:64],'musl')
