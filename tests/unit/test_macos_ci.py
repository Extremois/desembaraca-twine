import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[2] / 'tools/runtime'


def tool():
    spec = importlib.util.spec_from_file_location('macos_ci', HERE / 'prepare-macos-ci.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MacosCITests(unittest.TestCase):
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
                                    '/private/flex', '/private/python', '/private/make')
        self.assertIn("['/private/cmake',*args]", text)
        for argument in ('-DCMAKE_OSX_SYSROOT=/private/sdk', '-DBISON_EXECUTABLE=/private/bison',
                         '-DFLEX_EXECUTABLE=/private/flex', '-DPython3_EXECUTABLE=/private/python',
                         '-DCMAKE_MAKE_PROGRAM=/private/make'):
            self.assertIn(argument, text)
