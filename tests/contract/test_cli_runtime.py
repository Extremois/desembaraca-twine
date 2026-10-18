import contextlib
import io
import unittest
from unittest.mock import patch
from common import ROOT
from twine_edge_overlap import cli
from twine_edge_overlap.errors import DependencyError


class RuntimeCliTests(unittest.TestCase):
    def test_repair_uses_fixed_runtime_and_does_not_announce_story(self):
        stdout,stderr=io.StringIO(),io.StringIO()
        with patch.object(cli,'ensure_runtime') as prepare,contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
            self.assertEqual(cli.main(['--repair-runtime']),0)
        self.assertTrue(prepare.call_args.kwargs['force_repair'])
        self.assertIn('internet',stderr.getvalue())
        self.assertNotIn('Arquivo gerado:',stdout.getvalue())

    def test_dependency_error_and_cancel_have_no_partial_output(self):
        for error,code in ((DependencyError('Rede indisponível; nenhuma cópia gerada. Restabeleça a conexão e repita.'),1),(KeyboardInterrupt(),130)):
            stdout,stderr=io.StringIO(),io.StringIO()
            with patch.object(cli,'ensure_runtime',side_effect=error),contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
                self.assertEqual(cli.main(['--repair-runtime']),code)
            self.assertIn('Falha',stderr.getvalue())
            self.assertNotIn('Arquivo gerado:',stdout.getvalue())
            self.assertNotIn('Traceback',stderr.getvalue())

    def test_prepare_without_story_and_without_output_copy(self):
        stdout,stderr=io.StringIO(),io.StringIO()
        with patch.object(cli,'ensure_runtime',create=True) as prepare, contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
            self.assertEqual(cli.main(['--prepare-runtime']),0)
        prepare.assert_called_once()
        self.assertNotIn('Arquivo gerado:',stdout.getvalue())

    def test_conflicting_actions_and_input_do_not_prepare(self):
        for args in (['--prepare-runtime','story.twee'],['--prepare-runtime','--repair-runtime'],['--repair-runtime','story.twee']):
            with self.subTest(args=args),patch.object(cli,'ensure_runtime',create=True) as prepare,contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(cli.main(args),1)
                prepare.assert_not_called()

    def test_help_and_version_do_not_prepare(self):
        for arg in ('--help','--version'):
            with patch.object(cli,'ensure_runtime',create=True) as prepare,contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as result: cli.main([arg])
                self.assertEqual(result.exception.code,0)
                prepare.assert_not_called()
