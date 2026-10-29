import json
import hashlib
import os
import platform
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
        environment='wsl' if 'microsoft' in platform.release().lower() else ('container' if Path('/.dockerenv').exists() else 'native')
        report=dict(kind='reference-corpus-regression-not-support-promotion',environment_kind=environment,
                    python=platform.python_version(),kernel=platform.release(),architecture=platform.machine(),
                    artifact_identity=handle.identity,executable_sha256=hashlib.sha256(handle.executable.read_bytes()).hexdigest(),cases=[])
        with tempfile.TemporaryDirectory() as folder:
            for case in cases:
                with self.subTest(case=case['case']):
                    source=Path(folder)/case['file']
                    original=fixture(case['case'])
                    source.write_bytes(original)
                    result=run(source,runtime_provider=lambda:handle)
                    generated=result.path.read_bytes()
                    row=dict(case=case['case'],input_sha256=hashlib.sha256(original).hexdigest(),output_sha256=hashlib.sha256(generated).hexdigest(),
                             before=list(result.before.values),after=list(result.after.values),passed=False)
                    report['cases'].append(row)
                    self.assertEqual(source.read_bytes(),original)
                    verify(parse(original),parse(generated))
                    self.assertEqual(list(result.before.values),case['before'])
                    self.assertTrue(all(a<=b for a,b in zip(result.after.values,result.before.values)))
                    if case['known_resolvable']:
                        self.assertEqual(result.after.values,(0,0,0))
                        self.assertEqual(result.status,'sucesso')
                    row.update(passed=True,original_preserved=True,semantics_preserved=True)
        report['passed']=len(report['cases'])==len(cases) and all(row['passed'] for row in report['cases'])
        if destination:=os.environ.get('TWINE_REFERENCE_REPORT'):
            with Path(destination).open('x',encoding='utf-8') as stream:
                json.dump(report,stream,indent=2,ensure_ascii=False)
                stream.write('\n')
