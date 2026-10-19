import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import hashlib

HERE = Path(__file__).resolve().parents[2] / 'tools/runtime'


def tool():
    spec = importlib.util.spec_from_file_location('macos_ci', HERE / 'prepare-macos-ci.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MacosCITests(unittest.TestCase):
    def test_sdk_identity_binds_header_bytes_and_enforces_expansion_budget(self):
        module = tool()
        with tempfile.TemporaryDirectory() as directory:
            sdk = Path(directory)
            (sdk / 'header.h').write_bytes(b'first')
            first = module.sdk_identity(sdk)
            self.assertEqual(first['files'][0]['sha256'], hashlib.sha256(b'first').hexdigest())
            (sdk / 'header.h').write_bytes(b'other')
            self.assertNotEqual(first['sha256'], module.sdk_identity(sdk)['sha256'])
            with patch.object(module, 'MAX_SDK_BYTES', 2):
                with self.assertRaises(ValueError):
                    module.sdk_identity(sdk)

    def test_requires_matching_native_architecture_before_creating_output(self):
        module = tool()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'sdk'
            with patch.object(module.platform, 'system', return_value='Linux'):
                with self.assertRaises(ValueError):
                    module.prepare(output, 'aarch64')
            self.assertFalse(output.exists())

    def test_cmake_wrapper_uses_absolute_argv0_and_explicit_generators(self):
        module = tool()
        text = module.cmake_wrapper('/private/cmake', '/private/sdk', '/private/bison',
                                    '/private/flex', '/private/python', '/private/make', '/private/link-map.txt')
        self.assertIn("['/private/cmake',*args]", text)
        for argument in ('-DCMAKE_OSX_SYSROOT=/private/sdk', '-DBISON_EXECUTABLE=/private/bison',
                         '-DFLEX_EXECUTABLE=/private/flex', '-DPython3_EXECUTABLE=/private/python',
                         '-DCMAKE_MAKE_PROGRAM=/private/make',
                         '-DCMAKE_EXE_LINKER_FLAGS=-Wl,-map,/private/link-map.txt'):
            self.assertIn(argument, text)
