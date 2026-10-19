"""Linux CLI contracts with explicitly simulated engine acquisition."""
import contextlib
import io
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from common import fixture
from posix_support import simulated_runtime
from twine_edge_overlap import cli, runtime


class LinuxCliTests(unittest.TestCase):
    def invoke(self,args):
        out,err=io.StringIO(),io.StringIO()
        with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
            code=cli.main(args)
        return code,out.getvalue(),err.getvalue()

    def test_external_relative_and_absolute_paths_warn_without_changing_success(self):
        with simulated_runtime('linux') as (root,transport,host):
            source=root/('hist'+chr(0xf3)+'ria com espacos.twee')
            source.write_bytes(fixture())
            previous=os.getcwd()
            try:
                os.chdir(root)
                for value in (source.name,str(source)):
                    code,out,err=self.invoke([value])
                    self.assertEqual(code,0,err)
                    self.assertIn('melhor esforço',err)
                    self.assertNotIn('Aviso:',out)
                    generated=Path(next(line.removeprefix('Arquivo gerado: ') for line in out.splitlines()
                                        if line.startswith('Arquivo gerado: ')))
                    self.assertTrue(generated.is_absolute() and generated.is_file())
                    self.assertTrue(generated.parent.samefile(root))
                    self.assertEqual(out.count(' -> '),3)
                self.assertEqual(source.read_bytes(),fixture())
                self.assertEqual(len(transport.calls),1)
            finally:
                os.chdir(previous)

    def test_abi_arch_or_interpreter_mismatch_never_acquires(self):
        for facts in (dict(translated=True),dict(bits=32),dict(python_version=(3,13)),dict(libc_family='musl'),dict(arch='aarch64')):
            # Host defaults in the helper only contain fields unaffected by these overrides.
            with simulated_runtime('linux',**facts) as (root,transport,host):
                code,out,err=self.invoke(['--prepare-runtime'])
                self.assertEqual(code,1)
                self.assertNotIn('prontos',out)
                self.assertEqual(transport.calls,[])

    def test_invalid_input_precedes_detection_and_prepare_remains_idempotent(self):
        with patch.object(runtime,'load_catalog',side_effect=AssertionError('classification before validation')):
            code,out,err=self.invoke(['missing-file.twee'])
            self.assertEqual(code,1)
        with simulated_runtime('linux') as (root,transport,host):
            for _ in range(2):
                code,out,err=self.invoke(['--prepare-runtime'])
                self.assertEqual(code,0,err)
                self.assertNotIn('Arquivo gerado:',out)
                self.assertNotIn(' -> ',out)
            self.assertEqual(len(transport.calls),1)
