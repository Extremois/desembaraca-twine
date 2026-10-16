import json
from pathlib import Path
import tempfile
import unittest
from common import ROOT,fixture
from twine_edge_overlap.application import run
from twine_edge_overlap.formats.profile import parse,verify
from twine_edge_overlap.runtime import ensure_runtime


class ReferenceAcceptanceTests(unittest.TestCase):
    def test_reference_cases_and_non_regression(self):
        cases=json.loads((ROOT/'tests/fixtures/cases.json').read_text())
        handle=ensure_runtime()
        with tempfile.TemporaryDirectory() as folder:
            for case in cases:
                with self.subTest(case=case['case']):
                    source=Path(folder)/case['file']
                    original=fixture(case['case'])
                    source.write_bytes(original)
                    result=run(source,runtime_provider=lambda:handle)
                    self.assertEqual(source.read_bytes(),original)
                    verify(parse(original),parse(result.path.read_bytes()))
                    self.assertEqual(list(result.before.values),case['before'])
                    self.assertTrue(all(a<=b for a,b in zip(result.after.values,result.before.values)))
                    if case['known_resolvable']:
                        self.assertEqual(result.after.values,(0,0,0))
                        self.assertEqual(result.status,'sucesso')
