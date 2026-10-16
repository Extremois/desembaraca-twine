import contextlib
import io
from pathlib import Path
import unittest
from unittest.mock import patch
from common import fixture
from twine_edge_overlap.cli import main
from twine_edge_overlap.domain.model import Metrics,Result


class CliLimitationTests(unittest.TestCase):
    def test_each_kind_of_remaining_conflict_has_limited_code_and_counts(self):
        for values in ((1,0,0),(0,1,0),(0,0,1)):
            with self.subTest(values=values):
                result=Result('limitações',Path('copy.twee').resolve(),Metrics(*values),Metrics(*values),'Nenhuma melhoria admissível')
                stdout=io.StringIO()
                with patch('twine_edge_overlap.cli.run',return_value=result),contextlib.redirect_stdout(stdout):
                    code=main(['input.twee'])
                self.assertEqual(code,2)
                self.assertIn('limitações',stdout.getvalue())
                self.assertIn(str(result.path),stdout.getvalue())
                for label in ('Pares de arestas','Pares de nós','Pares aresta–nó'):
                    self.assertIn(label,stdout.getvalue())
                self.assertNotIn('impossível',stdout.getvalue())
