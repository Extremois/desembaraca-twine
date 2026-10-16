import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from common import fixture
from twine_edge_overlap.cli import main
from twine_edge_overlap.errors import DependencyError
from twine_edge_overlap.errors import WriteError


class CliFailureTests(unittest.TestCase):
    def invoke(self,args,code=1):
        stdout,stderr=io.StringIO(),io.StringIO()
        with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
            actual=main(args)
        self.assertEqual(actual,code)
        self.assertIn('Falha',stderr.getvalue())
        self.assertNotIn('Arquivo gerado:',stdout.getvalue())
        self.assertNotIn('Traceback',stderr.getvalue())
        return stderr.getvalue()

    def test_zero_and_multiple_inputs(self):
        for args in ([],['a.twee','b.twee']): self.assertIn('exatamente um',self.invoke(args))

    def test_missing_directory_and_unsupported_extension(self):
        with tempfile.TemporaryDirectory() as folder:
            for value in (str(Path(folder)/'missing.twee'),folder,str(Path(folder)/'story.txt')):
                with self.subTest(value=value): self.invoke([value])

    def test_corrupt_reference_duplicate_and_invalid_layout(self):
        invalid=[b'\xff',b':: StoryTitle\nx\n:: StoryData\nno-json',
                 fixture().replace(b'[[P1]]',b'[[missing]]'),
                 fixture()+b'\n:: P0 {"position":"0,0","size":"100,100"}\n',
                 fixture().replace(b'"position":',b'"position": null, "unrecognized":'),
                 fixture().replace(b'"size": "100,100"',b'"size": "NaN,100"')]
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'bad.twee'
            for data in invalid:
                with self.subTest(data=data[:30]):
                    source.write_bytes(data)
                    self.invoke([str(source)])
                    self.assertEqual(source.read_bytes(),data)
            self.assertEqual(list(Path(folder).glob('*.layout*.twee')),[])

    def test_missing_dependency_and_interruption(self):
        with patch('twine_edge_overlap.cli.run',side_effect=DependencyError('Instale Graphviz')):
            self.assertIn('Instale Graphviz',self.invoke(['a.twee']))
        with patch('twine_edge_overlap.cli.run',side_effect=KeyboardInterrupt):
            self.invoke(['a.twee'],code=130)

    def test_strict_json_rejects_nonstandard_constants_in_unknown_fields(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'bad.twee'
            for constant in (b'NaN',b'Infinity',b'-Infinity'):
                data=fixture().replace(b'"retain": true',b'"retain": '+constant)
                source.write_bytes(data)
                with self.subTest(constant=constant): self.invoke([str(source)])
            self.assertEqual(list(Path(folder).glob('*.layout*.twee')),[])

    def test_write_failure_and_cancellation_never_announce_output(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'story.twee';source.write_bytes(fixture())
            with patch('twine_edge_overlap.application.publish',side_effect=WriteError('Sem espaço na pasta')):
                self.assertIn('Sem espaço',self.invoke([str(source)]))
            with patch('twine_edge_overlap.files.os.fsync',side_effect=KeyboardInterrupt):
                self.invoke([str(source)],code=130)
            self.assertEqual(list(Path(folder).iterdir()),[source])
            self.assertEqual(source.read_bytes(),fixture())

    def test_unexpected_processing_error_is_reported_without_traceback(self):
        with patch('twine_edge_overlap.cli.run',side_effect=RuntimeError('controlled unexpected error')):
            self.assertIn('RuntimeError',self.invoke(['a.twee']))

    def test_oversized_header_is_refused(self):
        data=fixture().replace(b'"retain": true',b'"retain": "'+b'x'*9000+b'"')
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'bad.twee';source.write_bytes(data)
            self.invoke([str(source)])
            self.assertEqual(list(Path(folder).glob('*.layout*.twee')),[])
