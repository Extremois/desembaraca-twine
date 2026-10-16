import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from common import fixture
from twine_edge_overlap.cli import main


class CliSuccessTests(unittest.TestCase):
    def test_clean_unicode_path_and_three_metrics(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'história com espaços.twee'
            path.write_bytes(fixture())
            output=io.StringIO()
            with contextlib.redirect_stdout(output): code=main([str(path)])
            self.assertEqual(code,0)
            message=output.getvalue()
            self.assertIn('sucesso',message)
            self.assertIn(str(path.with_name(path.stem+'.layout.twee').resolve()),message)
            for label in ('Pares de arestas','Pares de nós','Pares aresta–nó'): self.assertIn(label,message)
            self.assertEqual(path.read_bytes(),fixture())
