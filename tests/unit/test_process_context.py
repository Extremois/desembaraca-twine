from pathlib import Path
import os
import sys
import tempfile
import unittest
from common import ROOT
from twine_edge_overlap.engines.process import run_bounded


class ProcessContextTests(unittest.TestCase):
    def test_cwd_and_env_are_local_to_child(self):
        before=dict(os.environ)
        with tempfile.TemporaryDirectory() as folder:
            result=run_bounded([sys.executable,'-c','import os;print(os.getcwd());print(os.environ["TWINE_TEST_CONTEXT"])'], cwd=folder, env={**os.environ,'TWINE_TEST_CONTEXT':'child only'})
            self.assertEqual(result.returncode,0)
            self.assertIn(str(Path(folder)).encode(),result.stdout)
            self.assertIn(b'child only',result.stdout)
        self.assertEqual(dict(os.environ),before)
