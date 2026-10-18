"""Darwin metadata simulation; real signing/Intel/ARM acceptance is separate."""
import contextlib
import io
import unittest
from common import fixture
from posix_support import simulated_runtime
from twine_edge_overlap import cli
from twine_edge_overlap.runtime_platform import HostEnvironment,cache_directory


class MacCliTests(unittest.TestCase):
    def test_translated_interpreter_is_rejected_without_bypass_instructions(self):
        out,err=io.StringIO(),io.StringIO()
        with simulated_runtime('darwin',translated=True) as (root,transport,host),contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
            self.assertEqual(cli.main(['--prepare-runtime']),1)
            self.assertEqual(transport.calls,[])
        for forbidden in ('xattr','spctl --master-disable','sudo','Instale Graphviz'):
            self.assertNotIn(forbidden,err.getvalue())

    def test_unicode_path_and_library_cache_convention(self):
        with simulated_runtime('darwin') as (root,transport,host):
            self.assertEqual(cache_directory(host,environ={},home=root),root.resolve()/'Library/Caches/DesembaracaTwine/runtimes/graphviz')
            source=root/('hist'+chr(0xf3)+'ria com espacos.twee')
            source.write_bytes(fixture())
            out,err=io.StringIO(),io.StringIO()
            with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
                self.assertEqual(cli.main([str(source)]),0,err.getvalue())
            self.assertIn(str(root),out.getvalue())
            self.assertIn('melhor esforço',err.getvalue())
            self.assertEqual(source.read_bytes(),fixture())
