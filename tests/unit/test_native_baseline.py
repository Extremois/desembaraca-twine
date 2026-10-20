import importlib.util
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
