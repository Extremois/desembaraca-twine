import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from common import ROOT


class KvmPreflightTests(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('kvm_probe',ROOT/'.github/scripts/probe-kvm.py')
        self.tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.tool)

    def test_api_requires_exact_version_and_userspace_memory_without_claiming_guest_execution(self):
        self.assertEqual('query-ready',self.tool.query_status(12,1))
        self.assertEqual('api-mismatch',self.tool.query_status(13,1))
        self.assertEqual('api-mismatch',self.tool.query_status(11,1))
        self.assertEqual('extension-unavailable',self.tool.query_status(12,0))
        self.assertEqual('extension-unavailable',self.tool.query_status(12,-1))

    def test_missing_regular_and_symlink_files_cannot_be_treated_as_a_kvm_device(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.assertEqual('not-present',self.tool.probe_device(root/'missing')['status'])
            device=root/'file';device.write_bytes(b'not a KVM device')
            self.assertEqual('not-character-device',self.tool.probe_device(device)['status'])
            self.assertEqual(b'not a KVM device',device.read_bytes())
            if os.name=='posix':
                link=root/'link';link.symlink_to(device)
                self.assertEqual('not-character-device',self.tool.probe_device(link)['status'])
